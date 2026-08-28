import json
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk


@dataclass
class PointRecord:
    x_norm: float
    y_norm: float


class PointPicker:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1200x820")
        self.root.minsize(980, 700)
        self.root.title("封闭图形坐标拾取")

        self.image_path = None
        self.orig_image = None
        self.photo = None
        self.image_id = None
        self._scaled_image = None
        self._display_cache_key = None
        self.points = []
        self.closed = False
        self.dragging = False
        self.active_index = None
        self.status_text = tk.StringVar(value="可先直接在空白画布上点位，也可先加载图片后再拾点。")
        self.export_path = None
        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        self.root.columnconfigure(0, weight=3)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(1, weight=1)

        toolbar = tk.Frame(self.root, bg="#f3f4f6", height=54)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        toolbar.grid_columnconfigure(0, weight=1)

        title_box = tk.Frame(toolbar, bg="#f3f4f6")
        title_box.grid(row=0, column=0, sticky="w", padx=16, pady=8)
        tk.Label(
            title_box,
            text="封闭图形点位拾取",
            bg="#f3f4f6",
            fg="#111827",
            font=("Microsoft YaHei UI", 14, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_box,
            text="支持无图直接拾点，也支持加载图片后按顺序标注、拖动、闭合和导出。",
            bg="#f3f4f6",
            fg="#6b7280",
            font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w")

        action_box = tk.Frame(toolbar, bg="#f3f4f6")
        action_box.grid(row=0, column=1, sticky="e", padx=12)
        self._button(action_box, "加载图片", self.load_image).pack(side="left", padx=4)
        self._button(action_box, "撤销点位", self.undo_point).pack(side="left", padx=4)
        self._button(action_box, "清空点位", self.clear_all).pack(side="left", padx=4)
        self._button(action_box, "闭合/取消", self.toggle_close).pack(side="left", padx=4)
        self._button(action_box, "导出坐标", self.export_points).pack(side="left", padx=4)

        canvas_wrap = tk.Frame(self.root, bg="#d1d5db")
        canvas_wrap.grid(row=1, column=0, sticky="nsew")
        canvas_wrap.rowconfigure(0, weight=1)
        canvas_wrap.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_wrap, bg="#111827", highlightthickness=0, cursor="crosshair")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        side = tk.Frame(self.root, bg="#ffffff", width=320, highlightthickness=1, highlightbackground="#e5e7eb")
        side.grid(row=1, column=1, sticky="nsew")
        side.grid_rowconfigure(2, weight=1)
        side.grid_columnconfigure(0, weight=1)

        head = tk.Frame(side, bg="#ffffff")
        head.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
        tk.Label(
            head,
            text="点位列表",
            bg="#ffffff",
            fg="#111827",
            font=("Microsoft YaHei UI", 12, "bold"),
        ).pack(anchor="w")
        tk.Label(
            head,
            text="点击条目可选中，拖动画布上的点可微调位置。",
            bg="#ffffff",
            fg="#6b7280",
            font=("Microsoft YaHei UI", 9),
        ).pack(anchor="w", pady=(4, 0))

        list_frame = tk.Frame(side, bg="#ffffff")
        list_frame.grid(row=1, column=0, sticky="ew", padx=14)
        self.listbox = tk.Listbox(list_frame, height=12, activestyle="none", selectmode="browse")
        self.listbox.pack(side="left", fill="both", expand=True)
        scrollbar = tk.Scrollbar(list_frame, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.configure(yscrollcommand=scrollbar.set)

        info = tk.Frame(side, bg="#f9fafb", highlightthickness=1, highlightbackground="#e5e7eb")
        info.grid(row=2, column=0, sticky="nsew", padx=14, pady=14)
        info.grid_columnconfigure(0, weight=1)
        tk.Label(
            info,
            text="操作说明",
            bg="#f9fafb",
            fg="#111827",
            font=("Microsoft YaHei UI", 11, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 4))
        tips = [
            "1. 你可以不加载图片，直接在黑色画布上点位。",
            "2. 加载图片后，点位会按图片比例映射到画布上。",
            "3. 按 Enter / Space 完成闭合，Esc 清空，Delete 撤销最后一点。",
            "4. 列表中可选中对应点位，拖动画布上的红点可微调。",
            "5. 导出时会保留 x1,y1,x2,y2... 扁平坐标列表和点集列表。",
        ]
        for tip in tips:
            tk.Label(
                info,
                text=tip,
                bg="#f9fafb",
                fg="#374151",
                justify="left",
                anchor="w",
                wraplength=260,
                font=("Microsoft YaHei UI", 9),
            ).pack(anchor="w", padx=12, pady=2)

        status_bar = tk.Label(
            self.root,
            textvariable=self.status_text,
            anchor="w",
            bg="#1f2937",
            fg="#f9fafb",
            padx=12,
            pady=8,
        )
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew")

    def _button(self, master, text, command):
        return tk.Button(
            master,
            text=text,
            command=command,
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=6,
            cursor="hand2",
        )

    def _bind_events(self):
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.root.bind("<Return>", self.finish)
        self.root.bind("<space>", self.finish)
        self.root.bind("<Escape>", lambda e: self.clear_all())
        self.root.bind("<Delete>", lambda e: self.undo_point())
        self.listbox.bind("<<ListboxSelect>>", self.on_select_point)
        self.listbox.bind("<Double-Button-1>", self.center_on_point)

    def _set_status(self, text):
        self.status_text.set(text)

    def _canvas_size(self):
        w = max(self.canvas.winfo_width(), 1)
        h = max(self.canvas.winfo_height(), 1)
        return w, h

    def _display_rect(self):
        cw, ch = self._canvas_size()
        if not self.orig_image:
            return 0, 0, cw, ch
        img_w, img_h = self.orig_image.size
        ratio = min(cw / img_w, ch / img_h)
        disp_w = max(int(img_w * ratio), 1)
        disp_h = max(int(img_h * ratio), 1)
        off_x = (cw - disp_w) // 2
        off_y = (ch - disp_h) // 2
        return off_x, off_y, disp_w, disp_h

    def _point_to_canvas(self, point):
        off_x, off_y, disp_w, disp_h = self._display_rect()
        return off_x + point.x_norm * disp_w, off_y + point.y_norm * disp_h

    def _canvas_to_point(self, x, y):
        off_x, off_y, disp_w, disp_h = self._display_rect()
        nx = (x - off_x) / disp_w
        ny = (y - off_y) / disp_h
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))
        return PointRecord(nx, ny)

    def _in_image_bounds(self, x, y):
        if self.orig_image is None:
            return True
        off_x, off_y, disp_w, disp_h = self._display_rect()
        return off_x <= x <= off_x + disp_w and off_y <= y <= off_y + disp_h

    def _refresh_list(self):
        self.listbox.delete(0, tk.END)
        for i, p in enumerate(self.points, start=1):
            self.listbox.insert(tk.END, f"{i:02d}  x={p.x_norm:.6f}  y={p.y_norm:.6f}")
        if self.active_index is not None and 0 <= self.active_index < len(self.points):
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.active_index)
            self.listbox.see(self.active_index)

    def redraw(self):
        self.canvas.delete("all")
        if self.orig_image is not None:
            off_x, off_y, disp_w, disp_h = self._display_rect()
            cache_key = (id(self.orig_image), disp_w, disp_h)
            if self._display_cache_key != cache_key:
                self._scaled_image = self.orig_image.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(self._scaled_image)
                self._display_cache_key = cache_key
            self.image_id = self.canvas.create_image(off_x, off_y, anchor="nw", image=self.photo)
            self.canvas.create_rectangle(off_x, off_y, off_x + disp_w, off_y + disp_h, outline="#374151", width=1)
        else:
            self.photo = None
            self.image_id = None
            self._scaled_image = None
            self._display_cache_key = None

        if not self.points:
            return

        coords = [self._point_to_canvas(p) for p in self.points]
        for i in range(len(coords) - 1):
            self.canvas.create_line(*coords[i], *coords[i + 1], fill="#60a5fa", width=2)
        if self.closed and len(coords) >= 3:
            self.canvas.create_line(*coords[-1], *coords[0], fill="#f59e0b", width=2, dash=(5, 3))

        for idx, (x, y) in enumerate(coords):
            r = 5 if idx != self.active_index else 7
            fill = "#111827" if idx != self.active_index else "#ef4444"
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill=fill, outline="#ffffff", width=2)
            self.canvas.create_text(x + 12, y - 10, text=str(idx + 1), fill="#ffffff", font=("Microsoft YaHei UI", 9, "bold"), anchor="w")

        self._set_status(f"已添加 {len(self.points)} 个点，{'已闭合' if self.closed else '未闭合'}。")

    def load_image(self):
        path = filedialog.askopenfilename(
            title="选择底图",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return
        if self.points:
            should_clear = messagebox.askyesno(
                "加载图片",
                "当前已有点位。加载图片会清空这些点位并按新图片重新拾取，是否继续？",
                parent=self.root,
            )
            if not should_clear:
                self._set_status("已取消加载图片，现有点位保持不变。")
                return
        try:
            self.orig_image = Image.open(path).convert("RGB")
        except Exception as exc:
            messagebox.showerror("错误", f"无法打开图片：{exc}")
            return

        self.image_path = Path(path)
        self.photo = None
        self._scaled_image = None
        self._display_cache_key = None
        self.points.clear()
        self.closed = False
        self.active_index = None
        self.export_path = self.image_path.with_suffix(".points.json")
        self._refresh_list()
        self.redraw()
        self._set_status(f"已加载图片：{self.image_path.name}，可以开始拾取点位。")

    def clear_all(self):
        self.points.clear()
        self.closed = False
        self.active_index = None
        self._refresh_list()
        self.redraw()
        self._set_status("已清空所有点位。")

    def undo_point(self):
        if not self.points:
            self._set_status("当前没有点位可撤销。")
            return
        removed = self.points.pop()
        self.closed = False
        self.active_index = None
        self._refresh_list()
        self.redraw()
        self._set_status(f"已撤销最后一个点：x={removed.x_norm:.6f}, y={removed.y_norm:.6f}")

    def toggle_close(self):
        if len(self.points) < 3:
            self._set_status("至少需要 3 个点才能闭合。")
            return
        self.closed = not self.closed
        self.redraw()
        self._set_status("已闭合图形。" if self.closed else "已取消闭合。")

    def on_canvas_click(self, event):
        idx = self._hit_test_point(event.x, event.y)
        if idx is not None:
            self.active_index = idx
            self.dragging = True
            self._refresh_list()
            self.redraw()
            return

        if not self._in_image_bounds(event.x, event.y):
            self._set_status("请在画布范围内点击添加点位。")
            return

        point = self._canvas_to_point(event.x, event.y)
        self.points.append(point)
        self.active_index = len(self.points) - 1
        self.closed = False
        self._refresh_list()
        self.redraw()
        self._set_status(f"已添加第 {len(self.points)} 个点。")

    def _hit_test_point(self, x, y, radius=9):
        for idx, point in enumerate(self.points):
            px, py = self._point_to_canvas(point)
            if (px - x) ** 2 + (py - y) ** 2 <= radius ** 2:
                return idx
        return None

    def on_canvas_drag(self, event):
        if self.active_index is None:
            return
        if not self._in_image_bounds(event.x, event.y):
            return
        self.dragging = True
        self.points[self.active_index] = self._canvas_to_point(event.x, event.y)
        self.closed = False
        self._refresh_list()
        self.redraw()

    def on_canvas_release(self, event):
        if self.dragging:
            self.dragging = False
            self._set_status("点位已更新。")

    def on_select_point(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        self.active_index = selection[0]
        self.redraw()

    def center_on_point(self, event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        idx = selection[0]
        self.active_index = idx
        self.redraw()
        self._set_status(f"已选中第 {idx + 1} 个点。")

    def finish(self, event=None):
        if len(self.points) < 3:
            self._set_status("至少需要 3 个点才能完成闭合。")
            return
        self.closed = True
        self.redraw()
        self._set_status("图形已闭合，可以导出坐标。")

    def get_points_as_list(self):
        return [[round(p.x_norm, 6), round(p.y_norm, 6)] for p in self.points]

    def get_smooth_flat_coords(self):
        """返回兼容旧版 ``x1,y1,x2,y2,...`` 的扁平坐标列表。"""
        coords = []
        for p in self.points:
            coords.extend([round(p.x_norm, 6), round(p.y_norm, 6)])
        return coords

    def export_points(self):
        if len(self.points) < 3:
            self._set_status("至少需要 3 个点才能导出。")
            return

        default_name = self.export_path.name if self.export_path else "points.json"
        path = filedialog.asksaveasfilename(
            title="导出坐标",
            defaultextension=".json",
            initialfile=default_name,
            filetypes=[
                ("JSON 文件", "*.json"),
                ("文本文件", "*.txt"),
                ("所有文件", "*.*"),
            ],
        )
        if not path:
            return

        point_pairs = self.get_points_as_list()
        smooth_flat = self.get_smooth_flat_coords()
        out_path = Path(path)
        try:
            if out_path.suffix.lower() == ".txt":
                out_path.write_text(
                    ",".join(f"{v:.6f}" for v in smooth_flat),
                    encoding="utf-8",
                )
            else:
                payload = {
                    "image": str(self.image_path) if self.image_path else "",
                    "closed": self.closed,
                    "points": point_pairs,
                    "smooth": smooth_flat,
                    "flat_xy": smooth_flat,
                    "x1y1x2y2": smooth_flat,
                }
                out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            messagebox.showerror("导出失败", str(exc))
            return

        self.export_path = out_path
        self._set_status(f"已导出到：{out_path.name}")


if __name__ == "__main__":
    root = tk.Tk()
    PointPicker(root)
    root.mainloop()
