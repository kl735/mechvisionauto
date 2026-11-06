# coding: utf-8
"""主窗口及核心区域 Page Object 的 smoke test。"""

from pages.main_window_page import MainWindowPage


def test_main_window_core_regions(main_page: MainWindowPage) -> None:
    """验证主窗口、工程列表、步骤库和工程编辑区均可定位。"""
    assert main_page.exists(), "没有定位到 Mech-Vision 主窗口"
    assert main_page.project_list.dock().exists(), "没有定位到工程列表"
    assert main_page.project_list.tree().exists(), "没有定位到工程树"
    assert main_page.step_library.dock().exists(), "没有定位到步骤库"
    assert main_page.project_editor.dock().exists(), "没有定位到工程编辑区"
    assert main_page.project_editor.canvas().exists(), "没有定位到流程画布"
