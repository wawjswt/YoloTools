import json
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .theme import *
from .ui_strings import STRINGS
from tools.conversion_service import convert_file
from tools.convert import collect_classes, load_class_file, parse_xml


class LogBox(tk.Frame):
    def __init__(self, master, height=16):
        super().__init__(master, bg=PANEL)
        self.txt = tk.Text(self, wrap=tk.WORD, height=height, font=("Consolas", 10),
                           bg="#08111d", fg="#dbeafe", insertbackground="white",
                           relief="flat", borderwidth=0)
        self.txt.pack(fill="both", expand=True)

    def write(self, s):
        self.txt.insert(tk.END, s)
        self.txt.see(tk.END)

    def flush(self):
        pass

    def clear(self):
        self.txt.delete("1.0", tk.END)


class SectionCard(tk.Frame):
    def __init__(self, master, title, subtitle=""):
        super().__init__(master, bg=PANEL, highlightthickness=1, highlightbackground=PRIMARY)
        head = tk.Frame(self, bg=PANEL)
        head.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(head, text=title, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(head, text=subtitle, bg=PANEL, fg=MUTED, font=("Microsoft YaHei UI", 9)).pack(anchor="w", pady=(4, 0))


class ConvertPage(tk.Frame):
    FORMATS = ["YOLO", "VOC XML", "LabelMe"]

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(top, text=STRINGS["convert_title"], bg=BG, fg=TEXT, font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="w")
        tk.Label(top, text="支持单文件与批量目录，输出带详细日志、转换摘要和类别信息。", bg=BG, fg=MUTED, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        card = SectionCard(body, STRINGS["convert_card"], STRINGS["convert_card_sub"])
        card.pack(fill="x")

        self.var_input = tk.StringVar()
        self.var_output = tk.StringVar()
        self.var_classes = tk.StringVar()
        self.var_save_classes = tk.StringVar()
        self.var_source_format = tk.StringVar(value="VOC XML")
        self.var_target_format = tk.StringVar(value="YOLO")
        self.var_input_mode = tk.StringVar(value="folder")

        form = tk.Frame(card, bg=PANEL)
        form.pack(fill="x", padx=16, pady=(0, 16))
        form.grid_columnconfigure(1, weight=1)

        self._row(form, 0, STRINGS["input_mode"], self.var_input_mode, ["folder", "file"], is_combo=True)
        self._row(form, 1, STRINGS["source_format"], self.var_source_format, self.FORMATS, is_combo=True)
        self._row(form, 2, STRINGS["target_format"], self.var_target_format, self.FORMATS, is_combo=True)
        self._row(form, 3, STRINGS["input_path"], self.var_input, self.browse_input)
        self._row(form, 4, STRINGS["output_path"], self.var_output, self.browse_output)
        self._row(form, 5, STRINGS["classes_file"], self.var_classes, self.browse_classes)
        self._row(form, 6, STRINGS["save_classes"], self.var_save_classes, self.browse_save_classes)

        actions = tk.Frame(card, bg=PANEL)
        actions.pack(fill="x", padx=16, pady=(0, 16))
        ttk.Button(actions, text=STRINGS["run_convert"], style="Primary.TButton", command=self.run).pack(side="left")
        ttk.Button(actions, text=STRINGS["clear_log"], command=self.clear_log).pack(side="left", padx=8)

        log_card = SectionCard(body, STRINGS["log_title"])
        log_card.pack(fill="both", expand=True, pady=(16, 0))
        self.log = LogBox(log_card, height=16)
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _row(self, parent, row, label, var, values_or_cmd, is_combo=False):
        tk.Label(parent, text=label, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 10)).grid(row=row, column=0, sticky="w", pady=8)
        if is_combo:
            ttk.Combobox(parent, textvariable=var, values=values_or_cmd, state="readonly").grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            ttk.Label(parent, text="").grid(row=row, column=2)
        else:
            ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=10, pady=8)
            ttk.Button(parent, text=STRINGS["browse"], command=values_or_cmd).grid(row=row, column=2, pady=8)

    def browse_input(self):
        if self.var_input_mode.get() == "folder":
            p = filedialog.askdirectory(title="选择输入目录")
        else:
            p = filedialog.askopenfilename(title="选择输入文件", filetypes=[("All", "*.*")])
        if p:
            self.var_input.set(p)

    def browse_output(self):
        p = filedialog.askdirectory(title="选择输出目录")
        if p:
            self.var_output.set(p)

    def browse_classes(self):
        p = filedialog.askopenfilename(title="选择 classes.txt", filetypes=[("TXT", "*.txt"), ("All", "*.*")])
        if p:
            self.var_classes.set(p)

    def browse_save_classes(self):
        p = filedialog.asksaveasfilename(title="保存 classes.txt", defaultextension=".txt", filetypes=[("TXT", "*.txt")])
        if p:
            self.var_save_classes.set(p)

    def clear_log(self):
        self.log.clear()

    def run(self):
        input_path = self.var_input.get().strip()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("错误", STRINGS["convert_missing_input"])
            return

        src = self.var_source_format.get()
        dst = self.var_target_format.get()
        self.log.clear()
        old_stdout = os.sys.stdout
        os.sys.stdout = self.log
        self.log.write(f"[INFO] src={src} dst={dst}\n")
        self.log.write(f"[INFO] input={input_path}\n")
        self.log.write(f"[INFO] mode={self.var_input_mode.get()} out={self.var_output.get().strip() or '(default)'}\n")

        def task():
            try:
                out_dir = self.var_output.get().strip() or None
                classes_file = self.var_classes.get().strip() or None
                save_classes = self.var_save_classes.get().strip() or None
                if classes_file and os.path.exists(classes_file):
                    print(f"已加载类别文件: {classes_file}")
                outputs = convert_file(src, dst, input_path, out_dir, classes_file)
                if not outputs:
                    print("未生成任何输出文件")
                else:
                    print(f"完成，输出 {len(outputs)} 个文件")
                    for item in outputs[:20]:
                        print(f"  - {item}")
                if src == "VOC XML" and dst == "YOLO" and not classes_file:
                    if os.path.isfile(input_path):
                        _, objs = parse_xml(input_path)
                        class_list = sorted({o["name"] for o in objs})
                    else:
                        class_list = collect_classes(input_path)
                    if class_list:
                        if not save_classes:
                            base_dir = os.path.dirname(input_path) if os.path.isfile(input_path) else input_path
                            save_classes = os.path.join(out_dir or base_dir, "classes.txt")
                        os.makedirs(os.path.dirname(save_classes) or ".", exist_ok=True)
                        with open(save_classes, "w", encoding="utf-8") as f:
                            f.write("\n".join(class_list))
                        print(f"类别已保存到: {save_classes}")
                        print(f"类别数: {len(class_list)}")
            except Exception as e:
                print(f"\n[错误] {e}")
            finally:
                os.sys.stdout = old_stdout

        threading.Thread(target=task, daemon=True).start()
