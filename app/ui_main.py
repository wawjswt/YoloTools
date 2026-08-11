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
        super().__init__(master, bg=theme["sidebar"], cursor="hand2", highlightthickness=1, highlightbackground=theme["border"])
        self.command = command
        self.active = False
        self.icon_label = tk.Label(self, text=icon, bg=theme["sidebar"], fg=theme["primary"], font=("Segoe UI Emoji", 12, "bold"), width=2)
        self.icon_label.pack(side="left", padx=(14, 8), pady=10)
        self.text_label = tk.Label(self, text=text, bg=theme["sidebar"], fg=theme["text"], font=(theme["font_family"], 10, "bold"), anchor="w")
        self.text_label.pack(side="left", fill="x", expand=True)
        for w in (self, self.icon_label, self.text_label):
            w.bind("<Button-1>", self.on_click)
            w.bind("<Enter>", self.on_enter)
            w.bind("<Leave>", self.on_leave)

    def set_active(self, active: bool):
        theme = get_theme()
        self.active = active
        color = theme["sidebar_active"] if active else theme["sidebar"]
        self.configure(bg=color)
        self.icon_label.configure(bg=color)
        self.text_label.configure(bg=color)

    def on_click(self, event=None):
        self.command()

    def on_enter(self, event=None):
        theme = get_theme()
        if not self.active:
            self.configure(bg=theme["sidebar_hover"])
            self.icon_label.configure(bg=theme["sidebar_hover"])
            self.text_label.configure(bg=theme["sidebar_hover"])

    def on_leave(self, event=None):
        theme = get_theme()
        if not self.active:
            self.configure(bg=theme["sidebar"])
            self.icon_label.configure(bg=theme["sidebar"])
            self.text_label.configure(bg=theme["sidebar"])


class HomePage(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=get_theme()["bg"])
        self.app = app
        self._build()

    def _build(self):
        theme = get_theme()
        top = tk.Frame(self, bg=theme["bg"])
        top.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(top, text="YOLO TOOLBOX // NEON CORE", bg=theme["bg"], fg=theme["primary"], font=(theme["font_family"], 18, "bold")).pack(anchor="w")
        tk.Label(top, text="统一入口，集中处理转换、统计、替换和工具启动", bg=theme["bg"], fg=theme["muted"], font=(theme["font_family"], 10)).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self, bg=theme["bg"])
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        left = self._card(body, "快速开始", "命令入口 / 高频操作")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        grid = tk.Frame(left, bg=theme["panel"])
        grid.pack(fill="x", padx=16, pady=(0, 16))
        self._btn(grid, "格式转换", lambda: self.app.show_page("convert")).grid(row=0, column=0, padx=6, pady=6, sticky="ew")
        self._btn(grid, "标注统计", lambda: self.app.show_page("count")).grid(row=0, column=1, padx=6, pady=6, sticky="ew")
        self._btn(grid, "类别替换", lambda: self.app.show_page("replace")).grid(row=1, column=0, padx=6, pady=6, sticky="ew")
        self._btn(grid, "其他工具", lambda: self.app.show_page("tools")).grid(row=1, column=1, padx=6, pady=6, sticky="ew")
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)

        right = self._card(body, "控制台说明", "页面状态与输出都尽量可追踪")
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))

    def _card(self, master, title, subtitle=""):
        theme = get_theme()
        card = tk.Frame(master, bg=theme["panel"], highlightthickness=1, highlightbackground=theme["border"])
        head = tk.Frame(card, bg=theme["panel"])
        head.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(head, text=title, bg=theme["panel"], fg=theme["text"], font=(theme["font_family"], 13, "bold")).pack(anchor="w")
        if subtitle:
            tk.Label(head, text=subtitle, bg=theme["panel"], fg=theme["muted"], font=(theme["font_family"], 9)).pack(anchor="w", pady=(4, 0))
        return card

    def _btn(self, master, text, command):
        theme = get_theme()
        f = tk.Frame(master, bg=theme["panel"], highlightthickness=1, highlightbackground=theme["border"], cursor="hand2")
        inner = tk.Frame(f, bg=theme["panel"])
        inner.pack(fill="both", expand=True, padx=1, pady=1)
        tk.Label(inner, text=text, bg=theme["panel"], fg=theme["text"], font=(theme["font_family"], 10, "bold")).pack(fill="x", expand=True, padx=12, pady=10)
        for w in (f, inner, *inner.winfo_children()):
            w.bind("<Button-1>", lambda e: command())
        return f


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YOLO 工具箱")
        self.root.geometry("1180x760")
        self.root.minsize(1000, 680)
        self.config = load_config()
        self.theme_name = self.config.get("theme_name", "Ocean")
        self.theme_override = self.config.get("theme_override")
        set_theme(self.theme_override or THEME_PRESETS.get(self.theme_name, DEFAULT_THEME))

        self.sidebar_items = {}
        self.pages = {}

        self._style()
        self._layout()
        self._load_state()
        self.show_page("home")

    def _style(self):
        style = ttk.Style()
        style.theme_use("clam")
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
            self.sidebar.configure(bg=theme["sidebar"])
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

        self.sidebar = tk.Frame(self.root, bg=theme["sidebar"], width=250, highlightthickness=1, highlightbackground=theme["border"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        brand = tk.Frame(self.sidebar, bg=theme["sidebar"])
        brand.pack(fill="x", pady=(18, 18))
        tk.Label(brand, text="YOLO TOOLBOX", bg=theme["sidebar"], fg=theme["primary"], font=(theme["font_family"], 16, "bold")).pack(anchor="w", padx=18)
        tk.Label(brand, text="NEON DATA OPS CONSOLE", bg=theme["sidebar"], fg=theme["muted"], font=(theme["font_family"], 9)).pack(anchor="w", padx=18, pady=(4, 0))

        nav = tk.Frame(self.sidebar, bg=theme["sidebar"])
        nav.pack(fill="x", pady=(10, 0))
        items = [("home", "首页", "⌂"), ("convert", "格式转换", "⇄"), ("count", "标注统计", "▣"), ("replace", "类别重整", "✎"), ("tools", "其他工具", "★")]
        for key, text, icon in items:
            item = SidebarItem(nav, text, icon, lambda k=key: self.show_page(k))
            item.pack(fill="x", pady=2)
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
                    widget.configure(bg=theme["bg"] if widget is self.content or widget is self.page_host else theme["panel"])
                elif cls == "Label":
                    widget.configure(bg=widget.master["bg"], fg=theme["text"])
                elif cls == "Text":
                    widget.configure(bg="#08111d", fg="#dbeafe", insertbackground="white")
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

    def _tool_button(self, master, text, command):
        theme = get_theme()
        btn = tk.Label(master, text=text, bg=theme["panel"], fg=theme["primary"], font=(theme["font_family"], 12, "bold"), width=2, height=1, cursor="hand2", highlightthickness=1, highlightbackground=theme["border"])
        btn.pack(side="left", padx=4)
        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(bg=theme["panel_alt"]))
        btn.bind("<Leave>", lambda e: btn.configure(bg=theme["panel"]))
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
