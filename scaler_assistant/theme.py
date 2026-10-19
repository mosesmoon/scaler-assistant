"""Visual system for Scaler Assistant, in MAKO Assistant's Liquid Glass style.

Near-black ground lit by soft teal / blue / coral glows, glass panels with
hairline borders. Buttons, switches and selected segments are clear crystal:
a translucent tint, a light hairline border and a brighter top edge, never a
gradient. Colours are tokens; `stylesheet()` renders the Qt style sheet from them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor, QFontDatabase, QGuiApplication, QPainter, QPainterPath, QPixmap, QRadialGradient,
)

TEAL, CORAL, PURPLE, BLUE = "#27d4b3", "#f86461", "#946eff", "#469ef6"

PALETTES: dict[str, dict[str, str]] = {
    "dark": {
        "bg": "#0a0a0c", "fg": "#f5f5f5", "muted": "rgba(245,245,245,0.56)",
        "faint": "rgba(245,245,245,0.36)", "panel": "rgba(255,255,255,0.035)",
        "panel2": "rgba(255,255,255,0.05)",
        "field": "rgba(255,255,255,0.06)", "field_hover": "rgba(255,255,255,0.10)",
        "border": "rgba(255,255,255,0.09)", "border_hover": "rgba(255,255,255,0.22)",
        "edge": "rgba(255,255,255,0.26)",
        "track": "rgba(255,255,255,0.14)", "popover": "#1a1a20",
        "ok": TEAL, "ok_bg": "rgba(39,212,179,0.13)", "warn": "#f2c14e",
        "warn_bg": "rgba(242,193,78,0.13)", "info": "#7cc0ff", "info_bg": "rgba(70,158,246,0.14)",
        "danger": "#ff8a87", "danger_bg": "rgba(248,100,97,0.12)", "idle_bg": "rgba(255,255,255,0.06)",
        "log_bg": "rgba(0,0,0,0.35)", "glow": "0.20",
        # Crystal buttons: tint, tint on hover, border, bright top edge, text.
        "glass": "rgba(110,190,255,0.16)", "glass_hover": "rgba(110,190,255,0.26)",
        "glass_border": "rgba(150,210,255,0.40)", "glass_edge": "rgba(225,242,255,0.78)",
        "glass_fg": "#eaf6ff",
        "glass_ok": "rgba(39,212,179,0.17)", "glass_ok_hover": "rgba(39,212,179,0.27)",
        "glass_ok_border": "rgba(80,230,200,0.42)", "glass_ok_fg": "#d9fff6",
        "glass_warn": "rgba(242,193,78,0.15)", "glass_warn_hover": "rgba(242,193,78,0.25)",
        "glass_warn_border": "rgba(242,193,78,0.45)", "glass_warn_fg": "#ffe9b3",
        "glass_danger": "rgba(248,100,97,0.12)", "glass_danger_hover": "rgba(248,100,97,0.22)",
        "glass_danger_border": "rgba(255,138,135,0.40)",
        "knob": "#ffffff",
    },
    "light": {
        "bg": "#eef0f3", "fg": "#15171c", "muted": "rgba(21,23,28,0.60)",
        "faint": "rgba(21,23,28,0.40)", "panel": "rgba(255,255,255,0.72)",
        "panel2": "rgba(255,255,255,0.85)",
        "field": "rgba(255,255,255,0.65)", "field_hover": "rgba(255,255,255,0.95)",
        "border": "rgba(21,23,28,0.10)", "border_hover": "rgba(21,23,28,0.24)",
        "edge": "rgba(255,255,255,1.0)",
        "track": "rgba(21,23,28,0.14)", "popover": "#ffffff",
        "ok": "#0f9e84", "ok_bg": "rgba(15,158,132,0.12)", "warn": "#a76d00",
        "warn_bg": "rgba(242,193,78,0.22)", "info": "#2b74d0", "info_bg": "rgba(70,158,246,0.14)",
        "danger": "#d2423f", "danger_bg": "rgba(248,100,97,0.12)", "idle_bg": "rgba(21,23,28,0.06)",
        "log_bg": "rgba(255,255,255,0.6)", "glow": "0.16",
        "glass": "rgba(70,158,246,0.14)", "glass_hover": "rgba(70,158,246,0.22)",
        "glass_border": "rgba(43,116,208,0.40)", "glass_edge": "rgba(255,255,255,1.0)",
        "glass_fg": "#1d5fae",
        "glass_ok": "rgba(15,158,132,0.13)", "glass_ok_hover": "rgba(15,158,132,0.21)",
        "glass_ok_border": "rgba(15,158,132,0.42)", "glass_ok_fg": "#0a7a66",
        "glass_warn": "rgba(242,193,78,0.22)", "glass_warn_hover": "rgba(242,193,78,0.32)",
        "glass_warn_border": "rgba(167,109,0,0.40)", "glass_warn_fg": "#7d5200",
        "glass_danger": "rgba(248,100,97,0.10)", "glass_danger_hover": "rgba(248,100,97,0.18)",
        "glass_danger_border": "rgba(210,66,63,0.40)",
        "knob": "#ffffff",
    },
}

DISPLAY = '"Onest SemiBold", "Onest", "Noto Sans CJK TC", "Noto Sans CJK SC", sans-serif'
DISPLAY_BOLD = '"Onest", "Onest SemiBold", "Noto Sans CJK TC", "Noto Sans CJK SC", sans-serif'
BODY = '"Inter", "Noto Sans CJK TC", "Noto Sans CJK SC", "Noto Sans", sans-serif'
BODY_MEDIUM = '"Inter Medium", "Inter", "Noto Sans CJK TC", "Noto Sans CJK SC", sans-serif'
BODY_SEMIBOLD = '"Inter SemiBold", "Inter", "Noto Sans CJK TC", "Noto Sans CJK SC", sans-serif'
MONO = '"JetBrains Mono", "DejaVu Sans Mono", "Noto Sans Mono", monospace'

_mode = "dark"          # resolved: dark | light
_fonts_loaded = False


def load_fonts() -> None:
    global _fonts_loaded
    if _fonts_loaded:
        return
    for path in sorted((Path(__file__).parent / "assets" / "fonts").glob("*.ttf")):
        QFontDatabase.addApplicationFont(str(path))
    _fonts_loaded = True


def resolve(choice: str) -> str:
    """auto → the desktop's colour scheme (dark when unknown)."""
    if choice in ("dark", "light"):
        return choice
    app = QGuiApplication.instance()
    try:
        scheme = app.styleHints().colorScheme() if app else None
        if scheme == Qt.ColorScheme.Light:
            return "light"
    except AttributeError:  # Qt < 6.5
        pass
    return "dark"


