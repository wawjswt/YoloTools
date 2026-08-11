import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk


class PointPicker:
    def __init__(self, root):
        self.root = root
        root.geometry("800x600")
        root.title("封闭图形标注 — 支持自适应缩放")

        self.canvas = tk.Canvas(root, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        frame = tk.Frame(root)
        frame.pack(pady=5)

        self.btn_load = tk.Button(frame, text="📂 加载底图", command=self.load_image)
        self.btn_load.pack(side=tk.LEFT, padx=5)

        self.btn_clear = tk.Button(frame, text="🗑️ 清除所有点", command=self.clear_all)
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        self.label = tk.Label(root, text="请点击添加点（至少3个），完成后按 Enter/Space/C 闭合")
        self.label.pack(pady=5)

        # 统一保存归一化坐标，这样窗口缩放或底图缩放后仍能正确重绘。
        self.points_norm = []
        self.is_finished = False
        self.orig_image = None
        self.photo = None
        self.image_id = None

        self.ref_w = 600
        self.ref_h = 400

        self.canvas.bind('<Button-1>', self.add_point)
        self.root.bind('<Return>', self.finish)
        self.root.bind('<space>', self.finish)
        self.root.bind('<c>', self.finish)
        self.canvas.bind('<Configure>', self.on_resize)

        self.graphic_ids = []

    def get_display_params(self):
        """返回当前显示区域的宽高和偏移，用于像素坐标与归一化坐标互转。"""
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1:
            canvas_w = 800
        if canvas_h <= 1:
            canvas_h = 600

        if self.orig_image is not None:
            img_w, img_h = self.orig_image.size
            ratio = min(canvas_w / img_w, canvas_h / img_h)
            disp_w = int(img_w * ratio)
            disp_h = int(img_h * ratio)
            off_x = (canvas_w - disp_w) // 2
            off_y = (canvas_h - disp_h) // 2
            return disp_w, disp_h, off_x, off_y

        return canvas_w, canvas_h, 0, 0

    def redraw(self):
        """根据当前窗口尺寸完整重绘底图、点和闭合线。"""
        for item in self.graphic_ids:
            self.canvas.delete(item)
        self.graphic_ids.clear()

        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w <= 1:
            canvas_w = 800
        if canvas_h <= 1:
            canvas_h = 600

        if self.orig_image is not None:
            img_w, img_h = self.orig_image.size
            ratio = min(canvas_w / img_w, canvas_h / img_h)
            disp_w = int(img_w * ratio)
            disp_h = int(img_h * ratio)
            off_x = (canvas_w - disp_w) // 2
            off_y = (canvas_h - disp_h) // 2

            img_resized = self.orig_image.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img_resized)
            if self.image_id is not None:
                self.canvas.delete(self.image_id)
            self.image_id = self.canvas.create_image(off_x, off_y, anchor='nw', image=self.photo)
        else:
            if self.image_id is not None:
                self.canvas.delete(self.image_id)
                self.image_id = None
                self.photo = None
            disp_w, disp_h = canvas_w, canvas_h
            off_x, off_y = 0, 0

        if not self.points_norm:
            return

        points_pixel = []
        for nx, ny in self.points_norm:
            px = nx * disp_w + off_x
            py = ny * disp_h + off_y
            points_pixel.append((px, py))

        for px, py in points_pixel:
            dot = self.canvas.create_oval(px - 3, py - 3, px + 3, py + 3, fill='black')
            self.graphic_ids.append(dot)

        for i in range(len(points_pixel) - 1):
            x0, y0 = points_pixel[i]
            x1, y1 = points_pixel[i + 1]
            line = self.canvas.create_line(x0, y0, x1, y1, fill='blue', width=2)
            self.graphic_ids.append(line)

        if self.is_finished and len(points_pixel) >= 3:
            x0, y0 = points_pixel[-1]
            x1, y1 = points_pixel[0]
            close_line = self.canvas.create_line(x0, y0, x1, y1, fill='red', width=2, dash=(4, 2))
            self.graphic_ids.append(close_line)

    def on_resize(self, event):
        self.redraw()

    def load_image(self):
        """加载底图，并把已有点位清空，避免旧点落在新图上。"""
        file_path = filedialog.askopenfilename(
            title="选择底图",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"), ("所有文件", "*.*")]
        )
        if not file_path:
            return

        try:
            img = Image.open(file_path)
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片：{e}")
            return

        self.orig_image = img
        self.ref_w, self.ref_h = img.size
        self.points_norm.clear()
        self.is_finished = False
        self.label.config(text=f"底图已加载（{self.ref_w}×{self.ref_h}），请点击添加点")
        self.redraw()

    def clear_all(self):
        self.points_norm.clear()
        self.is_finished = False
        self.label.config(text="已清除所有点，请重新添加")
        self.redraw()

    def add_point(self, event):
        """把点击位置转换为归一化坐标，保证不同显示尺寸下结果一致。"""
        x, y = event.x, event.y
        disp_w, disp_h, off_x, off_y = self.get_display_params()

        nx = (x - off_x) / disp_w
        ny = (y - off_y) / disp_h
        nx = max(0, min(1, nx))
        ny = max(0, min(1, ny))

        self.points_norm.append((nx, ny))
        self.is_finished = False
        self.label.config(text=f"已添加 {len(self.points_norm)} 个点，继续添加或按 Enter 闭合")
        self.redraw()

    def finish(self, event=None):
        """闭合图形，并把归一化坐标输出到控制台供外部复用。"""
        if len(self.points_norm) < 3:
            self.label.config(text="至少需要 3 个点，请继续添加")
            return

        self.is_finished = True
        self.redraw()

        print("\n===== 绘制完成 =====")
        if self.orig_image is not None:
            print(f"底图原始尺寸: {self.ref_w}×{self.ref_h}")
        else:
            print(f"无底图，参考尺寸: {self.ref_w}×{self.ref_h}")

        print("归一化坐标 (相对于参考尺寸):")
        for i, (nx, ny) in enumerate(self.points_norm):
            print(f"  点 {i + 1}: ({nx:.6f}, {ny:.6f})")

        flat_list = [coord for point in self.points_norm for coord in point]
        print("\n扁平列表 (可直接使用):")
        print(flat_list)

        self.label.config(text="已完成！坐标已输出到控制台。")


if __name__ == "__main__":
    root = tk.Tk()
    app = PointPicker(root)
    root.mainloop()
