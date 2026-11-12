# coding: utf-8
"""验证 Python 包管理工具页面对象的方法可用性。"""

from pages.main_window_page import MainWindowPage
from pages.python_package_manager_page import PythonPackageManagerPage


def test_python_package_manager_locators(
    main_page: MainWindowPage,
) -> None:
    """打开 Python 包管理工具并验证核心控件定位方法。"""
    try:
        opened_page = PythonPackageManagerPage.wait_for_open(
            main_page.handle,
            timeout=0.5,
        )
        opened_page.close()
    except TimeoutError:
        pass

    manager_page = main_page.title_bar.open_python_package_manager()
    try:
        info = manager_page.element_info
        assert info.name == PythonPackageManagerPage.TITLE
        assert info.class_name == PythonPackageManagerPage.CLASS_NAME
        assert (
            info.automation_id
            == PythonPackageManagerPage.AUTOMATION_ID
        )
        assert info.control_type == PythonPackageManagerPage.CONTROL_TYPE

        assert manager_page.python_interpreter_label().window_text().strip()
        assert manager_page.interpreter_combo_box().is_visible()
        assert manager_page.copy_path_button().is_visible()

        assert manager_page.installed_packages_label().is_visible()
        assert manager_page.installed_packages_table().is_visible()
        assert manager_page.installed_table_headers() == [
            "名称",
            "版本",
            "操作",
        ]
        assert manager_page.import_button().is_visible()
        assert manager_page.export_button().is_visible()

        assert manager_page.available_packages_label().is_visible()
        assert manager_page.package_name_edit().is_visible()
        assert manager_page.search_button().is_visible()
        assert manager_page.no_content_label().window_text().strip() == (
            "暂无可用"
        )

        assert manager_page.specify_source_checkbox().is_visible()
        assert manager_page.source_combo_box().is_visible()
        assert not manager_page.source_combo_box().is_enabled()
        assert manager_page.install_button().is_visible()
        assert not manager_page.install_button().is_enabled()

        assert manager_page.close_button().is_visible()
    finally:
        if manager_page.is_visible():
            manager_page.close()