def set_mode(mode: str) -> None:
    global _mode
    _mode = mode if mode in PALETTES else "dark"


def mode() -> str:
    return _mode


def token(name: str) -> str:
    return PALETTES[_mode][name]


def qcolor(name: str) -> QColor:
    value = token(name)
    if value.startswith("rgba("):
        r, g, b, a = (float(x) for x in value[5:-1].split(","))
        return QColor(int(r), int(g), int(b), int(round(a * 255)))
    return QColor(value)


def paint_glass(painter: QPainter, rect: QRectF, radius: float, fill: str = "glass",
                border: str = "glass_border", edge: str = "glass_edge") -> None:
    """A crystal surface: translucent tint, hairline border, brighter top edge (no gradient)."""
    painter.setBrush(qcolor(fill))
    painter.setPen(qcolor(border))
    painter.drawRoundedRect(rect, radius, radius)
    path = QPainterPath()
    inner = rect.adjusted(radius * 0.45, 0.5, -radius * 0.45, 0)
    path.moveTo(inner.left(), inner.top() + 0.5)
    path.lineTo(inner.right(), inner.top() + 0.5)
    painter.setPen(qcolor(edge))
    painter.drawPath(path)


def paint_backdrop(painter: QPainter, rect: QRectF) -> None:
    """Base colour plus soft teal / blue / coral glows."""
    painter.fillRect(rect, qcolor("bg"))
    strength = float(token("glow"))
    w, h = rect.width(), rect.height()
    for (fx, fy, radius, color) in ((0.18, 0.28, 0.55, TEAL), (0.88, 0.30, 0.50, BLUE),
                                    (0.55, 1.02, 0.55, CORAL)):
        center = QPointF(rect.left() + fx * w, rect.top() + fy * h)
        gradient = QRadialGradient(center, max(w, h) * radius)
        glow = QColor(color)
        glow.setAlphaF(strength)
        gradient.setColorAt(0.0, glow)
        glow.setAlphaF(0.0)
        gradient.setColorAt(1.0, glow)
        painter.fillRect(rect, gradient)


