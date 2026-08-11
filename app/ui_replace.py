import os
import tkinter as tk
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
        self.preview_results = None
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(top, text="类别重整", bg=BG, fg=TEXT, font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="w")
        tk.Label(top, text="先预览映射结果，再决定是否写回文件。输出会包含修改量、受影响文件和动作摘要。", bg=BG, fg=MUTED, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(4, 0))

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
        ttk.Button(actions, text="预览结果", style="Primary.TButton", command=self.preview_run).pack(fill="x")
        ttk.Button(actions, text="应用并落盘", command=self.apply_run).pack(fill="x", pady=(8, 0))
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
            self.preview.config(text="示例: 0 -> 2")
        elif mode == "merge":
            self._add_param("合并组", self.var_merge_groups)
            self.preview.config(text="示例: 0,1;2,3 表示两组分别合并为新类")
        elif mode == "delete":
            self._add_param("删除 ID", self.var_delete)
            self.preview.config(text="示例: 0,2,5 表示删除这些类别")
        elif mode == "reorder":
            self._add_param("新顺序", self.var_order)
            self.preview.config(text="示例: 2,0,1 表示按该顺序重排 classes.txt 和标签 ID")
        else:
            self._add_param("新 classes.txt", self.var_new_classes)
            self.preview.config(text="按新 classes.txt 的名称顺序自动重映射旧标签")

    def _add_param(self, label, var):
        row = tk.Frame(self.param_box, bg=PANEL)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 10)).pack(anchor="w")
        ttk.Entry(row, textvariable=var).pack(fill="x", pady=(4, 0))

    def _validate(self):
        folder = self.var_folder.get().strip()
        if not folder or not os.path.isdir(folder):
            raise ValueError("请选择有效标注文件夹")
        return folder

    def preview_run(self):
        try:
            folder = self._validate()
            classes_path = self.var_classes.get().strip()
            mode = self.var_mode.get()
            self.log.clear()
            results = self._compute(folder, classes_path, mode, preview_only=True)
            self.preview_results = results
            self.log.write("[PREVIEW] 仅模拟，不写盘\n")
            self.log.write("\n".join(results["lines"]) + "\n")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def apply_run(self):
        try:
            folder = self._validate()
            classes_path = self.var_classes.get().strip()
            mode = self.var_mode.get()
            self.log.clear()
            results = self._compute(folder, classes_path, mode, preview_only=False)
            self.log.write("[APPLY] 已写入文件\n")
            self.log.write("\n".join(results["lines"]) + "\n")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def _compute(self, folder, classes_path, mode, preview_only=False):
        lines = []
        if mode == "single":
            src = int(self.var_src.get().strip())
            dst = int(self.var_dst.get().strip())
            mapping = {src: dst}
            lines.append(f"映射: {src} -> {dst}")
            if preview_only:
                results = apply_mapping_to_folder(folder, mapping)
            else:
                results = apply_mapping_to_folder(folder, mapping)
                if classes_path and os.path.exists(classes_path):
                    classes = read_classes_file(classes_path)
                    if classes:
                        new_classes = remap_classes_by_index(classes, mapping)
                        write_classes_file(classes_path, new_classes)
            lines.extend([f"{r.path}: changed={r.changed_count}" for r in results[:20]])
            lines.append(f"文件数: {len(results)}")
            lines.append(f"修改文件: {sum(1 for r in results if r.modified)}")
            return {"lines": lines}

        if mode == "merge":
            groups_text = self.var_merge_groups.get().strip()
            groups = []
            for chunk in groups_text.split(";"):
                ids = [int(x.strip()) for x in chunk.split(",") if x.strip()]
                if ids:
                    groups.append(ids)
            if not groups:
                raise ValueError("请输入有效合并组")
            lines.append(f"合并组: {groups}")
            classes = read_classes_file(classes_path) if classes_path else []
            mapping = {}
            for idx, group in enumerate(groups):
                target_id = len(classes) + idx
                for old_id in group:
                    mapping[old_id] = target_id
            results = apply_mapping_to_folder(folder, mapping)
            if not preview_only and classes_path:
                new_classes = list(classes) + [f"merged_{i}" for i in range(len(groups))]
                write_classes_file(classes_path, new_classes)
            lines.extend([f"{r.path}: changed={r.changed_count}" for r in results[:20]])
            lines.append(f"文件数: {len(results)}")
            lines.append(f"修改文件: {sum(1 for r in results if r.modified)}")
            return {"lines": lines}

        if mode == "delete":
            delete_ids = [int(x.strip()) for x in self.var_delete.get().split(",") if x.strip()]
            mapping = {cid: None for cid in delete_ids}
            lines.append(f"删除: {delete_ids}")
            results = apply_mapping_to_folder(folder, mapping)
            if not preview_only and classes_path and os.path.exists(classes_path):
                classes = read_classes_file(classes_path)
                if classes:
                    new_classes = [name for idx, name in enumerate(classes) if idx not in set(delete_ids)]
                    write_classes_file(classes_path, new_classes)
            lines.extend([f"{r.path}: changed={r.changed_count}" for r in results[:20]])
            lines.append(f"文件数: {len(results)}")
            lines.append(f"修改文件: {sum(1 for r in results if r.modified)}")
            return {"lines": lines}

        if mode == "reorder":
            order = [int(x.strip()) for x in self.var_order.get().split(",") if x.strip()]
            classes = read_classes_file(classes_path)
            if not classes:
                raise ValueError("请先提供 classes.txt")
            new_classes = reorder_classes(classes, order)
            old_to_new = {old: new for new, old in enumerate(order) if 0 <= old < len(classes)}
            lines.append(f"新顺序: {order}")
            results = apply_mapping_to_folder(folder, old_to_new)
            if not preview_only and classes_path:
                write_classes_file(classes_path, new_classes)
            lines.extend([f"{r.path}: changed={r.changed_count}" for r in results[:20]])
            lines.append(f"文件数: {len(results)}")
            lines.append(f"修改文件: {sum(1 for r in results if r.modified)}")
            return {"lines": lines}

        new_classes_path = self.var_new_classes.get().strip()
        if not new_classes_path or not os.path.exists(new_classes_path):
            raise ValueError("请选择新的 classes.txt")
        old_classes = read_classes_file(classes_path)
        new_classes = read_classes_file(new_classes_path)
        mapping = build_remap_from_new_classes(old_classes, new_classes)
        lines.append(f"新 classes.txt: {new_classes_path}")
        results = apply_mapping_to_folder(folder, mapping)
        if not preview_only and classes_path:
            write_classes_file(classes_path, new_classes)
        lines.extend([f"{r.path}: changed={r.changed_count}" for r in results[:20]])
        lines.append(f"文件数: {len(results)}")
        lines.append(f"修改文件: {sum(1 for r in results if r.modified)}")
        return {"lines": lines}
