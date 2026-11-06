# coding: utf-8
"""验证画布 Step 问号能够显示说明 Tooltip。"""

import pytest

from image_locator import (
    TEMPLATE_DIR,
    hover_match,
    locate_step_help_icon,
    visible_tooltip_handles,
    wait_for_visible_tooltip,
)
from pages.main_window_page import MainWindowPage


STEP_NAME = "AI分类（正反/有无）"
STEP_TITLE_TEMPLATE = TEMPLATE_DIR / "ai_classify_title.png"
HELP_ICON_TEMPLATE = TEMPLATE_DIR / "step_help_icon.png"


@pytest.fixture
def ai_classify_step_on_canvas(main_page: MainWindowPage) -> int:
    """为问号测试准备一个 AI 分类 Step。"""
    step_library = main_page.step_library
    step = step_library.locate(STEP_NAME)

    canvas = main_page.project_editor.canvas()

    main_page.focus()
    canvas_rect = canvas.rectangle()
    destination = (
        round(canvas_rect.left + canvas_rect.width() * 0.55),
        round(canvas_rect.top + canvas_rect.height() * 0.35),
    )
    step_library.drag_item_to(step, destination)
    print(f"问号测试已准备 Step：{STEP_NAME}，画布坐标 {destination}")
    return main_page.handle


def test_step_help_tooltip(ai_classify_step_on_canvas: int) -> None:
    """悬停 Step 问号，验证说明 Tooltip 可见且已渲染内容。"""
    title_match, help_match, _screenshot, _origin = locate_step_help_icon(
        STEP_TITLE_TEMPLATE,
        HELP_ICON_TEMPLATE,
        threshold=0.8,
        help_threshold=0.65,
        timeout=15,
        hwnd=ai_classify_step_on_canvas,
        scales=(0.75, 0.9, 1.0, 1.1, 1.25, 1.5),
    )
    print(
        f"问号定位成功：标题相似度 {title_match.score:.3f}，"
        f"问号相似度 {help_match.score:.3f}"
    )

    existing_tooltips = visible_tooltip_handles(ai_classify_step_on_canvas)
    hover_match(help_match, seconds=0.5)
    tooltip_text = wait_for_visible_tooltip(
        timeout=5,
        ignored_handles=existing_tooltips,
        main_hwnd=ai_classify_step_on_canvas,
    )

    print(f"Step 说明：{tooltip_text}")
    assert tooltip_text.strip(), "悬停问号后未显示 Step 说明"
