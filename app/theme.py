# app/theme.py
DEFAULT_THEME = {
    "name": "Default",
    "bg": "SystemButtonFace",
    "bg_alt": "SystemButtonFace",
    "panel": "SystemButtonFace",
    "panel_alt": "SystemButtonFace",
    "sidebar": "SystemButtonFace",
    "sidebar_active": "SystemHighlight",
    "sidebar_hover": "SystemButtonFace",
    "text": "SystemWindowText",
    "muted": "SystemGrayText",
    "border": "#d9d9d9",
    "primary": "SystemHighlight",
    "primary_dark": "SystemHighlight",
    "accent": "SystemHighlight",
    "accent_dark": "SystemHighlight",
    "success": "SystemHighlight",
    "warning": "SystemHighlight",
    "danger": "#c00000",
    "font_family": "Microsoft YaHei UI",
    "font_size": 10,
    "title_size": 20,
    "show_grid": False,
    "show_axes": False,
    "scale_style": "fit",
    "button_radius": 0,
    "corner_accent": False,
}

THEME_PRESETS = {
    "Default": DEFAULT_THEME,
}


def normalize_theme(theme):
    out = dict(DEFAULT_THEME)
    if theme:
        out.update(theme)
    return out


_ACTIVE_THEME = normalize_theme(DEFAULT_THEME)


def set_theme(theme):
    global _ACTIVE_THEME
    _ACTIVE_THEME = normalize_theme(theme)


def get_theme():
    return dict(_ACTIVE_THEME)


def apply_to_tk(ttk_style):
    theme = get_theme()
    ttk_style.configure(".", font=(theme["font_family"], theme["font_size"]))
    ttk_style.configure("TFrame", background=theme["bg"])
    ttk_style.configure("TLabelframe", background=theme["bg"], borderwidth=1, relief="groove")
    ttk_style.configure("TLabelframe.Label", background=theme["bg"], foreground=theme["text"], font=(theme["font_family"], theme["font_size"], "bold"))
    ttk_style.configure("TLabel", background=theme["bg"], foreground=theme["text"])
    ttk_style.configure("TEntry", padding=(6, 4))
    ttk_style.configure("TCombobox", padding=(6, 4))
    ttk_style.configure("TButton", padding=(8, 4), font=(theme["font_family"], theme["font_size"]))
    ttk_style.configure("TNotebook", background=theme["bg"], borderwidth=0)
    ttk_style.configure("TNotebook.Tab", padding=(12, 6), background=theme["bg"], foreground=theme["text"])
    ttk_style.map("TNotebook.Tab", background=[("selected", theme["bg"])], foreground=[("selected", theme["text"])])
    ttk_style.configure("Treeview", background="white", fieldbackground="white", foreground="black", borderwidth=1, rowheight=24)
    ttk_style.configure("Treeview.Heading", background=theme["bg"], foreground=theme["text"], relief="flat", font=(theme["font_family"], theme["font_size"], "bold"))
    ttk_style.map("Treeview", background=[("selected", "SystemHighlight")], foreground=[("selected", "SystemHighlightText")])
    ttk_style.configure("TScrollbar", background=theme["bg"], troughcolor=theme["bg"], borderwidth=0, arrowcolor=theme["text"])
    ttk_style.configure("Primary.TButton", background=theme["bg"], foreground=theme["text"], borderwidth=1, relief="raised")
    ttk_style.configure("Ghost.TButton", background=theme["bg"], foreground=theme["text"], borderwidth=1, relief="raised")
    ttk_style.configure("TCheckbutton", background=theme["bg"], foreground=theme["text"], font=(theme["font_family"], theme["font_size"]))
    ttk_style.map("Primary.TButton", relief=[("pressed", "sunken"), ("active", "raised")])
    ttk_style.map("Ghost.TButton", relief=[("pressed", "sunken"), ("active", "raised")])


def apply_to_matplotlib():
    try:
        import matplotlib.pyplot as plt
        plt.rcParams["font.sans-serif"] = [DEFAULT_THEME["font_family"], "SimHei", "Arial Unicode MS"]
        plt.rcParams["axes.unicode_minus"] = False
    except Exception:
        pass


def _sync_legacy_constants():
    theme = get_theme()
    globals().update({
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
    })


_sync_legacy_constants()
