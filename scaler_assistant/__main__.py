import sys


def _self_test() -> int:
    """Used by the AppImage build: prove the bundled Python, Qt and translations work."""
    from PyQt6.QtCore import QCoreApplication
    from PyQt6.QtWidgets import QApplication

    from PyQt6.QtGui import QFontDatabase

    from . import __version__, components, i18n, theme, ui
    from .service import AssistantService  # noqa: F401

    app = QApplication(sys.argv[:1])
    theme.load_fonts()
    app.setStyleSheet(theme.stylesheet())
    missing_fonts = {"Inter", "Onest"} - set(QFontDatabase.families())
    if missing_fonts:
        print(f"Scaler Assistant self-test FAILED: fonts not loaded: {', '.join(sorted(missing_fonts))}")
        return 1
    qt_ok = []
    for code in i18n.CODES:
        i18n.set_language(code)
        ui.install_translations(app)
        if QCoreApplication.translate("QLineEdit", "&Copy") != "&Copy":
            qt_ok.append(code)
    seven_zip = components.seven_zip()
    if seven_zip is None:
        print("Scaler Assistant self-test FAILED: no 7-Zip to unpack OptiScaler")
        return 1
    print(f"Scaler Assistant {__version__} self-test OK (Qt platform: {app.platformName()}, "
          f"UI languages: {len(i18n.CODES)}, Qt translations: {', '.join(qt_ok) or 'none'}, "
          f"7-Zip: {seven_zip[0].rsplit('/', 1)[-1]})")
    return 0


if "--self-test" in sys.argv:
    sys.exit(_self_test())

from .ui import main  # noqa: E402

sys.exit(main())
