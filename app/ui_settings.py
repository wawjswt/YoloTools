import tkinter as tk
from tkinter import colorchooser, messagebox, ttk

from .theme import *
from .ui_convert import SectionCard


class SettingsPage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG)
        self.app = app
        self._build()

    def _build(self):
        theme = get_theme()
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(top, text="系统设置", bg=BG, fg=TEXT, font=(theme["font_family"], 20, "bold")).pack(anchor="w")
        tk.Label(top, text="在这里集中管理主题、视觉与界面偏好。", bg=BG, fg=MUTED, font=(theme["font_family"], 10)).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        scroll_host = tk.Frame(body, bg=BG)
        scroll_host.grid(row=0, column=0, columnspan=2, sticky="nsew")
        scroll_host.grid_rowconfigure(0, weight=1)
        scroll_host.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(scroll_host, bg=BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(scroll_host, orient="vertical", command=self.canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.scrollable = tk.Frame(self.canvas, bg=BG)
        self.scrollable_id = self.canvas.create_window((0, 0), window=self.scrollable, anchor="nw")
        self.scrollable.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        content = tk.Frame(self.scrollable, bg=BG)
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        left = SectionCard(content, "主题与外观", "支持预设主题与自定义颜色")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_propagate(False)

        self.var_theme = tk.StringVar(value=self.app.theme_name)
        self.var_font_family = tk.StringVar(value=theme["font_family"])
        self.var_font_size = tk.IntVar(value=theme["font_size"])
        self.var_title_size = tk.IntVar(value=theme.get("title_size", 20))
        self.var_show_grid = tk.BooleanVar(value=theme.get("show_grid", False))
        self.var_show_axes = tk.BooleanVar(value=theme.get("show_axes", False))
        self.var_corner_accent = tk.BooleanVar(value=theme.get("corner_accent", True))
        self.var_scale_style = tk.StringVar(value=theme.get("scale_style", "fit"))
        self.color_vars = {
            "bg": tk.StringVar(value=theme["bg"]),
            "bg_alt": tk.StringVar(value=theme.get("bg_alt", theme["bg"])),
            "panel": tk.StringVar(value=theme["panel"]),
            "panel_alt": tk.StringVar(value=theme.get("panel_alt", theme["panel"])),
            "sidebar": tk.StringVar(value=theme["sidebar"]),
            "sidebar_active": tk.StringVar(value=theme["sidebar_active"]),
            "sidebar_hover": tk.StringVar(value=theme["sidebar_hover"]),
            "text": tk.StringVar(value=theme["text"]),
            "muted": tk.StringVar(value=theme["muted"]),
            "border": tk.StringVar(value=theme["border"]),
            "primary": tk.StringVar(value=theme["primary"]),
            "primary_dark": tk.StringVar(value=theme["primary_dark"]),
            "accent": tk.StringVar(value=theme.get("accent", theme["primary"])),
            "accent_dark": tk.StringVar(value=theme.get("accent_dark", theme["primary_dark"])),
        }

        form = tk.Frame(left, bg=PANEL)
        form.pack(fill="x", padx=16, pady=(0, 16))
        form.grid_columnconfigure(1, weight=1)

        self._combo_row(form, 0, "主题预设", self.var_theme, list(THEME_PRESETS.keys()))
        self._entry_row(form, 1, "字体族", self.var_font_family)
        self._spin_row(form, 2, "字体大小", self.var_font_size, 8, 18)
        self._spin_row(form, 3, "标题大小", self.var_title_size, 14, 28)
        self._combo_row(form, 4, "缩放模式", self.var_scale_style, ["fit", "fill", "native"])
        self._check_row(form, 5, "显示网格", self.var_show_grid)
        self._check_row(form, 6, "显示坐标轴", self.var_show_axes)
        self._check_row(form, 7, "角标发光", self.var_corner_accent)

        color_card = SectionCard(content, "自定义颜色", "可覆盖当前主题的核心颜色")
        color_card.grid(row=0, column=1, sticky="nsew")
        color_card.grid_columnconfigure(1, weight=1)
        color_form = tk.Frame(color_card, bg=PANEL)
        color_form.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        color_form.grid_columnconfigure(1, weight=1)

        rows = [
            ("背景色", "bg"),
            ("背景副色", "bg_alt"),
            ("面板色", "panel"),
            ("面板副色", "panel_alt"),
            ("侧边栏", "sidebar"),
            ("侧边栏高亮", "sidebar_active"),
            ("侧边栏悬停", "sidebar_hover"),
            ("正文色", "text"),
            ("次要文字", "muted"),
            ("边框色", "border"),
            ("主色", "primary"),
            ("主色深", "primary_dark"),
            ("强调色", "accent"),
            ("强调色深", "accent_dark"),
        ]
        self._color_rows = {}
        for row, (label, key) in enumerate(rows):
            self._color_rows[key] = self._color_row(color_form, row, label, self.color_vars[key])

        self.footer = tk.Frame(self, bg=BG)
        self.footer.pack(fill="x", padx=24, pady=(0, 18))
        footer_inner = tk.Frame(self.footer, bg=BG)
        footer_inner.pack(anchor="e")
        ttk.Button(footer_inner, text="应用主题", style="Primary.TButton", command=self.apply_settings).pack(side="left")
        ttk.Button(footer_inner, text="保存设置", command=self.save_only).pack(side="left", padx=8)
        ttk.Button(footer_inner, text="恢复默认", style="Ghost.TButton", command=self.reset_default).pack(side="left", padx=8)

    def _combo_row(self, parent, row, label, var, values):
        tk.Label(parent, text=label, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 10)).grid(row=row, column=0, sticky="w", pady=8)
        ttk.Combobox(parent, textvariable=var, values=values, state="readonly").grid(row=row, column=1, sticky="ew", padx=10, pady=8)

    def _entry_row(self, parent, row, label, var):
        tk.Label(parent, text=label, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 10)).grid(row=row, column=0, sticky="w", pady=8)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=10, pady=8)

    def _spin_row(self, parent, row, label, var, lo, hi):
        tk.Label(parent, text=label, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 10)).grid(row=row, column=0, sticky="w", pady=8)
        ttk.Spinbox(parent, from_=lo, to=hi, textvariable=var, width=8).grid(row=row, column=1, sticky="w", padx=10, pady=8)

    def _check_row(self, parent, row, label, var):
        ttk.Checkbutton(parent, text=label, variable=var).grid(row=row, column=0, columnspan=2, sticky="w", pady=6)

    def _color_row(self, parent, row, label, var):
        tk.Label(parent, text=label, bg=PANEL, fg=TEXT, font=("Microsoft YaHei UI", 10)).grid(row=row, column=0, sticky="w", pady=8)
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky="ew", padx=10, pady=8)
        ttk.Button(parent, text="选择", command=lambda v=var: self.pick_color(v)).grid(row=row, column=2, pady=8)
        return entry

    def pick_color(self, var):
        color = colorchooser.askcolor(color=var.get(), title="选择颜色")
        if color and color[1]:
            var.set(color[1])

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.scrollable_id, width=event.width)

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            delta = event.delta
            if delta == 0:
                return
            self.canvas.yview_scroll(int(-1 * (delta / abs(delta))), "units")

    def build_theme(self):
        base = dict(DEFAULT_THEME)
        selected = THEME_PRESETS.get(self.var_theme.get(), DEFAULT_THEME)
        base.update(selected)
        base.update({
            "name": self.var_theme.get(),
            "font_family": self.var_font_family.get().strip() or DEFAULT_THEME["font_family"],
            "font_size": int(self.var_font_size.get()),
            "title_size": int(self.var_title_size.get()),
            "show_grid": bool(self.var_show_grid.get()),
            "show_axes": bool(self.var_show_axes.get()),
            "scale_style": self.var_scale_style.get(),
            "corner_accent": bool(self.var_corner_accent.get()),
        })
        for key, var in self.color_vars.items():
            base[key] = var.get().strip() or base[key]
        return base

    def apply_settings(self):
        try:
            theme = self.build_theme()
            set_theme(theme)
            self.app.theme_override = theme
            self.app.theme_name = theme["name"]
            self.app.apply_theme(theme["name"], persist=False)
            set_theme(theme)
            self.app.theme_override = theme
            self.app._propagate_theme_globals(theme)
            self.app._refresh_widget_tree()
            self.app._refresh_pages()
            self.app.save_settings()
            messagebox.showinfo("提示", "设置已应用并保存")
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def save_only(self):
        try:
            self.apply_settings()
        except Exception as e:
            messagebox.showerror("错误", str(e))

    def reset_default(self):
        for key, value in DEFAULT_THEME.items():
            if key in self.color_vars:
                self.color_vars[key].set(value)
        self.var_theme.set(DEFAULT_THEME["name"])
        self.var_font_family.set(DEFAULT_THEME["font_family"])
        self.var_font_size.set(DEFAULT_THEME["font_size"])
        self.var_title_size.set(DEFAULT_THEME["title_size"])
        self.var_show_grid.set(DEFAULT_THEME["show_grid"])
        self.var_show_axes.set(DEFAULT_THEME["show_axes"])
        self.var_scale_style.set(DEFAULT_THEME["scale_style"])
        self.var_corner_accent.set(DEFAULT_THEME["corner_accent"])
        messagebox.showinfo("提示", "已恢复默认值，尚未保存")
