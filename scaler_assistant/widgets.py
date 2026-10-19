"""Widgets for the Liquid Glass style interface (after MAKO Assistant): crystal switch,
segmented control, chevron button, wordmark, status pill and the game cards."""

from __future__ import annotations

import html
from typing import Any, Callable, Optional

from PyQt6.QtCore import (
    QEasingCurve, QPointF, QPropertyAnimation, QRectF, QSize, Qt, pyqtProperty, pyqtSignal,
)
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import (
    QAbstractButton, QButtonGroup, QFrame, QGridLayout, QHBoxLayout, QLabel, QMenu, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from . import theme
from .i18n import tr
from .launch_options import needs_override

THUMB_W, THUMB_H = 184, 86
API_LABELS = {"dx12": "DX12", "dx11": "DX11", "vulkan": "Vulkan"}


def _label(text: str = "", name: str = "", wrap: bool = False) -> QLabel:
    label = QLabel(text)
    if name:
        label.setObjectName(name)
    label.setWordWrap(wrap)
    return label


def repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def choice_text(choice: Optional[str]) -> str:
    return tr("choice_" + (choice or "none").replace(":", "_"))


# ---- primitives ---------------------------------------------------------------------------------

class Switch(QAbstractButton):
    """Pill toggle: clear crystal track when on, sliding white knob."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._offset = 0.0
        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def sizeHint(self) -> QSize:
        return QSize(42, 24)

    def _get_offset(self) -> float:
        return self._offset

    def _set_offset(self, value: float) -> None:
        self._offset = value
        self.update()

    offset = pyqtProperty(float, _get_offset, _set_offset)

    def _animate(self, checked: bool) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def setChecked(self, checked: bool) -> None:  # programmatic: no animation
        super().setChecked(checked)
        self._anim.stop()
        self._offset = 1.0 if checked else 0.0
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)
        radius = r.height() / 2
        if self.isChecked() and self.isEnabled():
            theme.paint_glass(p, r, radius, "glass_ok", "glass_ok_border")
        else:
            p.setBrush(theme.qcolor("track"))
            p.setPen(theme.qcolor("border"))
            p.drawRoundedRect(r, radius, radius)
        knob = r.height() - 6
        x = r.left() + 3 + self._offset * (r.width() - knob - 6)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(255, 255, 255, 255 if self.isEnabled() else 150))
        p.drawEllipse(QRectF(x, r.top() + 3, knob, knob))


class ChevronButton(QAbstractButton):
    """Round expand / collapse button."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(38, 38)

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(1, 1, self.width() - 2, self.height() - 2)
        if self.isChecked():
            theme.paint_glass(p, r, r.height() / 2)
            color = theme.qcolor("glass_fg")
        else:
            hover = self.underMouse()
            theme.paint_glass(p, r, r.height() / 2, "field_hover" if hover else "field",
                              "border_hover" if hover else "border", "edge")
            color = theme.qcolor("fg")
        c = r.center()
        d = 4.5
        p.setPen(QPen(color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                      Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        sign = -1 if self.isChecked() else 1
        path.moveTo(c + QPointF(-d, -sign * d / 2))
        path.lineTo(c + QPointF(0, sign * d / 2))
        path.lineTo(c + QPointF(d, -sign * d / 2))
        p.drawPath(path)

    def enterEvent(self, event) -> None:
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self.update()
        super().leaveEvent(event)


class Segmented(QFrame):
    """Pill-shaped segmented control; the selected segment is clear crystal."""

    changed = pyqtSignal(object)

    def __init__(self, options: list[tuple[Any, str]], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("segment")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.values: list[Any] = []
        for index, (value, label) in enumerate(options):
            button = QPushButton(label)
            button.setObjectName("seg")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            self.group.addButton(button, index)
            layout.addWidget(button)
            self.values.append(value)
        self.group.idClicked.connect(lambda i: self.changed.emit(self.values[i]))

    def set_value(self, value: Any) -> None:
        for index, candidate in enumerate(self.values):
            if candidate == value:
                self.group.button(index).setChecked(True)
                return


class Wordmark(QWidget):
    """The program's name set in Onest with a teal → blue → coral sheen."""

    def __init__(self, text: str, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.text = text
        self.font_ = QFont("Onest")
        self.font_.setPixelSize(21)
        self.font_.setWeight(QFont.Weight.Bold)
        self.setMinimumHeight(28)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:
        return QSize(QFontMetrics(self.font_).horizontalAdvance(self.text) + 4, 28)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = QFontMetrics(self.font_).horizontalAdvance(self.text)
        grad = QLinearGradient(0, 0, width, 0)
        grad.setColorAt(0.0, QColor(theme.TEAL))
        grad.setColorAt(0.55, QColor(theme.BLUE))
        grad.setColorAt(1.0, QColor(theme.CORAL))
        p.setPen(QPen(grad, 1))
        p.setFont(self.font_)
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text)


class Backdrop(QWidget):
    """Central widget painting the glow background behind everything."""

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        theme.paint_backdrop(p, QRectF(self.rect()))


# ---- game card ----------------------------------------------------------------------------------

def status_of(entry) -> tuple[str, str]:
    """(chip text, tone) for a game."""
    status = entry.status
    if status.installed:
        tone = "warn" if entry.issues else "info" if entry.outdated else "ok"
        return choice_text(status.choice), tone
    if entry.choices:
        return tr("st_not_installed").lstrip("○ ").strip(), "idle"
    return tr("st_unsupported").lstrip("— ").strip(), "idle"


class GameCard(QFrame):
    expand_toggled = pyqtSignal(int, bool)

    def __init__(self, entry, thumb: Optional[QPixmap], actions: dict[str, Callable],
                 helixsr_version: Optional[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.entry = entry
        self.actions = actions
        self.setObjectName("card")
        self.setProperty("expanded", False)
        self.setProperty("supported", bool(entry.supported))
        outer = QVBoxLayout(self)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(0)
        row = QHBoxLayout()
        row.setSpacing(16)

        cover = QLabel()
        cover.setFixedSize(THUMB_W, THUMB_H)
        if thumb is not None:
            cover.setPixmap(thumb)
        else:
            cover.setStyleSheet(f"background: {theme.token('field')}; border-radius: 10px;")
        row.addWidget(cover, 0, Qt.AlignmentFlag.AlignTop)

        info = QVBoxLayout()
        info.setSpacing(5)
        title = _label(entry.display_name, "gameTitle", wrap=True)
        title.setToolTip(entry.install_dir if entry.display_name == entry.name
                         else f"{entry.name}\n{entry.install_dir}")
        info.addWidget(title)
        chips = QHBoxLayout()
        chips.setSpacing(8)
        text, tone = status_of(entry)
        self.status = _label(text, "chip")
        self.status.setProperty("tone", tone)
        chips.addWidget(self.status)
        chips.addWidget(_label(f"App ID {entry.app_id}", "meta"))
        chips.addStretch(1)
        info.addLayout(chips)
        layout = entry.layout
        parts = ([API_LABELS[layout.api]] if layout.api in API_LABELS else []) + layout.upscalers
        meta = " · ".join(parts) or tr("st_unsupported_tip")
        info.addWidget(_label(meta, "meta", wrap=True))
        status = entry.status
        if status.installed:
            if status.upscaler == "helixsr":
                detail = tr("st_helixsr", version=status.version or "?")
                if status.opti_name:
                    detail += " · " + tr("st_opti", name=status.opti_name)
            else:
                detail = tr("st_opti_version", version=status.version or "?", name=status.opti_name)
            info.addWidget(_label(detail, "meta", wrap=True))
        self.fg_switch: Optional[Switch] = None
        if entry.fg is not None:
            info.addLayout(self._fg_row(entry))
        notes = []
        if entry.outdated:
            notes.append(tr("st_outdated", version=helixsr_version or "?")
                         if status.upscaler == "helixsr" else tr("st_outdated_fsr"))
        notes += ["⚠ " + tr(issue + "_short") for issue in entry.issues]
        if layout.anti_cheat:
            notes.append("⚠ " + ", ".join(layout.anti_cheat))
        if notes:
            issue = _label("   ".join(notes), "issue", wrap=True)
            issue.setToolTip("\n".join(tr(i) for i in entry.issues) or tr("ups_anti_cheat"))
            info.addWidget(issue)
        info.addStretch(1)
        row.addLayout(info, 5)

        self.live = QLabel()
        self.live.setTextFormat(Qt.TextFormat.RichText)
        self.live.setWordWrap(True)
        self.live.setMinimumWidth(180)
        self.live.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self.live, 4)

        self.actions_box = QWidget()
        self.actions_box.setObjectName("transparent")
        buttons = QHBoxLayout(self.actions_box)
        buttons.setContentsMargins(0, 0, 0, 0)
        buttons.setSpacing(8)
        self.launch_btn = QPushButton(tr("btn_launch"))
        self.launch_btn.setToolTip(tr("btn_launch_tip"))
        self.launch_btn.clicked.connect(lambda: actions["launch"](entry))
        buttons.addWidget(self.launch_btn)
        if entry.installed and entry.needs_attention:
            fix = QPushButton(tr("btn_repair") if entry.issues else tr("btn_update"))
            fix.setObjectName("update")
            fix.setToolTip(tr("btn_repair_tip") if entry.issues else tr("btn_update_tip"))
            fix.clicked.connect(lambda: actions["choose"](entry, str(entry.status.choice)))
            buttons.addWidget(fix)
        if entry.choices or entry.installed:
            choose = QPushButton(tr("btn_change") if entry.installed else tr("btn_choose"))
            choose.setObjectName("primary" if entry.installed else "install")
            choose.setProperty("menu", True)
            choose.setToolTip(tr("btn_change_tip") if entry.installed else tr("btn_choose_tip"))
            choose.setMenu(actions["menu"](entry, choose))
            buttons.addWidget(choose)
        if entry.installed:
            remove = QPushButton(tr("btn_remove"))
            remove.setObjectName("danger")
            remove.clicked.connect(lambda: actions["uninstall"](entry))
            buttons.addWidget(remove)
        self.chevron = ChevronButton()
        self.chevron.setToolTip(tr("det_title"))
        self.chevron.toggled.connect(self._toggled)
        buttons.addWidget(self.chevron)
        self.top_row = row
        row.addWidget(self.actions_box)
        outer.addLayout(row)
        # Narrow windows: the buttons move to their own row under the game details.
        self.compact_row = QHBoxLayout()
        self.compact_row.addStretch(1)
        outer.addLayout(self.compact_row)
        self.compact = False
        self.details: Optional[QFrame] = None
        self._running = False
        self.set_runtime(None)

    def _fg_row(self, entry) -> QHBoxLayout:
        """HelixSR's frame generation switch (HelixSR Scaler in a game with DLSS Frame Generation)."""
        row = QHBoxLayout()
        row.setSpacing(8)
        switch = Switch()
        switch.setChecked(bool(entry.fg))
        tip = tr("fg_switch_tip")
        if entry.fg_block:
            switch.setEnabled(False)
            tip = tr(entry.fg_block) + "\n\n" + tip
        switch.setToolTip(tip)
        switch.toggled.connect(lambda checked: self.actions["frame_gen"](entry, checked))
        label = _label(tr("fg_switch"), "meta")
        label.setToolTip(tip)
        row.addWidget(switch, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(label, 0, Qt.AlignmentFlag.AlignVCenter)
        if entry.fg_block:
            row.addWidget(_label("⚠ " + tr(entry.fg_block), "issue"), 0,
                          Qt.AlignmentFlag.AlignVCenter)
        row.addStretch(1)
        self.fg_switch = switch
        return row

    def wide_width(self) -> int:
        live = self.live.minimumWidth() + 16 if self._running else 0
        return 28 + THUMB_W + 16 + 300 + live + 16 + self.actions_box.sizeHint().width()

    def set_compact(self, compact: bool) -> None:
        if compact == self.compact:
            return
        self.compact = compact
        if compact:
            self.top_row.removeWidget(self.actions_box)
            self.compact_row.addWidget(self.actions_box)
            self.compact_row.setContentsMargins(0, 10, 0, 0)
        else:
            self.compact_row.removeWidget(self.actions_box)
            self.compact_row.setContentsMargins(0, 0, 0, 0)
            self.top_row.addWidget(self.actions_box)

    # ---- details ----

    def _build_details(self) -> QFrame:
        entry, layout, status = self.entry, self.entry.layout, self.entry.status
        panel = QFrame(self)
        panel.setObjectName("details")
        box = QVBoxLayout(panel)
        box.setContentsMargins(4, 14, 4, 2)
        box.setSpacing(10)
        box.addWidget(_label(tr("det_title"), "panelTitle"))
        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(6)
        rows: list[tuple[str, str]] = [
            (tr("det_api"), API_LABELS.get(layout.api, tr("ups_api_unknown"))),
            (tr("det_upscalers"), " · ".join(layout.upscalers) or "—"),
            (tr("det_exe"), layout.exe_dir or "—"),
        ]
        rows += [(tr("det_fsr_dll"), path) for path in layout.fsr_targets]
        if status.opti_name:
            rows.append(("OptiScaler", status.opti_name))
        if status.opti_name and needs_override(status.opti_name) or entry.launch_options:
            rows.append((tr("det_launch"), entry.launch_options or tr("empty")))
        if status.installed_by:
            rows.append((tr("det_installed_by"), status.installed_by))
        for index, (name, value) in enumerate(rows):
            grid.addWidget(_label(name, "fieldLabel"), index, 0, Qt.AlignmentFlag.AlignTop)
            label = _label(value, "path" if "/" in value else "fieldValue", wrap=True)
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            grid.addWidget(label, index, 1)
        grid.setColumnStretch(1, 1)
        box.addLayout(grid)
        hints = []
        if status.installed:
            hints.append(tr("svc_pick_" + str(status.choice).replace(":", "_")))
        hints += [tr(issue) for issue in entry.issues]
        if not entry.supported:
            hints.append(tr("st_unsupported_tip"))
        elif not layout.helixsr_possible and layout.optiscaler_possible:
            hints.append(tr("ups_no_helixsr"))
        if layout.anti_cheat:
            hints.append(tr("ups_anti_cheat"))
        for hint in hints:
            box.addWidget(_label(hint, "meta", wrap=True))
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        actions = self.actions
        if status.upscaler == "helixsr" and status.route != "hscaler":
            settings = QPushButton(tr("btn_settings"))
            settings.setToolTip(tr("btn_settings_tip"))
            settings.clicked.connect(lambda: actions["settings"](entry))
            buttons.addWidget(settings)
        if status.installed:
            log = QPushButton(tr("menu_log", file="helixsr.log" if status.upscaler == "helixsr"
                                 else "OptiScaler.log"))
            log.clicked.connect(lambda: actions["log"](entry))
            buttons.addWidget(log)
        folder = QPushButton(tr("menu_folder"))
        folder.clicked.connect(lambda: actions["folder"](entry))
        buttons.addWidget(folder)
        if layout.optiscaler_possible:
            name = QPushButton(tr("menu_opti_name", name=status.opti_name) if status.opti_name
                               else tr("menu_opti_name_auto"))
            name.clicked.connect(lambda: actions["opti_name"](entry))
            buttons.addWidget(name)
        buttons.addStretch(1)
        box.addLayout(buttons)
        return panel

    def _toggled(self, checked: bool) -> None:
        self.set_expanded(checked)
        self.expand_toggled.emit(self.entry.app_id, checked)

    def set_expanded(self, expanded: bool) -> None:
        if self.details is None:
            self.details = self._build_details()
            self.layout().addWidget(self.details)
        self.details.setVisible(expanded)
        self.layout().setSpacing(12 if expanded else 0)
        if self.chevron.isChecked() != expanded:
            self.chevron.blockSignals(True)
            self.chevron.setChecked(expanded)
            self.chevron.blockSignals(False)
        self.setProperty("expanded", expanded)
        repolish(self)

    def set_runtime(self, live_html: Optional[str], running: bool = False,
                    tip: str = "") -> None:
        self._running = running
        self.live.setVisible(bool(live_html))
        self.live.setText(live_html or "")
        self.live.setToolTip(tip)
        self.launch_btn.setEnabled(not running)
        self.launch_btn.setText(tr("btn_running") if running else tr("btn_launch"))
        self.launch_btn.setObjectName("running" if running else "")
        repolish(self.launch_btn)


def live_html(headline: str, color: str, lines, notes) -> str:
    ok, warn, muted, fg = (theme.token(k) for k in ("ok", "warn", "muted", "fg"))
    tone = {"ok": ok, "warn": warn, "orange": theme.token("danger")}.get(color, warn)
    parts = [f'<span style="color:{tone};font-weight:600">{html.escape(headline)}</span>']
    for name, detail, active in lines:
        mark, mtone = ("✓", ok) if active else ("✗", muted)
        extra = f' <span style="color:{muted}">— {html.escape(detail)}</span>' if detail else ""
        parts.append(f'<span style="color:{mtone}">{mark}</span> '
                     f'<span style="color:{fg}">{html.escape(name)}</span>{extra}')
    for note in notes:
        parts.append(f'<span style="color:{warn}">⚠ {html.escape(note)}</span>')
    return "<br>".join(parts)


def menu(parent: QWidget) -> QMenu:
    return QMenu(parent)
