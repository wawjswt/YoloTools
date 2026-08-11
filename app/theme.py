# app/theme.py
DEFAULT_THEME = {
    "name": "Ocean",
    "bg": "#e4ebf3",
    "panel": "#edf3f8",
    "sidebar": "#111827",
    "sidebar_active": "#2563eb",
    "sidebar_hover": "#1f2937",
    "text": "#111827",
    "muted": "#6b7280",
    "border": "#b8c4d4",
    "primary": "#2563eb",
    "primary_dark": "#1d4ed8",
    "font_family": "Microsoft YaHei UI",
    "font_size": 10,
    "title_size": 20,
    "show_grid": False,
    "show_axes": False,
    "scale_style": "fit",
}

THEME_PRESETS = {
    "Ocean": DEFAULT_THEME,
    "Dark": {
        **DEFAULT_THEME,
        "name": "Dark",
        "bg": "#0f172a",
        "panel": "#111827",
        "sidebar": "#020617",
        "sidebar_active": "#3b82f6",
        "sidebar_hover": "#1e293b",
        "text": "#e5e7eb",
        "muted": "#94a3b8",
        "border": "#334155",
        "primary": "#3b82f6",
        "primary_dark": "#2563eb",
    },
    "Warm": {
        **DEFAULT_THEME,
        "name": "Warm",
        "bg": "#faf3e8",
        "panel": "#fff8ef",
        "sidebar": "#4b2e1f",
        "sidebar_active": "#d97706",
        "sidebar_hover": "#5b3826",
        "text": "#2c1f17",
        "muted": "#7c5a46",
        "border": "#e6d5c3",
        "primary": "#d97706",
        "primary_dark": "#b45309",
    },
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
    ttk_style.configure("TEntry", padding=6)
    ttk_style.configure("TButton", padding=(10, 6), font=(theme["font_family"], theme["font_size"]))
    ttk_style.configure("Primary.TButton", background=theme["primary"], foreground="white", borderwidth=0)
    ttk_style.map("Primary.TButton", background=[("active", theme["primary_dark"]), ("pressed", theme["primary_dark"])])


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
