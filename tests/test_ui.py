"""Headless Qt integration tests. These do not assert native desktop acceptance."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import time
import pytest
from PySide6.QtWidgets import QApplication, QFileDialog

from pip_tables.engine import Project
from pip_tables.ui import Window, Builder, ResultModel


@pytest.fixture(scope="session")
def app():
    return QApplication.instance() or QApplication([])


def settle(app, window):
    until = time.monotonic()+20
    while window.busy and time.monotonic() < until:
        app.processEvents()
        time.sleep(.01)
    app.processEvents()
    assert not window.busy


def test_window_query_filter_error_history_reopen(app, tmp_path):
    project = Project.create(tmp_path / "project")
    source = tmp_path / "data.csv"
    source.write_text("name,amount\nAlice,1.5\nBob,2.5\nAlice,3.5\n")
    table = project.import_file(source)
    w = Window("baseline")
    w.replace_project(project)
    w.select_name(table)
    settle(app, w)
    assert w.result.total == 3
    assert w.profile_grid.model().rowCount() == 2
    w.search.setText("Alice")
    w.filter_table()
    settle(app, w)
    assert w.result.total == 2
    sql = w.result_sql
    w.editor.setPlainText("SELECT missing FROM data")
    w.run_query()
    settle(app, w)
    assert w.result.total == 2
    assert w.result_sql == sql
    assert w.error_details.toPlainText()
    assert w.history.count() >= 1
    assert w.export_btn.isEnabled()
    w.editor.setPlainText("SELECT SUM(amount) FROM data")
    w.save_draft()
    w.close()
    reopened = Project(tmp_path / "project")
    assert reopened.draft == "SELECT SUM(amount) FROM data"


def test_recipes_and_literal_filter(app, tmp_path):
    project = Project.create(tmp_path / "project")
    source = tmp_path / "data.csv"
    source.write_text("name,amount\na%b,1\na_b,2\naZZb,3\n")
    table = project.import_file(source)
    w = Window()
    w.replace_project(project)
    w.select_name(table)
    settle(app, w)
    for text in ["%", "_", "'", "\\"]:
        w.search.setText(text)
        w.filter_table()
        settle(app, w)
        assert w.result.total == (1 if text in ["%", "_"] else 0)
    b = Builder(w.table_info, w)
    b.column.setCurrentText("amount")
    b.group.setCurrentText("name")
    assert project.query(b.sql()).total == 3
    b.operation.setCurrentText("Change a column type")
    assert project.query(b.sql()).total == 3
    b.operation.setCurrentText("Join")
    b.right_column.setCurrentText("amount")
    assert project.query(b.sql()).total == 3
    b.operation.setCurrentText("Pivot")
    assert project.query(b.sql()).total >= 1
    w.close()


def test_empty_state_and_accessible_names(app):
    w = Window()
    assert w.stack.currentIndex() == 0
    assert not w.import_btn.isEnabled()
    assert not w.run_btn.isEnabled()
    assert not w.export_btn.isEnabled()
    assert w.editor.accessibleName()
    assert w.grid.accessibleName()
    assert w.stop_btn.accessibleName()
    w.close()


def test_all_pip_theme_pairs_have_readable_contrast_and_instant_state(app, tmp_path):
    from PySide6.QtCore import QSettings
    from pip_tables.theme import ANCHORS, tokens, apply
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)
    QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(tmp_path))
    def luminance(color):
        values = [int(color[i:i+2],16)/255 for i in (1,3,5)]
        rgb = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values]
        return sum(a*b for a,b in zip(rgb,[.2126,.7152,.0722]))
    def contrast(a,b):
        x,y = sorted([luminance(a),luminance(b)])
        return (y+.05)/(x+.05)
    original = app.palette()
    w=Window("pip")
    for name in ANCHORS:
        for dark in [False,True]:
            t=tokens(name,dark)
            assert contrast(t['text'],t['canvas']) >= 4.5
            assert contrast(t['muted'],t['surface']) >= 4.5
            assert contrast(t['control'],t['surface']) >= 3
            apply(w,name,dark)
            w.set_busy(True)
            assert w.mark.state == 'working'
            w.set_busy(False)
            assert w.mark.state == 'idle'
    w.close()
    app.setPalette(original)


def test_recovery_selection_sort_and_short_layout(app, tmp_path, monkeypatch):
    project=Project.create(tmp_path/'p')
    a=tmp_path/'one.csv';a.write_text('key,value\nB,2\nA,1\n')
    b=tmp_path/'two.csv';b.write_text('key,value\nC,3\n')
    project.import_file(a);project.import_file(b)
    w=Window('pip');w.replace_project(project);w.resize(900,720);w.show()
    w.select_name('one');settle(app,w)
    w.sort_result(0);settle(app,w)
    assert w.result.rows[0][0]=='A'
    assert w.grid.horizontalHeader().isSortIndicatorShown()
    w.sort_result(0);settle(app,w)
    assert w.result.rows[0][0]=='B'
    w.editor.setPlainText('SELECT bad FROM one');w.run_query();settle(app,w)
    assert w.status.objectName()=='statusError'
    app.processEvents()
    editor=w.editor.geometry()
    run=w.run_btn.geometry()
    assert editor.bottom() < run.top()
    position=w.run_btn.mapTo(w.workspace,w.run_btn.rect().bottomRight())
    assert position.y() <= w.workspace.height()
    assert position.x() <= w.workspace.width()
    old_profile=project.profile
    monkeypatch.setattr(project,'profile',lambda name: (_ for _ in ()).throw(ValueError('profile failed')))
    w.select_name('two');settle(app,w)
    assert w.current_table=='one' and w.result.rows[0][0]=='B'
    assert 'two' not in w.table_title.text()
    assert 'two' not in w.editor.toPlainText()
    monkeypatch.setattr(project,'profile',old_profile)
    w.editor.setPlainText('SELECT * FROM one');w.run_query();settle(app,w)
    assert w.status.objectName()=='status'
    assert not w.status.accessibleDescription()
    assert w.status.accessibleName()==w.status.text()
    assert not w.grid.horizontalHeader().isSortIndicatorShown()
    assert w.table_title.text()=='Query results'
    w.tabs.setCurrentIndex(2);app.processEvents()
    assert w.chart.height()>=180
    w.close()


def test_original_completion_motion_stops_and_honours_reduced_motion(app, monkeypatch):
    import pip_tables.theme as theme
    from PySide6.QtCore import QAbstractAnimation
    from PySide6.QtTest import QTest
    pip=theme.PipMark()
    pip.set_motion(True)
    monkeypatch.setattr(theme,'reduced_motion',lambda: True)
    pip.set_state('success')
    assert pip.animation.state()==QAbstractAnimation.State.Stopped
    monkeypatch.setattr(theme,'reduced_motion',lambda: False)
    pip.set_state('success')
    assert pip.animation.state()==QAbstractAnimation.State.Running
    QTest.qWait(320)
    assert pip.animation.state()==QAbstractAnimation.State.Stopped
    assert pip.nod==0
    pip.set_state('success')
    pip.set_state('working')
    assert pip.animation.state()==QAbstractAnimation.State.Stopped
    pip.set_state('success');pip.set_motion(False)
    assert pip.animation.state()==QAbstractAnimation.State.Stopped
