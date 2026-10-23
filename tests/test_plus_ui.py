"""Plus controls preserve Core scope and paged recovery semantics."""
from PySide6.QtWidgets import QComboBox
from pip_tables.engine import Project
from pip_tables.ui import Window, ImportOptions
from pip_tables.plus_ui import ImportInspection
from test_ui import app, settle


def test_core_has_no_plus_controls_and_plus_paging_recovers(app, tmp_path, monkeypatch):
    core = Window('baseline')
    assert core.page_controls.isHidden() and not core.enhanced
    core.close()
    p = Project.create(tmp_path/'project')
    source = tmp_path/'many.csv'
    source.write_text('id,value\n' + ''.join(f'{i},value{i}\n' for i in range(2101)))
    p.import_file(source)
    w = Window('pip', enhanced=True)
    w.replace_project(p)
    w.resize(900,720)
    w.show()
    w.editor.setPlainText('SELECT * FROM many ORDER BY id')
    w.run_query();settle(app,w)
    assert w.page_offset == 0 and w.next_btn.isEnabled() and not w.previous_btn.isEnabled()
    count = len(p.history())
    w.change_page(1);settle(app,w)
    assert w.page_offset == 1000 and w.result.rows[0][0] == 1000
    assert len(p.history()) == count
    w.change_page(1);settle(app,w)
    assert len(w.result.rows) == 101 and w.result.rows[-1][0] == 2100
    assert '2,001–2,101' in w.page_label.text() and not w.next_btn.isEnabled()
    assert w.grid.model().headerData(0,__import__('PySide6.QtCore',fromlist=['Qt']).Qt.Orientation.Vertical) == '2001'
    old_query=p.query
    monkeypatch.setattr(p,'query',lambda *a,**k: (_ for _ in ()).throw(ValueError('page failed')))
    w.change_page(-1);settle(app,w)
    assert w.page_offset == 2000 and w.result.rows[0][0] == 2000
    assert w.previous_btn.isEnabled() and not w.next_btn.isEnabled()
    monkeypatch.setattr(p,'query',old_query)
    w.editor.setPlainText('SELECT * FROM many ORDER BY id DESC')
    w.run_query();settle(app,w)
    assert w.page_offset == 0 and w.result.rows[0][0] == 2100
    assert 'Pages rerun the query' in w.provenance.text()
    run=w.run_btn.mapTo(w.workspace,w.run_btn.rect().bottomRight())
    assert run.y() < w.workspace.height() and run.x() < w.workspace.width()
    w.close()


def test_import_inspection_and_sheet_picker_are_read_only(app, tmp_path):
    w=Window('baseline',enhanced=True)
    options=ImportOptions(tmp_path/'book.xlsx',w,sheets=['Sales','Other'])
    assert isinstance(options.sheet,QComboBox)
    assert options.sheet.currentText()=='Sales' and options.sheet.count()==2
    preview={'columns':[{'name':'id','type':'BIGINT'}],'rows':[(1,),(2,)],'total':2,'sheets':[],'fingerprint':'sha256:test'}
    dialog=ImportInspection('sample.csv',preview,w)
    assert dialog.grid.model().rowCount()==2
    assert dialog.grid.model().columns==['id · BIGINT']
    dialog.reject()
    assert w.project is None
    w.close()
