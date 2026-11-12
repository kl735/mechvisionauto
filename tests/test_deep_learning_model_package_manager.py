# coding: utf-8
"""深度学习模型包管理工具的业务逻辑测试。"""

import re
from pathlib import Path

import pytest

from pages.deep_learning_model_package_manager_page import (
    DeepLearningModelPackageManagerPage,
    ModelPackageMessageBox,
)
from pages.main_window_page import MainWindowPage


TEST_DATA_DIR = Path(
    r"C:\Users\mech-mind\Desktop\DL_PACKAGE_MODEL_TEST_DATA"
)
VALID_MODEL_PACKAGE = TEST_DATA_DIR / "TextDet_Super_Model.dlkpack"
MODEL_NAME = VALID_MODEL_PACKAGE.stem
EXPECTED_HEADERS = [
    "缓存模型包名称",
    "使用工程",
    "模型包类型",
    "运行模式",
    "硬件类型",
    "模型效率",
    "模型包状态",
    "操作",
]


def close_opened_manager(main_page: MainWindowPage) -> None:
    """关闭上一次测试可能遗留的模型包管理窗口。"""
    try:
        page = DeepLearningModelPackageManagerPage.wait_for_open(
            main_page.handle,
            timeout=0.5,
        )
        page.close()
    except TimeoutError:
        pass


@pytest.fixture
def model_manager_page(
    main_page: MainWindowPage,
) -> DeepLearningModelPackageManagerPage:
    """每个测试打开一个模型包管理窗口并在结束后关闭。"""
    close_opened_manager(main_page)
    page = (
        main_page.title_bar
        .open_deep_learning_model_package_manager()
    )
    yield page
    if page.is_visible():
        page.close()


def test_memory_usage_and_table_schema(
    model_manager_page: DeepLearningModelPackageManagerPage,
) -> None:
    """显存占用率应合法，表格列应完整且不重复。"""
    memory_text = (
        model_manager_page.memory_usage_label()
        .window_text()
        .strip()
    )
    match = re.fullmatch(
        r"显存占用率：\s*(\d+)%\s*"
        r"\(([\d.]+)GB/([\d.]+)GB\)",
        memory_text,
    )
    assert match is not None, f"显存占用率格式错误：{memory_text!r}"

    percent = int(match.group(1))
    used_memory = float(match.group(2))
    total_memory = float(match.group(3))
    assert 0 <= percent <= 100
    assert 0 <= used_memory <= total_memory
    assert total_memory > 0
    calculated_percent = used_memory / total_memory * 100
    assert abs(percent - calculated_percent) <= 2

    headers = model_manager_page.table_header_names()
    assert headers == EXPECTED_HEADERS
    assert len(headers) == len(set(headers))


def test_manager_can_reopen(main_page: MainWindowPage) -> None:
    """模型包管理窗口关闭后应能再次打开。"""
    close_opened_manager(main_page)
    first_page = (
        main_page.title_bar
        .open_deep_learning_model_package_manager()
    )
    assert first_page.is_visible()
    first_page.close()
    assert not first_page.is_visible()

    second_page = (
        main_page.title_bar
        .open_deep_learning_model_package_manager()
    )
    try:
        assert second_page.is_visible()
        assert second_page.title_label().window_text().strip() == (
            "深度学习模型包管理"
        )
    finally:
        if second_page.is_visible():
            second_page.close()


def test_import_button_opens_file_dialog(
    model_manager_page: DeepLearningModelPackageManagerPage,
) -> None:
    """点击导入按钮后应打开可选择测试模型包的文件窗口。"""
    assert TEST_DATA_DIR.is_dir()
    assert VALID_MODEL_PACKAGE.is_file()

    dialog = model_manager_page.open_import_file_dialog()
    assert dialog.window.element_info.name == "选择文件"
    assert dialog.file_name_edit().is_visible()
    assert dialog.open_button().is_visible()
    assert dialog.cancel_button().is_visible()
    dialog.cancel()


def test_import_duplicate_and_delete_model_package(
    model_manager_page: DeepLearningModelPackageManagerPage,
) -> None:
    """验证有效导入、重复导入提示及删除模型包完整流程。"""
    assert VALID_MODEL_PACKAGE.is_file()

    if model_manager_page.has_model(MODEL_NAME):
        cleanup_dialog = (
            model_manager_page.open_delete_model_dialog(MODEL_NAME)
        )
        cleanup_dialog.confirm()
        model_manager_page.wait_for_model(
            MODEL_NAME,
            present=False,
            timeout=30,
        )

    before_names = model_manager_page.model_names()
    try:
        model_manager_page.import_model_package(VALID_MODEL_PACKAGE)
        model_manager_page.wait_for_model(
            MODEL_NAME,
            present=True,
            timeout=30,
        )
        after_names = model_manager_page.model_names()
        assert MODEL_NAME in after_names
        assert len(after_names) == len(before_names) + 1

        model_manager_page.import_model_package(VALID_MODEL_PACKAGE)
        duplicate_dialog = ModelPackageMessageBox.wait_for_open(
            model_manager_page.handle,
            timeout=10,
        )
        duplicate_texts = duplicate_dialog.text_contents()
        assert "导入失败" in duplicate_texts
        assert any(
            "已导入同名的模型包" in text
            for text in duplicate_texts
        )
        duplicate_dialog.confirm()
        assert model_manager_page.model_names().count(MODEL_NAME) == 1

        delete_dialog = (
            model_manager_page.open_delete_model_dialog(MODEL_NAME)
        )
        delete_texts = delete_dialog.text_contents()
        assert any(
            f"是否确认删除模型包“{MODEL_NAME}”" in text
            for text in delete_texts
        )
        delete_dialog.confirm()
        model_manager_page.wait_for_model(
            MODEL_NAME,
            present=False,
            timeout=30,
        )
        assert MODEL_NAME not in model_manager_page.model_names()
    finally:
        if model_manager_page.has_model(MODEL_NAME):
            cleanup_dialog = (
                model_manager_page.open_delete_model_dialog(MODEL_NAME)
            )
            cleanup_dialog.confirm()
            model_manager_page.wait_for_model(
                MODEL_NAME,
                present=False,
                timeout=30,
            )
