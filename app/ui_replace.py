import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .theme import *
from .ui_convert import LogBox, SectionCard
from tools.labelsto import (
    apply_mapping_to_folder,
    build_remap_from_new_classes,
    read_classes_file,
    reorder_classes,
    remap_classes_by_index,
    write_classes_file,
)


class ReplacePage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(top, text="类别重整", bg=BG, fg=TEXT, font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="w")
        tk.Label(top, text="单类替换、多类合并、删除、重排序、按新 classes.txt 自动重映射", bg=BG, fg=MUTED, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        left = SectionCard(body, "操作参数")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_propagate(False)

        self.var_folder = tk.StringVar()
        self.var_classes = tk.StringVar()
        self.var_mode = tk.StringVar(value="single")
        self.var_src = tk.StringVar(value="0")
        self.var_dst = tk.StringVar(value="1")
        self.var_merge_groups = tk.StringVar(value="0,1;2,3")
        self.var_delete = tk.StringVar(value="")
        self.var_order = tk.StringVar(value="")
        self.var_new_classes = tk.StringVar(value="")

        form = tk.Frame(left, bg=PANEL)
        form.pack(fill="x", padx=16, pady=(0, 12))
        form.grid_columnconfigure(1, weight=1)

        self._file_row(form, 0, "标注文件夹", self.var_folder, self.browse_folder)
        self._file_row(form, 1, "classes.txt", self.var_classes, self.browse_classes)

        mode_box = tk.LabelFrame(left, text="模式", bg=PANEL, fg=TEXT, padx=10, pady=10)
        mode_box.pack(fill="x", padx=16, pady=(0, 12))
        modes = [
            ("single", "单类替换"),
            ("merge", "多类合并"),
            ("delete", "类别删除"),
            ("reorder", "类别重排序"),
            ("remap", "按新 classes.txt 重映射"),
        ]
        for value, label in modes:
            ttk.Radiobutton(mode_box, text=label, value=value, variable=self.var_mode, command=self.update_mode).pack(anchor="w", pady=2)

        self.param_box = tk.Frame(left, bg=PANEL)
        self.param_box.pack(fill="x", padx=16, pady=(0, 12))

        self.preview = tk.Label(left, text="", bg=PANEL, fg=PRIMARY, font=("Microsoft YaHei UI", 9, "bold"), wraplength=300, justify="left")
        self.preview.pack(fill="x", padx=16, pady=(0, 12))

        actions = tk.Frame(left, bg=PANEL)
        actions.pack(fill="x", padx=16, pady=(0, 12))
        ttk.Button(actions, text="开始执行", style="Primary.TButton", command=self.run).pack(fill="x")
        ttk.Button(actions, text="清空日志", command=self.clear_log).pack(fill="x", pady=(8, 0))

        log_card = SectionCard(left, "处理日志")
        log_card.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.log = LogBox(log_card, height=16)
        self.log.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.update_mode()

    def _file_row(self, parent, row, label, var, command):
        tk.Label(parent, text=label, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 10)).grid(row=row, column=0, sticky="w", pady=8)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=10, pady=8)
        ttk.Button(parent, text="浏览", command=command).grid(row=row, column=2, pady=8)

    def browse_folder(self):
        p = filedialog.askdirectory(title="选择标注文件夹")
        if p:
            self.var_folder.set(p)

    def browse_classes(self):
        p = filedialog.askopenfilename(title="选择 classes.txt", filetypes=[("TXT", "*.txt"), ("All", "*.*")])
        if p:
            self.var_classes.set(p)

    def clear_log(self):
        self.log.clear()

    def update_mode(self):
        for child in self.param_box.winfo_children():
            child.destroy()

        mode = self.var_mode.get()
        if mode == "single":
            self._add_param("源 ID", self.var_src)
            self._add_param("目标 ID", self.var_dst)
            self.preview.config(text="示例：0 -> 2")
        elif mode == "merge":
            self._add_param("合并组", self.var_merge_groups)
            self.preview.config(text="格式：0,1;2,3 表示把两组分别合并为新类别")
        elif mode == "delete":
            self._add_param("删除 ID", self.var_delete)
            self.preview.config(text="格式：0,2,5 表示删除这些类别")
        elif mode == "reorder":
            self._add_param("新顺序", self.var_order)
            self.preview.config(text="格式：2,0,1 表示按这个顺序重排 classes.txt 和标签 ID")
        else:
            self._add_param("新 classes.txt", self.var_new_classes)
            self.preview.config(text="按新 classes.txt 名称顺序自动重映射旧标签")

    def _add_param(self, label, var):
        row = tk.Frame(self.param_box, bg=PANEL)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 10)).pack(anchor="w")
        ttk.Entry(row, textvariable=var).pack(fill="x", pady=(4, 0))

    def run(self):
        folder = self.var_folder.get().strip()
        classes_path = self.var_classes.get().strip()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("错误", "请选择有效标注文件夹")
            return

        mode = self.var_mode.get()
        self.log.clear()

        def task():
            try:
                if mode == "single":
                    self._run_single(folder, classes_path)
                elif mode == "merge":
                    self._run_merge(folder, classes_path)
                elif mode == "delete":
                    self._run_delete(folder, classes_path)
                elif mode == "reorder":
                    self._run_reorder(folder, classes_path)
                else:
                    self._run_remap(folder, classes_path)
            except Exception as e:
                self.after(0, lambda: self.log.write(f"\n[错误] {e}\n"))

        threading.Thread(target=task, daemon=True).start()

    def _run_single(self, folder, classes_path):
        src = int(self.var_src.get().strip())
        dst = int(self.var_dst.get().strip())
        classes = read_classes_file(classes_path) if classes_path else []
        mapping = {src: dst}
        results = apply_mapping_to_folder(folder, mapping)
        if classes_path and classes:
            new_classes = remap_classes_by_index(classes, mapping)
            write_classes_file(classes_path, new_classes)
        self.after(0, lambda: self._finish(results, classes_path, classes))

    def _run_merge(self, folder, classes_path):
        groups_text = self.var_merge_groups.get().strip()
        groups = []
        target_names = []
        for idx, chunk in enumerate(groups_text.split(";")):
            ids = [int(x.strip()) for x in chunk.split(",") if x.strip()]
            if ids:
                groups.append(ids)
                target_names.append(f"merged_{idx}")
        if not groups:
            raise ValueError("请填写有效合并组")

        classes = read_classes_file(classes_path) if classes_path else []
        mapping = {}
        for idx, group in enumerate(groups):
            target_id = len(classes) + idx
            for old_id in group:
                mapping[old_id] = target_id
        results = apply_mapping_to_folder(folder, mapping)
        new_classes = list(classes) + target_names
        if classes_path:
            write_classes_file(classes_path, new_classes)
        self.after(0, lambda: self._finish(results, classes_path, new_classes))

    def _run_delete(self, folder, classes_path):
        delete_ids = [int(x.strip()) for x in self.var_delete.get().split(",") if x.strip()]
        mapping = {cid: None for cid in delete_ids}
        results = apply_mapping_to_folder(folder, mapping)
        classes = read_classes_file(classes_path) if classes_path else []
        if classes:
            new_classes = [name for idx, name in enumerate(classes) if idx not in set(delete_ids)]
            if classes_path:
                write_classes_file(classes_path, new_classes)
        else:
            new_classes = []
        self.after(0, lambda: self._finish(results, classes_path, new_classes))

    def _run_reorder(self, folder, classes_path):
        order = [int(x.strip()) for x in self.var_order.get().split(",") if x.strip()]
        classes = read_classes_file(classes_path)
        if not classes:
            raise ValueError("请先提供 classes.txt")
        new_classes = reorder_classes(classes, order)
        old_to_new = {old: new for new, old in enumerate(order) if 0 <= old < len(classes)}
        results = apply_mapping_to_folder(folder, old_to_new)
        if classes_path:
            write_classes_file(classes_path, new_classes)
        self.after(0, lambda: self._finish(results, classes_path, new_classes))

    def _run_remap(self, folder, classes_path):
        new_classes_path = self.var_new_classes.get().strip()
        if not new_classes_path or not os.path.exists(new_classes_path):
            raise ValueError("请选择新的 classes.txt")
        old_classes = read_classes_file(classes_path)
        new_classes = read_classes_file(new_classes_path)
        mapping = build_remap_from_new_classes(old_classes, new_classes)
        results = apply_mapping_to_folder(folder, mapping)
        if classes_path:
            write_classes_file(classes_path, new_classes)
        self.after(0, lambda: self._finish(results, classes_path, new_classes))

    def _finish(self, results, classes_path, classes):
        updated = sum(1 for r in results if r.modified)
        changed = sum(r.changed_count for r in results)
        self.log.write(f"完成，更新文件 {updated} 个，修改标注 {changed} 处\n")
        if classes_path and classes:
            self.log.write(f"已同步更新类别文件: {classes_path}\n")
