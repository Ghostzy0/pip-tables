"""Original MIT Pip rendering and Qt theme. No proprietary motion code."""
from PySide6.QtCore import QSettings, Qt, QVariantAnimation, QEasingCurve
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont, QPainter, QPainterPath, QPalette
from PySide6.QtWidgets import QApplication, QWidget

# Theme anchors and semantic sizes are centralised here. Native window chrome,
# menus, file panels and keyboard navigation retain macOS semantics.
ANCHORS = {
    "Paper": (("#FFFFFF", "#121211", "#121211"), ("#0F0F0E", "#F1F1EE", "#F1F1EE")),
    "Oat": (("#F6F2EA", "#1E1B16", "#B4532A"), ("#181512", "#F2EDE3", "#E0865C")),
    "Harbour": (("#F3F6FA", "#14202E", "#1F5FBF"), ("#0F1722", "#E6EDF6", "#6FA3F0")),
    "Fern": (("#F2F6F1", "#16231A", "#2F7A4B"), ("#101A13", "#E4EFE6", "#6CC18A")),
    "Plum": (("#F8F3F6", "#25171F", "#8A2F67"), ("#1B1218", "#F4E8EF", "#D77DB3")),
    "Saffron": (("#FAF6EC", "#231C0E", "#A86A00"), ("#1A1509", "#F7EFD9", "#F0B43A")),
    "Slate": (("#F4F5F7", "#1B1E24", "#4A5568"), ("#121418", "#E8EAEE", "#9AA5B8")),
    "Graphite": (("#FFFFFF", "#0B0B0C", "#111111"), ("#0B0B0C", "#F5F5F5", "#FFFFFF")),
    "Coast": (("#F1F8F8", "#11262A", "#0F7C84"), ("#0D1A1C", "#E2F1F2", "#55C2CA")),
}
SPACE = {"tight": 4, "group": 8, "row": 12, "edge": 16, "section": 24}
SIZE = {"control": 34, "field": 36, "pill": 17, "card": 18, "small": 10}


def reduced_motion():
    """Read the documented NSWorkspace preference; fail to a still pose."""
    import sys
    if sys.platform != "darwin" or QApplication.platformName() != "cocoa":
        return True
    try:
        import ctypes
        ctypes.CDLL("/System/Library/Frameworks/AppKit.framework/AppKit")
        objc = ctypes.CDLL("/usr/lib/libobjc.A.dylib")
        objc.objc_getClass.argtypes = [ctypes.c_char_p]
        objc.objc_getClass.restype = ctypes.c_void_p
        objc.sel_registerName.argtypes = [ctypes.c_char_p]
        objc.sel_registerName.restype = ctypes.c_void_p
        pointer_send = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))
        bool_send = ctypes.CFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(("objc_msgSend", objc))
        workspace = pointer_send(objc.objc_getClass(b"NSWorkspace"), objc.sel_registerName(b"sharedWorkspace"))
        return not workspace or bool(bool_send(workspace, objc.sel_registerName(b"accessibilityDisplayShouldReduceMotion")))
    except (OSError, AttributeError, TypeError):
        return True


def mix(a, b, fraction):
    left, right = QColor(a), QColor(b)
    return QColor(*(round(x+(y-x)*fraction) for x, y in zip(left.getRgb()[:3], right.getRgb()[:3]))).name()


def tokens(name="Paper", dark=False):
    canvas, ink, accent = ANCHORS[name][int(dark)]
    return dict(canvas=canvas, ink=ink, accent=accent, text=ink,
                surface=mix(canvas, ink, .035), fill=mix(canvas, ink, .07),
                strong=mix(canvas, ink, .13), line=mix(canvas, ink, .17),
                control=mix(canvas, ink, .55), muted=mix(canvas, ink, .70),
                danger="#FF8B7E" if dark else "#AE2A1F")


