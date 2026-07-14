# -*- coding: utf-8 -*-
"""主题样式表与配色常量（含 dark / light 切换）"""

# ============================================================
# 颜色常量（向后兼容旧代码直接 import）
# ============================================================

# 背景色
BG_DARK = "#0d1117"
BG_PANEL = "#161b22"
BG_CARD = "#1c2129"
BG_INPUT = "#0d1117"
BG_HOVER = "#21262d"
BG_SELECTED = "#1f6feb"

# 文字色
TEXT_PRIMARY = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED = "#6e7681"
TEXT_ACCENT = "#58a6ff"

# 涨跌色
GREEN = "#3fb950"
RED = "#f85149"
YELLOW = "#d29922"
ORANGE = "#db6d28"

# 边框色
BORDER = "#30363d"
BORDER_FOCUS = "#1f6feb"
BORDER_DANGER = "#f85149"

# 按钮色
BTN_PRIMARY = "#238636"
BTN_PRIMARY_HOVER = "#2ea043"
BTN_DANGER = "#da3633"
BTN_DANGER_HOVER = "#f85149"
BTN_DEFAULT = "#21262d"
BTN_DEFAULT_HOVER = "#30363d"


# ============================================================
# QSS 模板：用 .format 占位符，便于多主题切换
# ============================================================

