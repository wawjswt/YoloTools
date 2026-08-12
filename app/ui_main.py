import json
from pathlib import Path
import tkinter as tk
from tkinter import ttk

from .theme import *
from .ui_convert import ConvertPage
from .ui_count import CountPage
from .ui_replace import ReplacePage
from .ui_tools import ToolsPage
from .ui_settings import SettingsPage


CONFIG_FILE = Path(__file__).resolve().parent.parent / "yolo_toolbox_config.json"


def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_config(config):
    try:
        CONFIG_FILE.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass


class SidebarItem(tk.Frame):
    def __init__(self, master, text, icon, command):
        theme = get_theme()
        super().__init__(master, bg=theme["sidebar"], cursor="hand2", highlightthickness=0)
        self.command = command
        self.active = False
        self.icon_label = tk.Label(self, text=icon, bg=theme["sidebar"], fg="#d8e4f2", font=("Segoe UI Symbol", 12, "bold"), width=2)
        self.icon_label.pack(side="left", padx=(14, 8), pady=10)
        self.text_label = tk.Label(self, text=text, bg=theme["sidebar"], fg="#d8e4f2", font=(theme["font_family"], 10, "bold"), anchor="w")
        self.text_label.pack(side="left", fill="x", expand=True)
        for w in (self, self.icon_label, self.text_label):
            w.bind("<Button-1>", self.on_click)
            w.bind("<Enter>", self.on_enter)
            w.bind("<Leave>", self.on_leave)

    def set_active(self, active: bool):
        self.active = active
        theme = get_theme()
        color = theme["sidebar"] if not active else theme["sidebar_active"]
        foreground = "#d8e4f2" if not active else "#ffffff"
        self.configure(bg=color)
        self.icon_label.configure(bg=color, fg=foreground)
        self.text_label.configure(bg=color, fg=foreground)

    def on_click(self, event=None):
        self.command()

    def on_enter(self, event=None):
        if not self.active:
            theme = get_theme()
            color = theme["sidebar_hover"]
            self.configure(bg=color)
            self.icon_label.configure(bg=color, fg="#ffffff")
            self.text_label.configure(bg=color, fg="#ffffff")

    def on_leave(self, event=None):
        if not self.active:
            theme = get_theme()
            self.configure(bg=theme["sidebar"])
            self.icon_label.configure(bg=theme["sidebar"], fg="#d8e4f2")
            self.text_label.configure(bg=theme["sidebar"], fg="#d8e4f2")


