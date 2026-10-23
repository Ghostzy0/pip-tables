"""Original Qt desktop interface. Baseline uses system styling."""
from __future__ import annotations

import argparse
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QObject, QRunnable, Qt, QThreadPool, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QFont, QKeySequence, QPainter, QPen, QAccessible, QAccessibleAnnouncementEvent
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QMenu, QMessageBox, QPlainTextEdit,
    QPushButton, QSplitter, QStackedWidget, QTabWidget, QTableView,
    QVBoxLayout, QWidget, QAbstractItemView, QScrollArea, QSizePolicy,
)

from . import __version__, copy as c
from .engine import Project


def ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


class ResultModel(QAbstractTableModel):
    def __init__(self, columns=(), rows=(), types=(), parent=None, offset=0):
        super().__init__(parent)
        self.columns, self.rows, self.types = list(columns), list(rows), list(types)
        self.offset = offset

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.rows)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        value = self.rows[index.row()][index.column()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.ToolTipRole):
            return c.NULL if value is None else str(value)
        if role == Qt.ItemDataRole.TextAlignmentRole and isinstance(value, (int, float, Decimal)):
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        if role == Qt.ItemDataRole.AccessibleTextRole:
            return "Missing value" if value is None else str(value)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal:
            if role == Qt.ItemDataRole.DisplayRole:
                return self.columns[section]
            if role == Qt.ItemDataRole.ToolTipRole and section < len(self.types):
                return self.types[section]
        elif role == Qt.ItemDataRole.DisplayRole:
            return str(section + 1 + self.offset)
        return None


class Signals(QObject):
    done = Signal(object)
    failed = Signal(str)


