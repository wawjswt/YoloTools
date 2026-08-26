import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from .theme import *
from tools.image_concat_service import get_image_info, tile_image


IMAGE_FILETYPES = [
    ("图片文件", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp"),
    ("所有文件", "*.*"),
]


class ImageConcatWindow:
    def __init__(self, master):
        self.master = master
        self.window = tk.Toplevel(master)
        self.window.title("图片拼接")
        self.window.geometry("1120x760")
        self.window.minsize(900, 620)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self.input_path = tk.StringVar()
        self.rows = tk.StringVar(value="2")
        self.columns = tk.StringVar(value="2")
        self.input_info = tk.StringVar(value="尚未选择图片")
        self.output_info = tk.StringVar(value="设置行列后生成预览")
        self.status = tk.StringVar(value="请选择一张图片")
        self.source = None
        self.preview = None
        self.preview_photo = None

        self._build()
        self.rows.trace_add("write", self._on_grid_changed)
        self.columns.trace_add("write", self._on_grid_changed)

    def _build(self):
        theme = get_theme()
        self.window.configure(bg=theme["bg"])
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)

        toolbar = tk.Frame(self.window, bg=theme["bg"])
        toolbar.grid(row=0, column=0, sticky="ew", padx=18, pady=(16, 10))
        ttk.Button(toolbar, text="选择图片", command=self.choose_image).pack(side="left")
        ttk.Label(toolbar, textvariable=self.input_path).pack(side="left", fill="x", expand=True, padx=10)
        ttk.Label(toolbar, text="行").pack(side="left", padx=(8, 4))
        ttk.Entry(toolbar, width=6, textvariable=self.rows).pack(side="left")
        ttk.Label(toolbar, text="列").pack(side="left", padx=(10, 4))
        ttk.Entry(toolbar, width=6, textvariable=self.columns).pack(side="left")
        ttk.Button(toolbar, text="生成预览", style="Primary.TButton", command=self.generate_preview).pack(side="left", padx=(12, 0))
        ttk.Button(toolbar, text="保存结果", command=self.save_result).pack(side="left", padx=(8, 0))

        content = tk.Frame(self.window, bg=theme["bg"])
        content.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 12))
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)

        preview_card = tk.Frame(content, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, relief="groove")
        preview_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        tk.Label(preview_card, text="预览", bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 13, "bold")).pack(anchor="w", padx=14, pady=(12, 8))
        canvas_wrap = tk.Frame(preview_card, bg="#202936")
        canvas_wrap.pack(fill="both", expand=True, padx=14, pady=(0, 14))
        self.canvas = tk.Canvas(canvas_wrap, bg="#202936", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda event: self._render_preview())

        info = tk.Frame(content, bg=theme["bg"], width=300)
        info.grid(row=0, column=1, sticky="nsew")
        info.grid_propagate(False)
        self._info_card(info, "输入图片信息", self.input_info).pack(fill="x", pady=(0, 12))
        self._info_card(info, "输出结果信息", self.output_info).pack(fill="x")
        tk.Label(info, textvariable=self.status, bg=theme["bg"], fg=MUTED, font=("Microsoft YaHei UI", 9), wraplength=290, justify="left").pack(anchor="w", pady=(14, 0))

    def _info_card(self, master, title, variable):
        card = tk.Frame(master, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, relief="groove")
        tk.Label(card, text=title, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 11, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        tk.Label(card, textvariable=variable, bg=PANEL, fg=MUTED, font=("Microsoft YaHei UI", 10), justify="left", anchor="w", wraplength=270).pack(fill="x", padx=14, pady=(0, 14))
        return card

    def choose_image(self):
        path = filedialog.askopenfilename(parent=self.window, title="选择要拼接的图片", filetypes=IMAGE_FILETYPES)
        if not path:
            return
        try:
            with Image.open(path) as image:
                self.source = image.copy()
                info = get_image_info(self.source)
                self.input_info.set(f"文件：{os.path.basename(path)}\n格式：{image.format or '未知'}\n尺寸：{info['width']} × {info['height']} px\n模式：{info['mode']}")
            self.input_path.set(path)
            self.status.set("图片已加载，正在生成预览")
            self.generate_preview()
        except Exception as error:
            self.source = None
            messagebox.showerror("打开失败", str(error), parent=self.window)

    def _parse_grid(self):
        try:
            rows = int(self.rows.get().strip())
            columns = int(self.columns.get().strip())
        except ValueError as error:
            raise ValueError("行数和列数必须是正整数") from error
        if rows <= 0 or columns <= 0:
            raise ValueError("行数和列数必须是正整数")
        return rows, columns

    def _on_grid_changed(self, *_):
        if self.source is not None:
            self.generate_preview(show_error=False)

    def generate_preview(self, show_error=True):
        if self.source is None:
            if show_error:
                messagebox.showwarning("提示", "请先选择一张图片。", parent=self.window)
            return
        try:
            rows, columns = self._parse_grid()
            self.preview = tile_image(self.source, rows, columns)
        except ValueError as error:
            self.preview = None
            self.output_info.set("无法生成结果\n" + str(error))
            self.status.set(str(error))
            if show_error:
                messagebox.showerror("参数错误", str(error), parent=self.window)
            self._render_preview()
            return
        info = get_image_info(self.preview)
        self.output_info.set(f"尺寸：{info['width']} × {info['height']} px\n模式：{info['mode']}\n网格：{rows} 行 × {columns} 列\n预计像素数：{info['width'] * info['height']:,}")
        self.status.set("预览已更新，可直接保存结果")
        self._render_preview()

    def _render_preview(self):
        self.canvas.delete("all")
        if self.preview is None:
            self.canvas.create_text(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, text="暂无预览", fill="#cbd5e1", font=("Microsoft YaHei UI", 12))
            return
        width = max(1, self.canvas.winfo_width() - 24)
        height = max(1, self.canvas.winfo_height() - 24)
        image = self.preview.copy()
        image.thumbnail((width, height), Image.Resampling.LANCZOS)
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
