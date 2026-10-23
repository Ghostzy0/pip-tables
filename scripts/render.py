"""Reproducible offscreen source renders and geometry, not native acceptance."""
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import json
import sys
import tempfile
import time
from pathlib import Path
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pip_tables.engine import Project
from pip_tables.ui import Window
from pip_tables.theme import apply

root = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]) if len(sys.argv) > 1 else root / ".local-evidence" / "renders"
out.mkdir(parents=True, exist_ok=True)
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(out / "preferences"))
app = QApplication([])
measurements = []
with tempfile.TemporaryDirectory(prefix="tables-render-") as temporary:
    p = Project.create(Path(temporary) / "Sample orders")
    p.import_file(root / "examples" / "orders.csv")
    p.import_file(root / "examples" / "customers.json")
    window = Window("pip", enhanced="--enhanced" in sys.argv)
    window.replace_project(p)
    window.show()
    sql = "SELECT region, SUM(CAST(amount AS DECIMAL(18,2))) AS revenue FROM orders GROUP BY region ORDER BY region"
    window.editor.setPlainText(sql)
    window.run_query()
    deadline = time.monotonic()+10
    while window.busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(.01)
    assert window.result.rows == [("North", __import__('decimal').Decimal('555.75')), ("South", __import__('decimal').Decimal('419.75')), ("West", __import__('decimal').Decimal('408.75'))]
    for name, dark, width, height in [("Paper",False,1440,900),("Paper",True,1280,720),("Oat",False,1280,720),("Harbour",True,1280,720),("Paper",False,900,720)]:
        apply(window, name, dark)
        window.resize(width,height)
        app.processEvents()
        file = f"{name.lower()}-{'dark' if dark else 'light'}-{width}x{height}.png"
        window.grab().save(str(out/file))
        controls = {}
        for key in ['new_btn','open_btn','import_btn','run_btn','export_btn','stop_btn','editor','grid','provenance']:
            widget = getattr(window,key)
            controls[key] = {'x':widget.x(),'y':widget.y(),'w':widget.width(),'h':widget.height(),'visible':widget.isVisible()}
        measurements.append({'file':file,'window':[window.width(),window.height()],'controls':controls})
    window.tabs.setCurrentIndex(2)
    app.processEvents()
    window.grab().save(str(out/'chart.png'))
    window.editor.setPlainText('SELECT missing FROM orders')
    window.run_query()
    while window.busy:
        app.processEvents();time.sleep(.01)
    window.grab().save(str(out/'error.png'))
    if window.enhanced:
        from pip_tables.plus_ui import ImportInspection
        preview = p.inspect_file(root / "examples" / "orders.csv")
        dialog = ImportInspection("orders.csv", preview, window)
        dialog.show();app.processEvents()
        dialog.grab().save(str(out/'import-inspection.png'))
        dialog.reject()
    window.close()
(out/'geometry.json').write_text(json.dumps(measurements,indent=2)+'\n')
print(out)
