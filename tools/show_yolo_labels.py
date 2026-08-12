import cv2
import numpy as np
import os
import json
import math
import copy
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

# ---------- 中文字体 ----------
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

CONFIG_FILE = "yolo_viewer_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

# ---------- YOLO 标注读写 ----------
def load_yolo_labels(label_path):
    labels = []
    if not os.path.exists(label_path):
        return labels
    with open(label_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 5:
                labels.append({
                    'class_id': int(parts[0]),
                    'x_center': float(parts[1]),
                    'y_center': float(parts[2]),
                    'width': float(parts[3]),
                    'height': float(parts[4])
                })
    return labels

def save_yolo_labels(label_path, labels):
    with open(label_path, 'w') as f:
        for lb in labels:
            f.write(f"{lb['class_id']} {lb['x_center']:.6f} {lb['y_center']:.6f} {lb['width']:.6f} {lb['height']:.6f}\n")

# ---------- 主应用 ----------
class YOLOEditor:
    def __init__(self, master):
        self.master = master
        master.title("YOLO 标注编辑器 v5.4 (全面滚轮平移与流畅缩放版)")
        master.geometry("1250x800")
        master.minsize(1100, 700)

        # 变量
        self.image_folder = tk.StringVar()
        self.label_folder = tk.StringVar()
        self.image_files = []
        self.current_idx = 0
        self.current_image_bgr = None
        self.current_labels = []
        self.modified = False
        self.status_message = "就绪"
        
        # 撤销与重做历史栈
        self.undo_stack = []
        self.redo_stack = []
        self.drag_state_pushed = False

        # 视图缩放标记
        self.is_new_image = True
        self.view_state_cache = {}
        self.remember_view_state = tk.BooleanVar(value=True)
        self.auto_save_on_nav = tk.BooleanVar(value=False)

        # 交互模式
        self.mode = 'view'
        self.selected_idx = -1

        # 标注框拖拽/调整大小变量
        self.dragging_box = False
        self.drag_action = None  # 'move', 'tl', 'tr', 'bl', 'br'
        self.drag_start_mouse = None
        self.drag_start_box = None
        self.drag_idx = -1

        # 矩形绘制临时变量
        self.rect_start = None
        self.drawing_rect = None

        # Matplotlib 图形 Artist 缓存
        self.rect_patches = []
        self.text_artists = []
        self.corner_handles_line = None
        self.coord_text = None
        self.hline = None
        self.vline = None
        
        # Blitting 加速相关缓存变量
        self.background_cache = None
        
        # 提示通知窗口句柄
        self.noti_win = None

        # 加载配置与记忆类别
        self.config = load_config()
        if 'image_folder' in self.config:
            self.image_folder.set(self.config['image_folder'])
        if 'label_folder' in self.config:
            self.label_folder.set(self.config['label_folder'])
        
        self.last_class_id = self.config.get('last_class_id', None)

        self.setup_styles()
        self.create_menu()
        self.create_widgets()
        self.bind_shortcuts()
        self.setup_matplotlib_events()

        if self.image_folder.get():
            self.master.after(500, self.load_images)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        base_font = ('Microsoft YaHei UI', 9)
        title_font = ('Microsoft YaHei UI', 10, 'bold')
        style.configure('TButton', font=base_font, padding=(10, 6), background='#e9eef5', foreground='#1f2937')
        style.map('TButton', background=[('active', '#d9e5f5'), ('pressed', '#c7d7ec')])
        style.configure('TLabel', font=base_font, background='#eef3f9', foreground='#1f2937')
        style.configure('TEntry', font=base_font, padding=4)
        style.configure('TCheckbutton', font=base_font, background='#f5f8fc', foreground='#1f2937')
        style.configure('TRadiobutton', font=base_font, background='#f5f8fc', foreground='#1f2937')
        style.configure('TLabelframe', background='#f5f8fc', borderwidth=1, relief='solid')
        style.configure('TLabelframe.Label', font=title_font, foreground='#16324f', background='#f5f8fc')
        style.configure('Accent.TButton', background='#1f6feb', foreground='white')
        style.map('Accent.TButton', background=[('active', '#1857c4'), ('pressed', '#174ea6')])
        style.configure('TFrame', background='#eef3f9')

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="加载图片列表", command=self.load_images, accelerator="Ctrl+O")
        file_menu.add_command(label="保存当前标注", command=self.save_current_labels, accelerator="Ctrl+S")
        file_menu.add_command(label="保存所有标注", command=self.save_all_labels, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit_app)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="撤销", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="重做", command=self.redo, accelerator="Ctrl+Y")

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="查看", menu=view_menu)
        view_menu.add_command(label="上一张", command=self.prev_image, accelerator="A / ←")
        view_menu.add_command(label="下一张", command=self.next_image, accelerator="D / →")

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="快捷键说明", command=self.show_shortcuts)

    def create_widgets(self):
        self.master.configure(bg='#eef3f9')
        main_paned = ttk.PanedWindow(self.master, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        left_frame = ttk.Frame(main_paned)
        right_frame = ttk.Frame(main_paned, width=340)

        main_paned.add(left_frame, weight=4)
        main_paned.add(right_frame, weight=1)

        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor='#101827')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax = self.fig.add_subplot(111)
        self.ax.axis('off')
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.get_tk_widget().config(cursor='cross')

        dir_frame = ttk.LabelFrame(right_frame, text="文件夹设置", padding=10)
        dir_frame.pack(fill=tk.X, pady=5)
        ttk.Label(dir_frame, text="图片:").grid(row=0, column=0, sticky='w', pady=2)
        self.entry_img = ttk.Entry(dir_frame, textvariable=self.image_folder, width=22)
        self.entry_img.grid(row=0, column=1, padx=5)
        ttk.Button(dir_frame, text="浏览", command=self.select_image_folder).grid(row=0, column=2)

        ttk.Label(dir_frame, text="标注:").grid(row=1, column=0, sticky='w', pady=2)
        self.entry_lbl = ttk.Entry(dir_frame, textvariable=self.label_folder, width=22)
        self.entry_lbl.grid(row=1, column=1, padx=5)
        ttk.Button(dir_frame, text="浏览", command=self.select_label_folder).grid(row=1, column=2)

        ttk.Button(dir_frame, text="加载图片列表", command=self.load_images, style='Accent.TButton').grid(row=2, column=1, pady=8)

        mode_frame = ttk.LabelFrame(right_frame, text="编辑模式 (快捷键: Q/W/E)", padding=5)
        mode_frame.pack(fill=tk.X, pady=5)

        self.mode_var = tk.StringVar(value='view')
        ttk.Radiobutton(mode_frame, text="查看(Q)", variable=self.mode_var, value='view',
                        command=self.set_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="添加框(W)", variable=self.mode_var, value='add',
                        command=self.set_mode).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="选择/移动(E)", variable=self.mode_var, value='select',
                        command=self.set_mode).pack(side=tk.LEFT, padx=5)

        action_frame = ttk.LabelFrame(right_frame, text="标签操作", padding=8)
        action_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(action_frame, text="删除选中框 (R)", command=self.delete_selected).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(action_frame, text="修改类别 (T)", command=self.modify_class).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        undo_redo_frame = ttk.LabelFrame(right_frame, text="撤销 / 重做", padding=8)
        undo_redo_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(undo_redo_frame, text="撤销 (Ctrl+Z)", command=self.undo).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(undo_redo_frame, text="重做 (Ctrl+Y)", command=self.redo).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        save_btn_frame = ttk.LabelFrame(right_frame, text="保存", padding=8)
        save_btn_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(save_btn_frame, text="保存标注 (覆盖txt)", command=self.save_current_labels, style='Accent.TButton').pack(fill=tk.X)

        view_frame = ttk.LabelFrame(right_frame, text="视图优化", padding=5)
        view_frame.pack(fill=tk.X, pady=5)
        ttk.Checkbutton(view_frame, text="记忆每张图片视图", variable=self.remember_view_state,
                        command=self.toggle_remember_view_state).pack(anchor='w')
        ttk.Checkbutton(view_frame, text="切换时自动保存", variable=self.auto_save_on_nav).pack(anchor='w')
        ttk.Button(view_frame, text="重置视图", command=self.reset_view).pack(fill=tk.X, pady=(4, 0))
        ttk.Button(view_frame, text="适配窗口", command=self.fit_to_window).pack(fill=tk.X, pady=(4, 0))

        list_frame = ttk.LabelFrame(right_frame, text="图片列表", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_container, width=30, height=16,
                                  font=('微软雅黑', 9), selectmode=tk.SINGLE,
                                  bg='white', fg='#333', selectbackground='#0078d7',
                                  activestyle='none', exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.bind('<<ListboxSelect>>', self.on_listbox_select)
        self.listbox.bind('<Double-Button-1>', self.on_listbox_double_click)

        nav_frame = ttk.Frame(right_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(nav_frame, text="◀ 上一张 (A)", command=self.prev_image).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)
        ttk.Button(nav_frame, text="下一张 (D) ▶", command=self.next_image).pack(side=tk.LEFT, padx=2, expand=True, fill=tk.X)

        status_frame = ttk.LabelFrame(right_frame, text="状态栏", padding=6)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        self.status_image = ttk.Label(status_frame, text="图片: -", anchor='w')
        self.status_image.pack(fill=tk.X)
        self.status_label_count = ttk.Label(status_frame, text="标签数: -", anchor='w')
        self.status_label_count.pack(fill=tk.X)
        self.status_zoom = ttk.Label(status_frame, text="缩放: -", anchor='w')
        self.status_zoom.pack(fill=tk.X)
        self.status_modified = ttk.Label(status_frame, text="已修改: -", anchor='w')
        self.status_modified.pack(fill=tk.X)
        self.status_label = ttk.Label(status_frame, text="状态: 就绪", relief='sunken', anchor='w', padding=5)
        self.status_label.pack(fill=tk.X, pady=(6, 0))

    def setup_matplotlib_events(self):
        self.cid_press = self.fig.canvas.mpl_connect('button_press_event', self.on_press)
        self.cid_release = self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_pick = self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.cid_scroll = self.fig.canvas.mpl_connect('scroll_event', self.on_scroll)
        self.cid_draw = self.fig.canvas.mpl_connect('draw_event', self.on_draw_event)

    def reset_drag_state(self):
        """彻底清除鼠标拖拽与选框临时状态"""
        self.dragging_box = False
        self.drag_action = None
        self.drag_idx = -1
        self.drag_start_mouse = None
        self.drag_start_box = None
        self.drag_state_pushed = False
        self.rect_start = None

    def show_quick_notification(self, title, message):
        if self.noti_win and self.noti_win.winfo_exists():
            try:
                self.noti_win.destroy()
            except Exception:
                pass
            
        self.noti_win = tk.Toplevel(self.master)
        self.noti_win.title(title)
        self.noti_win.geometry("380x140")
        self.noti_win.resizable(False, False)
        self.noti_win.transient(self.master)
        
        self.noti_win.update_idletasks()
        x = self.master.winfo_rootx() + (self.master.winfo_width() - 380) // 2
        y = self.master.winfo_rooty() + (self.master.winfo_height() - 140) // 2
        self.noti_win.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(self.noti_win, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        lbl = ttk.Label(frame, text=message, font=('微软雅黑', 10), wraplength=340, justify='center')
        lbl.pack(expand=True)
        
        tip = ttk.Label(frame, text="💡 点击通知框任意处 或 按任意键关闭", font=('微软雅黑', 8), foreground='#0078d7')
        tip.pack(pady=(5, 0))

        def close_noti(event=None):
            if self.noti_win and self.noti_win.winfo_exists():
                self.noti_win.destroy()

        self.noti_win.bind('<Button-1>', close_noti)
        self.noti_win.bind('<Key>', close_noti)
        frame.bind('<Button-1>', close_noti)
        lbl.bind('<Button-1>', close_noti)
        tip.bind('<Button-1>', close_noti)
        
        self.noti_win.focus_set()

    def ask_yes_no(self, title, message):
        return messagebox.askyesno(title, message, parent=self.master)

    def ask_ok_cancel(self, title, message):
        return messagebox.askokcancel(title, message, parent=self.master)

    def show_info(self, title, message):
        return messagebox.showinfo(title, message, parent=self.master)

    def show_warning(self, title, message):
        return messagebox.showwarning(title, message, parent=self.master)

    def show_error(self, title, message):
        return messagebox.showerror(title, message, parent=self.master)

    def ask_integer(self, title, message, **kwargs):
        kwargs.setdefault("parent", self.master)
        return simpledialog.askinteger(title, message, **kwargs)


    def set_status_message(self, message, color='black'):
        self.status_message = message
        self.status_label.config(text=f"状态: {message}", foreground=color)

    def update_status_panel(self):
        if self.current_image_bgr is None or not self.image_files:
            self.status_image.config(text="图片: -")
            self.status_label_count.config(text="标签数: -")
            self.status_zoom.config(text="缩放: -")
            self.status_modified.config(text="已修改: -")
            return
        self.status_image.config(text=f"图片: {self.image_files[self.current_idx]}")
        self.status_label_count.config(text=f"标签数: {len(self.current_labels)}")
        self.status_zoom.config(text=f"缩放: {self.get_zoom_text()}")
        self.status_modified.config(text=f"已修改: {'是' if self.modified else '否'}")

    def get_zoom_text(self):
        if self.current_image_bgr is None:
            return "-"
        img_h, img_w = self.current_image_bgr.shape[:2]
        x0, x1 = self.ax.get_xlim()
        view_w = max(1.0, abs(x1 - x0))
        return f"{img_w / view_w:.2f}x"

    def get_view_state_key(self):
        if not self.image_files:
            return None
        return os.path.join(self.image_folder.get(), self.image_files[self.current_idx])

    def cache_view_state(self):
        if not self.remember_view_state.get() or self.current_image_bgr is None:
            return
        key = self.get_view_state_key()
        if key:
            self.view_state_cache[key] = {'xlim': self.ax.get_xlim(), 'ylim': self.ax.get_ylim()}

    def restore_view_state(self):
        if not self.remember_view_state.get() or self.current_image_bgr is None:
            return False
        key = self.get_view_state_key()
        state = self.view_state_cache.get(key)
        if not state:
            return False
        self.ax.set_xlim(state['xlim'])
        self.ax.set_ylim(state['ylim'])
        return True

    def fit_to_window(self):
        if self.current_image_bgr is None:
            return
        img_h, img_w = self.current_image_bgr.shape[:2]
        self.ax.set_xlim(0, img_w)
        self.ax.set_ylim(img_h, 0)
        self.canvas.draw_idle()
        self.set_status_message("已重置视图")
        self.update_status_panel()

    def reset_view(self):
        self.fit_to_window()

    def toggle_remember_view_state(self):
        if not self.remember_view_state.get():
            self.view_state_cache.clear()
        self.set_status_message("视图记忆设置已更新")
        self.update_status_panel()


    def set_status_message(self, message, color='black'):
        self.status_message = message
        self.status_label.config(text=f"状态: {message}", foreground=color)

    def update_status_panel(self):
        if self.current_image_bgr is None or not self.image_files:
            self.status_image.config(text="图片: -")
            self.status_label_count.config(text="标签数: -")
            self.status_zoom.config(text="缩放: -")
            self.status_modified.config(text="已修改: -")
            return
        image_name = self.image_files[self.current_idx]
        self.status_image.config(text=f"图片: {image_name}")
        self.status_label_count.config(text=f"标签数: {len(self.current_labels)}")
        self.status_zoom.config(text=f"缩放: {self.get_zoom_text()}")
        self.status_modified.config(text=f"已修改: {'是' if self.modified else '否'}")

    def get_zoom_text(self):
        if self.current_image_bgr is None:
            return "-"
        img_h, img_w = self.current_image_bgr.shape[:2]
        x0, x1 = self.ax.get_xlim()
        view_w = max(1.0, abs(x1 - x0))
        return f"{img_w / view_w:.2f}x"

    def get_view_state_key(self):
        if not self.image_files:
            return None
        return os.path.join(self.image_folder.get(), self.image_files[self.current_idx])

    def cache_view_state(self):
        if not self.remember_view_state.get() or self.current_image_bgr is None:
            return
        key = self.get_view_state_key()
        if key:
            self.view_state_cache[key] = {'xlim': self.ax.get_xlim(), 'ylim': self.ax.get_ylim()}

    def restore_view_state(self):
        if not self.remember_view_state.get() or self.current_image_bgr is None:
            return False
        key = self.get_view_state_key()
        state = self.view_state_cache.get(key)
        if not state:
            return False
        self.ax.set_xlim(state['xlim'])
        self.ax.set_ylim(state['ylim'])
        return True

    def fit_to_window(self):
        if self.current_image_bgr is None:
            return
        img_h, img_w = self.current_image_bgr.shape[:2]
        self.ax.set_xlim(0, img_w)
        self.ax.set_ylim(img_h, 0)
        self.canvas.draw_idle()
        self.set_status_message("已重置视图")
        self.update_status_panel()

    def reset_view(self):
        self.fit_to_window()

    def toggle_remember_view_state(self):
        if not self.remember_view_state.get():
            self.view_state_cache.clear()
        self.set_status_message("视图记忆设置已更新")
        self.update_status_panel()

    def push_state(self):
        self.undo_stack.append(copy.deepcopy(self.current_labels))
        if len(self.undo_stack) > 50:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        focused = self.master.focus_get()
        if isinstance(focused, (ttk.Entry, tk.Entry)):
            return
        if not self.undo_stack:
            return
        self.redo_stack.append(copy.deepcopy(self.current_labels))
        self.current_labels = self.undo_stack.pop()
        self.modified = True
        self.clear_selection()
        self.redraw_display()

    def redo(self):
        focused = self.master.focus_get()
        if isinstance(focused, (ttk.Entry, tk.Entry)):
            return
        if not self.redo_stack:
            return
        self.undo_stack.append(copy.deepcopy(self.current_labels))
        self.current_labels = self.redo_stack.pop()
        self.modified = True
        self.clear_selection()
        self.redraw_display()

    def on_draw_event(self, event):
        if event.canvas == self.canvas:
            self.background_cache = self.canvas.copy_from_bbox(self.ax.bbox)

    def get_clamped_mouse_coords(self, event):
        if self.current_image_bgr is None or event.x is None or event.y is None:
            return None, None
        img_h, img_w = self.current_image_bgr.shape[:2]
        try:
            inv = self.ax.transData.inverted()
            x_data, y_data = inv.transform((event.x, event.y))
            x_clamped = max(0.0, min(float(img_w), float(x_data)))
            y_clamped = max(0.0, min(float(img_h), float(y_data)))
            return x_clamped, y_clamped
        except Exception:
            return None, None

    def get_box_coords_px(self, lb):
        img_h, img_w = self.current_image_bgr.shape[:2]
        xc = lb['x_center'] * img_w
        yc = lb['y_center'] * img_h
        bw = lb['width'] * img_w
        bh = lb['height'] * img_h
        x1 = max(0.0, xc - bw/2)
        y1 = max(0.0, yc - bh/2)
        x2 = min(float(img_w), xc + bw/2)
        y2 = min(float(img_h), yc + bh/2)
        return x1, y1, x2, y2

    # 滚轮响应：直接滚轮上下平移，Shift 左右平移，Ctrl 缩放
    def on_scroll(self, event):
        if event.inaxes != self.ax or self.current_image_bgr is None:
            return

        key = (event.key or '').lower()

        # ---------- 1. Ctrl + 滚轮：以鼠标为中心放大/缩小 ----------
        if 'control' in key or 'ctrl' in key:
            xdata, ydata = event.xdata, event.ydata
            if xdata is None or ydata is None:
                return

            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()
            scale_factor = 0.8 if event.button == 'up' else (1.25 if event.button == 'down' else 1.0)

            new_x_min = xdata - (xdata - x_min) * scale_factor
            new_x_max = xdata + (x_max - xdata) * scale_factor
            new_y_min = ydata - (ydata - y_min) * scale_factor
            new_y_max = ydata + (y_max - ydata) * scale_factor

            self.ax.set_xlim([new_x_min, new_x_max])
            self.ax.set_ylim([new_y_min, new_y_max])
            self.canvas.draw_idle()
            return

        # ---------- 2. Shift + 滚轮：图片左右滑动平移 ----------
        if 'shift' in key:
            x_min, x_max = self.ax.get_xlim()
            view_width = x_max - x_min
            step = view_width * 0.1  # 每次滑动当前可视宽度的 10%

            if event.button == 'up':
                dx = -step  # 向上滚：向左平移
            elif event.button == 'down':
                dx = step   # 向下滚：向右平移
            else:
                dx = 0

            if dx != 0:
                self.ax.set_xlim([x_min + dx, x_max + dx])
                self.canvas.draw_idle()
            return

        # ---------- 3. 直接滚轮：图片上下滑动平移 ----------
        y_min, y_max = self.ax.get_ylim()
        view_height = abs(y_max - y_min)
        step = view_height * 0.1  # 每次滑动当前可视高度的 10%

        if event.button == 'up':
            dy = -step  # 向上滚：向上平移
        elif event.button == 'down':
            dy = step   # 向下滚：向下平移
        else:
            dy = 0

        if dy != 0:
            self.ax.set_ylim([y_min + dy, y_max + dy])
            self.canvas.draw_idle()

    def set_mode(self):
        self.mode = self.mode_var.get()
        curr_cls_str = f" | 默认类别: {self.last_class_id}" if self.last_class_id is not None else ""
        self.status_label.config(text=f"模式: {self.mode}{curr_cls_str}", foreground='black')
        self.clear_selection()
        self.reset_drag_state()
        self.redraw_display()

    def switch_mode_by_key(self, mode_name):
        focused = self.master.focus_get()
        if isinstance(focused, (ttk.Entry, tk.Entry)):
            return
        self.mode_var.set(mode_name)
        self.set_mode()

    def safe_prev_image(self, event=None):
        focused = self.master.focus_get()
        if isinstance(focused, (ttk.Entry, tk.Entry)):
            return
        self.prev_image()

    def safe_next_image(self, event=None):
        focused = self.master.focus_get()
        if isinstance(focused, (ttk.Entry, tk.Entry)):
            return
        self.next_image()

    def select_image_folder(self):
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            self.image_folder.set(folder)
            self.config['image_folder'] = folder
            save_config(self.config)

    def select_label_folder(self):
        folder = filedialog.askdirectory(title="选择标注文件夹 (若与图片相同可不选)")
        if folder:
            self.label_folder.set(folder)
            self.config['label_folder'] = folder
            save_config(self.config)
        else:
            if self.image_folder.get():
                self.label_folder.set(self.image_folder.get())

    def load_images(self):
        img_folder = self.image_folder.get()
        if not img_folder:
            self.show_error("错误", "请先选择图片文件夹")
            return
        if not self.label_folder.get():
            self.label_folder.set(img_folder)

        ext_list = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
        files = [f for f in os.listdir(img_folder) if f.lower().endswith(ext_list)]
        if not files:
            self.show_info("提示", "该文件夹中没有支持的图片文件")
            return
        files.sort()
        self.image_files = files
        self.listbox.delete(0, tk.END)
        for f in files:
            self.listbox.insert(tk.END, f)
        self.current_idx = 0
        self.listbox.selection_set(0)
        self.listbox.see(0)
        self.modified = False
        self.update_display()

    def update_display(self):
        if not self.image_files:
            return
        idx = self.current_idx
        if idx < 0 or idx >= len(self.image_files):
            return
        img_path = os.path.join(self.image_folder.get(), self.image_files[idx])
        img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            self.status_label.config(text=f"无法读取: {self.image_files[idx]}")
            return
        self.current_image_bgr = img

        base = os.path.splitext(self.image_files[idx])[0]
        label_path = os.path.join(self.label_folder.get(), base + '.txt')
        self.current_labels = load_yolo_labels(label_path) if os.path.exists(label_path) else []
        self.modified = False
        
        self.undo_stack.clear()
        self.redo_stack.clear()

        self.is_new_image = True
        self.drawing_rect = None
        self.reset_drag_state()
        self.redraw_display()

    # ---------- 画布重建与高性能双缓冲初始化 ----------
    def redraw_display(self):
        if self.current_image_bgr is None:
            return

        self.cache_view_state()
        xlim, ylim = None, None
        if not self.is_new_image:
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()

        rgb = cv2.cvtColor(self.current_image_bgr, cv2.COLOR_BGR2RGB)
        self.ax.clear()
        self.ax.imshow(rgb)
        self.ax.axis('off')
        
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        if not self.restore_view_state() and xlim is not None and ylim is not None:
            self.ax.set_xlim(xlim)
            self.ax.set_ylim(ylim)
        elif xlim is None and ylim is None:
            img_h, img_w = self.current_image_bgr.shape[:2]
            self.ax.set_xlim(0, img_w)
            self.ax.set_ylim(img_h, 0)

        self.is_new_image = False

        self.coord_text = self.ax.text(0.01, 0.02, '', transform=self.ax.transAxes,
                                       color='yellow', fontsize=10, animated=True,
                                       bbox=dict(facecolor='black', alpha=0.6, edgecolor='none'))

        self.hline = Line2D([], [], color='lightgray', linewidth=1, linestyle='-', alpha=0.6, visible=False, animated=True)
        self.vline = Line2D([], [], color='lightgray', linewidth=1, linestyle='-', alpha=0.6, visible=False, animated=True)
        self.ax.add_line(self.hline)
        self.ax.add_line(self.vline)

        self.rect_patches = []
        self.text_artists = []

        for i, lb in enumerate(self.current_labels):
            x1, y1, x2, y2 = self.get_box_coords_px(lb)
            is_selected = (i == self.selected_idx)

            rect = Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False,
                             edgecolor='red' if is_selected else 'cyan',
                             linewidth=3 if is_selected else 2,
                             animated=True)
            self.ax.add_patch(rect)
            self.rect_patches.append(rect)

            bg_color = 'red' if is_selected else '#0078d7'
            txt = self.ax.text(x1, y1-5 if y1 >= 15 else y1+15, str(lb['class_id']), color='white',
                               fontsize=10, bbox=dict(facecolor=bg_color, alpha=0.8, edgecolor='none'),
                               picker=True, animated=True)
            txt.label_idx = i
            txt.is_text_label = True
            self.text_artists.append(txt)

        self.corner_handles_line = Line2D([], [], marker='s', color='yellow', markeredgecolor='black',
                                           linestyle='None', markersize=7, animated=True)
        self.ax.add_line(self.corner_handles_line)

        if 0 <= self.selected_idx < len(self.current_labels):
            x1, y1, x2, y2 = self.get_box_coords_px(self.current_labels[self.selected_idx])
            self.corner_handles_line.set_data([x1, x2, x1, x2], [y1, y1, y2, y2])
            self.corner_handles_line.set_visible(True)
        else:
            self.corner_handles_line.set_visible(False)

        self.canvas.draw()
        self.background_cache = self.canvas.copy_from_bbox(self.ax.bbox)
        self.fast_render_all()

        cls_info = f" | 默认类别: {self.last_class_id}" if self.last_class_id is not None else " | 未设置默认类别"
        self.status_label.config(
            text=f"第 {self.current_idx+1}/{len(self.image_files)} 张 | 标注数: {len(self.current_labels)}{cls_info}",
            foreground='black'
        )

    # ---------- Blitting 局部极速渲染 ----------
    def fast_render_all(self, x_m=None, y_m=None):
        if self.background_cache is None or self.current_image_bgr is None:
            return

        img_h, img_w = self.current_image_bgr.shape[:2]
        self.canvas.restore_region(self.background_cache)

        for patch in self.rect_patches:
            self.ax.draw_artist(patch)

        for txt in self.text_artists:
            self.ax.draw_artist(txt)

        if self.corner_handles_line and self.corner_handles_line.get_visible():
            self.ax.draw_artist(self.corner_handles_line)

        if x_m is not None and y_m is not None:
            if self.coord_text is not None:
                self.coord_text.set_text(f'x: {int(x_m)}  y: {int(y_m)}')
                self.ax.draw_artist(self.coord_text)

            if self.hline is not None and self.vline is not None:
                self.hline.set_data([0, img_w-1], [y_m, y_m])
                self.vline.set_data([x_m, x_m], [0, img_h-1])
                self.hline.set_visible(True)
                self.vline.set_visible(True)
                self.ax.draw_artist(self.hline)
                self.ax.draw_artist(self.vline)

            if self.mode == 'add' and self.rect_start is not None:
                x0, y0 = self.rect_start
                width = abs(x_m - x0)
                height = abs(y_m - y0)
                if width > 2 and height > 2:
                    x = min(x0, x_m)
                    y = min(y0, y_m)
                    if self.drawing_rect is None:
                        self.drawing_rect = Rectangle((x, y), width, height, fill=False,
                                                      edgecolor='yellow', linewidth=2, linestyle='--', animated=True)
                        self.ax.add_patch(self.drawing_rect)
                    else:
                        self.drawing_rect.set_xy((x, y))
                        self.drawing_rect.set_width(width)
                        self.drawing_rect.set_height(height)
                        self.drawing_rect.set_visible(True)
                    self.ax.draw_artist(self.drawing_rect)

        self.canvas.blit(self.ax.bbox)
        self.update_status_panel()

    # ---------- 鼠标按下 ----------
    def on_press(self, event):
        if event.button != 1 or self.current_image_bgr is None:
            return

        x_m, y_m = self.get_clamped_mouse_coords(event)
        if x_m is None or y_m is None:
            return

        if self.mode == 'add':
            self.clear_selection()
            self.rect_start = (x_m, y_m)
            return

        ax_w = abs(self.ax.get_xlim()[1] - self.ax.get_xlim()[0])
        corner_thresh = max(12.0, ax_w * 0.025)

        # [优先级 1] 当前选中框的 4 个角点
        if 0 <= self.selected_idx < len(self.current_labels):
            x1, y1, x2, y2 = self.get_box_coords_px(self.current_labels[self.selected_idx])
            box_w, box_h = x2 - x1, y2 - y1
            thresh = min(corner_thresh, max(8.0, min(box_w, box_h) * 0.45))

            dists = {
                'tl': math.hypot(x_m - x1, y_m - y1),
                'tr': math.hypot(x_m - x2, y_m - y1),
                'bl': math.hypot(x_m - x1, y_m - y2),
                'br': math.hypot(x_m - x2, y_m - y2)
            }
            best_corner, min_dist = min(dists.items(), key=lambda item: item[1])

            if min_dist <= thresh:
                self.start_drag(self.selected_idx, best_corner, (x_m, y_m), (x1, y1, x2, y2))
                return

        # [优先级 2] 其他框的 4 个角点
        for i, lb in enumerate(self.current_labels):
            if i == self.selected_idx:
                continue
            x1, y1, x2, y2 = self.get_box_coords_px(lb)
            box_w, box_h = x2 - x1, y2 - y1
            thresh = min(corner_thresh, max(8.0, min(box_w, box_h) * 0.45))

            dists = {
                'tl': math.hypot(x_m - x1, y_m - y1),
                'tr': math.hypot(x_m - x2, y_m - y1),
                'bl': math.hypot(x_m - x1, y_m - y2),
                'br': math.hypot(x_m - x2, y_m - y2)
            }
            best_corner, min_dist = min(dists.items(), key=lambda item: item[1])

            if min_dist <= thresh:
                self.selected_idx = i
                self.redraw_display()
                self.start_drag(i, best_corner, (x_m, y_m), (x1, y1, x2, y2))
                return

        # [优先级 3] 当前选中框内部
        if self.mode == 'select' and 0 <= self.selected_idx < len(self.current_labels):
            x1, y1, x2, y2 = self.get_box_coords_px(self.current_labels[self.selected_idx])
            if x1 <= x_m <= x2 and y1 <= y_m <= y2:
                self.start_drag(self.selected_idx, 'move', (x_m, y_m), (x1, y1, x2, y2))
                return

        # [优先级 4] 其他框内部（重叠优先选中小框）
        if self.mode == 'select':
            hit_indices = []
            for i, lb in enumerate(self.current_labels):
                x1, y1, x2, y2 = self.get_box_coords_px(lb)
                if x1 <= x_m <= x2 and y1 <= y_m <= y2:
                    area = (x2 - x1) * (y2 - y1)
                    hit_indices.append((i, area, (x1, y1, x2, y2)))

            if hit_indices:
                hit_indices.sort(key=lambda x: x[1])
                best_idx, _, box_coords = hit_indices[0]
                self.selected_idx = best_idx
                self.redraw_display()
                self.start_drag(best_idx, 'move', (x_m, y_m), box_coords)
                return

            self.clear_selection()

    def start_drag(self, idx, action, mouse_pos, box_coords):
        if not self.drag_state_pushed:
            self.push_state()
            self.drag_state_pushed = True
        self.dragging_box = True
        self.drag_action = action
        self.drag_idx = idx
        self.drag_start_mouse = mouse_pos
        self.drag_start_box = box_coords

    # ---------- 鼠标移动 ----------
    def on_motion(self, event):
        if self.current_image_bgr is None:
            return

        if event.button != 1 and self.dragging_box:
            self.reset_drag_state()

        img_h, img_w = self.current_image_bgr.shape[:2]
        x_m, y_m = self.get_clamped_mouse_coords(event)

        if self.dragging_box:
            if x_m is None or y_m is None:
                return

            sx, sy = self.drag_start_mouse
            x1, y1, x2, y2 = self.drag_start_box
            dx = x_m - sx
            dy = y_m - sy

            if self.drag_action == 'move':
                w_box = x2 - x1
                h_box = y2 - y1
                w_box = min(w_box, img_w)
                h_box = min(h_box, img_h)

                nx1 = max(0, min(img_w - w_box, x1 + dx))
                ny1 = max(0, min(img_h - h_box, y1 + dy))
                nx2 = nx1 + w_box
                ny2 = ny1 + h_box
            else:
                nx1, ny1, nx2, ny2 = x1, y1, x2, y2
                min_size = 5
                if 't' in self.drag_action:
                    ny1 = max(0, min(y1 + dy, y2 - min_size))
                if 'b' in self.drag_action:
                    ny2 = min(img_h, max(y2 + dy, y1 + min_size))
                if 'l' in self.drag_action:
                    nx1 = max(0, min(x1 + dx, x2 - min_size))
                if 'r' in self.drag_action:
                    nx2 = min(img_w, max(x2 + dx, x1 + min_size))

            bw = (nx2 - nx1) / float(img_w)
            bh = (ny2 - ny1) / float(img_h)
            xc = (nx1 + nx2) / 2.0 / float(img_w)
            yc = (ny1 + ny2) / 2.0 / float(img_h)

            idx = self.drag_idx
            self.current_labels[idx]['x_center'] = xc
            self.current_labels[idx]['y_center'] = yc
            self.current_labels[idx]['width'] = bw
            self.current_labels[idx]['height'] = bh
            self.modified = True

            if idx < len(self.rect_patches):
                self.rect_patches[idx].set_xy((nx1, ny1))
                self.rect_patches[idx].set_width(nx2 - nx1)
                self.rect_patches[idx].set_height(ny2 - ny1)

            if idx < len(self.text_artists):
                self.text_artists[idx].set_position((nx1, ny1-5 if ny1 >= 15 else ny1+15))

            if self.corner_handles_line:
                self.corner_handles_line.set_data([nx1, nx2, nx1, nx2], [ny1, ny1, ny2, ny2])

            self.fast_render_all(x_m, y_m)
            return

        self.fast_render_all(x_m, y_m)

    def on_release(self, event):
        if self.dragging_box:
            self.reset_drag_state()
            self.redraw_display()
            return

        if self.mode != 'add' or self.rect_start is None:
            return

        x0, y0 = self.rect_start
        self.rect_start = None

        x_m, y_m = self.get_clamped_mouse_coords(event)

        if self.drawing_rect:
            self.drawing_rect.set_visible(False)
            self.drawing_rect = None

        if x_m is None or y_m is None:
            return

        img_h, img_w = self.current_image_bgr.shape[:2]

        xmin, xmax = min(x0, x_m), max(x0, x_m)
        ymin, ymax = min(y0, y_m), max(y0, y_m)

        width = xmax - xmin
        height = ymax - ymin
        if width < 5 or height < 5:
            return

        x_center = (xmin + width / 2.0) / img_w
        y_center = (ymin + height / 2.0) / img_h
        width_norm = width / img_w
        height_norm = height / img_h

        if self.last_class_id is None:
            self.reset_drag_state()
            class_id = self.ask_integer("设置初始类别", "请输入首个标注框类别 ID (0-9):", minvalue=0, maxvalue=9)
            self.reset_drag_state()
            if class_id is None:
                return
            self.last_class_id = class_id
            self.config['last_class_id'] = class_id
            save_config(self.config)
        else:
            class_id = self.last_class_id

        self.push_state()
        new_label = {
            'class_id': class_id,
            'x_center': x_center,
            'y_center': y_center,
            'width': width_norm,
            'height': height_norm
        }
        self.current_labels.append(new_label)
        self.selected_idx = len(self.current_labels) - 1
        self.modified = True
        self.redraw_display()

    # ---------- 类别修改事件响应 ----------
    def on_pick(self, event):
        if self.dragging_box:
            return

        artist = event.artist
        if getattr(artist, 'is_text_label', False) and event.mouseevent and event.mouseevent.dblclick:
            idx = getattr(artist, 'label_idx', -1)
            if idx >= 0:
                self.change_class_by_index(idx)

    def change_class_by_index(self, idx):
        if idx < 0 or idx >= len(self.current_labels):
            return

        self.reset_drag_state()
        self.dragging_box = False
        self.rect_start = None

        old_class = self.current_labels[idx]['class_id']
        new_id = self.ask_integer(
            "修改类别",
            f"当前标注框类别: {old_class}\n请输入新类别 ID (0-9):",
            minvalue=0, maxvalue=9,
            initialvalue=old_class
        )

        self.reset_drag_state()
        self.dragging_box = False
        self.rect_start = None

        if new_id is not None and new_id != old_class:
            self.push_state()
            self.current_labels[idx]['class_id'] = new_id
            self.last_class_id = new_id
            self.config['last_class_id'] = new_id
            save_config(self.config)

            self.modified = True
            self.redraw_display()

    def clear_selection(self):
        if self.selected_idx != -1:
            self.selected_idx = -1
            self.redraw_display()

    def duplicate_selected(self):
        if self.selected_idx < 0 or self.selected_idx >= len(self.current_labels):
            self.show_warning("提示", "请先选中一个标注框")
            return
        lb = copy.deepcopy(self.current_labels[self.selected_idx])
        img_h, img_w = self.current_image_bgr.shape[:2]
        x1, y1, x2, y2 = self.get_box_coords_px(lb)
        offset_x = min(20.0, max(5.0, (x2 - x1) * 0.1))
        offset_y = min(20.0, max(5.0, (y2 - y1) * 0.1))
        nx1 = min(max(0.0, x1 + offset_x), img_w - 1)
        ny1 = min(max(0.0, y1 + offset_y), img_h - 1)
        nx2 = min(float(img_w), nx1 + (x2 - x1))
        ny2 = min(float(img_h), ny1 + (y2 - y1))
        self.push_state()
        lb['x_center'] = ((nx1 + nx2) / 2.0) / img_w
        lb['y_center'] = ((ny1 + ny2) / 2.0) / img_h
        lb['width'] = (nx2 - nx1) / img_w
        lb['height'] = (ny2 - ny1) / img_h
        self.current_labels.append(lb)
        self.selected_idx = len(self.current_labels) - 1
        self.modified = True
        self.set_status_message("已复制当前标注框")
        self.redraw_display()

    def align_selected_to_edges(self):
        if self.selected_idx < 0 or self.selected_idx >= len(self.current_labels):
            self.show_warning("提示", "请先选中一个标注框")
            return
        img_h, img_w = self.current_image_bgr.shape[:2]
        lb = self.current_labels[self.selected_idx]
        x1, y1, x2, y2 = self.get_box_coords_px(lb)
        distances = {
            'left': x1,
            'right': img_w - x2,
            'top': y1,
            'bottom': img_h - y2
        }
        edge = min(distances, key=distances.get)
        self.push_state()
        if edge == 'left':
            x2 -= x1
            x1 = 0
        elif edge == 'right':
            x1 += distances['right']
            x2 = float(img_w)
        elif edge == 'top':
            y2 -= y1
            y1 = 0
        else:
            y1 += distances['bottom']
            y2 = float(img_h)
        lb['x_center'] = ((x1 + x2) / 2.0) / img_w
        lb['y_center'] = ((y1 + y2) / 2.0) / img_h
        lb['width'] = (x2 - x1) / img_w
        lb['height'] = (y2 - y1) / img_h
        self.modified = True
        self.set_status_message(f"已对齐到{edge}边缘")
        self.redraw_display()

    def nudge_selected(self, dx=0, dy=0, resize=False, dw=0, dh=0):
        if self.selected_idx < 0 or self.selected_idx >= len(self.current_labels):
            return
        img_h, img_w = self.current_image_bgr.shape[:2]
        lb = self.current_labels[self.selected_idx]
        x1, y1, x2, y2 = self.get_box_coords_px(lb)
        self.push_state()
        if resize:
            x2 = min(float(img_w), max(x1 + 5, x2 + dw))
            y2 = min(float(img_h), max(y1 + 5, y2 + dh))
        else:
            width = x2 - x1
            height = y2 - y1
            x1 = max(0.0, min(float(img_w) - width, x1 + dx))
            y1 = max(0.0, min(float(img_h) - height, y1 + dy))
            x2 = x1 + width
            y2 = y1 + height
        lb['x_center'] = ((x1 + x2) / 2.0) / img_w
        lb['y_center'] = ((y1 + y2) / 2.0) / img_h
        lb['width'] = (x2 - x1) / img_w
        lb['height'] = (y2 - y1) / img_h
        self.modified = True
        self.redraw_display()

    def delete_selected(self):
        focused = self.master.focus_get()
        if isinstance(focused, (ttk.Entry, tk.Entry)):
            return
            
        if self.selected_idx < 0 or self.selected_idx >= len(self.current_labels):
            self.show_warning("提示", "请先选择一个标注框（选择模式下点击框）")
            return
        if self.ask_yes_no("确认删除", f"确定要删除类别 {self.current_labels[self.selected_idx]['class_id']} 的标注框吗？"):
            self.push_state()
            del self.current_labels[self.selected_idx]
            self.modified = True
            self.clear_selection()

    def modify_class(self):
        if self.selected_idx < 0 or self.selected_idx >= len(self.current_labels):
            self.show_warning("提示", "请先选择一个标注框或直接双击图片上的类别编号")
            return
        self.change_class_by_index(self.selected_idx)

    def modify_class_by_key(self):
        """按 T 键修改当前选中框的类别（仅在 select 模式下）"""
        focused = self.master.focus_get()
        if isinstance(focused, (ttk.Entry, tk.Entry)):
            return
        if self.mode != 'select':
            return
        if self.selected_idx < 0 or self.selected_idx >= len(self.current_labels):
            self.show_warning("提示", "请先选择一个标注框（选择模式下点击框）")
            return
        self.change_class_by_index(self.selected_idx)

    # ---------- 保存 (静默模式优化) ----------
    def save_current_labels(self):
        if not self.image_files:
            self.show_warning("提示", "没有加载任何图片")
            return
        
        if not self.modified:
            self.status_label.config(text="当前标注未修改，已为您静默跳过保存", foreground='#666666')
            return

        base = os.path.splitext(self.image_files[self.current_idx])[0]
        label_path = os.path.join(self.label_folder.get(), base + '.txt')
        save_yolo_labels(label_path, self.current_labels)
        self.modified = False
        self.status_label.config(text=f"标注已保存到 {label_path}", foreground='green')
        self.show_quick_notification("保存成功", f"标注已保存到:\n{label_path}")

    def save_all_labels(self):
        if not self.image_files:
            self.show_warning("提示", "没有加载任何图片")
            return
        if self.modified:
            self.save_current_labels()
        else:
            saved = 0
            for fname in self.image_files:
                base = os.path.splitext(fname)[0]
                label_path = os.path.join(self.label_folder.get(), base + '.txt')
                labels = load_yolo_labels(label_path) if os.path.exists(label_path) else []
                save_yolo_labels(label_path, labels)
                saved += 1
            self.status_label.config(text=f"已保存 {saved} 个标注文件", foreground='blue')
            self.show_quick_notification("保存完成", f"已保存 {saved} 个标注文件（覆盖原文件）")

    # ---------- 导航与准确过滤拦截 ----------
    def prev_image(self):
        if self.current_idx <= 0:
            return
        if self.modified and not self.ask_yes_no("未保存", "当前标注已修改，切换到其他图片将丢失修改，确定继续？"):
            return
        self.current_idx -= 1
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.current_idx)
        self.listbox.see(self.current_idx)
        self.clear_selection()
        self.update_display()

    def next_image(self):
        if self.current_idx >= len(self.image_files) - 1:
            return
        if self.modified and not self.ask_yes_no("未保存", "当前标注已修改，切换到其他图片将丢失修改，确定继续？"):
            return
        self.current_idx += 1
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(self.current_idx)
        self.listbox.see(self.current_idx)
        self.clear_selection()
        self.update_display()

    def on_listbox_select(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        
        target_idx = selection[0]
        if target_idx == self.current_idx:
            return

        if self.modified and not self.ask_yes_no("未保存", "当前标注已修改，切换到其他图片将丢失修改，确定继续？"):
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_idx)
            return

        self.current_idx = target_idx
        self.clear_selection()
        self.update_display()

    def on_listbox_double_click(self, event):
        self.update_display()

    # ---------- 快捷键绑定 ----------
    def bind_shortcuts(self):
        self.master.bind('<Left>', lambda e: self.safe_prev_image())
        self.master.bind('<Right>', lambda e: self.safe_next_image())
        self.master.bind('<Control-o>', lambda e: self.load_images())
        self.master.bind('<Control-s>', lambda e: self.save_current_labels())
        self.master.bind('<Control-Shift-S>', lambda e: self.save_all_labels())
        self.master.bind('<Escape>', lambda e: self.quit_app())
        self.master.bind('<Control-d>', lambda e: self.duplicate_selected())
        self.master.bind('<Control-r>', lambda e: self.align_selected_to_edges())
        self.master.bind('<Control-0>', lambda e: self.reset_view())
        self.master.bind('<Shift-Left>', lambda e: self.nudge_selected(dx=-1))
        self.master.bind('<Shift-Right>', lambda e: self.nudge_selected(dx=1))
        self.master.bind('<Shift-Up>', lambda e: self.nudge_selected(dy=-1))
        self.master.bind('<Shift-Down>', lambda e: self.nudge_selected(dy=1))
        self.master.bind('<Control-Shift-Left>', lambda e: self.nudge_selected(resize=True, dw=-1, dh=0))
        self.master.bind('<Control-Shift-Right>', lambda e: self.nudge_selected(resize=True, dw=1, dh=0))
        self.master.bind('<Control-Shift-Up>', lambda e: self.nudge_selected(resize=True, dw=0, dh=-1))
        self.master.bind('<Control-Shift-Down>', lambda e: self.nudge_selected(resize=True, dw=0, dh=1))

        for key in ['a', 'A']:
            self.master.bind(key, self.safe_prev_image)
        for key in ['d', 'D']:
            self.master.bind(key, self.safe_next_image)

        for key in ['<Control-z>', '<Control-Z>']:
            self.master.bind(key, lambda e: self.undo())
        for key in ['<Control-y>', '<Control-Y>']:
            self.master.bind(key, lambda e: self.redo())

        for key in ['q', 'Q']:
            self.master.bind(key, lambda e: self.switch_mode_by_key('view'))
        for key in ['w', 'W']:
            self.master.bind(key, lambda e: self.switch_mode_by_key('add'))
        for key in ['e', 'E']:
            self.master.bind(key, lambda e: self.switch_mode_by_key('select'))
        for key in ['r', 'R']:
            self.master.bind(key, lambda e: self.delete_selected())

        for key in ['t', 'T']:
            self.master.bind(key, lambda e: self.modify_class_by_key())

    def show_shortcuts(self):
        msg = (
            "快捷键与操作说明：\n\n"
            "A / D 或 ← / → : 切换上一张 / 下一张图片\n"
            "Q / W / E      : 快速切换模式（查看 / 添加框 / 选择与移动）\n"
            "R              : 快速删除当前选中的标注框\n"
            "T              : 修改当前选中框的类别（仅在选择模式下）\n"
            "双击类别编号    : 修改当前标注框的类别编号\n"
            "Ctrl + Z       : 撤销上一步操作\n"
            "Ctrl + Y       : 重做操作\n"
            "Ctrl+O         : 加载图片列表\n"
            "Ctrl+S         : 保存当前标注\n"
            "Ctrl+Shift+S   : 保存所有标注\n"
            "直接鼠标滚轮    : 上下平移图片\n"
            "Shift + 鼠标滚轮: 左右平移图片\n"
            "Ctrl + 鼠标滚轮 : 以鼠标位置为中心缩放图片\n"
            "Esc            : 退出"
        )
        self.show_info("快捷键与操作说明", msg)

    def quit_app(self):
        if self.modified and not self.ask_yes_no("未保存", "当前标注已修改，确定退出吗？"):
            return
        if self.ask_ok_cancel("退出", "确定退出程序吗？"):
            self.master.quit()

# ---------- 启动 ----------
def main():
    root = tk.Tk()
    app = YOLOEditor(root)
    root.mainloop()

if __name__ == "__main__":
    main()
