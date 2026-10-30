# coding: utf-8
"""启动 Mech-Vision，并把步骤库中的 AI 分类拖到画布。"""

from pages.step_library_page import StepLibraryPage


STARTUP_TIMEOUT = 60
AI_STEP_NAME = "AI分类（正反/有无）"


def test_drag_ai_classify_to_canvas(mech_win) -> None:
    """新建空白方案后，把 AI 分类拖到画布中心。"""
    # 定位步骤库，搜索步骤名后拖到画布
    step_library = StepLibraryPage(mech_win, timeout=STARTUP_TIMEOUT)
    step_library.dock()
    print("步骤库定位成功")
    ai_step = step_library.locate(AI_STEP_NAME)
    print(f"已找到步骤：{AI_STEP_NAME}")

    # 定位工程编辑区
    editor = mech_win.child_window(
        title="工程编辑区",
        class_name="mmind::tailor_impl::TDockWidget",
    )
    editor.wait("exists", timeout=STARTUP_TIMEOUT)

    # 定位画布 ScaleGraphicsView
    canvas = editor.child_window(
        class_name="mmind::ScaleGraphicsView",
        control_type="Group",
    )
    canvas.wait("exists", timeout=STARTUP_TIMEOUT)
    print("画布定位成功")

    # 从步骤库拖到画布中心
    mech_win.set_focus()
    canvas_rect = canvas.rectangle()
    destination = (
        round(canvas_rect.left + canvas_rect.width() * 0.55),
        round(canvas_rect.top + canvas_rect.height() * 0.50),
    )
    step_library.drag_item_to(ai_step, destination)
    print(f"已拖放：{AI_STEP_NAME} 到画布 {destination}")
