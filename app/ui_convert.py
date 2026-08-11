import os
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .theme import *
from tools.convert import collect_classes, load_class_file, parse_xml, process_folder, process_single_file


class LogBox(tk.Frame):
    def __init__(self, master, height=16):
        super().__init__(master, bg=PANEL)
        self.txt = tk.Text(self, wrap=tk.WORD, height=height, font=("Consolas", 10),
                           bg="#eaf0f7", fg="#0f172a", insertbackground="black",
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
        super().__init__(master, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        head = tk.Frame(self, bg=PANEL)
        head.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(head, text=title, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(head, text=subtitle, bg=PANEL, fg=MUTED, font=("Microsoft YaHei UI", 9)).pack(anchor="w", pady=(4, 0))


class ConvertPage(tk.Frame):
    FORMATS = ["YOLO", "VOC XML", "COCO JSON", "LabelMe", "DOTA"]

    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(top, text="格式转换", bg=BG, fg=TEXT, font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="w")
        tk.Label(top, text="先保留统一入口，后续可继续扩展到 COCO / LabelMe / VOC / DOTA",
                 bg=BG, fg=MUTED, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        card = SectionCard(body, "转换参数", "当前先实现 XML -> YOLO，其他格式预留入口")
        card.pack(fill="x")

        self.var_input = tk.StringVar()
        self.var_output = tk.StringVar()
        self.var_classes = tk.StringVar()
        self.var_save_classes = tk.StringVar()
        self.var_source_format = tk.StringVar(value="VOC XML")
        self.var_target_format = tk.StringVar(value="YOLO")

        form = tk.Frame(card, bg=PANEL)
        form.pack(fill="x", padx=16, pady=(0, 16))
        form.grid_columnconfigure(1, weight=1)

        rows = [
            ("源格式", self.var_source_format, None),
            ("目标格式", self.var_target_format, None),
            ("输入文件/文件夹", self.var_input, self.browse_input),
            ("输出文件夹", self.var_output, self.browse_output),
            ("类别文件", self.var_classes, self.browse_classes),
            ("保存类别路径", self.var_save_classes, self.browse_save_classes),
        ]

        for i, (label, var, cmd) in enumerate(rows):
            tk.Label(form, text=label, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 10)).grid(row=i, column=0, sticky="w", pady=8)
            if label in ("源格式", "目标格式"):
                ttk.Combobox(form, textvariable=var, values=self.FORMATS, state="readonly").grid(row=i, column=1, sticky="ew", padx=10, pady=8)
                ttk.Label(form, text="").grid(row=i, column=2)
            else:
                ttk.Entry(form, textvariable=var).grid(row=i, column=1, sticky="ew", padx=10, pady=8)
                ttk.Button(form, text="浏览", command=cmd).grid(row=i, column=2, pady=8)

        actions = tk.Frame(card, bg=PANEL)
        actions.pack(fill="x", padx=16, pady=(0, 16))
        ttk.Button(actions, text="开始转换", style="Primary.TButton", command=self.run).pack(side="left")
        ttk.Button(actions, text="清空日志", command=self.clear_log).pack(side="left", padx=8)

        log_card = SectionCard(body, "运行日志")
        log_card.pack(fill="both", expand=True, pady=(16, 0))
        self.log = LogBox(log_card, height=16)
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def browse_input(self):
        if messagebox.askyesno("选择输入", "是否选择文件夹？\n点“否”则选择单个文件。"):
            p = filedialog.askdirectory(title="选择输入文件夹")
        else:
            p = filedialog.askopenfilename(title="选择输入文件", filetypes=[("All", "*.*")])
        if p:
            self.var_input.set(p)

    def browse_output(self):
        p = filedialog.askdirectory(title="选择输出文件夹")
        if p:
            self.var_output.set(p)

    def browse_classes(self):
        p = filedialog.askopenfilename(title="选择类别文件", filetypes=[("TXT", "*.txt"), ("All", "*.*")])
        if p:
            self.var_classes.set(p)

    def browse_save_classes(self):
        p = filedialog.asksaveasfilename(title="保存类别文件", defaultextension=".txt", filetypes=[("TXT", "*.txt")])
        if p:
            self.var_save_classes.set(p)

    def clear_log(self):
        self.log.clear()

    def run(self):
        input_path = self.var_input.get().strip()
        if not input_path or not os.path.exists(input_path):
            messagebox.showerror("错误", "请输入有效输入路径")
            return

        src = self.var_source_format.get()
        dst = self.var_target_format.get()
        self.log.clear()
        old_stdout = sys.stdout
        sys.stdout = self.log

        def task():
            try:
                if src != "VOC XML" or dst != "YOLO":
                    print(f"[提示] 当前仅实现 VOC XML -> YOLO，已选择: {src} -> {dst}")
                    return

                out_dir = self.var_output.get().strip() or None
                class_file = self.var_classes.get().strip() or None
                save_classes = self.var_save_classes.get().strip() or None

                if class_file:
                    class_map = load_class_file(class_file)
                    if class_map is None:
                        return
                    print(f"已加载类别文件: {class_file}")
                else:
                    if os.path.isfile(input_path):
                        _, objs = parse_xml(input_path)
                        class_list = sorted({o["name"] for o in objs})
                    else:
                        class_list = collect_classes(input_path)

                    if not class_list:
                        print("未找到任何类别")
                        return

                    class_map = {name: idx for idx, name in enumerate(class_list)}
                    print(f"自动收集类别 {len(class_list)} 个: {class_list}")

                    if not save_classes:
                        base_dir = os.path.dirname(input_path) if os.path.isfile(input_path) else input_path
                        save_classes = os.path.join(out_dir or base_dir, "classes.txt")

                    os.makedirs(os.path.dirname(save_classes) or ".", exist_ok=True)
                    with open(save_classes, "w", encoding="utf-8") as f:
                        f.write("\n".join(class_list))
                    print(f"类别已保存到: {save_classes}")

                if os.path.isfile(input_path):
                    process_single_file(input_path, out_dir, class_map)
                else:
                    process_folder(input_path, out_dir, class_map)
            except Exception as e:
                print(f"\n[错误] {e}")
            finally:
                sys.stdout = old_stdout

        threading.Thread(target=task, daemon=True).start()