def rounded(pixmap: QPixmap, radius: float) -> QPixmap:
    """A copy of `pixmap` with rounded corners (thumbnails)."""
    out = QPixmap(pixmap.size())
    out.setDevicePixelRatio(pixmap.devicePixelRatio())
    out.fill(Qt.GlobalColor.transparent)
    painter = QPainter(out)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    size = pixmap.deviceIndependentSize()
    path.addRoundedRect(QRectF(0, 0, size.width(), size.height()), radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, pixmap)
    painter.end()
    return out


def _glass_button(selector: str, p: dict, kind: str = "") -> str:
    k = f"_{kind}" if kind else ""
    fg = p.get(f"glass{k}_fg", p["glass_fg"] if not kind else p["danger"])
    return f"""
{selector} {{ background: {p[f'glass{k}']}; border: 1px solid {p[f'glass{k}_border']};
    border-top-color: {p['glass_edge']}; color: {fg}; font-family: {BODY_SEMIBOLD}; }}
{selector}:hover {{ background: {p[f'glass{k}_hover']}; }}
{selector}:pressed {{ background: {p[f'glass{k}']}; border-top-color: {p[f'glass{k}_border']}; }}
{selector}:disabled {{ background: {p['field']}; border-color: {p['border']}; color: {p['faint']}; }}
"""


