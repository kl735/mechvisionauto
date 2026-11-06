# coding: utf-8
"""AI 分类配置向导第一批稳定 UIA 自动化用例。"""

from __future__ import annotations

import time

from pages.ai_classification_config_page import AiClassificationConfigPage
from pages.message_box_page import MessageBoxPage


def test_M85028_0673_model_list_is_visible(
    ai_classification_page: AiClassificationConfigPage,
) -> None:
    """模型列表能够显示，并且至少存在一个模型。"""
    page = ai_classification_page

    assert page.model_list().is_visible()
    assert len(page.model_items()) >= 1


def test_M85028_0674_create_model(
    ai_classification_page: AiClassificationConfigPage,
) -> None:
    """点击“新建”后，模型数量增加一个。"""
    page = ai_classification_page
    original_count = len(page.model_items())
    created = False

    try:
        before_count, after_count = page.create_model()
        created = True
        assert before_count == original_count
        assert after_count == original_count + 1
    finally:
        if created:
            _, restored_count, _ = page.delete_model(-1)
            assert restored_count == original_count


def test_M85028_0677_rename_model_confirm(
    ai_classification_page: AiClassificationConfigPage,
) -> None:
    """输入新名称并点击确定后，模型名称修改成功。"""
    page = ai_classification_page
    original_count = len(page.model_items())
    created = False
    expected_name = f"自动化Test_模型-{time.time_ns()}"

    try:
        page.create_model()
        created = True
        page.set_model_name(expected_name, model_index=-1)

        deadline = time.monotonic() + page.timeout
        while time.monotonic() < deadline:
            if page.model_name(-1) == expected_name:
                break
            time.sleep(0.2)

        assert page.model_name(-1) == expected_name
    finally:
        if created:
            page.click_model_menu(-1, "删除")
            message_box = MessageBoxPage.wait_for_open(
                page.handle,
                timeout=page.timeout,
            )
            message_box.confirm()

            deadline = time.monotonic() + page.timeout
            while time.monotonic() < deadline:
                if page.model_count() == original_count:
                    break
                time.sleep(0.2)

            assert page.model_count() == original_count


def test_M85028_0677_rename_model_cancel(
    ai_classification_page: AiClassificationConfigPage,
) -> None:
    """输入新名称并点击取消后，模型名称保持不变。"""
    page = ai_classification_page
    original_count = page.model_count()
    created = False
    new_name = f"不应保存的名称-{time.time_ns()}"

    try:
        page.create_model()
        created = True
        original_name = page.model_name(-1)

        page.cancel_model_rename(new_name, model_index=-1)

        assert page.model_name(-1) == original_name
        assert page.model_name(-1) != new_name
    finally:
        if created:
            page.click_model_menu(-1, "删除")
            message_box = MessageBoxPage.wait_for_open(
                page.handle,
                timeout=page.timeout,
            )
            message_box.confirm()

            deadline = time.monotonic() + page.timeout
            while time.monotonic() < deadline:
                if page.model_count() == original_count:
                    break
                time.sleep(0.2)

            assert page.model_count() == original_count


def test_M85028_0678_0679_delete_model_confirm(
    ai_classification_page: AiClassificationConfigPage,
) -> None:
    """删除模型时显示确认提示，确认后模型数量减少。"""
    page = ai_classification_page
    original_count = len(page.model_items())
    created = False

    try:
        _, created_count = page.create_model()
        created = True
        before_count, after_count, message = page.delete_model(-1)
        created = False

        assert before_count == created_count
        assert after_count == original_count
        assert "确认删除" in message
        assert "无法恢复" in message
    finally:
        if created:
            page.delete_model(-1)


def test_M85028_0680_delete_model_cancel(
    ai_classification_page: AiClassificationConfigPage,
) -> None:
    """在删除确认框点击取消后，模型数量保持不变。"""
    page = ai_classification_page
    before_count = len(page.model_items())

    page.click_model_menu(-1, "删除")
    message_box = MessageBoxPage.wait_for_open(
        page.handle,
        timeout=page.timeout,
    )
    assert "确认删除" in message_box.message()
    message_box.cancel()

    assert len(page.model_items()) == before_count


def test_ai_classification_core_controls(
    ai_classification_page: AiClassificationConfigPage,
) -> None:
    """验证 AI 分类默认配置页的核心控件均可定位。"""
    page = ai_classification_page

    assert page.target_region_edit_button().is_visible()
    assert page.ok_label_button().is_visible()
    assert page.ng_label_button().is_visible()
    assert page.advanced_settings_checkbox().is_visible()
    assert page.confidence_spinner().is_visible()
    assert page.heatmap_checkbox().is_visible()
    assert page.judgment_combo().is_visible()
    assert page.single_capture_button().is_visible()
    assert page.continuous_capture_checkbox().is_visible()


def test_M85028_0700_open_target_region_editor(
    ai_classification_page: AiClassificationConfigPage,
) -> None:
    """点击编辑后进入目标区域页面，取消后返回默认配置页。"""
    page = ai_classification_page
    editor = page.open_target_region_editor()

    try:
        assert editor.rectangle_button().is_visible()
        assert editor.circle_button().is_visible()
        assert editor.mask_region_button().is_visible()
        assert editor.save_button().is_visible()
        assert editor.cancel_button().is_visible()
    finally:
        editor.cancel()

    assert page.target_region_edit_button().is_visible()


def test_create_named_copy_from_any_model(
    ai_classification_page: AiClassificationConfigPage,
) -> None:
    """为任意模型创建指定名称的副本，并在测试结束后清理。"""
    page = ai_classification_page
    original_count = page.model_count()
    copy_name = f"自动化副本_{time.time_ns()}"
    created = False

    try:
        assert page.exists()
        assert page.title() == page.TITLE
        assert page.model_item(0).is_visible()

        page.create_model_copy(
            copy_name=copy_name,
            model_index=0,
        )
        created = True

        deadline = time.monotonic() + page.timeout
        while time.monotonic() < deadline:
            if page.model_count() == original_count + 1:
                break
            time.sleep(0.2)

        assert page.model_count() == original_count + 1
        assert page.model_item(-1).is_visible()
    finally:
        if created:
            page.click_model_menu(-1, "删除")
            message_box = MessageBoxPage.wait_for_open(
                page.handle,
                timeout=page.timeout,
            )
            message_box.confirm()

            deadline = time.monotonic() + page.timeout
            while time.monotonic() < deadline:
                if page.model_count() == original_count:
                    break
                time.sleep(0.2)

            assert page.model_count() == original_count
