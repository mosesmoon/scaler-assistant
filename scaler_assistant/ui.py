"""PyQt6 user interface for Scaler Assistant (Scaler 助手)."""

from __future__ import annotations

import html
import shlex
import shutil
import subprocess
import sys
import time
import traceback
from datetime import datetime
from functools import cmp_to_key
from pathlib import Path
from typing import Callable, Optional

from PyQt6.QtCore import (
    QCollator, QEvent, QLibraryInfo, QLocale, QObject, QRunnable, Qt, QThreadPool, QTimer,
    QTranslator, QUrl, pyqtSignal,
)
from PyQt6.QtGui import QAction, QDesktopServices, QGuiApplication, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from . import __version__, components, gpu, i18n, optiscaler, overlay, settings, status, theme
from .helixsr import HelixSRFolder, MIN_VERSION
from .i18n import tr
from .launch_options import needs_override
from .runtime import RunningGame, detect_running
from .service import (
    AssistantService, ChoicePlan, GameEntry, GameRunningError, NeedsDownloadError,
    NeedsHelixSRError, SteamMustCloseError, choice_label, component_label, upscaler_of,
)
from .widgets import (
    API_LABELS, THUMB_H, THUMB_W, Backdrop, GameCard, Segmented, Switch, Wordmark, live_html,
)

POLL_MS = 3000
OVERLAY_SECONDS = 10
# Upscaler installed, game running, DLL still not loaded after this long: say so.
OVERLAY_NOT_LOADED_AFTER = 90
RELEASES_URL = "https://github.com/lonewolf0622/HelixSR/releases"
# The overlay is always dark glass, whatever the window's theme.
OVERLAY_COLORS = {"ok": theme.TEAL, "warn": "#f2c14e", "orange": "#ff9a5c"}

(FILTER_SUPPORTED, FILTER_INSTALLED, FILTER_NOT_INSTALLED, FILTER_ATTENTION, FILTER_RUNNING,
 FILTER_ALL) = range(6)


def window_title() -> str:
    name = tr("app_name")
    return name if name == "Scaler Assistant" else f"{name} (Scaler Assistant)"


def mb(size: int) -> str:
    return f"{size / 1_000_000:.0f} MB"


class _Signals(QObject):
    done = pyqtSignal(object)
    failed = pyqtSignal(object)
    progress = pyqtSignal(object)


class _Task(QRunnable):
    def __init__(self, fn: Callable, *args) -> None:
        super().__init__()
        self.fn, self.args = fn, args
        self.signals = _Signals()

    def run(self) -> None:
        try:
            result = self.fn(*self.args)
        except Exception as error:  # surfaced to the UI
            error.trace = traceback.format_exc()
            self.signals.failed.emit(error)
        else:
            self.signals.done.emit(result)


# ---- terminal for HelixSR's own setup --------------------------------------------------------

_TERMINALS = (
    ("konsole", ["-e"]), ("gnome-terminal", ["--"]), ("kgx", ["-e"]), ("ptyxis", ["--"]),
    ("xfce4-terminal", ["-x"]), ("alacritty", ["-e"]), ("kitty", []), ("foot", []),
    ("wezterm", ["start", "--"]), ("xterm", ["-e"]),
)


def find_terminal() -> Optional[tuple[str, list[str]]]:
    for name, flags in _TERMINALS:
        path = shutil.which(name)
        if path:
            return path, flags
    return None