class HomePage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=get_theme()["bg"])
        self.app = app
        self._build()

    def _build(self):
        theme = get_theme()
        top = tk.Frame(self, bg=theme["bg"], highlightthickness=1, highlightbackground=theme["border"], relief="groove")
        top.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(top, text="YOLO TOOLBOX", bg=theme["bg"], fg=theme["text"], font=(theme["font_family"], 20, "bold")).pack(anchor="w", padx=18, pady=(16, 0))
        tk.Label(top, text="统一入口，集中处理转换、统计、替换和工具启动。", bg=theme["bg"], fg=theme["muted"], font=(theme["font_family"], 10)).pack(anchor="w", padx=18, pady=(4, 0))

        stats = tk.Frame(top, bg=theme["bg"])
        stats.pack(fill="x", padx=18, pady=(12, 16))
        self._mini_stat(stats, "4", "核心模块").pack(side="left", padx=(0, 10))
        self._mini_stat(stats, "1", "统一入口").pack(side="left", padx=(0, 10))
        self._mini_stat(stats, "∞", "批处理").pack(side="left")

        body = tk.Frame(self, bg=theme["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        left = self._card(body, "快速开始", "最常用入口")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        grid = tk.Frame(left, bg=theme["bg"])
        grid.pack(fill="x", padx=16, pady=(0, 16))
        self._btn(grid, "格式转换", lambda: self.app.show_page("convert")).grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        self._btn(grid, "标注统计", lambda: self.app.show_page("count")).grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        self._btn(grid, "类别替换", lambda: self.app.show_page("replace")).grid(row=1, column=0, padx=6, pady=6, sticky="ew")
        self._btn(grid, "其他工具", lambda: self.app.show_page("tools")).grid(row=1, column=1, padx=6, pady=6, sticky="ew")
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        right = self._card(body, "使用提示", "当前状态")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        tip_box = tk.Frame(right, bg=theme["bg"])
        tip_box.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        tips = [
            "从左侧选择功能页，再填写参数。",
            "日志区会显示处理过程和结果摘要。",
            "默认配色保持系统原生风格，减少干扰。",
        ]
        for tip in tips:
            row = tk.Frame(tip_box, bg=theme["bg"])
            row.pack(fill="x", pady=6)
            tk.Label(row, text="•", bg=theme["bg"], fg=theme["text"], font=(theme["font_family"], 12, "bold")).pack(side="left")
            tk.Label(row, text=tip, bg=theme["bg"], fg=theme["text"], font=(theme["font_family"], 10), wraplength=320, justify="left").pack(side="left", padx=8, fill="x", expand=True)

    def _card(self, master, title, subtitle=""):
        theme = get_theme()
        card = tk.Frame(master, bg=theme["bg"], highlightthickness=1, highlightbackground=theme["border"], relief="groove")
        head = tk.Frame(card, bg=theme["bg"])
        head.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(head, text=title, bg=theme["bg"], fg=theme["text"], font=(theme["font_family"], 13, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(head, text=subtitle, bg=theme["bg"], fg=theme["muted"], font=(theme["font_family"], 9)).pack(anchor="w", pady=(4, 0))
        return card

    def _mini_stat(self, master, value, label):
        theme = get_theme()
        box = tk.Frame(master, bg=theme["bg"], highlightthickness=1, highlightbackground=theme["border"], relief="groove")
        tk.Label(box, text=value, bg=theme["bg"], fg=theme["text"], font=(theme["font_family"], 16, "bold")).pack(padx=14, pady=(10, 0))
        tk.Label(box, text=label, bg=theme["bg"], fg=theme["muted"], font=(theme["font_family"], 9)).pack(padx=14, pady=(0, 10))
        return box

    def _btn(self, master, text, command):
        theme = get_theme()
        f = tk.Frame(master, bg=theme["bg"], highlightthickness=1, highlightbackground=theme["border"], cursor="hand2", relief="raised")
        inner = tk.Frame(f, bg=theme["bg"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(inner, text=text, bg=theme["bg"], fg=theme["text"], font=(theme["font_family"], 10, "bold")).pack(fill="x", expand=True, padx=12, pady=10)
        for w in (f, inner, *inner.winfo_children()):
            w.bind("<Button-1>", lambda e: command())
            w.bind("<Enter>", lambda e, widget=f, child=inner: (widget.configure(bg="#f0f0f0"), child.configure(bg="#f0f0f0")))
            w.bind("<Leave>", lambda e, widget=f, child=inner: (widget.configure(bg=theme["bg"]), child.configure(bg=theme["bg"])))
        return f


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO 工具箱")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 680)
        self.config = load_config()
        self.theme_name = self.config.get("theme_name", "Default")
        self.theme_override = self.config.get("theme_override")
        set_theme(self.theme_override or THEME_PRESETS.get(self.theme_name, DEFAULT_THEME))

        self.sidebar_items = {}
        self.pages = {}
        self.status_var = tk.StringVar(value="就绪")
        self.status_detail_var = tk.StringVar(value="等待操作")
        self.status_kind = "idle"

        self._style()
        self._layout()
        self._load_state()
        self.show_page("home")

    def _style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        apply_to_tk(style)

    def apply_theme(self, name, persist=True):
        theme = THEME_PRESETS.get(name, DEFAULT_THEME)
        self.theme_name = theme["name"]
        if self.theme_override and self.theme_override.get("name") == name:
            theme = {**theme, **self.theme_override}
        set_theme(theme)
        self._propagate_theme_globals(theme)
        if persist:
            self.config["theme_name"] = self.theme_name
            self.config["theme"] = theme
            self.config["theme_override"] = self.theme_override
            save_config(self.config)
        self.root.configure(bg=theme["bg"])
        if hasattr(self, "content"):
            self.content.configure(bg=theme["bg"])
        if hasattr(self, "sidebar"):
            self.sidebar.configure(bg=theme["bg"])
        self._refresh_widget_tree()
        for item in getattr(self, "sidebar_items", {}).values():
            item.set_active(item.active)
        self._refresh_pages()

    def _propagate_theme_globals(self, theme):
        for mod_name in ("app.ui_convert", "app.ui_count", "app.ui_replace", "app.ui_tools", "app.ui_settings"):
            mod = __import__(mod_name, fromlist=["*"])
            for key, value in {
                "BG": theme["bg"],
                "PANEL": theme["panel"],
                "PANEL_ALT": theme["panel_alt"],
                "SIDEBAR": theme["sidebar"],
                "SIDEBAR_ACTIVE": theme["sidebar_active"],
                "SIDEBAR_HOVER": theme["sidebar_hover"],
                "TEXT": theme["text"],
                "MUTED": theme["muted"],
                "BORDER": theme["border"],
                "PRIMARY": theme["primary"],
                "PRIMARY_DARK": theme["primary_dark"],
            }.items():
                setattr(mod, key, value)

    def _layout(self):
        theme = get_theme()
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.sidebar = tk.Frame(self.root, bg=theme["bg"], width=250, highlightthickness=1, highlightbackground=theme["border"], relief="groove")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        brand = tk.Frame(self.sidebar, bg=theme["bg"])
        brand.pack(fill="x", pady=(18, 18))
        tk.Label(brand, text="YOLO TOOLBOX", bg=theme["bg"], fg=theme["text"], font=(theme["font_family"], 16, "bold")).pack(anchor="w", padx=18)
        tk.Label(brand, text="DATA OPS CONSOLE", bg=theme["bg"], fg=theme["muted"], font=(theme["font_family"], 9)).pack(anchor="w", padx=18, pady=(4, 0))

        nav = tk.Frame(self.sidebar, bg=theme["bg"])
        nav.pack(fill="x", pady=(10, 0))
        items = [("home", "首页", "⌂"), ("convert", "格式转换", "⇄"), ("count", "标注统计", "≡"), ("replace", "类别替换", "✎"), ("tools", "其他工具", "⚙")]
        for key, text, icon in items:
            item = SidebarItem(nav, text, icon, lambda k=key: self.show_page(k))
            item.pack(fill="x", pady=2, padx=8)
            self.sidebar_items[key] = item

        self.content = tk.Frame(self.root, bg=theme["bg"], highlightthickness=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

        self.page_host = tk.Frame(self.content, bg=theme["bg"])
        self.page_host.pack(fill="both", expand=True, padx=18, pady=18)

        self.pages["home"] = HomePage(self.page_host, self)
        self.pages["convert"] = ConvertPage(self.page_host, self)
        self.pages["count"] = CountPage(self.page_host, self)
        self.pages["replace"] = ReplacePage(self.page_host, self)
        self.pages["tools"] = ToolsPage(self.page_host, self)
        self.pages["settings"] = SettingsPage(self.page_host, self)
        for page in self.pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._top_actions = tk.Frame(self.content, bg=theme["bg"])
        self._top_actions.place(relx=1.0, x=-18, y=8, anchor="ne")
        self._tool_button(self._top_actions, "⚙", self.open_settings)
        self._tool_button(self._top_actions, "×", self.close_app)

        self.status_bar = tk.Frame(self.root, bg=theme["bg"], highlightthickness=1, highlightbackground=theme["border"], relief="groove")
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.status_bar.grid_columnconfigure(1, weight=1)
        self.status_dot = tk.Label(self.status_bar, text="●", bg=theme["bg"], fg=theme["muted"], font=(theme["font_family"], 10, "bold"))
        self.status_dot.grid(row=0, column=0, padx=(12, 6), pady=8, sticky="w")
        self.status_text = tk.Label(self.status_bar, textvariable=self.status_var, bg=theme["bg"], fg=theme["text"], font=(theme["font_family"], 10, "bold"), anchor="w")
        self.status_text.grid(row=0, column=1, padx=4, pady=8, sticky="ew")
        self.status_detail = tk.Label(self.status_bar, textvariable=self.status_detail_var, bg=theme["bg"], fg=theme["muted"], font=(theme["font_family"], 9), anchor="e")
        self.status_detail.grid(row=0, column=2, padx=(4, 12), pady=8, sticky="e")

    def _refresh_pages(self):
        for page in self.pages.values():
            page.configure(bg=get_theme()["bg"])
        self._on_content_resize()
        self.root.update_idletasks()

    def _load_state(self):
        self.config = load_config()
        if "theme_name" in self.config:
            self.apply_theme(self.config["theme_name"], persist=False)

    def _on_content_resize(self, event=None):
        if not hasattr(self, "page_host"):
            return
        for page in self.pages.values():
            try:
                page.configure(width=max(1, self.page_host.winfo_width()), height=max(1, self.page_host.winfo_height()))
            except Exception:
                pass

    def _refresh_widget_tree(self):
        theme = get_theme()
        roots = [self.root]
        while roots:
            widget = roots.pop()
            try:
                cls = widget.winfo_class()
            except Exception:
                continue
            try:
                if isinstance(widget, tk.Tk) or isinstance(widget, tk.Toplevel):
                    widget.configure(bg=theme["bg"])
                elif cls in ("Frame", "Labelframe"):
                    widget.configure(bg=theme["bg"])
                elif cls == "Label":
                    widget.configure(bg=widget.master["bg"], fg=theme["text"])
                elif cls == "Text":
                    widget.configure(bg="white", fg="black", insertbackground="black")
                elif cls == "Canvas":
                    widget.configure(bg=theme["bg"])
            except Exception:
                pass
            try:
                roots.extend(list(widget.winfo_children()))
            except Exception:
                pass

    def show_page(self, key):
        self.pages[key].lift()
        for name, item in self.sidebar_items.items():
            item.set_active(name == key)

    def set_status(self, text, detail="", kind="info"):
        self.status_var.set(text)
        self.status_detail_var.set(detail)
        self.status_kind = kind
        theme = get_theme()
        color_map = {
            "idle": theme["muted"],
            "info": theme["primary"],
            "success": theme.get("success", theme["primary"]),
            "warning": theme.get("warning", "#d98b18"),
            "error": theme.get("danger", "#c00000"),
        }
        if hasattr(self, "status_dot"):
            self.status_dot.configure(fg=color_map.get(kind, theme["primary"]))

    def clear_status(self):
        self.set_status("就绪", "等待操作", "idle")

    def _tool_button(self, master, text, command):
        theme = get_theme()
        btn = tk.Label(master, text=text, bg=theme["bg"], fg=theme["text"], font=(theme["font_family"], 12, "bold"), width=2, height=1, cursor="hand2", highlightthickness=1, highlightbackground=theme["border"], relief="raised")
        btn.pack(side="left", padx=4)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(bg="#f0f0f0"))
        btn.bind("<Leave>", lambda e: btn.configure(bg=theme["bg"]))
        return btn

    def open_settings(self):
        self.show_page("settings")

    def close_app(self):
        self.root.destroy()

    def save_settings(self):
        self.config["theme_name"] = self.theme_name
        self.config["theme_override"] = self.theme_override
        save_config(self.config)


def run_app():
    root = tk.Tk()
    MainApp(root)
    root.mainloop()
