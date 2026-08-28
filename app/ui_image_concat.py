import os
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageTk

from .theme import *
from tools.image_concat_service import concat_images, concat_images_grid, get_image_info, tile_image


IMAGE_FILETYPES = [("图片文件", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"), ("所有文件", "*.*")]


class ImageConcatWindow:
    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("图片拼接")
        self.window.geometry("1180x800")
        self.window.minsize(980, 660)
        self.window.protocol("WM_DELETE_WINDOW", self.close)
        self.mode = tk.StringVar(value="single")
        self.input_path = tk.StringVar()
        self.rows = tk.StringVar(value="2")
        self.columns = tk.StringVar(value="2")
        self.direction = tk.StringVar(value="horizontal")
        self.grid_rows = tk.StringVar(value="2")
        self.grid_columns = tk.StringVar(value="2")
        self.gap = tk.StringVar(value="0")
        self.alignment = tk.StringVar(value="start")
        self.background = (0, 0, 0)
        self.background_text = tk.StringVar(value="#000000")
        self.input_info = tk.StringVar(value="尚未选择图片")
        self.output_info = tk.StringVar(value="设置参数后生成预览")
        self.status = tk.StringVar(value="请选择图片")
        self.source = None
        self.sources = []
        self.preview = None
        self.preview_photo = None
        self._build()
        self._update_multi_layout_controls()
        for variable in (self.rows, self.columns, self.direction, self.grid_rows, self.grid_columns, self.gap, self.alignment):
            variable.trace_add("write", self._on_parameter_changed)

    def _build(self):
        theme = get_theme()
        self.window.configure(bg=theme["bg"])
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        tabs = ttk.Notebook(self.window)
        tabs.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 10))
        single = tk.Frame(tabs, bg=theme["bg"])
        multi = tk.Frame(tabs, bg=theme["bg"])
        tabs.add(single, text="单图复制拼接")
        tabs.add(multi, text="多图拼接")
        tabs.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._build_single_controls(single)
        self._build_multi_controls(multi)

        content = tk.Frame(self.window, bg=theme["bg"])
        content.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        self._build_preview(content)

    def _build_single_controls(self, parent):
        ttk.Button(parent, text="选择图片", command=self.choose_single).pack(side="left", pady=8)
        ttk.Label(parent, textvariable=self.input_path).pack(side="left", fill="x", expand=True, padx=10)
        ttk.Label(parent, text="行").pack(side="left", padx=(8, 4))
        ttk.Entry(parent, width=6, textvariable=self.rows).pack(side="left")
        ttk.Label(parent, text="列").pack(side="left", padx=(10, 4))
        ttk.Entry(parent, width=6, textvariable=self.columns).pack(side="left")
        ttk.Button(parent, text="生成预览", style="Primary.TButton", command=self.generate_preview).pack(side="left", padx=(12, 0))
        ttk.Button(parent, text="保存结果", command=self.save_result).pack(side="left", padx=(8, 0))

    def _build_multi_controls(self, parent):
        parent.grid_columnconfigure(1, weight=1)
        ttk.Button(parent, text="添加图片", command=self.choose_multiple).grid(row=0, column=0, padx=(0, 8), pady=8, sticky="w")
        ttk.Label(parent, text="可重复添加同一文件，并调整每个条目的顺序。").grid(row=0, column=1, sticky="w")
        ttk.Button(parent, text="生成预览", style="Primary.TButton", command=self.generate_preview).grid(row=0, column=2, padx=(12, 0))
        ttk.Button(parent, text="保存结果", command=self.save_result).grid(row=0, column=3, padx=(8, 0))
        list_frame = tk.Frame(parent, bg=get_theme()["bg"])
        list_frame.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 8))
        list_frame.grid_columnconfigure(0, weight=1)
        self.file_list = tk.Listbox(list_frame, height=3, exportselection=False)
        self.file_list.grid(row=0, column=0, sticky="ew")
        buttons = tk.Frame(list_frame, bg=get_theme()["bg"])
        buttons.grid(row=0, column=1, padx=(8, 0))
        ttk.Button(buttons, text="上移", command=lambda: self.move_file(-1)).pack(side="left")
        ttk.Button(buttons, text="下移", command=lambda: self.move_file(1)).pack(side="left", padx=4)
        ttk.Button(buttons, text="移除", command=self.remove_file).pack(side="left")
        ttk.Button(buttons, text="清空列表", command=self.clear_files).pack(side="left", padx=(4, 0))
        ttk.Label(parent, text="拼接布局").grid(row=2, column=0, sticky="w", pady=(0, 8))
        ttk.Radiobutton(parent, text="左右拼接", variable=self.direction, value="horizontal").grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(parent, text="上下拼接", variable=self.direction, value="vertical").grid(row=2, column=1, sticky="w", padx=(100, 0))
        ttk.Radiobutton(parent, text="网格拼接", variable=self.direction, value="grid").grid(row=2, column=1, sticky="w", padx=(200, 0))
        ttk.Label(parent, text="图片间距").grid(row=3, column=0, sticky="w", pady=(0, 8))
        ttk.Entry(parent, width=8, textvariable=self.gap).grid(row=3, column=1, sticky="w")
        ttk.Label(parent, text="像素").grid(row=3, column=1, sticky="w", padx=(70, 0))
        ttk.Label(parent, text="对齐").grid(row=3, column=2, sticky="e", padx=(8, 4))
        self.alignment_combo = ttk.Combobox(parent, width=8, state="readonly", textvariable=self.alignment, values=["start", "center", "end"])
        self.alignment_combo.grid(row=3, column=3, sticky="w")
        self.alignment_hint = ttk.Label(parent, text="")
        self.alignment_hint.grid(row=4, column=3, sticky="w", pady=(0, 8))
        self.grid_rows_label = ttk.Label(parent, text="网格行")
        self.grid_rows_label.grid(row=4, column=0, sticky="w", pady=(0, 8))
        self.grid_rows_entry = ttk.Entry(parent, width=8, textvariable=self.grid_rows)
        self.grid_rows_entry.grid(row=4, column=1, sticky="w")
        self.grid_columns_label = ttk.Label(parent, text="网格列")
        self.grid_columns_label.grid(row=4, column=2, sticky="e", padx=(8, 4))
        self.grid_columns_entry = ttk.Entry(parent, width=8, textvariable=self.grid_columns)
        self.grid_columns_entry.grid(row=4, column=3, sticky="w")
        ttk.Label(parent, text="背景").grid(row=5, column=0, sticky="w", pady=(0, 8))
        ttk.Button(parent, textvariable=self.background_text, command=self.choose_background).grid(row=5, column=1, sticky="w")

    def _build_preview(self, content):
        preview_card = tk.Frame(content, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, relief="groove")
        preview_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(preview_card, text="预览", bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=14, pady=(12, 8))
        canvas_wrap = tk.Frame(preview_card, bg="#202936")
        canvas_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.canvas = tk.Canvas(canvas_wrap, bg="#202936", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self._render_preview())
        info = tk.Frame(content, bg=get_theme()["bg"], width=310)
        info.grid(row=0, column=1, sticky="nsew")
        info.grid_propagate(False)
        self._info_card(info, "输入图片信息", self.input_info).pack(fill="x", pady=(0, 12))
        self._info_card(info, "输出结果信息", self.output_info).pack(fill="x")
        tk.Label(info, textvariable=self.status, bg=get_theme()["bg"], fg=MUTED, font=("Microsoft YaHei UI", 9), wraplength=300, justify="left").pack(anchor="w", pady=(14, 0))

    def _info_card(self, master, title, variable):
        card = tk.Frame(master, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, relief="groove")
        tk.Label(card, text=title, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        tk.Label(card, textvariable=variable, bg=PANEL, fg=MUTED, font=("Microsoft YaHei UI", 10), justify="left", anchor="w", wraplength=280).pack(fill="x", padx=14, pady=(0, 14))
        return card

    def _on_tab_changed(self, event):
        self.mode.set("multi" if event.widget.tab(event.widget.select(), "text") == "多图拼接" else "single")
        self.preview = None
        self.generate_preview(show_error=False)

    def choose_single(self):
        path = filedialog.askopenfilename(parent=self.window, title="选择要拼接的图片", filetypes=IMAGE_FILETYPES)
        if not path:
            return
        try:
            with Image.open(path) as image:
                self.source = image.copy()
                info = get_image_info(self.source)
                self.input_info.set(f"文件：{os.path.basename(path)}\n格式：{image.format or '未知'}\n尺寸：{info['width']} × {info['height']} px\n模式：{info['mode']}")
            self.input_path.set(path)
            self.status.set("单图已加载")
            self.generate_preview()
        except Exception as error:
            messagebox.showerror("打开失败", str(error), parent=self.window)

    def choose_multiple(self):
        paths = filedialog.askopenfilenames(parent=self.window, title="选择多张图片", filetypes=IMAGE_FILETYPES)
        if not paths:
            return
        self._append_multi_paths(paths)

    def _append_multi_paths(self, paths):
        added = []
        try:
            for path in paths:
                with Image.open(path) as image:
                    added.append((image.copy(), os.path.basename(path)))
            for image, name in added:
                self.sources.append(image)
                self.file_list.insert(tk.END, name)
            self.input_info.set(self._multi_input_text())
            self.status.set(f"已加载 {len(self.sources)} 张图片")
            self.generate_preview()
        except Exception as error:
            messagebox.showerror("打开失败", str(error), parent=self.window)

    def _multi_input_text(self):
        if not self.sources:
            return "尚未选择图片"
        sizes = ", ".join(f"{image.width} × {image.height}" for image in self.sources[:5])
        return f"图片数量：{len(self.sources)}\n尺寸：{sizes}{' ...' if len(self.sources) > 5 else ''}\n模式：{self.sources[0].mode}"

    def move_file(self, offset):
        selected = self.file_list.curselection()
        if not selected:
            return
        index, target = selected[0], selected[0] + offset
        if target < 0 or target >= len(self.sources):
            return
        self.sources[index], self.sources[target] = self.sources[target], self.sources[index]
        names = list(self.file_list.get(0, tk.END))
        names[index], names[target] = names[target], names[index]
        self.file_list.delete(0, tk.END)
        for name in names:
            self.file_list.insert(tk.END, name)
        self.file_list.selection_set(target)
        self.generate_preview(show_error=False)

    def remove_file(self):
        selected = self.file_list.curselection()
        if not selected:
            return
        del self.sources[selected[0]]
        self.file_list.delete(selected[0])
        self.input_info.set(self._multi_input_text())
        self.generate_preview(show_error=False)

    def clear_files(self):
        self.sources.clear()
        self.file_list.delete(0, tk.END)
        self.input_info.set("尚未选择图片")
        self.preview = None
        self.output_info.set("设置参数后生成预览")
        self.status.set("图片列表已清空")
        self._render_preview()

    def choose_background(self):
        color = colorchooser.askcolor(color=self.background_text.get(), parent=self.window, title="选择拼接背景色")
        if color[0] is None:
            return
        self.background = tuple(int(value) for value in color[0])
        self.background_text.set(color[1])
        self.generate_preview(show_error=False)

    def _parse_grid(self):
        try:
            rows, columns = int(self.rows.get().strip()), int(self.columns.get().strip())
        except ValueError as error:
            raise ValueError("行数和列数必须是正整数") from error
        if rows <= 0 or columns <= 0:
            raise ValueError("行数和列数必须是正整数")
        return rows, columns

    def _parse_multi_grid(self):
        try:
            rows, columns = int(self.grid_rows.get().strip()), int(self.grid_columns.get().strip())
        except ValueError as error:
            raise ValueError("网格行数和列数必须是正整数") from error
        if rows <= 0 or columns <= 0:
            raise ValueError("网格行数和列数必须是正整数")
        return rows, columns

    def _update_multi_layout_controls(self):
        if not hasattr(self, "alignment_combo"):
            return
        is_grid = self.direction.get() == "grid"
        grid_state = "normal" if is_grid else "disabled"
        self.grid_rows_entry.configure(state=grid_state)
        self.grid_columns_entry.configure(state=grid_state)
        self.alignment_combo.configure(state="disabled" if is_grid else "readonly")
        self.alignment_hint.configure(text="网格单元内居中" if is_grid else "")

    def _on_parameter_changed(self, *_):
        self._update_multi_layout_controls()
        self.generate_preview(show_error=False)

    def generate_preview(self, show_error=True):
        try:
            if self.mode.get() == "single":
                if self.source is None:
                    if show_error:
                        messagebox.showwarning("提示", "请先选择一张图片。", parent=self.window)
                    return
                rows, columns = self._parse_grid()
                self.preview = tile_image(self.source, rows, columns)
                description = f"网格：{rows} 行 × {columns} 列"
            else:
                if not self.sources:
                    if show_error:
                        messagebox.showwarning("提示", "请先选择至少一张图片。", parent=self.window)
                    return
                try:
                    gap = int(self.gap.get().strip())
                except ValueError as error:
                    raise ValueError("图片间距必须是非负整数") from error
                if gap < 0:
                    raise ValueError("图片间距必须是非负整数")
                if self.direction.get() == "grid":
                    rows, columns = self._parse_multi_grid()
                    self.preview = concat_images_grid(
                        self.sources,
                        rows=rows,
                        columns=columns,
                        gap=gap,
                        background=self.background,
                    )
                    cell_width = max(image.width for image in self.sources)
                    cell_height = max(image.height for image in self.sources)
                    description = (
                        f"布局：网格拼接（{rows} 行 × {columns} 列）\n"
                        f"已放置：{len(self.sources)} / {rows * columns} 张\n"
                        f"单元格：{cell_width} × {cell_height} px\n"
                        f"间距：{gap}px"
                    )
                else:
                    self.preview = concat_images(
                        self.sources,
                        self.direction.get(),
                        gap=gap,
                        background=self.background,
                        alignment=self.alignment.get(),
                    )
                    description = "布局：左右拼接" if self.direction.get() == "horizontal" else "布局：上下拼接"
                    description += f"\n间距：{gap}px"
            info = get_image_info(self.preview)
            self.output_info.set(f"尺寸：{info['width']} × {info['height']} px\n模式：{info['mode']}\n{description}\n预计像素数：{info['width'] * info['height']:,}")
            self.status.set("预览已更新，可直接保存结果")
        except ValueError as error:
            self.preview = None
            self.output_info.set("无法生成结果\n" + str(error))
            self.status.set(str(error))
            if show_error:
                messagebox.showerror("参数错误", str(error), parent=self.window)
        self._render_preview()

    def _render_preview(self):
        if not hasattr(self, "canvas"):
            return
        self.canvas.delete("all")
        if self.preview is None:
            self.canvas.create_text(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, text="暂无预览", fill="#cbd5e1", font=("Microsoft YaHei UI", 12))
            return
        image = self.preview.copy()
        image.thumbnail((max(1, self.canvas.winfo_width() - 24), max(1, self.canvas.winfo_height() - 24)), Image.Resampling.LANCZOS)
        self.preview_photo = ImageTk.PhotoImage(image)
        self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, image=self.preview_photo)

    def save_result(self):
        if self.preview is None:
            self.generate_preview()
            if self.preview is None:
                return
        output_path = filedialog.asksaveasfilename(parent=self.window, title="保存拼接结果", defaultextension=".png", filetypes=[("PNG 图片", "*.png"), ("JPEG 图片", "*.jpg *.jpeg"), ("BMP 图片", "*.bmp"), ("所有文件", "*.*")])
        if not output_path:
            return
        result = self.preview
        if os.path.splitext(output_path)[1].lower() in {".jpg", ".jpeg"} and result.mode not in {"RGB", "L"}:
            result = result.convert("RGB")
        try:
            result.save(output_path)
            self.status.set(f"已保存：{output_path}")
            messagebox.showinfo("保存完成", f"拼接结果已保存：\n{output_path}", parent=self.window)
        except Exception as error:
            messagebox.showerror("保存失败", str(error), parent=self.window)

    def close(self):
        self.window.destroy()