class Task(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.signals = Signals()

    def run(self):
        try:
            self.signals.done.emit(self.operation())
        except Exception as exc:
            self.signals.failed.emit(str(exc))


class Chart(QWidget):
    """First-column labels, second-column numeric values; exact grid alternative."""
    def __init__(self):
        super().__init__()
        self.points = []
        self.message = c.NO_CHART
        self.kind = "Bar"
        self.setMinimumHeight(180)
        self.setAccessibleName(c.CHART)

    def set_result(self, result):
        self.points = []
        self.message = c.NO_CHART
        if result and len(result.columns) >= 2:
            values = result.rows[:50]
            if values and all(isinstance(row[1], (int, float, Decimal)) and not isinstance(row[1], bool)
                              and math.isfinite(float(row[1])) for row in values):
                self.points = [(str(row[0])[:30], float(row[1])) for row in values]
                self.message = ""
                self.setAccessibleDescription(c.CHART_HELP)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        text = self.palette().text().color()
        painter.setPen(text)
        if not self.points:
            painter.drawText(self.rect().adjusted(24, 24, -24, -24), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.message)
            return
        r = self.rect().adjusted(90, 24, -24, -60)
        lo = min(0.0, min(v for _, v in self.points))
        hi = max(0.0, max(v for _, v in self.points))
        if lo == hi:
            hi = lo + 1
        y = lambda value: r.bottom() - (value-lo)/(hi-lo)*r.height()
        zero = y(0)
        painter.setPen(QPen(self.palette().mid().color(), 1))
        painter.drawLine(r.left(), round(zero), r.right(), round(zero))
        painter.setPen(text)
        painter.drawText(8, r.top()+12, f"{hi:.6g}")
        painter.drawText(8, r.bottom(), f"{lo:.6g}")
        step = r.width() / len(self.points)
        last = None
        painter.setBrush(text)
        for i, (label, value) in enumerate(self.points):
            x = r.left() + step*(i+0.5)
            if self.kind == "Bar":
                painter.drawRect(round(x-step*.32), round(min(y(value), zero)), max(1, round(step*.64)), max(1, round(abs(y(value)-zero))))
            elif self.kind == "Line":
                if last:
                    painter.drawLine(last[0], last[1], round(x), round(y(value)))
                painter.drawEllipse(round(x)-3, round(y(value))-3, 6, 6)
            else:
                painter.drawEllipse(round(x)-4, round(y(value))-4, 8, 8)
            last = (round(x), round(y(value)))
            if i % max(1, math.ceil(len(self.points)/6)) == 0:
                painter.save()
                painter.translate(x-4, r.bottom()+18)
                painter.rotate(25)
                painter.drawText(0, 0, label[:16])
                painter.restore()


class ImportOptions(QDialog):
    def __init__(self, path, parent, sheets=None):
        super().__init__(parent)
        self.setWindowTitle(c.IMPORT)
        layout = QFormLayout(self)
        name = QLabel(Path(path).name)
        name.setWordWrap(True)
        layout.addRow(name)
        self.encoding = QComboBox()
        self.encoding.addItems(["utf-8", "utf-16", "latin-1"])
        layout.addRow("Text encoding", self.encoding)
        self.text = QCheckBox("Keep CSV columns as text")
        layout.addRow(self.text)
        self.sheet = QComboBox() if sheets is not None else QLineEdit()
        if sheets is not None:
            self.sheet.addItems(sheets)
        else:
            self.sheet.setPlaceholderText("Required when the workbook has several sheets")
        self.sheet.setAccessibleName("Excel sheet name")
        layout.addRow("Excel sheet name", self.sheet)
        self.encoding.setEnabled(Path(path).suffix.lower() in (".csv", ".tsv"))
        self.text.setEnabled(self.encoding.isEnabled())
        self.sheet.setEnabled(Path(path).suffix.lower() == ".xlsx")
        hint = QLabel("Imports a local copy. Source files stay unchanged. Excel formula cells are rejected; export values from Excel first.")
        hint.setWordWrap(True)
        layout.addRow(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class Builder(QDialog):
    """Deterministic, editable query recipes; never executes on open."""
    def __init__(self, tables, parent):
        super().__init__(parent)
        self.setWindowTitle("Build a query")
        self.resize(500, 380)
        self.tables = tables
        layout = QFormLayout(self)
        self.operation = QComboBox()
        self.operation.addItems(["Summary", "Join", "Pivot", "Change a column type"])
        self.left = QComboBox()
        self.left.addItems([t["name"] for t in tables])
        self.column = QComboBox()
        self.group = QComboBox()
        self.right = QComboBox()
        self.right.addItems([t["name"] for t in tables])
        self.right_column = QComboBox()
        self.function = QComboBox()
        self.function.addItems(["sum", "avg", "count", "min", "max"])
        self.cast = QComboBox()
        self.cast.addItems(["VARCHAR", "BIGINT", "DECIMAL(18,4)", "DOUBLE", "DATE", "TIMESTAMP"])
        for name, widget in [("Task", self.operation), ("Table", self.left), ("Value / left key", self.column),
                             ("Group / pivot on", self.group), ("Summary", self.function), ("Join table", self.right),
                             ("Right key", self.right_column), ("New type", self.cast)]:
            layout.addRow(name, widget)
        self.left.currentIndexChanged.connect(self.refresh_left)
        self.right.currentIndexChanged.connect(self.refresh_right)
        self.refresh_left()
        self.refresh_right()
        hint = QLabel("Creates a visible query for you to check and run. Type changes use TRY_CAST; values that do not fit become NULL.")
        hint.setWordWrap(True)
        layout.addRow(hint)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def names(self, combo):
        table = next(t for t in self.tables if t["name"] == combo.currentText())
        return [col["name"] for col in table["columns"]]

    def refresh_left(self):
        for control in [self.column, self.group]:
            control.clear()
            control.addItems(self.names(self.left))

    def refresh_right(self):
        self.right_column.clear()
        self.right_column.addItems(self.names(self.right))

    def sql(self):
        table, col, group = map(ident, [self.left.currentText(), self.column.currentText(), self.group.currentText()])
        func = self.function.currentText().upper()
        op = self.operation.currentText()
        if op == "Summary":
            return f"SELECT {group}, {func}({col}) AS value\nFROM {table}\nGROUP BY {group}\nORDER BY {group}"
        if op == "Join":
            return f"SELECT a.*, b.*\nFROM {table} AS a\nLEFT JOIN {ident(self.right.currentText())} AS b\nON a.{col} = b.{ident(self.right_column.currentText())}"
        if op == "Pivot":
            return f"PIVOT {table}\nON {group}\nUSING {func}({col})"
        return f"SELECT * REPLACE (TRY_CAST({col} AS {self.cast.currentText()}) AS {col})\nFROM {table}"


class Window(QMainWindow):
    def __init__(self, edition="baseline", project=None, enhanced=False):
        super().__init__()
        self.edition = edition
        self.enhanced = enhanced
        self.variant_name = (c.BASELINE if edition == "baseline" else c.APP) + (" Plus" if enhanced else "")
        self.version = "0.2.0a1" if enhanced else __version__
        self.page_offset = 0
        self.project = None
        self.busy = False
        self.result = None
        self.result_sql = ""
        self.current_table = ""
        self.table_info = []
        self.tasks = set()
        self.pool = QThreadPool(self)
        self.pool.setMaxThreadCount(1)
        self.sort_section = None
        self.sort_order = Qt.SortOrder.AscendingOrder
        self.sort_source_sql = ""
        self.setWindowTitle(self.variant_name)
        self.resize(1280, 820)
        self.setMinimumSize(900, 720)
        self.build_ui()
        self.build_menu()
        self.draft_timer = QTimer(self)
        self.draft_timer.setSingleShot(True)
        self.draft_timer.timeout.connect(self.save_draft)
        self.editor.textChanged.connect(lambda: self.draft_timer.start(700))
        if edition == "pip":
            from .theme import install
            install(self)
        self.set_busy(False)
        if project:
            self.load_project(Path(project))

    def button(self, text, handler, primary=False):
        button = QPushButton(text)
        button.setObjectName("primary" if primary else "secondary")
        button.clicked.connect(handler)
        button.setAccessibleName(text)
        return button

    def build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(16)
        header = QHBoxLayout()
        brand = QVBoxLayout()
        title = QLabel(self.variant_name)
        title.setObjectName("wordmark")
        brand.addWidget(title)
        tag = QLabel(c.LOCAL)
        tag.setObjectName("muted")
        brand.addWidget(tag)
        header.addLayout(brand)
        header.addStretch()
        self.new_btn = self.button(c.NEW, self.new_project)
        self.open_btn = self.button(c.OPEN, self.open_project)
        self.import_btn = self.button(c.IMPORT, self.import_file, True)
        for b in (self.new_btn, self.open_btn, self.import_btn):
            header.addWidget(b)
        outer.addLayout(header)
        self.split = QSplitter()
        outer.addWidget(self.split, 1)
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 16, 16, 16)
        self.project_title = QLabel("No project open")
        self.project_title.setObjectName("section")
        self.project_title.setWordWrap(True)
        side.addWidget(self.project_title)
        self.project_path = QLabel(c.PROJECT_HELP)
        self.project_path.setObjectName("muted")
        self.project_path.setWordWrap(True)
        side.addWidget(self.project_path)
        side.addSpacing(16)
        side.addWidget(QLabel(c.TABLES))
        self.tables = QListWidget()
        self.tables.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tables.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.tables.setAccessibleName(c.TABLES)
        self.tables.itemClicked.connect(self.select_table)
        self.tables.itemActivated.connect(self.select_table)
        side.addWidget(self.tables, 2)
        side.addWidget(QLabel(c.HISTORY))
        self.history = QListWidget()
        self.history.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.history.setAccessibleName(c.HISTORY)
        self.history.itemActivated.connect(self.recall)
        self.history.itemClicked.connect(self.recall)
        side.addWidget(self.history, 1)
        side.addWidget(QLabel("Local copies · originals unchanged"))
        self.split.addWidget(sidebar)
        self.stack = QStackedWidget()
        self.split.addWidget(self.stack)
        self.split.setSizes([260, 980])
        self.split.setStretchFactor(1, 1)
        landing = QWidget()
        lay = QVBoxLayout(landing)
        lay.addStretch()
        self.empty_title = QLabel(c.EMPTY)
        self.empty_title.setObjectName("hero")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_title.setWordWrap(True)
        lay.addWidget(self.empty_title)
        help_label = QLabel(c.EMPTY_HELP)
        help_label.setWordWrap(True)
        help_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(help_label)
        row = QHBoxLayout()
        row.addStretch()
        self.start_btn = self.button(c.NEW, self.new_project, True)
        row.addWidget(self.start_btn)
        row.addStretch()
        lay.addLayout(row)
        lay.addStretch()
        self.stack.addWidget(landing)
        workspace = QWidget()
        work = QVBoxLayout(workspace)
        work.setContentsMargins(16, 0, 0, 0)
        self.table_title = QLabel(c.NO_TABLE)
        self.table_title.setObjectName("section")
        work.addWidget(self.table_title)
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(c.FILTER)
        self.search.setAccessibleName(c.FILTER)
        self.search.returnPressed.connect(self.filter_table)
        self.find_btn = self.button("Find", self.filter_table)
        self.builder_btn = self.button("Build a query", self.build_query)
        top.addWidget(self.search, 1)
        top.addWidget(self.find_btn)
        top.addWidget(self.builder_btn)
        work.addLayout(top)
        self.tabs = QTabWidget()
        self.grid = QTableView()
        self.grid.setAccessibleName("Query results table")
        self.grid.setAlternatingRowColors(True)
        self.grid.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.grid.horizontalHeader().setSectionsClickable(True)
        self.grid.horizontalHeader().sectionClicked.connect(self.sort_result)
        self.grid.setModel(ResultModel())
        self.profile_grid = QTableView()
        self.profile_grid.setAccessibleName(c.PROFILE)
        self.profile_grid.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.profile_grid.setModel(ResultModel())
        chart_page = QWidget()
        chart_layout = QVBoxLayout(chart_page)
        chart_bar = QHBoxLayout()
        self.chart_kind = QComboBox()
        self.chart_kind.addItems(["Bar", "Line", "Points"])
        self.chart_kind.setAccessibleName("Chart type")
        self.chart_kind.currentTextChanged.connect(self.change_chart)
        chart_bar.addWidget(self.chart_kind)
        chart_bar.addWidget(QLabel(c.CHART_HELP), 1)
        self.chart = Chart()
        chart_layout.addLayout(chart_bar)
        chart_layout.addWidget(self.chart, 1)
        self.tabs.addTab(self.grid, c.PREVIEW)
        self.tabs.addTab(self.profile_grid, c.PROFILE)
        self.tabs.setTabEnabled(1, False)
        chart_scroll = QScrollArea()
        chart_scroll.setWidgetResizable(True)
        chart_scroll.setFrameShape(QFrame.Shape.NoFrame)
        chart_scroll.setAccessibleName("Chart content, scroll for labels in a short window")
        chart_scroll.setWidget(chart_page)
        self.tabs.addTab(chart_scroll, c.CHART)
        self.vertical_split = QSplitter(Qt.Orientation.Vertical)
        self.vertical_split.setChildrenCollapsible(False)
        self.vertical_split.setMinimumHeight(260)
        self.tabs.setMinimumHeight(70)
        self.tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Ignored)
        self.vertical_split.addWidget(self.tabs)
        query_panel = QWidget()
        query_panel.setMinimumHeight(190)
        query_layout = QVBoxLayout(query_panel)
        query_layout.setContentsMargins(0, 8, 0, 0)
        query_layout.addWidget(QLabel(c.QUERY))
        self.editor = QPlainTextEdit()
        self.editor.setAccessibleName(c.QUERY)
        self.editor.setPlaceholderText("SELECT * FROM your_table")
        self.editor.setMinimumHeight(70)
        self.editor.setFont(QFont("Menlo", 13))
        query_layout.addWidget(self.editor, 1)
        actions = QHBoxLayout()
        query_help = QLabel(c.QUERY_HELP)
        query_help.setWordWrap(True)
        actions.addWidget(query_help, 1)
        self.stop_btn = self.button(c.STOP, self.cancel)
        self.run_btn = self.button(c.RUN, self.run_query, True)
        self.export_btn = self.button(c.EXPORT, self.export_result)
        for b in (self.stop_btn, self.export_btn, self.run_btn):
            actions.addWidget(b)
        query_layout.addLayout(actions)
        self.vertical_split.addWidget(query_panel)
        self.vertical_split.setSizes([440, 200])
        work.addWidget(self.vertical_split, 1)
        self.page_controls = QWidget()
        pages = QHBoxLayout(self.page_controls)
        pages.setContentsMargins(0, 0, 0, 0)
        self.page_label = QLabel("No page yet")
        self.page_label.setAccessibleName("Result page range")
        self.previous_btn = self.button("Previous rows", lambda: self.change_page(-1))
        self.next_btn = self.button("Next rows", lambda: self.change_page(1))
        pages.addWidget(self.page_label, 1)
        pages.addWidget(self.previous_btn)
        pages.addWidget(self.next_btn)
        self.page_controls.setVisible(self.enhanced)
        work.addWidget(self.page_controls)
        self.provenance = QLabel("No result yet")
        self.provenance.setObjectName("muted")
        self.provenance.setWordWrap(True)
        self.provenance.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        work.addWidget(self.provenance)
        self.workspace = workspace
        self.stack.addWidget(workspace)
        self.status = QLabel(c.READY)
        self.status.setAccessibleName("Status")
        self.status.setWordWrap(True)
        outer.addWidget(self.status)
        self.error_details = QPlainTextEdit()
        self.error_details.setReadOnly(True)
        self.error_details.setAccessibleName("Technical error details")
        self.error_details.setFixedHeight(64)
        self.error_details.hide()
        outer.addWidget(self.error_details)

    def build_menu(self):
        file_menu = self.menuBar().addMenu("File")
        self.menu_actions = []
        for name, shortcut, handler in [(c.NEW, "Ctrl+N", self.new_project), (c.OPEN, "Ctrl+O", self.open_project),
                                        (c.IMPORT, "Ctrl+I", self.import_file), (c.RUN, "Ctrl+Return", self.run_query),
                                        (c.EXPORT, "Ctrl+E", self.export_result)]:
            action = QAction(name, self)
            action.setShortcut(QKeySequence(shortcut))
            action.triggered.connect(handler)
            file_menu.addAction(action)
            self.menu_actions.append(action)
        file_menu.addSeparator()
        quit_action = file_menu.addAction("Quit", self.close)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("About", self.about)
        help_menu.addAction(c.DETAILS, lambda: self.error_details.setVisible(not self.error_details.isVisible()))

    def about(self):
        dialog = QMessageBox(self)
        dialog.setWindowTitle("About " + self.windowTitle())
        dialog.setTextFormat(Qt.TextFormat.PlainText)
        dialog.setText(f"{self.windowTitle()} {self.version}\n\n{c.ABOUT}\n\n{c.PRIVACY}\n\n{c.LIMITS}\n\n{c.SOURCE}\n\nBuilt with DuckDB (MIT), Qt for Python (LGPLv3), openpyxl (MIT). See THIRD-PARTY-NOTICES.md for licences.")
        dialog.exec()

    def set_busy(self, value):
        self.busy = value
        if hasattr(self, "mark"):
            self.mark.set_state("working" if value else "idle")
        for widget in [self.new_btn, self.open_btn, self.start_btn]:
            widget.setEnabled(not value)
        for widget in [self.import_btn, self.tables, self.history, self.builder_btn, self.search, self.find_btn, self.run_btn]:
            widget.setEnabled(not value and self.project is not None)
        self.export_btn.setEnabled(not value and self.result is not None)
        self.stop_btn.setEnabled(value and self.project is not None)
        self.update_page_controls()
        self.editor.setReadOnly(value)
        for i, action in enumerate(self.menu_actions):
            needs = True if i < 2 else self.project is not None
            if i == 4:
                needs = self.result is not None
            action.setEnabled(not value and needs)
        self.find_btn.setEnabled(not value and bool(self.current_table))
        self.search.setEnabled(not value and bool(self.current_table))

    def set_status(self, text, error=False):
        self.status.setText(text)
        self.status.setAccessibleName(text)
        self.status.setAccessibleDescription("")
        self.status.setObjectName("statusError" if error else "status")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        QAccessible.updateAccessibility(QAccessibleAnnouncementEvent(self.status, text))

    def task(self, operation, success, failure=None):
        if self.busy:
            return
        self.set_busy(True)
        self.set_status(c.WORKING)
        self.status.setObjectName("status")
        self.error_details.hide()
        task = Task(operation)
        self.tasks.add(task)
        def done(value):
            self.tasks.discard(task)
            self.set_busy(False)
            try:
                success(value)
            except Exception as exc:
                self.failed(str(exc))
        def failed(reason):
            self.tasks.discard(task)
            self.set_busy(False)
            if failure:
                failure()
            self.failed(reason)
        task.signals.done.connect(done)
        task.signals.failed.connect(failed)
        self.pool.start(task)

    def failed(self, reason):
        if hasattr(self, "mark"):
            self.mark.set_state("error")
        self.set_status(c.ERROR, error=True)
        self.error_details.setPlainText(reason)
        self.error_details.show()

    def new_project(self):
        if self.busy:
            return
        path = QFileDialog.getExistingDirectory(self, c.NEW)
        if not path:
            return
        try:
            project = Project.create(Path(path))
            self.replace_project(project)
        except Exception as exc:
            self.failed(str(exc))

    def open_project(self):
        if self.busy:
            return
        path = QFileDialog.getExistingDirectory(self, c.OPEN)
        if path:
            self.load_project(Path(path))

    def load_project(self, path):
        try:
            self.replace_project(Project(path))
        except Exception as exc:
            self.failed(str(exc))

    def replace_project(self, project):
        self.save_draft()
        if self.project:
            self.project.close()
        self.project = project
        self.result = None
        self.result_sql = ""
        self.page_offset = 0
        self.current_table = ""
        self.tabs.setTabText(1, c.PROFILE)
        self.tabs.setTabEnabled(1, False)
        self.grid.setModel(ResultModel(parent=self.grid))
        self.profile_grid.setModel(ResultModel(parent=self.profile_grid))
        self.chart.set_result(None)
        self.project_title.setText(project.path.name)
        self.project_path.setText("Saved on this Mac")
        self.project_path.setToolTip(str(project.path))
        self.editor.setPlainText(project.draft)
        self.provenance.setText("No result yet")
        self.set_status(c.READY)
        self.stack.setCurrentIndex(1)
        self.set_busy(False)
        self.refresh_tables()
        self.refresh_history()
        self.table_title.setText("Choose a table or run your saved query" if self.table_info else c.NO_TABLE)

    def save_draft(self):
        if self.project and not self.busy:
            try:
                self.project.save_draft(self.editor.toPlainText())
            except Exception as exc:
                self.failed(str(exc))
        elif self.busy:
            self.draft_timer.start(700)

    def refresh_tables(self):
        self.table_info = self.project.tables()
        self.tables.clear()
        for table in self.table_info:
            item = QListWidgetItem(f"{table['name']}\n{table['rows']:,} rows · {len(table['columns'])} columns")
            item.setData(Qt.ItemDataRole.UserRole, table["name"])
            item.setToolTip(table.get("source", ""))
            self.tables.addItem(item)

    def refresh_history(self):
        self.history.clear()
        for entry in self.project.history()[:100]:
            sql = entry["sql"]
            item = QListWidgetItem(sql.replace("\n", " ")[:80])
            item.setData(Qt.ItemDataRole.UserRole, sql)
            item.setToolTip(sql)
            self.history.addItem(item)

    def recall(self, item):
        self.editor.setPlainText(item.data(Qt.ItemDataRole.UserRole))
        self.editor.setFocus()
        self.set_status("Query recalled. Check it, then press Run query.")

    def import_file(self):
        if not self.project or self.busy:
            return
        path, _ = QFileDialog.getOpenFileName(self, c.IMPORT, "", "Tables (*.csv *.xlsx *.json *.jsonl *.ndjson *.parquet)")
        if not path:
            return
        if self.enhanced and Path(path).suffix.lower() == ".xlsx":
            self.task(lambda: self.project.worksheet_names(Path(path)), lambda sheets: self.import_options(path, sheets))
        else:
            self.import_options(path)

    def import_options(self, path, sheets=None):
        options = ImportOptions(path, self, sheets=sheets)
        if options.exec() != QDialog.DialogCode.Accepted:
            return
        encoding, all_text = options.encoding.currentText(), options.text.isChecked()
        sheet = (options.sheet.currentText() if sheets is not None else options.sheet.text()).strip() or None
        settings = dict(sheet=sheet, encoding=encoding, all_text=all_text)
        if self.enhanced:
            def inspected(preview):
                from .plus_ui import ImportInspection
                dialog = ImportInspection(path, preview, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    self.commit_import(path, settings, preview["fingerprint"])
                else:
                    self.set_status("Import cancelled. Project and source unchanged.")
            self.task(lambda: self.project.inspect_file(Path(path), **settings), inspected)
        else:
            self.commit_import(path, settings)

    def commit_import(self, path, settings, fingerprint=None):
        def imported(table):
            self.refresh_tables()
            self.select_name(table)
        extra = {"expected_fingerprint": fingerprint} if fingerprint is not None else {}
        self.task(lambda: self.project.import_file(Path(path), **settings, **extra), imported)

    def select_table(self, item):
        self.select_name(item.data(Qt.ItemDataRole.UserRole))

    def select_name(self, name):
        if self.busy:
            return
        previous_editor = self.editor.toPlainText()
        self.editor.setPlainText(f"SELECT * FROM {ident(name)}")
        sql = self.editor.toPlainText()
        self.save_draft()
        def done(value):
            result, profile = value
            self.current_table = name
            self.search.clear()
            self.show_result(result, sql)
            self.table_title.setText(f"Source table: {name}")
            self.search.setEnabled(True)
            self.find_btn.setEnabled(True)
            self.tabs.setTabText(1, f"Profile · {name[:24]}")
            self.tabs.setTabEnabled(1, True)
            columns = ["Column", "Type", "Missing", "Distinct", "Minimum", "Maximum"]
            rows = [[p.get(k) for k in ["name", "type", "nulls", "distinct", "min", "max"]] for p in profile]
            self.profile_grid.setModel(ResultModel(columns, rows, parent=self.profile_grid))
            self.profile_grid.resizeColumnsToContents()
        def restore():
            self.editor.setPlainText(previous_editor)
            for index in range(self.tables.count()):
                item = self.tables.item(index)
                if item.data(Qt.ItemDataRole.UserRole) == self.current_table:
                    self.tables.setCurrentItem(item)
                    return
            self.tables.clearSelection()
        self.task(lambda: (self.project.query(sql), self.project.profile(name)), done, restore)

    def filter_table(self):
        if not self.project or not self.current_table or self.busy:
            return
        table = next(t for t in self.table_info if t["name"] == self.current_table)
        # Literal substring search. SQL LIKE wildcards are escaped explicitly.
        term = self.search.text().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_").replace("'", "''")
        predicates = [f"CAST({ident(col['name'])} AS VARCHAR) ILIKE '%{term}%' ESCAPE '\\'" for col in table["columns"]]
        sql = f"SELECT * FROM {ident(self.current_table)}"
        if term:
            sql += "\nWHERE " + " OR ".join(predicates)
        self.editor.setPlainText(sql)
        self.run_query()

    def sort_result(self, section):
        if self.busy or not self.result:
            return
        self.sort_order = (Qt.SortOrder.DescendingOrder if self.sort_section == section and self.sort_order == Qt.SortOrder.AscendingOrder else Qt.SortOrder.AscendingOrder)
        self.sort_section = section
        direction = "DESC" if self.sort_order == Qt.SortOrder.DescendingOrder else "ASC"
        sql = f"SELECT * FROM ({self.sort_source_sql.rstrip().rstrip(';')}) AS result ORDER BY {section+1} {direction} NULLS LAST"
        self.editor.setPlainText(sql)
        self.run_query(preserve_sort=True)

    def build_query(self):
        if not self.table_info or self.busy:
            return
        builder = Builder(self.table_info, self)
        if builder.exec() == QDialog.DialogCode.Accepted:
            self.editor.setPlainText(builder.sql())
            self.editor.setFocus()

    def run_query(self, preserve_sort=False):
        if not self.project or self.busy:
            return
        sql = self.editor.toPlainText().strip()
        if not sql:
            self.set_status("Write a read-only query or select a table first.")
            return
        self.save_draft()
        self.task(lambda: self.project.query(sql), lambda result: self.show_result(result, sql, preserve_sort=preserve_sort))

    def show_result(self, result, sql, preserve_sort=False):
        if hasattr(self, "mark"):
            self.mark.set_state("success")
        self.result, self.result_sql = result, sql
        self.page_offset = getattr(result, "offset", 0)
        if not preserve_sort:
            self.sort_section = None
            self.sort_source_sql = sql
        self.table_title.setText("Query results")
        self.grid.setModel(ResultModel(result.columns, result.rows, result.types, self.grid, offset=self.page_offset))
        self.grid.horizontalHeader().setSortIndicatorShown(self.sort_section is not None)
        if self.sort_section is not None:
            self.grid.horizontalHeader().setSortIndicator(self.sort_section, self.sort_order)
        self.grid.resizeColumnsToContents()
        for i in range(len(result.columns)):
            self.grid.setColumnWidth(i, min(320, max(100, self.grid.columnWidth(i))))
        self.chart.set_result(result)
        self.provenance.setText(f"{result.total:,} result rows · showing {len(result.rows):,} · {len(result.columns)} columns · {result.elapsed:.3f}s\nExport reruns this successful query with all matching rows. Generated values may change. Grid values have no display rounding.")
        self.provenance.setToolTip(sql)
        if self.enhanced:
            self.provenance.setText(self.provenance.text() + "\nPages rerun the query. Use ORDER BY for an order; changing/generated values may move between pages.")
        self.update_page_controls()
        self.refresh_history()
        self.export_btn.setEnabled(True)
        self.set_status(f"Query finished. {result.total:,} result rows. Originals unchanged.")

    def update_page_controls(self):
        if not hasattr(self, "previous_btn"):
            return
        ready = self.enhanced and not self.busy and self.result is not None
        self.previous_btn.setEnabled(ready and self.page_offset > 0)
        self.next_btn.setEnabled(ready and self.page_offset + len(self.result.rows) < self.result.total)
        if self.result:
            start = self.page_offset + 1 if self.result.rows else 0
            end = self.page_offset + len(self.result.rows)
            self.page_label.setText(f"Rows {start:,}–{end:,} of {self.result.total:,}")
        else:
            self.page_label.setText("No page yet")

    def change_page(self, direction):
        if not self.enhanced or self.busy or self.result is None:
            return
        offset = self.page_offset + direction * 1000
        if offset < 0 or offset >= self.result.total:
            return
        sql = self.result_sql
        self.task(lambda: self.project.query(sql, offset=offset, record_history=False),
                  lambda result: self.show_result(result, sql, preserve_sort=True))

    def change_chart(self, kind):
        self.chart.kind = kind
        self.chart.update()

    def export_result(self):
        if self.busy or not self.result or not self.project:
            return
        path, selected = QFileDialog.getSaveFileName(self, c.EXPORT, "result.csv", "CSV (*.csv);;Excel (*.xlsx);;JSON (*.json);;Parquet (*.parquet)")
        if not path:
            return
        extension = {"CSV (*.csv)": "csv", "Excel (*.xlsx)": "xlsx", "JSON (*.json)": "json", "Parquet (*.parquet)": "parquet"}[selected]
        if not Path(path).suffix:
            path += "." + extension
        if Path(path).suffix.lower() != "." + extension:
            self.failed("Choose a filename with the selected format's extension.")
            return
        sql = self.result_sql
        self.task(lambda: self.project.export(sql, Path(path), extension), lambda n: self.set_status(f"Exported {n:,} rows to {Path(path).name}."))

    def cancel(self):
        if self.project and self.busy:
            self.project.cancel()
            self.set_status("Stop requested. Waiting for the operation to finish safely.")

    def closeEvent(self, event):
        if self.busy:
            self.cancel()
            self.set_status("Waiting for work to stop. Close the window again when it has finished.")
            event.ignore()
            return
        self.save_draft()
        if self.project:
            self.project.close()
        self.pool.clear()
        self.pool.waitForDone(200)
        event.accept()


def main(default_edition="baseline", default_enhanced=False):
    parser = argparse.ArgumentParser(description=c.ABOUT)
    parser.add_argument("--edition", choices=["baseline", "pip"], default=default_edition)
    extras = parser.add_mutually_exclusive_group()
    extras.add_argument("--enhanced", action="store_true", dest="enhanced", help="Enable Plus import inspection and result pages")
    extras.add_argument("--core", action="store_false", dest="enhanced", help="Use Core feature scope")
    parser.set_defaults(enhanced=default_enhanced)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--smoke", type=Path, help="Run a synthetic packaged-engine verification and write JSON, without desktop interaction")
    args = parser.parse_args()
    if args.smoke:
        from .smoke import run
        run(args.smoke, args.edition, enhanced=args.enhanced)
        return
    app = QApplication(sys.argv[:1])
    app.setApplicationName((c.BASELINE if args.edition == "baseline" else c.APP) + (" Plus" if args.enhanced else ""))
    app.setOrganizationName("Pip Tables")
    window = Window(args.edition, args.project, enhanced=args.enhanced)
    window.show()
    sys.exit(app.exec())
