"""Plus-only bounded import inspection. No changes until explicit Import."""
from pathlib import Path
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QTableView, QVBoxLayout
from .ui import ResultModel


class ImportInspection(QDialog):
    def __init__(self, path, preview, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Inspect import · " + Path(path).name)
        self.resize(760, 480)
        layout = QVBoxLayout(self)
        heading = QLabel(f"{preview['total']:,} rows · {len(preview['columns'])} columns · first {len(preview['rows'])} rows")
        heading.setWordWrap(True)
        layout.addWidget(heading)
        help_text = QLabel("These are the inferred types used by import. Cancel to choose another encoding, sheet or CSV text option. Nothing has been added to your project.")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)
        self.grid = QTableView()
        self.grid.setAccessibleName("Import inspection rows and inferred types")
        columns = [item['name'] for item in preview['columns']]
        types = [item['type'] for item in preview['columns']]
        self.grid.setModel(ResultModel([f"{name} · {kind}" for name, kind in zip(columns, types)], preview['rows'], types, self.grid))
        self.grid.resizeColumnsToContents()
        layout.addWidget(self.grid, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Import inspected file")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
