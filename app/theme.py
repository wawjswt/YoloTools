# app/theme.py
DEFAULT_THEME = {
    "name": "NeonCore",
    "bg": "#050816",
    "bg_alt": "#09111f",
    "panel": "#0b1220",
    "panel_alt": "#111a2e",
    "sidebar": "#040913",
    "sidebar_active": "#00d4ff",
    "sidebar_hover": "#0b1526",
    "text": "#eaf2ff",
    "muted": "#8ca3c7",
    "border": "#1c2a44",
    "primary": "#00d4ff",
    "primary_dark": "#00a7cc",
    "accent": "#8b5cf6",
    "accent_dark": "#6d28d9",
    "success": "#22c55e",
    "warning": "#f59e0b",
    "danger": "#ef4444",
    "font_family": "Microsoft YaHei UI",
    "font_size": 10,
    "title_size": 20,
    "show_grid": False,
    "show_axes": False,
    "scale_style": "fit",
    "button_radius": 0,
    "corner_accent": True,
}

THEME_PRESETS = {
    "NeonCore": DEFAULT_THEME,
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
    "Ocean": {
        **DEFAULT_THEME,
        "name": "Ocean",
        "bg": "#e4ebf3",
        "bg_alt": "#d8e3ef",
        "panel": "#edf3f8",
        "panel_alt": "#dde8f3",
        "sidebar": "#111827",
        "sidebar_active": "#2563eb",
        "sidebar_hover": "#1f2937",
        "text": "#111827",
        "muted": "#6b7280",
        "border": "#b8c4d4",
        "primary": "#2563eb",
        "primary_dark": "#1d4ed8",
        "accent": "#8b5cf6",
        "accent_dark": "#6d28d9",
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
    "Aurora": {
        **DEFAULT_THEME,
        "name": "Aurora",
        "bg": "#07111f",
        "bg_alt": "#0b1b31",
        "panel": "#0d1728",
        "panel_alt": "#12213a",
        "sidebar": "#020617",
        "sidebar_active": "#22d3ee",
        "sidebar_hover": "#0f172a",
        "text": "#e2f3ff",
        "muted": "#89a8c9",
        "border": "#1e3352",
        "primary": "#22d3ee",
        "primary_dark": "#0891b2",
        "accent": "#a855f7",
        "accent_dark": "#7e22ce",
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
    ttk_style.configure("TNotebook", background=theme["bg"], borderwidth=0)
    ttk_style.configure("TNotebook.Tab", padding=(14, 8), background=theme["panel"], foreground=theme["muted"])
    ttk_style.map("TNotebook.Tab", background=[("selected", theme["panel_alt"])], foreground=[("selected", theme["text"])])
    ttk_style.configure("Primary.TButton", background=theme["primary"], foreground="#001018", borderwidth=0)
    ttk_style.configure("Ghost.TButton", background=theme["panel_alt"], foreground=theme["text"], borderwidth=0)
    ttk_style.configure("TCheckbutton", background=theme["bg"], foreground=theme["text"], font=(theme["font_family"], theme["font_size"]))
    ttk_style.map("Primary.TButton", background=[("active", theme["primary_dark"]), ("pressed", theme["primary_dark"])])
    ttk_style.map("Ghost.TButton", background=[("active", theme["border"]), ("pressed", theme["border"])])


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