class PipMark(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = "idle"
        self.nod = 0.0
        self.motion = False
        self.animation = QVariantAnimation(self)
        self.animation.setDuration(280)
        self.animation.setStartValue(0.0)
        self.animation.setKeyValueAt(.5, 1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.animation.valueChanged.connect(self.set_nod)
        self.colors = tokens()
        self.setFixedSize(52, 52)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_state(self, state):
        self.animation.stop()
        self.nod = 0.0
        self.state = state
        if state == "success" and self.motion and not reduced_motion():
            self.animation.start()
        self.update()

    def set_nod(self, amount):
        if not self.motion or reduced_motion():
            self.animation.stop()
            self.nod = 0.0
        else:
            self.nod = amount
        self.update()

    def set_motion(self, enabled):
        self.motion = enabled
        if not enabled:
            self.animation.stop()
            self.nod = 0.0
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.translate(26, 26-self.nod*3)
        p.rotate(self.nod*6)
        p.translate(-26, -26)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(self.colors["ink"]))
        shape = QPainterPath()
        shape.moveTo(10, 37)
        shape.cubicTo(2, 23, 12, 6, 26, 8)
        shape.cubicTo(40, 5, 49, 19, 44, 34)
        shape.cubicTo(40, 47, 17, 50, 10, 37)
        p.drawPath(shape)
        p.setBrush(QColor(self.colors["canvas"]))
        if self.state == "success":
            p.drawRoundedRect(17, 24, 5, 2, 1, 1)
            p.drawRoundedRect(31, 24, 5, 2, 1, 1)
        else:
            offset = -2 if self.state == "working" else 0
            p.drawEllipse(17, 21+offset, 5, 7)
            p.drawEllipse(31, 21+offset, 5, 7)


def apply(window, name, dark):
    app = QApplication.instance()
    t = tokens(name, dark)
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: t["canvas"], QPalette.ColorRole.WindowText: t["text"],
        QPalette.ColorRole.Base: t["canvas"], QPalette.ColorRole.AlternateBase: t["surface"],
        QPalette.ColorRole.Text: t["text"], QPalette.ColorRole.Button: t["fill"],
        QPalette.ColorRole.ButtonText: t["text"], QPalette.ColorRole.Highlight: t["strong"],
        QPalette.ColorRole.HighlightedText: t["text"], QPalette.ColorRole.Mid: t["control"],
        QPalette.ColorRole.ToolTipBase: t["ink"], QPalette.ColorRole.ToolTipText: t["canvas"],
        QPalette.ColorRole.PlaceholderText: t["muted"],
    }
    for role, value in roles.items():
        palette.setColor(role, QColor(value))
    app.setPalette(palette)
    app.setFont(QFont(".AppleSystemUIFont", 13))
    window.setStyleSheet(f"""
        QWidget {{ color: {t['text']}; font-size: 14px; }}
        QMainWindow, QDialog {{ background: {t['canvas']}; }}
        QLabel {{ background: transparent; }}
        QLabel#wordmark {{ font-size: 24px; font-weight: 600; }}
        QLabel#hero {{ font-size: 26px; font-weight: 600; }}
        QLabel#section {{ font-size: 18px; font-weight: 600; }}
        QLabel#muted {{ color: {t['muted']}; font-size: 13px; }}
        QLabel#statusError {{ color: {t['danger']}; }}
        QWidget#sidebar {{ background: {t['surface']}; border-radius: {SIZE['card']}px; }}
        QPushButton {{ min-height: {SIZE['control']}px; padding: 0 {SPACE['edge']}px;
            border: 1px solid {t['line']}; border-radius: {SIZE['pill']}px; background: {t['fill']}; font-weight: 500; }}
        QPushButton:hover {{ background: {t['strong']}; }}
        QPushButton:pressed {{ background: {t['strong']}; border-color: {t['control']}; }}
        QPushButton:focus {{ border: 2px solid {t['ink']}; }}
        QPushButton#primary {{ background: {t['ink']}; color: {t['canvas']}; border-color: {t['ink']}; }}
        QPushButton:disabled, QPushButton#primary:disabled {{ background: {t['fill']}; color: {t['muted']}; border-color: {t['line']}; }}
        QLineEdit, QComboBox {{ min-height: {SIZE['field']}px; padding: 0 {SPACE['row']}px;
            background: {t['surface']}; border: 1px solid {t['control']}; border-radius: {SIZE['pill']}px; }}
        QLineEdit:focus, QComboBox:focus {{ border: 2px solid {t['ink']}; }}
        QPlainTextEdit {{ background: {t['surface']}; border: 1px solid {t['control']}; border-radius: {SIZE['small']}px;
            padding: {SPACE['row']}px; font-family: Menlo, monospace; font-size: 13px; }}
        QPlainTextEdit:focus {{ border: 2px solid {t['ink']}; }}
        QListWidget {{ border: none; background: transparent; outline: 0; }}
        QListWidget::item {{ padding: {SPACE['group']}px {SPACE['row']}px; border-radius: {SIZE['small']}px; }}
        QListWidget::item:selected {{ background: {t['strong']}; color: {t['text']}; }}
        QListWidget::item:hover {{ background: {t['fill']}; }}
        QListWidget::item:focus {{ border: 1px solid {t['ink']}; }}
        QTableView {{ background: {t['canvas']}; alternate-background-color: {t['surface']};
            gridline-color: {t['line']}; border: 1px solid {t['line']}; selection-background-color: {t['strong']}; selection-color: {t['text']}; }}
        QHeaderView::section {{ background: {t['surface']}; color: {t['muted']}; padding: {SPACE['group']}px;
            border: none; border-bottom: 1px solid {t['line']}; font-size: 12px; font-weight: 500; }}
        QTabWidget::pane {{ border: none; padding-top: {SPACE['group']}px; }}
        QTabBar::tab {{ padding: {SPACE['group']}px {SPACE['edge']}px; background: {t['surface']}; color: {t['muted']}; }}
        QTabBar::tab:selected {{ background: {t['strong']}; color: {t['text']}; }}
        QTabBar::tab:focus {{ border-bottom: 2px solid {t['ink']}; }}
        QSplitter::handle {{ background: {t['canvas']}; }}
        QToolTip {{ background: {t['ink']}; color: {t['canvas']}; border: none; padding: {SPACE['group']}px; }}
    """)
    for grid in [window.grid, window.profile_grid]:
        grid.verticalHeader().setDefaultSectionSize(34)
    window.mark.colors = t
    window.mark.update()
    window.look_settings.setValue("theme", name)
    window.look_settings.setValue("dark", dark)