def run_setup_in_terminal(folder: Path) -> bool:
    terminal = find_terminal()
    script = folder / "helixsr-setup.sh"
    if terminal is None or not script.is_file():
        return False
    pause = shlex.quote(tr("term_done"))
    command = (f"cd {shlex.quote(str(folder))} && bash ./helixsr-setup.sh; "
               f"echo; read -r -p {pause} _")
    path, flags = terminal
    subprocess.Popen([path, *flags, "bash", "-c", command], stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    return True


# ---- dialogs -----------------------------------------------------------------------------------

def confirm(parent: QWidget, title: str, text: str, ok_text: str,
            icon=QMessageBox.Icon.Warning) -> bool:
    box = QMessageBox(icon, title, text, parent=parent)
    box.setTextFormat(Qt.TextFormat.RichText)
    ok = box.addButton(ok_text, QMessageBox.ButtonRole.AcceptRole)
    box.addButton(tr("cancel"), QMessageBox.ButtonRole.RejectRole)
    box.exec()
    return box.clickedButton() is ok


def _label(text: str, name: str = "", rich: bool = True) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    if rich:
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setOpenExternalLinks(True)
    if name:
        label.setObjectName(name)
    return label


class _FitDialog(QDialog):
    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Top-level windows ignore height-for-width: size the dialog for its wrapped texts.
        layout = self.layout()
        layout.activate()
        height = (layout.totalHeightForWidth(self.width()) if layout.hasHeightForWidth()
                  else layout.totalMinimumSize().height())
        if height > self.height():
            self.setMinimumHeight(height)
            self.resize(self.width(), height)


class RemoveDialog(_FitDialog):
    def __init__(self, entry: GameEntry, has_settings: bool, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("remove_title"))
        self.setMinimumWidth(520)
        layout = QVBoxLayout(self)
        body = tr("remove_body", name=html.escape(entry.display_name),
                  choice=html.escape(choice_label(entry.status.choice)))
        if entry.launch_options and entry.status.opti_name and needs_override(entry.status.opti_name):
            body += "<br><br>" + tr("remove_launch")
        layout.addWidget(_label(body))
        self.remove_settings = QCheckBox(tr("remove_settings"))
        if entry.status.upscaler != "helixsr":
            self.remove_settings.setVisible(False)
        elif not has_settings:
            self.remove_settings.setEnabled(False)
            self.remove_settings.setToolTip(tr("remove_no_settings"))
        layout.addWidget(self.remove_settings)
        buttons = QDialogButtonBox()
        ok = buttons.addButton(tr("btn_remove"), QDialogButtonBox.ButtonRole.AcceptRole)
        ok.setObjectName("danger")
        buttons.addButton(tr("cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class SettingsDialog(_FitDialog):
    """helixsr.ini as a form. "Default" removes the line: HelixSR then uses its own default."""

    def __init__(self, entry: GameEntry, values: dict[str, str], folder: Optional[HelixSRFolder],
                 gpus: list[gpu.Gpu], parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("set_title", name=entry.display_name))
        self.setMinimumWidth(620)
        self.result_values: dict[str, Optional[str]] = {}
        newer = folder.reads_int8() if folder and folder.version else True
        layout = QVBoxLayout(self)
        # Word-wrapped hints otherwise let the dialog shrink below what its rows need.
        layout.setSizeConstraint(QVBoxLayout.SizeConstraint.SetMinimumSize)
        layout.addWidget(_label(tr("set_intro"), "subtitle", rich=False))

        self.combos: dict[str, QComboBox] = {}

        def combo(key: str, options: list[tuple[str, Optional[str]]]) -> QComboBox:
            box = QComboBox()
            for label, value in options:
                box.addItem(label, value)
            current = values.get(key)
            index = box.findData(current.lower() if current else None)
            box.setCurrentIndex(max(index, 0))
            self.combos[key] = box
            return box

        sharp = QGroupBox(tr("set_sharpening"))
        form = QFormLayout(sharp)
        form.addRow(tr("set_sharpener"), combo("Sharpener", [
            (tr("set_default"), None), (tr("set_off"), "off"),
            (tr("set_nvidia"), "nvidia"), (tr("set_rcas"), "rcas")]))
        row = QHBoxLayout()
        self.sharpness_default = QCheckBox(tr("set_default"))
        self.sharpness = QDoubleSpinBox()
        self.sharpness.setRange(0.0, 1.0)
        self.sharpness.setSingleStep(0.05)
        self.sharpness.setDecimals(2)
        current = settings.normalize(settings.BY_KEY["sharpness"], values.get("Sharpness"))
        self.sharpness.setValue(float(current) if current else 0.10)
        self.sharpness_default.setChecked(current is None)
        self.sharpness.setEnabled(current is not None)
        self.sharpness_default.toggled.connect(lambda on: self.sharpness.setEnabled(not on))
        row.addWidget(self.sharpness)
        row.addWidget(self.sharpness_default)
        row.addStretch(1)
        form.addRow(tr("set_sharpness"), row)
        form.addRow(tr("set_game_slider"), combo("UseGameSlider", [
            (tr("set_default"), None), (tr("set_yes"), "true"), (tr("set_no"), "false")]))
        form.addRow(_label(tr("set_sharp_hint"), "subtitle", rich=False))
        layout.addWidget(sharp)

        upscaling = QGroupBox(tr("set_upscaling"))
        form = QFormLayout(upscaling)
        form.addRow(tr("set_int8"), combo("Int8", [
            (tr("set_default_auto"), None), (tr("set_auto"), "auto"), (tr("set_on"), "on"),
            (tr("set_off"), "off")]))
        form.addRow(tr("set_filter"), combo("UpscaleFilter", [
            (tr("set_default_lanczos"), None), ("Lanczos", "lanczos"), (tr("set_easu"), "easu")]))
        form.addRow(_label(tr("set_upscaling_hint") + ("" if newer else "<br><b>" + tr(
            "set_needs_190", version=folder.version if folder else "?") + "</b>"), "subtitle"))
        upscaling.setEnabled(newer or bool(values.get("Int8") or values.get("UpscaleFilter")))
        layout.addWidget(upscaling)

        compat = QGroupBox(tr("set_compat"))
        form = QFormLayout(compat)
        form.addRow(tr("set_wave"), combo("WaveSize", [
            (tr("set_default"), None), ("64", "64"), ("32", "32")]))
        rdna3 = any(g.rdna3_or_newer for g in gpus)
        form.addRow(_label(tr("set_wave_hint") + ("<br>" + tr("set_wave_hint_rdna3")
                                                   if rdna3 and entry.status.route == "optiscaler"
                                                   else ""), "subtitle"))
        layout.addWidget(compat)

        where = _label(tr("set_where", paths="<br>".join(
            html.escape(str(d / settings.INI)) for d in entry.status.ini_dirs)), "subtitle")
        where.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(where)

        buttons = QDialogButtonBox()
        save = buttons.addButton(tr("btn_save"), QDialogButtonBox.ButtonRole.AcceptRole)
        save.setObjectName("primary")
        reset = buttons.addButton(tr("btn_reset"), QDialogButtonBox.ButtonRole.ResetRole)
        buttons.addButton(tr("cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        reset.clicked.connect(self._reset)
        layout.addWidget(buttons)

    def _reset(self) -> None:
        for box in self.combos.values():
            box.setCurrentIndex(0)
        self.sharpness_default.setChecked(True)

    def _save(self) -> None:
        self.result_values = {key: box.currentData() for key, box in self.combos.items()}
        self.result_values["Sharpness"] = (None if self.sharpness_default.isChecked()
                                           else f"{self.sharpness.value():.2f}")
        self.accept()


class LogDialog(QDialog):
    def __init__(self, entry: GameEntry, path: Optional[Path], text: str, can_fix_wave: bool,
                 parent: "MainWindow") -> None:
        super().__init__(parent)
        name = path.name if path else ("helixsr.log" if entry.status.upscaler == "helixsr"
                                       else optiscaler.LOG)
        self.setWindowTitle(tr("log_title", file=name, name=entry.display_name))
        self.resize(900, 560)
        layout = QVBoxLayout(self)
        where = _label(html.escape(str(path)) if path else tr("log_none", file=name), "subtitle")
        where.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(where)
        if can_fix_wave:
            layout.addWidget(_label(tr("log_wave32"), "banner", rich=False))
        view = QPlainTextEdit(text or "")
        view.setReadOnly(True)
        view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(view, 1)
        buttons = QDialogButtonBox()
        if can_fix_wave:
            fix = buttons.addButton(tr("btn_fix_wave"), QDialogButtonBox.ButtonRole.ActionRole)
            fix.setObjectName("primary")
            fix.clicked.connect(lambda: (self.accept(), parent.fix_wave(entry)))
        copy = buttons.addButton(tr("btn_copy"), QDialogButtonBox.ButtonRole.ActionRole)
        copy.clicked.connect(lambda: QGuiApplication.clipboard().setText(text or ""))
        copy.setEnabled(bool(text))
        if path:
            folder = buttons.addButton(tr("btn_open_folder"), QDialogButtonBox.ButtonRole.ActionRole)
            folder.clicked.connect(lambda: AssistantService.open_path(path.parent))
        close = buttons.addButton(tr("close"), QDialogButtonBox.ButtonRole.RejectRole)
        close.clicked.connect(self.reject)
        layout.addWidget(buttons)


class HelixSRDialog(_FitDialog):
    """The user's HelixSR folder: where it is, whether it is set up, and how to get there."""

    def __init__(self, folder: Optional[HelixSRFolder], parent: "MainWindow") -> None:
        super().__init__(parent)
        self.main = parent
        self.setWindowTitle(tr("hx_title"))
        self.setMinimumWidth(640)
        layout = QVBoxLayout(self)
        minimum = ".".join(map(str, MIN_VERSION))
        if folder is not None and folder.ready:
            text = tr("hx_ready_body", version=html.escape(folder.version or "?"),
                      path=html.escape(str(folder.path)))
            box = "card"
        else:
            if folder is None:
                problem = "hx_none"
            else:
                problem = folder.problem or "hx_not_helixsr"
            text = tr("banner_" + problem.removeprefix("hx_"),
                      path=html.escape(str(folder.path)) if folder else "",
                      version=html.escape(folder.version or "?") if folder else "?",
                      minimum=minimum)
            text = text.replace("<a href=", '<a style="color:#ffd27a;" href=')
            text += "<br><br>" + tr("banner_note")
            box = "banner"
        layout.addWidget(_label(tr("hx_intro"), "subtitle"))
        layout.addWidget(_label(text, box))
        buttons = QHBoxLayout()
        choose = QPushButton(tr("btn_choose_folder"))
        choose.setObjectName("primary")
        choose.clicked.connect(lambda: (self.accept(), self.main.choose_folder()))
        buttons.addWidget(choose)
        if folder is not None and folder.version and not folder.built:
            setup = QPushButton(tr("btn_run_setup"))
            setup.setToolTip(tr("btn_run_setup_tip"))
            setup.setEnabled(find_terminal() is not None)
            if find_terminal() is None:
                setup.setToolTip(tr("btn_run_setup_none"))
            setup.clicked.connect(lambda: (self.accept(), self.main.run_setup()))
            buttons.addWidget(setup)
        download = QPushButton(tr("btn_download"))
        download.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(RELEASES_URL)))
        buttons.addWidget(download)
        buttons.addStretch(1)
        close = QPushButton(tr("close"))
        close.clicked.connect(self.reject)
        buttons.addWidget(close)
        layout.addLayout(buttons)


class DownloadsDialog(_FitDialog):
    """OptiScaler and the FSR 4.1 DLLs: what is downloaded, which FSR 4.1 build is used."""

    def __init__(self, service: AssistantService, parent: "MainWindow") -> None:
        super().__init__(parent)
        self.service = service
        self.main = parent
        self.setWindowTitle(tr("dl_title"))
        self.setMinimumWidth(700)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(tr("dl_intro", folder=html.escape(
            str(service.components_root or components.data_dir()))), "subtitle"))
        for component in components.ALL:
            ready = service.component_ready(component)
            state = (f'<span style="color:{theme.token("ok")}">✓ {html.escape(tr("dl_ready"))}</span>' if ready
                     else f'<span style="color:{theme.token("muted")}">{html.escape(tr("dl_missing", size=mb(component.size)))}</span>')
            text = (f"<b>{html.escape(component_label(component))}</b> · {html.escape(component.version)}"
                    f" — {state}<br>"
                    f'<span style="color:#9aa3b2">{html.escape(tr("dl_desc_" + component.key.replace("-", "_")))}</span><br>'
                    f'<span style="color:#9aa3b2">{html.escape(tr("dl_licence", licence=component.licence))} · '
                    f'<a style="color:{theme.token("info")}" href="{component.project}">{html.escape(component.project.removeprefix("https://"))}</a></span>')
            layout.addWidget(_label(text, "card"))

        build = QGroupBox(tr("dl_build"))
        form = QFormLayout(build)
        self.build_box = QComboBox()
        main_gpu = service.main_gpu()
        auto = tr("dl_build_auto", build=tr("dl_build_" + (
            gpu.fsr4_pack(main_gpu) or "native")), gpu=main_gpu.label() if main_gpu else "?")
        for value, label in (("auto", auto), ("dgpu", tr("dl_build_dgpu")),
                             ("igpu", tr("dl_build_igpu")), ("native", tr("dl_build_native"))):
            self.build_box.addItem(label, value)
        self.build_box.setCurrentIndex(max(0, self.build_box.findData(service.fsr4_build_setting)))
        self.build_box.currentIndexChanged.connect(self._build_changed)
        form.addRow(tr("dl_build_label"), self.build_box)
        form.addRow(_label(tr("dl_build_hint"), "subtitle"))
        layout.addWidget(build)

        buttons = QHBoxLayout()
        self.get_btn = QPushButton(tr("dl_get"))
        self.get_btn.setObjectName("primary")
        self.get_btn.clicked.connect(self._download)
        buttons.addWidget(self.get_btn)
        remove = QPushButton(tr("dl_remove"))
        remove.setToolTip(tr("dl_remove_tip"))
        remove.clicked.connect(self._remove)
        remove.setEnabled(any(service.component_ready(c) for c in components.ALL))
        buttons.addWidget(remove)
        buttons.addStretch(1)
        close = QPushButton(tr("close"))
        close.clicked.connect(self.reject)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self._update_get()

    def _wanted(self) -> list:
        wanted = [components.OPTISCALER]
        if self.service.fsr4_build() != "native":
            wanted += self.service.needed_components("fsr4:exact")[1:]
        return [c for c in wanted if not self.service.component_ready(c)]

    def _update_get(self) -> None:
        wanted = self._wanted()
        self.get_btn.setEnabled(bool(wanted))
        self.get_btn.setText(tr("dl_get_size", size=mb(sum(c.size for c in wanted)))
                             if wanted else tr("dl_all_ready"))

    def _build_changed(self) -> None:
        self.service.fsr4_build_setting = self.build_box.currentData()
        self._update_get()
        self.main.refresh(rescan=False)

    def _download(self) -> None:
        wanted = self._wanted()
        self.accept()
        self.main.download(wanted)

    def _remove(self) -> None:
        if confirm(self, tr("dl_remove"), tr("dl_remove_q"), tr("dl_remove")):
            self.main.write_log(self.service.remove_downloads())
            self.accept()
            self.main.refresh(rescan=False)


class OptiNameDialog(_FitDialog):
    """Which file name OptiScaler gets next to the game's .exe."""

    def __init__(self, entry: GameEntry, current: Optional[str], automatic: tuple[str, str],
                 chosen: Optional[str], parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("on_title", name=entry.display_name))
        self.setMinimumWidth(600)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(tr("on_intro")))
        self.box = QComboBox()
        self.box.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        auto_name, reason = automatic
        self.box.addItem(tr("on_auto", name=auto_name, reason=tr("on_reason_" + reason)), None)
        for name in optiscaler.NAMES:
            note = "" if not needs_override(name) else "  " + tr("on_needs_launch")
            self.box.addItem(name + note, name)
        self.box.setCurrentIndex(max(0, self.box.findData(chosen)))
        layout.addWidget(self.box)
        self.setMinimumWidth(max(600, self.box.sizeHint().width() + 40))
        if current:
            layout.addWidget(_label(tr("on_current", name=html.escape(current)), "subtitle"))
        layout.addWidget(_label(tr("on_launch_hint"), "subtitle"))
        buttons = QDialogButtonBox()
        ok = buttons.addButton(tr("btn_save"), QDialogButtonBox.ButtonRole.AcceptRole)
        ok.setObjectName("primary")
        buttons.addButton(tr("cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @property
    def chosen(self) -> Optional[str]:
        return self.box.currentData()


class LossyDialog(QDialog):
    """WARNING.txt of the Lossy DLL, shown once before it is used the first time."""

    def __init__(self, text: str, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("lossy_title"))
        self.resize(820, 600)
        layout = QVBoxLayout(self)
        layout.addWidget(_label(tr("lossy_intro"), "banner"))
        view = QPlainTextEdit(text or tr("lossy_missing"))
        view.setReadOnly(True)
        layout.addWidget(view, 1)
        buttons = QDialogButtonBox()
        ok = buttons.addButton(tr("lossy_accept"), QDialogButtonBox.ButtonRole.AcceptRole)
        ok.setObjectName("primary")
        buttons.addButton(tr("cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


# ---- main window -----------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self, service: Optional[AssistantService] = None,
                 entries: Optional[list[GameEntry]] = None, *, autostart: bool = True,
                 expanded: Optional[set[int]] = None) -> None:
        super().__init__()
        self.service = service or AssistantService()
        self.pool = QThreadPool.globalInstance()
        self.entries: list[GameEntry] = list(entries or [])
        self.running: dict[int, RunningGame] = {}
        self.folder: Optional[HelixSRFolder] = None
        self.gpus: list[gpu.Gpu] = self.service.gpus()
        self.busy = False
        self._polling = False
        self._first_poll = True
        # app id -> {"since": monotonic seconds, "shown": bool} per game session
        self._sessions: dict[int, dict] = {}
        self._thumbs: dict[int, Optional[QPixmap]] = {}
        self._cards: dict[int, GameCard] = {}
        self._expanded: set[int] = set(expanded or ())
        self._steam = None

        self.setWindowTitle(window_title())
        self.resize(1480, 920)
        self.setMinimumSize(1100, 640)
        central = Backdrop()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(24, 16, 24, 14)
        root.setSpacing(14)
        root.addWidget(self._build_topbar())
        root.addWidget(self._build_toolbar())

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_host = QWidget()
        self.list_host.setObjectName("transparent")
        self.list_layout = QVBoxLayout(self.list_host)
        self.list_layout.setContentsMargins(0, 0, 6, 0)
        self.list_layout.setSpacing(12)
        self.empty_label = QLabel(tr("no_matches"))
        self.empty_label.setObjectName("empty")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        self.list_layout.addWidget(self.empty_label)
        self.list_layout.addStretch(1)
        self.scroll.setWidget(self.list_host)
        self.scroll.viewport().installEventFilter(self)
        root.addWidget(self.scroll, 1)
        root.addWidget(self._build_drawer())
        self.statusBar().hide()

        quit_action = QAction(self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        self.addAction(quit_action)

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(POLL_MS)
        self.poll_timer.timeout.connect(self.poll_runtime)

        hints = QApplication.instance().styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(lambda *_: self.apply_theme())

        self.write_log(tr("log_started", version=__version__))
        self._update_downloads_pill()
        if self.entries:
            self.populate()
        if not autostart:
            return
        if self.entries or self.service.has_scanned:
            QTimer.singleShot(0, lambda: self.refresh(rescan=False))
        else:
            self.write_log(tr("log_first_scan"))
            QTimer.singleShot(0, lambda: self.refresh(rescan=True))
        self.poll_timer.start()
        QTimer.singleShot(0, self.poll_runtime)
        QApplication.instance().aboutToQuit.connect(self._shutdown)

    # ---- chrome -------------------------------------------------------------------------------

    def _pill(self, text: str, slot: Optional[Callable] = None) -> QWidget:
        if slot is None:
            pill = QLabel(text)
        else:
            pill = QPushButton(text)
            pill.setCursor(Qt.CursorShape.PointingHandCursor)
            pill.clicked.connect(slot)
        pill.setObjectName("pill")
        pill.setFixedHeight(32)
        return pill

    def _build_topbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("topbar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        brand = QVBoxLayout()
        brand.setSpacing(0)
        brand.addWidget(Wordmark(tr("app_name")))
        self.tagline = QLabel(tr("subtitle") if tr("app_name") == "Scaler Assistant"
                              else f"Scaler Assistant · {tr('subtitle')}")
        self.tagline.setObjectName("tagline")
        brand.addWidget(self.tagline)
        row.addLayout(brand)
        row.addStretch(1)
        center = Qt.AlignmentFlag.AlignVCenter
        self.helixsr_pill = self._pill(tr("hx_pill_unknown"), self.show_helixsr)
        self.downloads_pill = self._pill("", self.show_downloads)
        self.gpu_pill = self._pill(self._gpu_text(), self.show_downloads)
        self.count_pill = self._pill("")
        for widget in (self.helixsr_pill, self.downloads_pill, self.gpu_pill, self.count_pill):
            row.addWidget(widget, 0, center)
        self.language_box = QComboBox()
        self.language_box.setToolTip(tr("language"))
        for code, native, _ in i18n.LANGUAGES:
            self.language_box.addItem(f"🌐  {native}", code)
        self.language_box.setCurrentIndex(i18n.CODES.index(i18n.current()))
        self.language_box.currentIndexChanged.connect(self.change_language)
        row.addWidget(self.language_box, 0, center)
        self.rescan_btn = QPushButton(tr("rescan"))
        self.rescan_btn.setObjectName("primary")
        self.rescan_btn.setToolTip(tr("rescan_tip"))
        self.rescan_btn.clicked.connect(lambda: self.refresh(rescan=True))
        row.addWidget(self.rescan_btn, 0, center)
        return bar

    def _build_toolbar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("toolbar")
        row = QHBoxLayout(bar)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(10)
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("search"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.apply_filter)
        row.addWidget(self.search, 1)
        self.filter = QComboBox()
        self.filter.addItems([tr("filter_supported"), tr("filter_installed"),
                              tr("filter_not_installed"), tr("filter_attention"),
                              tr("filter_running"), tr("filter_all")])
        self.filter.currentIndexChanged.connect(self.apply_filter)
        row.addWidget(self.filter)
        self.update_all_btn = QPushButton(tr("btn_update_all", count=0))
        self.update_all_btn.setObjectName("update")
        self.update_all_btn.setToolTip(tr("btn_update_all_tip"))
        self.update_all_btn.clicked.connect(self.update_all)
        self.update_all_btn.setVisible(False)
        row.addWidget(self.update_all_btn)
        self.theme_box = Segmented([("auto", tr("theme_auto")), ("dark", tr("theme_dark")),
                                    ("light", tr("theme_light"))])
        self.theme_box.setToolTip(tr("theme"))
        self.theme_box.set_value(self.service.theme)
        self.theme_box.changed.connect(self.change_theme)
        row.addWidget(self.theme_box, 0, Qt.AlignmentFlag.AlignVCenter)
        self.overlay_switch = Switch()
        self.overlay_switch.setChecked(self.service.overlay_enabled)
        self.overlay_switch.toggled.connect(
            lambda checked: setattr(self.service, "overlay_enabled", checked))
        self.overlay_switch.setToolTip(tr("osd_toggle_tip"))
        overlay_label = QLabel(tr("osd_toggle"))
        overlay_label.setToolTip(tr("osd_toggle_tip"))
        row.addSpacing(6)
        row.addWidget(self.overlay_switch, 0, Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(overlay_label)
        return bar

    def _build_drawer(self) -> QWidget:
        drawer = QFrame()
        drawer.setObjectName("drawer")
        layout = QVBoxLayout(drawer)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(6)
        head = QHBoxLayout()
        self.log_toggle = QPushButton(f"▸  {tr('activity')}")
        self.log_toggle.setObjectName("link")
        self.log_toggle.setCheckable(True)
        self.log_toggle.toggled.connect(self._toggle_log)
        head.addWidget(self.log_toggle)
        self.last_line = QLabel("")
        self.last_line.setObjectName("muted")
        head.addWidget(self.last_line, 1)
        footer = QLabel(f"Scaler Assistant v{__version__}")
        footer.setObjectName("footer")
        head.addWidget(footer)
        layout.addLayout(head)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        self.log.setFixedHeight(150)
        self.log.hide()
        layout.addWidget(self.log)
        return drawer

    def _toggle_log(self, shown: bool) -> None:
        self.log.setVisible(shown)
        self.log_toggle.setText(f"{'▾' if shown else '▸'}  {tr('activity')}")
        self.last_line.setVisible(not shown)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._reflow()

    def eventFilter(self, watched, event) -> bool:
        # The list viewport settles its width after the window's own resize event.
        if watched is self.scroll.viewport() and event.type() == QEvent.Type.Resize:
            self._reflow()
        return super().eventFilter(watched, event)

    def _reflow(self) -> None:
        """Hide the tagline and move card buttons under the details as the window narrows."""
        self.tagline.setVisible(self.width() >= 1420)
        width = self.scroll.viewport().width() - 6
        for card in self._cards.values():
            card.set_compact(card.wide_width() > width)

    def _shutdown(self) -> None:
        """Let background tasks finish before Qt and Python tear down."""
        self.poll_timer.stop()
        self.pool.waitForDone(15000)

    # ---- theme & language -----------------------------------------------------------------------

    def change_theme(self, choice: str) -> None:
        self.service.theme = choice
        self.apply_theme()

    def apply_theme(self) -> None:
        theme.set_mode(theme.resolve(self.service.theme))
        QApplication.instance().setStyleSheet(theme.stylesheet())
        self.centralWidget().update()
        self.update_runtime()
        for card in self._cards.values():
            card.update()

    def change_language(self, index: int) -> None:
        code = self.language_box.itemData(index)
        if code == i18n.current():
            return
        self.service.language = code
        i18n.set_language(code)
        app = QApplication.instance()
        install_translations(app)
        app.setApplicationDisplayName(tr("app_name"))
        replacement = MainWindow(self.service, self.entries, expanded=self._expanded)
        replacement.setGeometry(self.geometry())
        if self.isMaximized():
            replacement.showMaximized()
        else:
            replacement.show()
        app.main_window = replacement
        self.poll_timer.stop()
        self.close()
        self.deleteLater()

    # ---- helpers ------------------------------------------------------------------------------

    def write_log(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        lines = str(text).splitlines() or [""]
        for line in lines:
            self.log.appendPlainText(f"[{stamp}] {line}")
        self.last_line.setText(lines[0] if len(lines) == 1 else f"{lines[0]} …")

    def set_busy(self, busy: bool, message: str = "") -> None:
        self.busy = busy
        for widget in (self.rescan_btn, self.language_box, self.list_host, self.update_all_btn,
                       self.helixsr_pill, self.downloads_pill, self.gpu_pill):
            widget.setEnabled(not busy)
        if busy:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            if message:
                self.last_line.setText(message)
        else:
            QApplication.restoreOverrideCursor()

    def error_box(self, message: str) -> None:
        box = QMessageBox(QMessageBox.Icon.Critical, window_title(), message, parent=self)
        box.addButton(tr("ok"), QMessageBox.ButtonRole.AcceptRole)
        box.exec()

    def run_task(self, message: str, fn: Callable, *args,
                 on_done: Callable[[object], None], on_error: Optional[Callable] = None,
                 on_progress: Optional[Callable[[object], None]] = None) -> None:
        self.set_busy(True, message)
        task = _Task(fn, *args)
        if on_progress is not None:
            task.args = (*args, task.signals.progress.emit)
            task.signals.progress.connect(on_progress)

        def done(result):
            self.set_busy(False)
            on_done(result)

        def failed(error):
            self.set_busy(False)
            if on_error is not None and on_error(error):
                return
            self.write_log(tr("log_error", error=error))
            self.error_box(str(error))

        task.signals.done.connect(done)
        task.signals.failed.connect(failed)
        self.pool.start(task)

    def _gpu_text(self) -> str:
        main = self.service.main_gpu()
        return tr("gpu_pill", gpu=main.label()) if main else tr("gpu_unknown")

    def _gpu_tooltip(self) -> str:
        lines = [g.label() + (f" — {g.name}" if g.name else "") for g in self.gpus]
        build = self.service.fsr4_build()
        lines.append(tr("gpu_fsr4", build=tr("dl_build_" + build)))
        amd = [g for g in self.gpus if g.vendor == "AMD"]
        if not amd:
            lines.append(tr("gpu_not_amd"))
        elif all(g.supported is False for g in amd):
            lines.append(tr("gpu_too_old"))
        if any(g.family == "Vega" for g in amd):
            lines.append(tr("gpu_vega"))
        if any(g.rdna3_or_newer for g in amd):
            lines.append(tr("gpu_rdna3"))
        lines.append(tr("gpu_click"))
        return "\n".join(lines)

    @property
    def rdna3(self) -> bool:
        return any(g.rdna3_or_newer for g in self.gpus)

    def _update_downloads_pill(self) -> None:
        opti = self.service.component_ready(components.OPTISCALER)
        fsr4 = (self.service.fsr4_build() == "native"
                or all(self.service.component_ready(c)
                       for c in self.service.needed_components("fsr4:exact")))
        if opti and fsr4:
            text = tr("dl_pill_ready", version=components.OPTISCALER.version)
        elif opti:
            text = tr("dl_pill_partly")
        else:
            text = tr("dl_pill_none")
        self.downloads_pill.setText(text)
        self.downloads_pill.setToolTip(tr("dl_pill_tip"))
        self.gpu_pill.setText(self._gpu_text())
        self.gpu_pill.setToolTip(self._gpu_tooltip())

    # ---- data -----------------------------------------------------------------

    def refresh(self, rescan: bool) -> None:
        if self.busy:
            return

        def work():
            entries = self.service.scan(rescan_library=rescan)
            folder = self.service.helixsr()
            newer = self.service.newer_helixsr() if rescan else None
            return entries, folder, newer

        def done(result):
            entries, folder, newer = result
            self.entries = entries
            self._set_folder(folder)
            self._update_downloads_pill()
            if rescan:
                self.write_log(tr("log_scan_done", count=len(entries),
                                  supported=sum(1 for e in entries if e.supported)))
            self.populate()
            if newer is not None:
                self._offer_newer(newer)

        self.run_task(tr("busy_scan") if rescan else tr("busy_load"), work, on_done=done)

    def _set_folder(self, folder: Optional[HelixSRFolder]) -> None:
        self.folder = folder
        minimum = ".".join(map(str, MIN_VERSION))
        if folder is None:
            text, tip = tr("hx_pill_none"), tr("hx_pill_choose")
        elif folder.ready:
            text = tr("hx_pill_ready", version=folder.version)
            tip = f"{folder.path}\n{tr('hx_pill_choose')}"
        else:
            problem = folder.problem or "hx_not_helixsr"
            text = tr("hx_pill_problem", version=folder.version or "?")
            message = tr(problem, path=folder.path, version=folder.version or "?", minimum=minimum)
            tip = f"{message}\n{tr('hx_pill_choose')}"
        self.helixsr_pill.setText(text)
        self.helixsr_pill.setToolTip(tip)

    def _offer_newer(self, newer: HelixSRFolder) -> None:
        current = self.folder.version if self.folder and self.folder.version else "—"
        if confirm(self, window_title(),
                   tr("newer_found", version=html.escape(newer.version or "?"), current=current,
                      path=html.escape(str(newer.path))),
                   tr("btn_use_newer"), QMessageBox.Icon.Question):
            self._apply_folder(str(newer.path))

    def show_helixsr(self) -> None:
        HelixSRDialog(self.folder, self).exec()

    def show_downloads(self) -> None:
        DownloadsDialog(self.service, self).exec()

    def choose_folder(self) -> None:
        start = str(self.folder.path) if self.folder else str(Path.home())
        path = QFileDialog.getExistingDirectory(self, tr("choose_folder_title"), start)
        if path:
            self._apply_folder(path)

    def _apply_folder(self, path: str) -> None:
        try:
            folder = self.service.set_helixsr_folder(path)
        except FileNotFoundError as error:
            self.write_log(tr("log_error", error=error))
            self.error_box(str(error))
            return
        self.write_log(tr("log_folder", path=folder.path, version=folder.version or "?"))
        if folder.problem:
            self.write_log(tr(folder.problem, path=folder.path, version=folder.version or "?",
                              minimum=".".join(map(str, MIN_VERSION))))
        self.refresh(rescan=False)

    def run_setup(self) -> None:
        if self.folder is None:
            return
        if run_setup_in_terminal(self.folder.path):
            self.write_log(tr("log_setup_started", path=self.folder.path))
        else:
            self.error_box(tr("btn_run_setup_none"))

    def poll_runtime(self) -> None:
        if self._polling:
            return
        self._polling = True
        watch = {e.app_id: e.watch() for e in self.entries if e.installed}
        recheck = self.folder is not None and not self.folder.ready and not self.busy

        def work():
            folder = self.service.helixsr() if recheck else None
            return detect_running(watch), folder

        task = _Task(work)

        def done(result):
            self._polling = False
            self.running, folder = result
            if folder is not None and folder.ready and not self.busy:
                # helixsr-setup has just built the network (or a release was put back)
                self.write_log(tr("log_ready", version=folder.version, path=folder.path))
                self.refresh(rescan=False)
            self._track_sessions()
            self.update_runtime()

        def failed(_error):
            self._polling = False

        task.signals.done.connect(done)
        task.signals.failed.connect(failed)
        self.pool.start(task)

    def _wave32_problem(self, entry: Optional[GameEntry], game: RunningGame) -> bool:
        return status.wave32_problem(entry, game, self.rdna3)

    def _track_sessions(self) -> None:
        """Show the overlay once per game launch, when the upscaler's state is known."""
        now = time.monotonic()
        for app_id in list(self._sessions):
            if app_id not in self.running:
                del self._sessions[app_id]  # game exited: the next launch is a new session
        entries = {e.app_id: e for e in self.entries}
        for app_id, game in self.running.items():
            # Games already running when the assistant opened are not "starting".
            session = self._sessions.setdefault(
                app_id, {"since": now, "shown": self._first_poll})
            entry = entries.get(app_id)
            if session["shown"] or not self.overlay_switch.isChecked() or not (entry and entry.installed):
                continue
            late = now - session["since"] > OVERLAY_NOT_LOADED_AFTER
            if game.helixsr_loaded or late:
                session["shown"] = True
                self._show_overlay(entry, game)
                if self._wave32_problem(entry, game):
                    self.write_log(tr("log_wave32_hint", name=entry.display_name))
        self._first_poll = False

    def _describe(self, entry: GameEntry, game: RunningGame) -> tuple[str, str, list[tuple[str, str, bool]], list[str]]:
        """(headline, tone, [(label, detail, ok)], notes) for a running game."""
        return status.describe(entry, game, self.rdna3)

    def _show_overlay(self, entry: GameEntry, game: RunningGame) -> None:
        headline, color, lines, notes = self._describe(entry, game)
        try:
            overlay.show({
                "kicker": "Scaler Assistant",
                "title": entry.display_name,
                "headline": headline,
                "color": OVERLAY_COLORS[color],
                "lines": [{"label": label, "detail": detail, "active": ok}
                          for label, detail, ok in lines],
                "notes": notes,
                "seconds": OVERLAY_SECONDS,
            })
        except OSError as error:
            self.write_log(tr("log_error", error=error))

    def _thumb(self, app_id: int) -> Optional[QPixmap]:
        if app_id not in self._thumbs:
            pixmap = None
            try:
                if self._steam is None:
                    self._steam = self.service.steam()
                path = self._steam.header_image(app_id)
            except FileNotFoundError:
                path = None
            if path:
                loaded = QPixmap(str(path))
                if not loaded.isNull():
                    ratio = self.devicePixelRatioF()
                    w, h = int(THUMB_W * ratio), int(THUMB_H * ratio)
                    scaled = loaded.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                           Qt.TransformationMode.SmoothTransformation)
                    scaled = scaled.copy((scaled.width() - w) // 2, (scaled.height() - h) // 2, w, h)
                    scaled.setDevicePixelRatio(ratio)
                    pixmap = theme.rounded(scaled, 10)
            self._thumbs[app_id] = pixmap
        return self._thumbs[app_id]

    def populate(self) -> None:
        for card in self._cards.values():
            self.list_layout.removeWidget(card)
            card.deleteLater()
        self._cards.clear()
        collator = QCollator(QLocale(i18n.qt_suffix()))
        collator.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        collator.setNumericMode(True)
        # Games that can use an upscaler first, then the rest.
        self.entries.sort(key=cmp_to_key(lambda a, b: (b.supported - a.supported) or
                                         collator.compare(a.display_name, b.display_name)))
        actions = {"launch": self.launch, "choose": self.choose, "uninstall": self.uninstall,
                   "menu": self._choice_menu, "settings": self.edit_settings,
                   "log": self.show_log, "folder": self.open_folder,
                   "opti_name": self.choose_opti_name}
        version = self.folder.version if self.folder else None
        installed = outdated = 0
        for index, entry in enumerate(self.entries):
            card = GameCard(entry, self._thumb(entry.app_id), actions, version, self.list_host)
            card.expand_toggled.connect(self._on_expand)
            self.list_layout.insertWidget(index, card)
            self._cards[entry.app_id] = card
            installed += entry.installed
            outdated += entry.installed and entry.outdated
            if entry.app_id in self._expanded:
                card.set_expanded(True)
        self.count_pill.setText(tr("count", installed=installed,
                                   supported=sum(1 for e in self.entries if e.supported)))
        self.update_all_btn.setText(tr("btn_update_all", count=outdated))
        self.update_all_btn.setVisible(outdated > 0)
        self.update_runtime()

    def _on_expand(self, app_id: int, expanded: bool) -> None:
        if expanded:
            self._expanded.add(app_id)
        else:
            self._expanded.discard(app_id)

    def _choice_menu(self, entry: GameEntry, parent: QWidget) -> QMenu:
        """DLSS 3.7 (HelixSR) ▸ its ways, FSR 4.1, FSR 3 — the current one ticked, ways this GPU
        can't use greyed out, the one recommended for this PC marked."""
        menu = QMenu(parent)
        menu.setToolTipsVisible(True)
        current = entry.status.choice

        def add(target: QMenu, choice: str, text: str) -> None:
            if choice == entry.recommended:
                text = f"{text}   {tr('rec_suffix')}"
            action = target.addAction(text)
            action.setCheckable(True)
            action.setChecked(choice == current)
            if choice == entry.recommended:
                action.setToolTip(tr("rec_lossy"))
            action.triggered.connect(lambda _, e=entry, c=choice: self.choose(e, c))

        helixsr_ways = [w for w in entry.ways]
        if helixsr_ways:
            sub = menu.addMenu(tr("menu_helixsr"))
            sub.setToolTipsVisible(True)
            for way in helixsr_ways:
                choice = f"helixsr:{way}"
                reason = entry.blocked.get(choice)
                if reason:
                    action = sub.addAction(f"{tr('menu_install_' + way)}   ({tr(reason + '_short')})")
                    action.setEnabled(False)
                    action.setToolTip(tr(reason))
                else:
                    add(sub, choice, tr("menu_install_" + way))
            if upscaler_of(current) == "helixsr":
                sub.setTitle("✓ " + tr("menu_helixsr"))
        elif entry.layout.optiscaler_possible and not entry.layout.helixsr_possible:
            action = menu.addAction(tr("menu_helixsr_api",
                                       api=API_LABELS.get(entry.layout.api, "?")))
            action.setEnabled(False)
        fsr = [c for c in entry.choices if upscaler_of(c) in ("fsr4", "fsr3")]
        if fsr:
            menu.addSeparator()
            for choice in fsr:
                add(menu, choice, tr("menu_" + choice.replace(":", "_")))
        return menu

    def _runtime_html(self, entry: Optional[GameEntry], game: RunningGame) -> tuple[str, str]:
        """(rich text, tooltip) for a running game's card."""
        tip = [tr("rt_pids", pids=", ".join(map(str, game.pids)))]
        if entry is None or not entry.installed:
            muted = theme.token("muted")
            return (f'<span style="color:{muted}">{html.escape(tr("rt_running_without"))}</span>',
                    tip[0])
        headline, tone, lines, notes = self._describe(entry, game)
        if game.log:
            tip.append(str(game.log.path))
            if game.log.wave_line:
                tip.append(game.log.wave_line)
        return live_html(headline, tone, lines, notes), "\n".join(tip)

    def update_runtime(self) -> None:
        entries = {e.app_id: e for e in self.entries}
        for app_id, card in self._cards.items():
            game = self.running.get(app_id)
            if game is None:
                card.set_runtime(None)
                continue
            text, tip = self._runtime_html(entries.get(app_id), game)
            card.set_runtime(text, running=True, tip=tip)
        self.apply_filter()
        self._reflow()

    def apply_filter(self) -> None:
        query = self.search.text().strip().casefold()
        mode = self.filter.currentIndex()
        shown = 0
        for entry in self.entries:
            card = self._cards.get(entry.app_id)
            if card is None:
                continue
            visible = not query or entry.matches(query)
            if mode == FILTER_SUPPORTED:
                visible &= entry.supported
            elif mode == FILTER_INSTALLED:
                visible &= entry.installed
            elif mode == FILTER_NOT_INSTALLED:
                visible &= bool(entry.choices) and not entry.installed
            elif mode == FILTER_ATTENTION:
                visible &= entry.needs_attention
            elif mode == FILTER_RUNNING:
                visible &= entry.app_id in self.running
            card.setVisible(visible)
            shown += visible
        self.empty_label.setVisible(bool(self._cards) and shown == 0)

    # ---- actions ------------------------------------------------------------

    def launch(self, entry: GameEntry) -> None:
        self.write_log(tr("log_launch", name=entry.display_name))
        try:
            self.service.launch_game(entry.app_id)
        except RuntimeError as error:
            self.write_log(tr("log_error", error=error))
            self.error_box(str(error))
            return
        card = self._cards.get(entry.app_id)
        if card is not None:
            card.launch_btn.setEnabled(False)  # re-enabled by polling if the game never starts
        QTimer.singleShot(1500, self.poll_runtime)

    def _warnings_ok(self, entry: GameEntry, choice: str) -> bool:
        name = html.escape(entry.display_name)
        if entry.status.choice == choice:
            return True   # update or repair of what is already there
        if choice == "helixsr:dlss" and not confirm(self, tr("warn_dlss_title"),
                                                    tr("warn_dlss", name=name),
                                                    tr("btn_install_anyway")):
            return False
        if entry.layout.anti_cheat and not entry.installed and not confirm(
                self, tr("warn_ac_title"),
                tr("warn_ac", name=name, ac=html.escape(", ".join(entry.layout.anti_cheat))),
                tr("btn_install_anyway")):
            return False
        return True

    def choose(self, entry: GameEntry, choice: str) -> None:
        """Install, switch to, update or repair a choice: ask for whatever it needs first."""
        if not self._warnings_ok(entry, choice):
            self.write_log(tr("log_cancelled"))
            return
        self.run_task(tr("busy_check", name=entry.display_name), self.service.plan,
                      entry.app_id, choice, on_done=lambda plan: self._continue(entry, plan))

    def _continue(self, entry: GameEntry, plan: ChoicePlan) -> None:
        if plan.needs_helixsr:
            self.write_log(tr("log_needs_helixsr"))
            self.show_helixsr()
            return
        if plan.downloads:
            if not self._confirm_download(plan.downloads, choice_label(plan.choice)):
                self.write_log(tr("log_cancelled"))
                return
            self.download(plan.downloads, then=lambda: self.choose(entry, plan.choice))
            return
        if plan.lossy_warning:
            dialog = LossyDialog(self.service.lossy_warning_text(), self)
            if dialog.exec() != QDialog.DialogCode.Accepted:
                self.write_log(tr("log_cancelled"))
                return
            self.service.accept_lossy()
        if entry.status.choice == plan.choice:
            key = "log_update"
        elif entry.status.installed:
            key = "log_switch"
        else:
            key = "log_install"
        self.write_log(tr(key, name=entry.display_name, choice=choice_label(plan.choice)))
        if plan.launch_change:
            self.write_log(tr("log_launch_change", options=plan.launch_after or tr("empty")))
        self._run_action(tr("busy_install", name=entry.display_name),
                         self.service.apply, entry.app_id, plan.choice)

    def _confirm_download(self, wanted: list, what: str = "") -> bool:
        what = what or window_title()
        items = "".join(
            f"<li><b>{html.escape(component_label(c))}</b> {html.escape(c.version)} "
            f"({mb(c.size)}) — {html.escape(c.licence)}</li>" for c in wanted)
        return confirm(self, tr("dl_title"), tr("dl_confirm", what=html.escape(what), items=items),
                       tr("dl_confirm_ok"), QMessageBox.Icon.Question)

    def download(self, wanted: list, then: Optional[Callable[[], None]] = None) -> None:
        if not wanted:
            return

        def progress(value):
            component, done, total = value
            self.last_line.setText(tr("busy_download_progress", name=component_label(component),
                                      done=f"{done / 1_000_000:.0f}",
                                      total=f"{total / 1_000_000:.0f}"))

        def done(result):
            self.write_log(result)
            self._update_downloads_pill()
            if then is not None:
                then()
            else:
                self.refresh(rescan=False)

        self.write_log(tr("log_download", names=", ".join(component_label(c) for c in wanted)))
        self.run_task(tr("busy_download"),
                      lambda emit: self.service.download(wanted, lambda c, d, t: emit((c, d, t))),
                      on_done=done, on_progress=progress)

    def uninstall(self, entry: GameEntry) -> None:
        has_settings = any((d / settings.INI).is_file() for d in entry.status.ini_dirs)
        dialog = RemoveDialog(entry, has_settings, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        remove_settings = dialog.remove_settings.isChecked()
        self.write_log(tr("log_remove", name=entry.display_name,
                          choice=choice_label(entry.status.choice)))
        self._run_action(tr("busy_remove", name=entry.display_name),
                         self.service.uninstall, entry.app_id, remove_settings)

    def update_all(self) -> None:
        missing = self.service.missing_for_update()
        if missing:
            what = ", ".join(sorted({choice_label(e.status.choice)
                                     for e in self.service.outdated_entries()}))
            if not self._confirm_download(missing, what):
                self.write_log(tr("log_cancelled"))
                return
            self.download(missing, then=self.update_all)
            return
        self.write_log(tr("log_update_all"))
        self._run_action(tr("busy_update_all"), self.service.update_all)

    def choose_opti_name(self, entry: GameEntry) -> None:
        try:
            automatic = self.service.opti_name_auto(entry.app_id)
        except (LookupError, OSError) as error:
            self.error_box(str(error))
            return
        chosen = self.service.opti_name_setting(entry.app_id)
        dialog = OptiNameDialog(entry, entry.status.opti_name, automatic, chosen, self)
        if dialog.exec() != QDialog.DialogCode.Accepted or dialog.chosen == chosen:
            return
        self.service.set_opti_name(entry.app_id, dialog.chosen)
        self.write_log(tr("log_opti_name", name=entry.display_name,
                          file=dialog.chosen or tr("on_auto_short", name=automatic[0])))
        wanted = dialog.chosen or automatic[0]
        if entry.status.opti_name and wanted != entry.status.opti_name:
            self.choose(entry, str(entry.status.choice))   # move OptiScaler to the new name

    def edit_settings(self, entry: GameEntry) -> None:
        try:
            values = self.service.read_settings(entry.app_id)
        except LookupError as error:
            self.error_box(str(error))
            return
        dialog = SettingsDialog(entry, values, self.folder, self.gpus, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._run_action(tr("busy_settings"), self.service.write_settings, entry.app_id,
                         dialog.result_values)

    def fix_wave(self, entry: GameEntry) -> None:
        self._run_action(tr("busy_settings"), self.service.fix_wave_size, entry.app_id)

    def show_log(self, entry: GameEntry) -> None:
        try:
            path, text = self.service.log_text(entry.app_id)
        except LookupError as error:
            self.error_box(str(error))
            return
        from .hxlog import summarize
        summary = summarize(path) if path and entry.status.upscaler == "helixsr" else None
        can_fix = bool(summary and summary.wave == 32 and self.rdna3
                       and entry.status.route == "optiscaler")
        LogDialog(entry, path, text, can_fix, self).exec()

    def open_folder(self, entry: GameEntry) -> None:
        try:
            AssistantService.open_path(self.service.game_folder(entry.app_id))
        except (LookupError, OSError) as error:
            self.error_box(str(error))

    def _run_action(self, message: str, fn: Callable, *args) -> None:
        def done(result):
            self.write_log(result)
            self.refresh(rescan=False)

        def on_error(error):
            if isinstance(error, GameRunningError):
                self.write_log(str(error))
                self.error_box(str(error))
                return True
            if isinstance(error, SteamMustCloseError):
                self._offer_steam_restart(message, fn, *args)
                return True
            if isinstance(error, NeedsHelixSRError):
                self.write_log(str(error))
                self.show_helixsr()
                return True
            if isinstance(error, NeedsDownloadError):
                if self._confirm_download(error.missing):
                    self.download(error.missing, then=lambda: self._run_action(message, fn, *args))
                return True
            return False

        self.run_task(message, fn, *args, on_done=done, on_error=on_error)

    def _offer_steam_restart(self, message: str, fn: Callable, *args) -> None:
        """Steam keeps launch options in memory and writes them back when it exits, so
        localconfig.vdf can only be changed while Steam is closed (MAKO Assistant's way)."""
        box = QMessageBox(QMessageBox.Icon.Question, window_title(), tr("steam_close_q"),
                          parent=self)
        confirm_btn = box.addButton(tr("steam_close_confirm"), QMessageBox.ButtonRole.AcceptRole)
        box.addButton(tr("cancel"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is not confirm_btn:
            self.write_log(tr("log_steam_cancel"))
            return

        def work():
            if not self.service.shutdown_steam():
                raise RuntimeError(tr("err_steam_timeout"))
            try:
                result = fn(*args)
            finally:
                self.service.start_steam()  # reopen Steam even if applying failed
            return result + "\n" + tr("log_steam_restarted")

        def done(result):
            self.write_log(result)
            self.refresh(rescan=False)

        self.write_log(tr("svc_closing_steam"))
        self.run_task(tr("busy_steam_apply"), work, on_done=done)


def install_translations(app: QApplication) -> None:
    """Translate Qt's own texts (context menus, standard dialogs) to the UI language."""
    for translator in getattr(app, "_scaler_translators", []):
        app.removeTranslator(translator)
    app._scaler_translators = []
    suffix = i18n.qt_suffix()
    QLocale.setDefault(QLocale(suffix))
    directories = (
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath),
        "/usr/share/qt6/translations",
    )
    for name in (f"qtbase_{suffix}", f"qt_{suffix}"):
        for directory in directories:
            translator = QTranslator(app)
            if translator.load(name, directory):
                app.installTranslator(translator)
                app._scaler_translators.append(translator)
                break


def prepare_app(app: QApplication, service: AssistantService) -> None:
    i18n.set_language(service.language)
    install_translations(app)
    app.setApplicationName("Scaler Assistant")
    app.setApplicationDisplayName(tr("app_name"))
    app.setDesktopFileName("scaler-assistant")
    app.setStyle("Fusion")
    theme.load_fonts()
    theme.set_mode(theme.resolve(service.theme))
    app.setStyleSheet(theme.stylesheet())


def main() -> int:
    app = QApplication(sys.argv)
    service = AssistantService()
    prepare_app(app, service)
    app.main_window = MainWindow(service)
    app.main_window.show()
    return app.exec()
