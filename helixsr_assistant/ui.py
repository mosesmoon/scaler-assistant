"""PyQt6 user interface for HelixSR Assistant (HelixSR 助手)."""

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
    QCollator, QLibraryInfo, QLocale, QObject, QRunnable, QSize, Qt, QThreadPool, QTimer,
    QTranslator, QUrl, pyqtSignal,
)
from PyQt6.QtGui import QAction, QColor, QDesktopServices, QGuiApplication, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QMenu, QMessageBox, QPlainTextEdit, QPushButton, QSplitter,
    QTableWidget, QTableWidgetItem, QToolButton, QVBoxLayout, QWidget,
)

from . import __version__, gpu, i18n, overlay, settings
from .helixsr import HelixSRFolder, MIN_VERSION
from .i18n import tr
from .runtime import RunningGame, detect_running
from .service import AssistantService, GameEntry, GameRunningError

THUMB_W, THUMB_H = 138, 64
ROW_H = THUMB_H + 30
POLL_MS = 3000
OVERLAY_SECONDS = 10
# HelixSR installed, game running, DLL still not loaded after this long: say so.
OVERLAY_NOT_LOADED_AFTER = 90
RELEASES_URL = "https://github.com/lonewolf0622/HelixSR/releases"

COL_GAME, COL_STATUS, COL_UPSCALERS, COL_RUNTIME, COL_ACTIONS = range(5)
(FILTER_SUPPORTED, FILTER_INSTALLED, FILTER_NOT_INSTALLED, FILTER_ATTENTION, FILTER_RUNNING,
 FILTER_ALL) = range(6)

GREEN, YELLOW, ORANGE, BLUE, GREY, DIM = ("#4cd384", "#f2c14e", "#ff9a5c", "#8fb3ff",
                                          "#8b93a1", "#6b7380")

STYLE = """
QMainWindow, QDialog { background: #15171c; }
QWidget { color: #e6e8ee; font-size: 14px; }
QLabel#title { font-size: 22px; font-weight: 700; }
QLabel#subtitle { color: #9aa3b2; }
QLabel[class="pill"], QPushButton[class="pill"] { border-radius: 10px; padding: 3px 10px;
    background: #252a33; color: #c9d1dc; border: none; }
QPushButton[class="pill"]:hover { background: #2f3542; }
QLabel#banner { background: #3a3020; border: 1px solid #7a6330; border-radius: 8px; padding: 10px 12px;
    color: #f5dfa8; }
QLineEdit, QComboBox, QDoubleSpinBox { background: #1f232b; border: 1px solid #323846; border-radius: 6px;
    padding: 6px 8px; }
QPushButton, QToolButton { background: #2a303b; border: 1px solid #3a4150; border-radius: 6px;
    padding: 7px 12px; }
QPushButton:hover, QToolButton:hover { background: #343b48; }
QPushButton:disabled, QToolButton:disabled { color: #6b7380; background: #1f232b; }
QPushButton#primary { background: #2f6fed; border-color: #2f6fed; color: white; font-weight: 600; }
QPushButton#primary:hover { background: #4682f5; }
QPushButton#install, QToolButton#install { background: #1f8a4c; border-color: #1f8a4c; color: white;
    font-weight: 600; }
QPushButton#install:hover, QToolButton#install:hover { background: #27a35b; }
QPushButton#update { background: #6b5317; border-color: #b08a2a; color: #ffe7a8; font-weight: 600; }
QPushButton#update:hover { background: #7d621d; }
QPushButton#remove { background: #3a2226; border-color: #8a3340; color: #ffb3bd; }
QPushButton#remove:hover { background: #4d2a30; }
QPushButton#launch { background: #23324d; border-color: #3b5b96; color: #cfe0ff; font-weight: 600; }
QPushButton#launch:hover { background: #2c3f61; }
QPushButton#launch:disabled { background: #1c3a2a; border-color: #2c6b48; color: #7fe0a6; }
QToolButton::menu-button { border-left: 1px solid rgba(255, 255, 255, 60); width: 18px; }
QMenu { background: #1f232b; border: 1px solid #3a4150; padding: 4px; }
QMenu::item { padding: 6px 18px; border-radius: 4px; }
QMenu::item:selected { background: #2f3a52; }
QMenu::item:disabled { color: #6b7380; }
QTableWidget { background: #1a1d23; border: 1px solid #2a2f3a; border-radius: 8px;
    gridline-color: transparent; alternate-background-color: #1d2128; }
QTableWidget::item { padding: 4px; }
QTableWidget::item:selected { background: #26324a; }
QHeaderView::section { background: #1f232b; color: #9aa3b2; border: none; padding: 6px; }
QPlainTextEdit { background: #111318; border: 1px solid #2a2f3a; border-radius: 8px;
    font-family: monospace; font-size: 12px; color: #b8c0cc; }
QGroupBox { border: 1px solid #2a2f3a; border-radius: 8px; margin-top: 14px; padding: 10px 10px 6px; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; color: #9aa3b2; }
QCheckBox { spacing: 8px; }
"""