def stylesheet(palette: Optional[dict[str, str]] = None) -> str:
    p = palette or PALETTES[_mode]
    return f"""
* {{ font-family: {BODY}; font-size: 13px; color: {p['fg']}; }}
QMainWindow, QDialog, QMessageBox {{ background: {p['bg']}; }}
QWidget#transparent, QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; }}
QToolTip {{ background: {p['popover']}; color: {p['fg']}; border: 1px solid {p['border_hover']};
    border-radius: 8px; padding: 6px 8px; }}

QLabel#tagline, QLabel#muted, QLabel#footer, QLabel#subtitle {{ color: {p['muted']}; }}
QLabel#footer {{ font-size: 11px; }}
QLabel#gameTitle {{ font-family: {DISPLAY}; font-size: 16px; }}
QLabel#meta {{ color: {p['muted']}; font-size: 12px; }}
QLabel#issue {{ color: {p['warn']}; font-size: 12px; }}
QLabel#path {{ color: {p['faint']}; font-size: 11px; font-family: {MONO}; }}
QLabel#panelTitle {{ font-family: {DISPLAY}; font-size: 15px; }}
QLabel#fieldLabel {{ color: {p['muted']}; font-family: {BODY_MEDIUM}; font-size: 12px; }}
QLabel#fieldValue {{ font-size: 12px; }}
QLabel#empty {{ color: {p['muted']}; font-size: 14px; padding: 40px; }}
QLabel#banner {{ background: {p['warn_bg']}; border: 1px solid {p['glass_warn_border']};
    border-radius: 12px; padding: 10px 12px; color: {p['fg']}; }}
QLabel#card {{ background: {p['panel2']}; border: 1px solid {p['border']}; border-radius: 12px;
    padding: 10px 12px; }}

QLabel#pill, QPushButton#pill {{ background: {p['panel2']}; border: 1px solid {p['border']};
    border-top-color: {p['edge']}; border-radius: 16px; padding: 0 14px; min-height: 30px;
    max-height: 30px; font-family: {BODY_MEDIUM}; font-size: 12px; }}
QPushButton#pill:hover {{ background: {p['field_hover']}; border-color: {p['border_hover']};
    border-top-color: {p['edge']}; }}
QLabel#chip {{ border-radius: 10px; padding: 3px 10px; font-family: {BODY_MEDIUM}; font-size: 12px; }}
QLabel#chip[tone="ok"] {{ color: {p['ok']}; background: {p['ok_bg']}; }}
QLabel#chip[tone="warn"] {{ color: {p['warn']}; background: {p['warn_bg']}; }}
QLabel#chip[tone="info"] {{ color: {p['info']}; background: {p['info_bg']}; }}
QLabel#chip[tone="idle"] {{ color: {p['muted']}; background: {p['idle_bg']}; }}
QLabel#chip[tone="danger"] {{ color: {p['danger']}; background: {p['danger_bg']}; }}

QFrame#card {{ background: {p['panel']}; border: 1px solid {p['border']}; border-radius: 16px; }}
QFrame#card[expanded="true"] {{ border-color: {p['border_hover']}; }}
QFrame#card[supported="false"] {{ background: transparent; }}
QFrame#details {{ background: transparent; border: none; border-top: 1px solid {p['border']};
    border-radius: 0; }}
QFrame#topbar, QFrame#toolbar {{ background: transparent; }}
QFrame#drawer {{ background: {p['panel']}; border: 1px solid {p['border']}; border-radius: 14px; }}
QGroupBox {{ background: {p['panel2']}; border: 1px solid {p['border']}; border-radius: 14px;
    margin-top: 16px; padding: 14px 12px 10px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 4px; color: {p['muted']};
    font-family: {DISPLAY}; }}

QPushButton {{ background: {p['field']}; border: 1px solid {p['border']}; border-top-color: {p['edge']};
    border-radius: 17px; padding: 7px 16px; font-family: {BODY_MEDIUM}; min-height: 20px; }}
QPushButton:hover {{ background: {p['field_hover']}; border-color: {p['border_hover']};
    border-top-color: {p['edge']}; }}
QPushButton:pressed {{ background: {p['border']}; }}
QPushButton:disabled {{ color: {p['faint']}; background: {p['field']}; border-color: {p['border']}; }}
QPushButton:focus {{ border-color: {p['border_hover']}; }}
QPushButton::menu-indicator {{ subcontrol-origin: padding; subcontrol-position: right center;
    right: 10px; width: 8px; }}
QPushButton[menu="true"] {{ padding-right: 28px; }}
{_glass_button("QPushButton#primary", p)}
{_glass_button("QPushButton#install", p, "ok")}
{_glass_button("QPushButton#update", p, "warn")}
{_glass_button("QPushButton#danger", p, "danger")}
QPushButton#running, QPushButton#running:disabled {{ color: {p['ok']}; background: {p['ok_bg']};
    border-color: transparent; }}
QPushButton#link {{ background: transparent; border: none; color: {p['muted']}; padding: 4px 6px; }}
QPushButton#link:hover {{ color: {p['fg']}; }}

QFrame#segment {{ background: {p['field']}; border: 1px solid {p['border']}; border-radius: 17px; }}
QPushButton#seg {{ background: transparent; border: 1px solid transparent; border-radius: 14px;
    padding: 5px 10px; color: {p['muted']}; font-family: {BODY_MEDIUM}; font-size: 12px;
    min-height: 18px; }}
QPushButton#seg:hover {{ color: {p['fg']}; }}
QPushButton#seg:checked {{ background: {p['glass']}; border-color: {p['glass_border']};
    border-top-color: {p['glass_edge']}; color: {p['glass_fg']}; }}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {{ background: {p['field']}; border: 1px solid {p['border']};
    border-radius: 17px; padding: 7px 14px; selection-background-color: {BLUE}; min-height: 20px; }}
QLineEdit:hover, QComboBox:hover, QDoubleSpinBox:hover {{ border-color: {p['border_hover']}; }}
QLineEdit:focus, QDoubleSpinBox:focus {{ border-color: {p['glass_border']}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{ background: {p['popover']}; border: 1px solid {p['border_hover']};
    border-radius: 10px; padding: 4px; selection-background-color: {p['field_hover']};
    selection-color: {p['fg']}; outline: none; }}
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ width: 0; border: none; }}
QMenu {{ background: {p['popover']}; border: 1px solid {p['border_hover']}; border-radius: 12px;
    padding: 6px; }}
QMenu::item {{ padding: 7px 18px 7px 28px; border-radius: 8px; }}
QMenu::item:selected {{ background: {p['glass']}; color: {p['fg']}; }}
QMenu::item:disabled {{ color: {p['faint']}; }}
QMenu::separator {{ height: 1px; background: {p['border']}; margin: 5px 8px; }}

QCheckBox {{ spacing: 8px; }}
QPlainTextEdit {{ background: {p['log_bg']}; border: none; border-radius: 10px; padding: 6px;
    font-family: {MONO}; font-size: 12px; color: {p['muted']}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: {p['track']}; border-radius: 3px; min-height: 40px; }}
QScrollBar::handle:vertical:hover {{ background: {p['border_hover']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px 4px; }}
QScrollBar::handle:horizontal {{ background: {p['track']}; border-radius: 3px; min-width: 40px; }}
QStatusBar {{ background: transparent; color: {p['muted']}; }}
QMessageBox QLabel {{ font-size: 13px; }}
"""