def install(window):
    window.mark = PipMark(window)
    header = window.centralWidget().layout().itemAt(0).layout()
    header.insertWidget(0, window.mark)
    header.setSpacing(SPACE["edge"])
    window.look_settings = QSettings("Ghostzy0", window.variant_name)
    look = window.menuBar().addMenu("Look")
    group = QActionGroup(window)
    group.setExclusive(True)
    selected_name = str(window.look_settings.value("theme", "Paper"))
    if selected_name not in ANCHORS:
        selected_name = "Paper"
    selected_dark = window.look_settings.value("dark", False, type=bool)
    motion = QAction("Still Pip", window)
    motion.setCheckable(True)
    motion.setChecked(not window.look_settings.value("motion", True, type=bool))
    def motion_changed(still):
        window.mark.set_motion(not still)
        window.look_settings.setValue("motion", not still)
    motion.toggled.connect(motion_changed)
    look.addAction(motion)
    look.addSeparator()
    window.mark.set_motion(not motion.isChecked())
    for name in ANCHORS:
        menu = look.addMenu(name)
        for dark, mode in [(False, "Light"), (True, "Dark")]:
            action = QAction(mode, window)
            action.setCheckable(True)
            action.setChecked((name, dark) == (selected_name, selected_dark))
            action.triggered.connect(lambda checked, name=name, dark=dark: apply(window, name, dark))
            group.addAction(action)
            menu.addAction(action)
    apply(window, selected_name, selected_dark)