_QSS_TEMPLATE = """\
/* Global */
QMainWindow {{ background-color: {BG_DARK}; color: {TEXT_PRIMARY}; }}
QWidget    {{ background-color: {BG_DARK}; color: {TEXT_PRIMARY};
              font-family: "Segoe UI", "Microsoft YaHei", sans-serif; font-size: 13px; }}

/* Panel / Card */
QFrame#panel {{ background-color: {BG_PANEL}; border: 1px solid {BORDER};
                border-radius: 8px; padding: 12px; }}
QFrame#card  {{ background-color: {BG_CARD};  border: 1px solid {BORDER};
                border-radius: 6px; padding: 8px; }}

/* Label */
QLabel {{ color: {TEXT_PRIMARY}; background: transparent; border: none; }}
QLabel#title    {{ font-size: 18px; font-weight: bold; padding: 4px 0; }}
QLabel#subtitle {{ font-size: 14px; font-weight: bold; color: {TEXT_SECONDARY}; }}
QLabel#value    {{ font-size: 20px; font-weight: bold; color: {TEXT_ACCENT}; }}
QLabel#positive {{ font-size: 16px; font-weight: bold; color: {GREEN}; }}
QLabel#negative {{ font-size: 16px; font-weight: bold; color: {RED}; }}
QLabel#neutral  {{ font-size: 16px; font-weight: bold; color: {TEXT_MUTED}; }}
QLabel#muted    {{ color: {TEXT_MUTED}; font-size: 11px; }}

/* Input */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {BG_INPUT}; color: {TEXT_PRIMARY};
    border: 1px solid {BORDER}; border-radius: 6px;
    padding: 6px 10px; min-height: 28px; }}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border-color: {BORDER_FOCUS}; }}
QComboBox::drop-down {{ border: none; padding-right: 8px; }}
QComboBox QAbstractItemView {{
    background-color: {BG_PANEL}; color: {TEXT_PRIMARY};
    border: 1px solid {BORDER}; selection-background-color: {BG_SELECTED};
    selection-color: {TEXT_PRIMARY}; outline: none; }}

/* Button */
QPushButton {{
    background-color: {BTN_DEFAULT}; color: {TEXT_PRIMARY};
    border: 1px solid {BORDER}; border-radius: 6px;
    padding: 8px 18px; font-weight: bold; min-height: 32px; }}
QPushButton:hover   {{ background-color: {BTN_DEFAULT_HOVER}; }}
QPushButton:pressed {{ background-color: {BG_SELECTED}; }}
QPushButton#primary {{ background-color: {BTN_PRIMARY}; border-color: {BTN_PRIMARY}; color: #ffffff; }}
QPushButton#primary:hover {{ background-color: {BTN_PRIMARY_HOVER}; }}
QPushButton#danger  {{ background-color: {BTN_DANGER};  border-color: {BTN_DANGER};  color: #ffffff; }}
QPushButton#danger:hover  {{ background-color: {BTN_DANGER_HOVER}; }}
QPushButton#buy     {{ background-color: {GREEN}; border-color: {GREEN}; color: #ffffff;
                       font-size: 15px; min-height: 40px; }}
QPushButton#sell    {{ background-color: {RED};   border-color: {RED};   color: #ffffff;
                       font-size: 15px; min-height: 40px; }}
QPushButton:disabled {{ background-color: {BTN_DEFAULT}; color: {TEXT_MUTED};
                        border-color: {BORDER}; }}

/* Table */
QTableWidget {{ background-color: {BG_PANEL}; color: {TEXT_PRIMARY};
               border: 1px solid {BORDER}; border-radius: 6px;
               gridline-color: {BORDER};
               selection-background-color: {BG_HOVER}; selection-color: {TEXT_PRIMARY}; }}
QTableWidget::item {{ padding: 6px 10px; border-bottom: 1px solid {BORDER}; }}
QHeaderView::section {{ background-color: {BG_CARD}; color: {TEXT_SECONDARY};
                        border: none; border-bottom: 2px solid {BORDER};
                        padding: 8px 10px; font-weight: bold; font-size: 12px; }}
QTableWidget::item:selected {{ background-color: {BG_SELECTED}; }}

/* Tabs */
QTabWidget::pane {{ background-color: {BG_DARK}; border: 1px solid {BORDER};
                    border-radius: 6px; }}
QTabBar::tab {{ background-color: {BG_PANEL}; color: {TEXT_SECONDARY};
                border: 1px solid {BORDER}; border-bottom: none;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                padding: 8px 20px; margin-right: 2px; font-weight: bold; }}
QTabBar::tab:selected {{ background-color: {BG_DARK}; color: {TEXT_ACCENT};
                          border-bottom: 2px solid {TEXT_ACCENT}; }}
QTabBar::tab:hover {{ background-color: {BG_HOVER}; color: {TEXT_PRIMARY}; }}

/* Scrollbar */
QScrollBar:vertical   {{ background: {BG_DARK}; width: 8px; border-radius: 4px; }}
QScrollBar::handle:vertical {{ background: {BORDER}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: {BG_DARK}; height: 8px; border-radius: 4px; }}
QScrollBar::handle:horizontal {{ background: {BORDER}; border-radius: 4px; min-width: 30px; }}
QScrollBar::handle:horizontal:hover {{ background: {TEXT_MUTED}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

/* GroupBox */
QGroupBox {{ background-color: {BG_PANEL}; border: 1px solid {BORDER};
             border-radius: 8px; margin-top: 12px;
             padding: 16px 12px 12px 12px; font-weight: bold; color: {TEXT_PRIMARY}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 16px; padding: 0 8px;
                    color: {TEXT_ACCENT}; }}

/* ProgressBar */
QProgressBar {{ background-color: {BG_CARD}; border: 1px solid {BORDER};
                border-radius: 4px; text-align: center; color: {TEXT_PRIMARY}; height: 20px; }}
QProgressBar::chunk {{ background-color: {BTN_PRIMARY}; border-radius: 3px; }}

/* Tooltip / Editor / Status / MenuBar */
QToolTip                  {{ background-color: {BG_PANEL}; color: {TEXT_PRIMARY};
                             border: 1px solid {BORDER}; border-radius: 4px; padding: 4px 8px;
                             font-size: 12px; }}
QPlainTextEdit, QTextEdit  {{ background-color: {BG_INPUT}; color: {TEXT_PRIMARY};
                             border: 1px solid {BORDER}; border-radius: 6px; padding: 8px;
                             font-family: "Cascadia Code", "Consolas", monospace; font-size: 12px; }}
QStatusBar                {{ background-color: {BG_PANEL}; color: {TEXT_SECONDARY};
                             border-top: 1px solid {BORDER}; font-size: 12px; }}
QMenuBar                  {{ background-color: {BG_PANEL}; color: {TEXT_PRIMARY};
                             border-bottom: 1px solid {BORDER}; padding: 2px 0; }}
QMenuBar::item            {{ padding: 4px 12px; border-radius: 4px; }}
QMenuBar::item:selected   {{ background-color: {BG_HOVER}; }}
QMenu                     {{ background-color: {BG_PANEL}; color: {TEXT_PRIMARY};
                             border: 1px solid {BORDER}; border-radius: 6px; padding: 4px; }}
QMenu::item               {{ padding: 6px 30px 6px 16px; border-radius: 4px; }}
QMenu::item:selected      {{ background-color: {BG_SELECTED}; }}
"""

