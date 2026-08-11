# app/ui_tools.py
import tkinter as tk
from tkinter import ttk, messagebox
from .theme import *
from .ui_convert import SectionCard
from tools.show_yolo_labels import YOLOEditor
from tools.plotpoint import PointPicker


class ToolsPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self.editor_win = None
        self.point_win = None
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(top, text="其他工具", bg=BG, fg=TEXT, font=("Microsoft YaHei UI", 20, "bold")).pack(anchor="w")
        tk.Label(top, text="启动独立窗口工具", bg=BG, fg=MUTED, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        left = SectionCard(body, "标注编辑器", "打开 show_yolo_labels.py")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        left_box = tk.Frame(left, bg=PANEL)
        left_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        tk.Label(left_box, text="适合查看、编辑 YOLO 标注。", bg=PANEL, fg=MUTED, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(0, 10))
        ttk.Button(left_box, text="启动 YOLO 标注编辑器", style="Primary.TButton", command=self.launch_editor).pack(anchor="w")

        right = SectionCard(body, "点位拾取", "打开 plotpoint.py")
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        right_box = tk.Frame(right, bg=PANEL)
        right_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        tk.Label(right_box, text="适合拾取封闭区域顶点坐标。", bg=PANEL, fg=MUTED, font=("Microsoft YaHei UI", 10)).pack(anchor="w", pady=(0, 10))
        ttk.Button(right_box, text="启动封闭图形点位拾取", style="Primary.TButton", command=self.launch_point_picker).pack(anchor="w")

    def launch_editor(self):
        if self.editor_win and self.editor_win.winfo_exists():
            self.editor_win.lift()
            self.editor_win.focus_force()
            return
        try:
            win = tk.Toplevel(self.winfo_toplevel())
            win.title("YOLO 标注编辑器")
            win.geometry("1200x800")
            self.editor_win = win
            YOLOEditor(win)
        except Exception as e:
            messagebox.showerror("启动失败", str(e))

    def launch_point_picker(self):
        if self.point_win and self.point_win.winfo_exists():
            self.point_win.lift()
            self.point_win.focus_force()
            return
        try:
            win = tk.Toplevel(self.winfo_toplevel())
            win.title("封闭图形坐标拾取")
            win.geometry("1200x800")
            self.point_win = win
            PointPicker(win)
        except Exception as e:
            messagebox.showerror("启动失败", str(e))