def window_title() -> str:
    name = tr("app_name")
    return name if name == "HelixSR Assistant" else f"{name} (HelixSR Assistant)"


def way_label(route: str) -> str:
    return tr("way_" + route)


class _Signals(QObject):
    done = pyqtSignal(object)
    failed = pyqtSignal(object)


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


class RemoveDialog(QDialog):
    def __init__(self, entry: GameEntry, has_settings: bool, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("remove_title"))
        self.setMinimumWidth(500)
        layout = QVBoxLayout(self)
        text = QLabel(tr("remove_body", name=html.escape(entry.display_name),
                         way=html.escape(way_label(entry.status.route or "direct"))))
        text.setTextFormat(Qt.TextFormat.RichText)
        text.setWordWrap(True)
        layout.addWidget(text)
        self.remove_settings = QCheckBox(tr("remove_settings"))
        if not has_settings:
            self.remove_settings.setEnabled(False)
            self.remove_settings.setToolTip(tr("remove_no_settings"))
        layout.addWidget(self.remove_settings)
        buttons = QDialogButtonBox()
        ok = buttons.addButton(tr("btn_remove"), QDialogButtonBox.ButtonRole.AcceptRole)
        ok.setObjectName("remove")
        buttons.addButton(tr("cancel"), QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


class SettingsDialog(QDialog):
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
        intro = QLabel(tr("set_intro"))
        intro.setWordWrap(True)
        intro.setObjectName("subtitle")
        layout.addWidget(intro)

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
        hint = QLabel(tr("set_sharp_hint"))
        hint.setWordWrap(True)
        hint.setObjectName("subtitle")
        form.addRow(hint)
        layout.addWidget(sharp)

        upscaling = QGroupBox(tr("set_upscaling"))
        form = QFormLayout(upscaling)
        form.addRow(tr("set_int8"), combo("Int8", [
            (tr("set_default_auto"), None), (tr("set_auto"), "auto"), (tr("set_on"), "on"),
            (tr("set_off"), "off")]))
        form.addRow(tr("set_filter"), combo("UpscaleFilter", [
            (tr("set_default_lanczos"), None), ("Lanczos", "lanczos"), (tr("set_easu"), "easu")]))
        hint = QLabel(tr("set_upscaling_hint") + ("" if newer else "<br><b>" + tr(
            "set_needs_190", version=folder.version if folder else "?") + "</b>"))
        hint.setTextFormat(Qt.TextFormat.RichText)
        hint.setWordWrap(True)
        hint.setObjectName("subtitle")
        form.addRow(hint)
        upscaling.setEnabled(newer or bool(values.get("Int8") or values.get("UpscaleFilter")))
        layout.addWidget(upscaling)

        compat = QGroupBox(tr("set_compat"))
        form = QFormLayout(compat)
        form.addRow(tr("set_wave"), combo("WaveSize", [
            (tr("set_default"), None), ("64", "64"), ("32", "32")]))
        rdna3 = any(g.rdna3_or_newer for g in gpus)
        hint = QLabel(tr("set_wave_hint") + ("<br>" + tr("set_wave_hint_rdna3")
                                             if rdna3 and entry.status.route == "optiscaler" else ""))
        hint.setTextFormat(Qt.TextFormat.RichText)
        hint.setWordWrap(True)
        hint.setObjectName("subtitle")
        form.addRow(hint)
        layout.addWidget(compat)

        where = QLabel(tr("set_where", paths="<br>".join(
            html.escape(str(d / settings.INI)) for d in entry.status.ini_dirs)))
        where.setTextFormat(Qt.TextFormat.RichText)
        where.setWordWrap(True)
        where.setObjectName("subtitle")
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

    def showEvent(self, event) -> None:
        super().showEvent(event)
        # Top-level windows ignore height-for-width: size the dialog for its wrapped hints.
        layout = self.layout()
        layout.activate()
        height = (layout.totalHeightForWidth(self.width()) if layout.hasHeightForWidth()
                  else layout.totalMinimumSize().height())
        if height > self.height():
            self.setMinimumHeight(height)
            self.resize(self.width(), height)

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
        self.setWindowTitle(tr("log_title", name=entry.display_name))
        self.resize(900, 560)
        layout = QVBoxLayout(self)
        where = QLabel(html.escape(str(path)) if path else tr("log_none"))
        where.setObjectName("subtitle")
        where.setWordWrap(True)
        where.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(where)
        if can_fix_wave:
            note = QLabel(tr("log_wave32"))
            note.setObjectName("banner")
            note.setWordWrap(True)
            layout.addWidget(note)
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


# ---- main window -----------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self, service: Optional[AssistantService] = None,
                 entries: Optional[list[GameEntry]] = None) -> None:
        super().__init__()
        self.service = service or AssistantService()
        self.pool = QThreadPool.globalInstance()
        self.entries: list[GameEntry] = list(entries or [])
        self.running: dict[int, RunningGame] = {}
        self.folder: Optional[HelixSRFolder] = None
        self.gpus: list[gpu.Gpu] = gpu.detect()
        self.busy = False
        self._polling = False
        self._first_poll = True
        # app id -> {"since": monotonic seconds, "shown": bool} per game session
        self._sessions: dict[int, dict] = {}
        self._thumbs: dict[int, Optional[QPixmap]] = {}
        self._row_widgets: dict[int, tuple[QLabel, QPushButton, int]] = {}
        self._steam = None

        self.setWindowTitle(window_title())
        self.resize(1440, 820)
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel(tr("app_name"))
        title.setObjectName("title")
        subtitle = QLabel(f"HelixSR Assistant · {tr('subtitle')}")
        subtitle.setObjectName("subtitle")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch(1)
        center = Qt.AlignmentFlag.AlignVCenter
        self.helixsr_pill = QPushButton(tr("hx_pill_unknown"))
        self.helixsr_pill.setProperty("class", "pill")
        self.helixsr_pill.setCursor(Qt.CursorShape.PointingHandCursor)
        self.helixsr_pill.clicked.connect(self.choose_folder)
        self.gpu_pill = QLabel(self._gpu_text())
        self.gpu_pill.setProperty("class", "pill")
        self.gpu_pill.setToolTip(self._gpu_tooltip())
        self.count_pill = QLabel("")
        self.count_pill.setProperty("class", "pill")
        for widget in (self.helixsr_pill, self.gpu_pill, self.count_pill):
            header.addWidget(widget, 0, center)
        self.language_box = QComboBox()
        self.language_box.setToolTip(tr("language"))
        for code, native, _ in i18n.LANGUAGES:
            self.language_box.addItem(f"🌐 {native}", code)
        self.language_box.setCurrentIndex(i18n.CODES.index(i18n.current()))
        self.language_box.currentIndexChanged.connect(self.change_language)
        header.addWidget(self.language_box, 0, center)
        self.rescan_btn = QPushButton(tr("rescan"))
        self.rescan_btn.setObjectName("primary")
        self.rescan_btn.setToolTip(tr("rescan_tip"))
        self.rescan_btn.clicked.connect(lambda: self.refresh(rescan=True))
        header.addWidget(self.rescan_btn, 0, center)
        root.addLayout(header)

        self.banner = QWidget()
        banner_box = QHBoxLayout(self.banner)
        banner_box.setContentsMargins(0, 0, 0, 0)
        self.banner_text = QLabel()
        self.banner_text.setObjectName("banner")
        self.banner_text.setWordWrap(True)
        self.banner_text.setTextFormat(Qt.TextFormat.RichText)
        self.banner_text.setOpenExternalLinks(True)
        banner_box.addWidget(self.banner_text, 1)
        actions = QVBoxLayout()
        self.choose_btn = QPushButton(tr("btn_choose_folder"))
        self.choose_btn.setObjectName("primary")
        self.choose_btn.clicked.connect(self.choose_folder)
        self.setup_btn = QPushButton(tr("btn_run_setup"))
        self.setup_btn.setToolTip(tr("btn_run_setup_tip"))
        self.setup_btn.clicked.connect(self.run_setup)
        self.download_btn = QPushButton(tr("btn_download"))
        self.download_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(RELEASES_URL)))
        for button in (self.choose_btn, self.setup_btn, self.download_btn):
            actions.addWidget(button)
        actions.addStretch(1)
        banner_box.addLayout(actions)
        self.banner.setVisible(False)
        root.addWidget(self.banner)

        tools = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(tr("search"))
        self.search.textChanged.connect(self.apply_filter)
        self.filter = QComboBox()
        self.filter.addItems([tr("filter_supported"), tr("filter_installed"),
                              tr("filter_not_installed"), tr("filter_attention"),
                              tr("filter_running"), tr("filter_all")])
        self.filter.currentIndexChanged.connect(self.apply_filter)
        self.update_all_btn = QPushButton(tr("btn_update_all", count=0))
        self.update_all_btn.setObjectName("update")
        self.update_all_btn.setToolTip(tr("btn_update_all_tip"))
        self.update_all_btn.clicked.connect(self.update_all)
        self.update_all_btn.setVisible(False)
        self.overlay_box = QCheckBox(tr("osd_toggle"))
        self.overlay_box.setToolTip(tr("osd_toggle_tip"))
        self.overlay_box.setChecked(self.service.overlay_enabled)
        self.overlay_box.toggled.connect(
            lambda checked: setattr(self.service, "overlay_enabled", checked))
        tools.addWidget(self.search, 1)
        tools.addWidget(self.filter)
        tools.addWidget(self.update_all_btn)
        tools.addWidget(self.overlay_box)
        root.addLayout(tools)

        columns = (tr("col_game"), tr("col_status"), tr("col_upscalers"), tr("col_runtime"),
                   tr("col_actions"))
        self.table = QTableWidget(0, len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setWordWrap(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setIconSize(QSize(THUMB_W, THUMB_H))
        self.table.verticalHeader().setDefaultSectionSize(ROW_H)
        head = self.table.horizontalHeader()
        for col, width in ((COL_GAME, 330), (COL_STATUS, 240), (COL_UPSCALERS, 170)):
            head.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.table.setColumnWidth(col, width)
        head.setSectionResizeMode(COL_RUNTIME, QHeaderView.ResizeMode.Stretch)
        head.setSectionResizeMode(COL_ACTIONS, QHeaderView.ResizeMode.Fixed)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(2000)
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self.table)
        splitter.addWidget(self.log)
        splitter.setSizes([620, 140])
        root.addWidget(splitter, 1)

        quit_action = QAction(self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        self.addAction(quit_action)

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(POLL_MS)
        self.poll_timer.timeout.connect(self.poll_runtime)

        self.write_log(tr("log_started", version=__version__))
        if self.entries:
            self.populate()
            QTimer.singleShot(0, lambda: self.refresh(rescan=False))
        elif self.service.has_scanned:
            QTimer.singleShot(0, lambda: self.refresh(rescan=False))
        else:
            self.write_log(tr("log_first_scan"))
            QTimer.singleShot(0, lambda: self.refresh(rescan=True))
        self.poll_timer.start()
        QTimer.singleShot(0, self.poll_runtime)
        QApplication.instance().aboutToQuit.connect(self._shutdown)

    def _shutdown(self) -> None:
        """Let background tasks finish before Qt and Python tear down."""
        self.poll_timer.stop()
        self.pool.waitForDone(15000)

    # ---- language -------------------------------------------------------------

    def change_language(self, index: int) -> None:
        code = self.language_box.itemData(index)
        if code == i18n.current():
            return
        self.service.language = code
        i18n.set_language(code)
        app = QApplication.instance()
        install_translations(app)
        app.setApplicationDisplayName(tr("app_name"))
        replacement = MainWindow(self.service, self.entries)
        replacement.setGeometry(self.geometry())
        if self.isMaximized():
            replacement.showMaximized()
        else:
            replacement.show()
        app.main_window = replacement
        self.poll_timer.stop()
        self.close()
        self.deleteLater()

    # ---- helpers ------------------------------------------------------------

    def write_log(self, text: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        for line in str(text).splitlines() or [""]:
            self.log.appendPlainText(f"[{stamp}] {line}")

    def set_busy(self, busy: bool, message: str = "") -> None:
        self.busy = busy
        for widget in (self.rescan_btn, self.language_box, self.table, self.update_all_btn,
                       self.helixsr_pill, self.banner):
            widget.setEnabled(not busy)
        if busy:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            if message:
                self.statusBar().showMessage(message)
        else:
            QApplication.restoreOverrideCursor()
            self.statusBar().clearMessage()

    def error_box(self, message: str) -> None:
        box = QMessageBox(QMessageBox.Icon.Critical, window_title(), message, parent=self)
        box.addButton(tr("ok"), QMessageBox.ButtonRole.AcceptRole)
        box.exec()

    def run_task(self, message: str, fn: Callable, *args,
                 on_done: Callable[[object], None], on_error: Optional[Callable] = None) -> None:
        self.set_busy(True, message)
        task = _Task(fn, *args)

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
        if not self.gpus:
            return tr("gpu_unknown")
        best = next((g for g in self.gpus if g.vendor == "AMD" and g.family), self.gpus[0])
        return tr("gpu_pill", gpu=best.label())

    def _gpu_tooltip(self) -> str:
        lines = [g.label() + (f" — {g.name}" if g.name else "") for g in self.gpus]
        amd = [g for g in self.gpus if g.vendor == "AMD"]
        if not amd:
            lines.append(tr("gpu_not_amd"))
        elif all(g.supported is False for g in amd):
            lines.append(tr("gpu_too_old"))
        if any(g.family == "Vega" for g in amd):
            lines.append(tr("gpu_vega"))
        if any(g.rdna3_or_newer for g in amd):
            lines.append(tr("gpu_rdna3"))
        return "\n".join(lines) or tr("gpu_unknown")

    @property
    def rdna3(self) -> bool:
        return any(g.rdna3_or_newer for g in self.gpus)

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
            text, tip, banner = tr("hx_pill_none"), tr("hx_pill_choose"), tr("banner_none")
        elif folder.ready:
            text = tr("hx_pill_ready", version=folder.version)
            tip, banner = f"{folder.path}\n{tr('hx_pill_choose')}", ""
        else:
            problem = folder.problem or "hx_not_helixsr"
            text = tr("hx_pill_problem", version=folder.version or "?")
            message = tr(problem, path=folder.path, version=folder.version or "?", minimum=minimum)
            tip = f"{message}\n{tr('hx_pill_choose')}"
            banner = tr("banner_" + problem.removeprefix("hx_"), path=html.escape(str(folder.path)),
                        version=folder.version or "?", minimum=minimum)
        self.helixsr_pill.setText(text)
        self.helixsr_pill.setToolTip(tip)
        self.banner.setVisible(bool(banner))
        if banner:
            banner = banner.replace("<a href=", '<a style="color:#ffd27a;" href=')
            self.banner_text.setText(banner + "<br><br>" + tr("banner_note"))
            built = folder is not None and folder.version and not folder.built
            self.setup_btn.setVisible(bool(built))
            self.setup_btn.setEnabled(find_terminal() is not None)
            if find_terminal() is None:
                self.setup_btn.setToolTip(tr("btn_run_setup_none"))

    def _offer_newer(self, newer: HelixSRFolder) -> None:
        current = self.folder.version if self.folder and self.folder.version else "—"
        if confirm(self, window_title(),
                   tr("newer_found", version=html.escape(newer.version or "?"), current=current,
                      path=html.escape(str(newer.path))),
                   tr("btn_use_newer"), QMessageBox.Icon.Question):
            self._apply_folder(str(newer.path))

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
        return bool(entry and entry.status.route == "optiscaler" and self.rdna3
                    and game.log and game.log.wave == 32)

    def _track_sessions(self) -> None:
        """Show the overlay once per game launch, when HelixSR's state is known."""
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
            if session["shown"] or not self.overlay_box.isChecked() or not (entry and entry.installed):
                continue
            late = now - session["since"] > OVERLAY_NOT_LOADED_AFTER
            if game.helixsr_loaded or late:
                session["shown"] = True
                self._show_overlay(entry, game)
                if self._wave32_problem(entry, game):
                    self.write_log(tr("log_wave32_hint", name=entry.display_name))
        self._first_poll = False

    def _describe(self, entry: GameEntry, game: RunningGame) -> tuple[str, str, list[tuple[str, str, bool]], list[str]]:
        """(headline, colour, [(label, detail, ok)], notes) for a running game."""
        status = entry.status
        route = status.route or "direct"
        lines: list[tuple[str, str, bool]] = []
        notes: list[str] = []
        if game.helixsr_loaded:
            headline = tr("rt_loaded", version=status.version or "?", way=way_label(route))
            color = GREEN
        else:
            headline = tr("rt_not_loaded_" + route)
            color = YELLOW
        if route == "optiscaler":
            lines.append(("OptiScaler", tr("rt_menu_hint"), game.helper_loaded))
        elif route == "dlss":
            lines.append((tr("rt_loader"), "", game.helper_loaded))
        log = game.log
        if log:
            if log.wave:
                lines.append((tr("rt_wave"), f"wave{log.wave}", True))
            if log.version and status.version and log.version != status.version:
                notes.append(tr("rt_log_version", version=log.version))
            notes += log.problems
            if log.problems:
                color = ORANGE if game.helixsr_loaded else color
        if self._wave32_problem(entry, game):
            notes.append(tr("rt_wave32"))
        return headline, color, lines, notes

    def _show_overlay(self, entry: GameEntry, game: RunningGame) -> None:
        headline, color, lines, notes = self._describe(entry, game)
        try:
            overlay.show({
                "title": entry.display_name,
                "headline": headline,
                "color": color,
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
                    pixmap = loaded.scaled(THUMB_W, THUMB_H,
                                           Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                           Qt.TransformationMode.SmoothTransformation)
            self._thumbs[app_id] = pixmap
        return self._thumbs[app_id]

    def _status(self, entry: GameEntry) -> tuple[str, str, str]:
        """(text, colour, tooltip) for the status column."""
        status = entry.status
        if status.installed:
            text = tr("st_installed", version=status.version or "?", way=way_label(status.route))
            tip = [tr("svc_pick_" + status.route)]
            tip += [str(p) for p in status.dll_files]
            if status.installed_by:
                tip.append(tr("st_installed_by", by=status.installed_by))
            color = GREEN
            if entry.outdated and self.folder:
                text += "\n" + tr("st_outdated", version=self.folder.version)
                color = YELLOW
            for issue in status.issues:
                text += "\n⚠ " + tr(issue + "_short")
                tip.append(tr(issue))
                color = ORANGE
            return text, color, "\n".join(tip)
        if entry.ways:
            default = entry.ways[0]
            return (tr("st_not_installed"), GREY,
                    tr("st_can_install", ways=", ".join(way_label(w) for w in entry.ways),
                       default=way_label(default)))
        return tr("st_unsupported"), DIM, tr("st_unsupported_tip")

    def populate(self) -> None:
        self.table.setRowCount(0)
        self._row_widgets.clear()
        installed = outdated = 0
        collator = QCollator(QLocale(i18n.qt_suffix()))
        collator.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        collator.setNumericMode(True)
        # Games HelixSR can use first, then the rest.
        self.entries.sort(key=cmp_to_key(lambda a, b: (b.supported - a.supported) or
                                         collator.compare(a.display_name, b.display_name)))
        for entry in self.entries:
            row = self.table.rowCount()
            self.table.insertRow(row)

            name_item = QTableWidgetItem(f"{entry.display_name}\nApp ID {entry.app_id}")
            name_item.setData(Qt.ItemDataRole.UserRole, entry.app_id)
            thumb = self._thumb(entry.app_id)
            if thumb:
                name_item.setIcon(QIcon(thumb))
            tooltip = entry.install_dir
            if entry.display_name != entry.name:
                tooltip = f"{entry.name}\n{tooltip}"
            name_item.setToolTip(tooltip)
            if not entry.supported:
                name_item.setForeground(QColor(GREY))
            self.table.setItem(row, COL_GAME, name_item)

            text, color, tip = self._status(entry)
            status = QTableWidgetItem(text)
            status.setForeground(QColor(color))
            status.setToolTip(tip)
            self.table.setItem(row, COL_STATUS, status)

            layout = entry.layout
            ups = " · ".join(layout.upscalers) or "—"
            if layout.anti_cheat:
                ups += "\n⚠ " + ", ".join(layout.anti_cheat)
            ups_item = QTableWidgetItem(ups)
            ups_tip = [tr("ups_exe", path=layout.exe_dir or "—")]
            ups_tip += [tr("ups_fsr", path=p) for p in layout.fsr_targets]
            if layout.anti_cheat:
                ups_tip.append(tr("ups_anti_cheat"))
            ups_item.setToolTip("\n".join(ups_tip))
            if layout.anti_cheat:
                ups_item.setForeground(QColor(YELLOW))
            elif not entry.supported:
                ups_item.setForeground(QColor(DIM))
            self.table.setItem(row, COL_UPSCALERS, ups_item)

            runtime_label = QLabel()
            runtime_label.setWordWrap(True)
            runtime_label.setTextFormat(Qt.TextFormat.RichText)
            runtime_label.setContentsMargins(6, 2, 6, 2)
            self.table.setCellWidget(row, COL_RUNTIME, runtime_label)

            cell = QWidget()
            box = QHBoxLayout(cell)
            box.setContentsMargins(6, 4, 6, 4)
            box.setSpacing(6)
            launch = QPushButton(tr("btn_launch"))
            launch.setObjectName("launch")
            launch.setToolTip(tr("btn_launch_tip"))
            launch.clicked.connect(lambda _, e=entry: self.launch(e))
            box.addWidget(launch)
            if entry.installed:
                installed += 1
                outdated += entry.outdated
                if entry.needs_attention:
                    fix = QPushButton(tr("btn_repair") if entry.status.issues else tr("btn_update"))
                    fix.setObjectName("update")
                    fix.setToolTip(tr("btn_repair_tip") if entry.status.issues
                                   else tr("btn_update_tip"))
                    fix.clicked.connect(lambda _, e=entry: self.install(e, e.status.route))
                    box.addWidget(fix)
                gear = QPushButton(tr("btn_settings"))
                gear.setToolTip(tr("btn_settings_tip"))
                gear.clicked.connect(lambda _, e=entry: self.edit_settings(e))
                box.addWidget(gear)
                more = QToolButton()
                more.setText(tr("btn_more"))
                more.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
                more.setMenu(self._more_menu(entry, more))
                box.addWidget(more)
                remove = QPushButton(tr("btn_remove"))
                remove.setObjectName("remove")
                remove.clicked.connect(lambda _, e=entry: self.uninstall(e))
                box.addWidget(remove)
            elif entry.ways:
                button = QToolButton()
                button.setObjectName("install")
                button.setText(tr("btn_install"))
                button.setToolTip(tr("btn_install_tip", way=way_label(entry.ways[0])))
                button.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
                button.clicked.connect(lambda _, e=entry: self.install(e, e.ways[0]))
                menu = QMenu(button)
                for route in entry.ways:
                    action = menu.addAction(tr("menu_install_" + route))
                    action.triggered.connect(lambda _, e=entry, r=route: self.install(e, r))
                button.setMenu(menu)
                box.addWidget(button)
            box.addStretch(1)
            self.table.setCellWidget(row, COL_ACTIONS, cell)
            self._row_widgets[entry.app_id] = (runtime_label, launch, row)
        self.count_pill.setText(tr("count", installed=installed,
                                   supported=sum(1 for e in self.entries if e.supported)))
        self.update_all_btn.setText(tr("btn_update_all", count=outdated))
        self.update_all_btn.setVisible(outdated > 0)
        # Cell widgets are ignored by ResizeToContents; size the column from the
        # widest button row (button labels differ a lot between languages).
        widest = max((self.table.cellWidget(r, COL_ACTIONS).sizeHint().width()
                      for r in range(self.table.rowCount())), default=200)
        self.table.setColumnWidth(COL_ACTIONS, widest + 8)
        self.update_runtime()

    def _more_menu(self, entry: GameEntry, parent: QWidget) -> QMenu:
        menu = QMenu(parent)
        for route in entry.ways:
            if route == entry.status.route:
                continue
            action = menu.addAction(tr("menu_switch_" + route))
            action.triggered.connect(lambda _, e=entry, r=route: self.install(e, r))
        if not menu.isEmpty():
            menu.addSeparator()
        menu.addAction(tr("menu_log")).triggered.connect(lambda: self.show_log(entry))
        menu.addAction(tr("menu_folder")).triggered.connect(lambda: self.open_folder(entry))
        return menu

    def update_runtime(self) -> None:
        entries = {e.app_id: e for e in self.entries}
        width = max(120, self.table.columnWidth(COL_RUNTIME) - 12)
        for app_id, (label, launch, row) in self._row_widgets.items():
            game = self.running.get(app_id)
            launch.setEnabled(game is None)
            launch.setText(tr("btn_running") if game else tr("btn_launch"))
            entry = entries.get(app_id)
            if game is None or entry is None:
                label.setText(f'<span style="color:{DIM}">—</span>')
                label.setToolTip("")
                self.table.setRowHeight(row, ROW_H)
                continue
            if not entry.installed:
                label.setText(f'<span style="color:{GREY}">{html.escape(tr("rt_running_without"))}</span>')
                label.setToolTip(tr("rt_pids", pids=", ".join(map(str, game.pids))))
                continue
            headline, color, lines, notes = self._describe(entry, game)
            parts = [f'<b style="color:{color}">{html.escape(headline)}</b>']
            for name, detail, ok in lines:
                mark, tone = ("✓", "#7fe0a6") if ok else ("✗", GREY)
                extra = f" — {html.escape(detail)}" if detail else ""
                parts.append(f'<span style="color:{tone}">{mark} {html.escape(name)}</span>'
                             f'<span style="color:#b8c0cc">{extra}</span>')
            for note in notes:
                parts.append(f'<span style="color:{YELLOW}">⚠ {html.escape(note)}</span>')
            label.setText("<br>".join(parts))
            tip = [tr("rt_pids", pids=", ".join(map(str, game.pids)))]
            if game.log:
                tip.append(str(game.log.path))
                if game.log.wave_line:
                    tip.append(game.log.wave_line)
            label.setToolTip("\n".join(tip))
            # A running game can need more lines than a normal row has.
            self.table.setRowHeight(row, max(ROW_H, label.heightForWidth(width) + 12))
        self.apply_filter()

    def apply_filter(self) -> None:
        query = self.search.text().strip().casefold()
        mode = self.filter.currentIndex()
        by_id = {e.app_id: e for e in self.entries}
        for row in range(self.table.rowCount()):
            item = self.table.item(row, COL_GAME)
            entry = by_id.get(item.data(Qt.ItemDataRole.UserRole)) if item else None
            if entry is None:
                continue
            visible = not query or entry.matches(query)
            if mode == FILTER_SUPPORTED:
                visible &= entry.supported
            elif mode == FILTER_INSTALLED:
                visible &= entry.installed
            elif mode == FILTER_NOT_INSTALLED:
                visible &= bool(entry.ways) and not entry.installed
            elif mode == FILTER_ATTENTION:
                visible &= entry.needs_attention
            elif mode == FILTER_RUNNING:
                visible &= entry.app_id in self.running
            self.table.setRowHidden(row, not visible)

    # ---- actions ------------------------------------------------------------

    def launch(self, entry: GameEntry) -> None:
        self.write_log(tr("log_launch", name=entry.display_name))
        try:
            self.service.launch_game(entry.app_id)
        except RuntimeError as error:
            self.write_log(tr("log_error", error=error))
            self.error_box(str(error))
            return
        _, launch, _ = self._row_widgets.get(entry.app_id, (None, None, None))
        if launch is not None:
            launch.setEnabled(False)  # re-enabled by polling if the game never starts
        QTimer.singleShot(1500, self.poll_runtime)

    def _warnings_ok(self, entry: GameEntry, route: str) -> bool:
        name = html.escape(entry.display_name)
        if entry.status.route == route:
            return True   # update or repair of the way already chosen
        if route == "dlss" and not confirm(self, tr("warn_dlss_title"),
                                           tr("warn_dlss", name=name), tr("btn_install_anyway")):
            return False
        if entry.layout.anti_cheat and not confirm(
                self, tr("warn_ac_title"),
                tr("warn_ac", name=name, ac=html.escape(", ".join(entry.layout.anti_cheat))),
                tr("btn_install_anyway")):
            return False
        return True

    def install(self, entry: GameEntry, route: str) -> None:
        if not self._warnings_ok(entry, route):
            self.write_log(tr("log_cancelled"))
            return
        if entry.status.route == route:
            key = "log_update"
        elif entry.status.route:
            key = "log_switch"
        else:
            key = "log_install"
        self.write_log(tr(key, name=entry.display_name, way=way_label(route)))
        self._run_action(tr("busy_install", name=entry.display_name),
                         self.service.install, entry.app_id, route)

    def uninstall(self, entry: GameEntry) -> None:
        has_settings = any((d / settings.INI).is_file() for d in entry.status.ini_dirs)
        dialog = RemoveDialog(entry, has_settings, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        remove_settings = dialog.remove_settings.isChecked()
        self.write_log(tr("log_remove", name=entry.display_name))
        self._run_action(tr("busy_remove", name=entry.display_name),
                         self.service.uninstall, entry.app_id, remove_settings)

    def update_all(self) -> None:
        self.write_log(tr("log_update_all"))
        self._run_action(tr("busy_update_all"), self.service.update_all)

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
        summary = summarize(path) if path else None
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
            return False

        self.run_task(message, fn, *args, on_done=done, on_error=on_error)


def install_translations(app: QApplication) -> None:
    """Translate Qt's own texts (context menus, standard dialogs) to the UI language."""
    for translator in getattr(app, "_helixsr_translators", []):
        app.removeTranslator(translator)
    app._helixsr_translators = []
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
                app._helixsr_translators.append(translator)
                break


def main() -> int:
    app = QApplication(sys.argv)
    service = AssistantService()
    i18n.set_language(service.language)
    install_translations(app)
    app.setApplicationName("HelixSR Assistant")
    app.setApplicationDisplayName(tr("app_name"))
    app.setDesktopFileName("helixsr-assistant")
    app.setStyleSheet(STYLE)
    app.main_window = MainWindow(service)
    app.main_window.show()
    return app.exec()