# 兼容老代码：GLOBAL_STYLESHEET 仍按 f-string 当前变量插值；新增 _QSS_TEMPLATE 用作 .format 输入
GLOBAL_STYLESHEET = _QSS_TEMPLATE.format(
    BG_DARK=BG_DARK, BG_PANEL=BG_PANEL, BG_CARD=BG_CARD,
    BG_INPUT=BG_INPUT, BG_HOVER=BG_HOVER, BG_SELECTED=BG_SELECTED,
    TEXT_PRIMARY=TEXT_PRIMARY, TEXT_SECONDARY=TEXT_SECONDARY,
    TEXT_MUTED=TEXT_MUTED, TEXT_ACCENT=TEXT_ACCENT,
    GREEN=GREEN, RED=RED,
    BORDER=BORDER, BORDER_FOCUS=BORDER_FOCUS,
    BTN_PRIMARY=BTN_PRIMARY, BTN_PRIMARY_HOVER=BTN_PRIMARY_HOVER,
    BTN_DANGER=BTN_DANGER, BTN_DANGER_HOVER=BTN_DANGER_HOVER,
    BTN_DEFAULT=BTN_DEFAULT, BTN_DEFAULT_HOVER=BTN_DEFAULT_HOVER,
)


# ============================================================
# 浅色主题与切换
# ============================================================

LIGHT_PALETTE = {
    "BG_DARK": "#ffffff", "BG_PANEL": "#f6f8fa", "BG_CARD": "#eef2f7",
    "BG_INPUT": "#ffffff", "BG_HOVER": "#e9eef4", "BG_SELECTED": "#0969da",
    "TEXT_PRIMARY": "#1f2328", "TEXT_SECONDARY": "#59636e", "TEXT_MUTED": "#818b97",
    "TEXT_ACCENT": "#0969da",
    "GREEN": "#1a7f37", "RED": "#cf222e",
    "BORDER": "#d1d9e0", "BORDER_FOCUS": "#0969da",
    "BTN_PRIMARY": "#1a7f37", "BTN_PRIMARY_HOVER": "#116329",
    "BTN_DANGER": "#cf222e", "BTN_DANGER_HOVER": "#a40e26",
    "BTN_DEFAULT": "#eaeef2", "BTN_DEFAULT_HOVER": "#d1d9e0",
}


def get_palette(name: str = "dark") -> dict:
    if name == "light":
        return LIGHT_PALETTE
    return {
        "BG_DARK": BG_DARK, "BG_PANEL": BG_PANEL, "BG_CARD": BG_CARD,
        "BG_INPUT": BG_INPUT, "BG_HOVER": BG_HOVER, "BG_SELECTED": BG_SELECTED,
        "TEXT_PRIMARY": TEXT_PRIMARY, "TEXT_SECONDARY": TEXT_SECONDARY,
        "TEXT_MUTED": TEXT_MUTED, "TEXT_ACCENT": TEXT_ACCENT,
        "GREEN": GREEN, "RED": RED,
        "BORDER": BORDER, "BORDER_FOCUS": BORDER_FOCUS,
        "BTN_PRIMARY": BTN_PRIMARY, "BTN_PRIMARY_HOVER": BTN_PRIMARY_HOVER,
        "BTN_DANGER": BTN_DANGER, "BTN_DANGER_HOVER": BTN_DANGER_HOVER,
        "BTN_DEFAULT": BTN_DEFAULT, "BTN_DEFAULT_HOVER": BTN_DEFAULT_HOVER,
    }


def apply_theme(app, name: str = "dark") -> str:
    """切换全局主题；若 app 不为空则应用。可作为菜单项或 Ctrl+T 绑定。"""
    palette = get_palette(name)
    qss = _QSS_TEMPLATE.format(**palette)
    if app is not None:
        app.setStyleSheet(qss)
    return qss


__all__ = [
    "BG_DARK", "BG_PANEL", "BG_CARD", "BG_INPUT", "BG_HOVER", "BG_SELECTED",
    "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_MUTED", "TEXT_ACCENT",
    "GREEN", "RED", "YELLOW", "ORANGE",
    "BORDER", "BORDER_FOCUS", "BORDER_DANGER",
    "BTN_PRIMARY", "BTN_PRIMARY_HOVER", "BTN_DANGER", "BTN_DANGER_HOVER",
    "BTN_DEFAULT", "BTN_DEFAULT_HOVER",
    "GLOBAL_STYLESHEET", "_QSS_TEMPLATE",
    "LIGHT_PALETTE", "apply_theme", "get_palette",
]
