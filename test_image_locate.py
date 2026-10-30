# coding: utf-8
"""截图定位画布 Step，点击后 Delete，并用 SDK 确认是否删除。"""

from pathlib import Path
import time

import mmind_vision
from pywinauto import Application
import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]

from image_locator import (
    TEMPLATE_DIR,
    click_match,
    find_mech_vision_hwnd,
    grab_full_screen,
    hover_match,
    locate_step_help_icon,
    locate_template,
    press_delete,
    save_match_preview,
)


TEMPLATE_PATH = TEMPLATE_DIR / "barcode_title.png"
PREVIEW_PATH = TEMPLATE_DIR / "locate_result.png"
BARCODE_TITLE_TEMPLATE = TEMPLATE_DIR / "barcode_title.png"
HELP_ICON_TEMPLATE = TEMPLATE_DIR / "step_help_icon.png"
HELP_PREVIEW_PATH = TEMPLATE_DIR / "locate_help_result.png"
HELP_HOVER_PATH = TEMPLATE_DIR / "help_hover.png"
STEP_NAME_PREFIX = "AI一维码/二维码识别"
SDK_WAIT = 10


def maximize_mech_vision() -> None:
    """最大化 Mech-Vision，避免窗口尺寸变化导致模板匹配失败。"""
    hwnd = find_mech_vision_hwnd()
    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
    time.sleep(0.8)


def get_current_project_name(project_names: set[str]) -> str | None:
    """从工程编辑区/工程列表读取当前打开的工程名。"""
    hwnd = find_mech_vision_hwnd()
    app = Application(backend="uia").connect(handle=hwnd, timeout=15)
    main_window = app.window(handle=hwnd)

    editor = main_window.child_window(
        title="工程编辑区",
        class_name="mmind::tailor_impl::TDockWidget",
    )
    if editor.exists(timeout=5):
        for item in editor.descendants(control_type="Text"):
            text = item.window_text().strip().lstrip("*")
            if text in project_names:
                return text

    project_dock = main_window.child_window(title="工程列表", control_type="Window")
    if project_dock.exists(timeout=3):
        for item in project_dock.descendants(control_type="TreeItem"):
            text = item.window_text().strip().lstrip("*")
            if text in project_names and getattr(item, "is_selected", lambda: False)():
                return text
    return None


def list_target_steps(project_name: str | None = None) -> list[tuple[str, str, str]]:
    """返回当前工程（或指定工程）中的目标 Step。"""
    found: list[tuple[str, str, str]] = []
    solution = mmind_vision.Solution()
    for project_info in solution.get_all_projects_info():
        if project_name is not None and project_info.name != project_name:
            continue
        project = mmind_vision.Project(project_info.name)
        for step in project.get_all_steps_info():
            if step.name.startswith(STEP_NAME_PREFIX):
                found.append((project_info.name, step.name, step.guid))
    return found


def wait_until_missing(
    before: list[tuple[str, str, str]],
    project_name: str | None,
) -> list[str]:
    """等待当前工程里 before 中的 GUID 至少有一个从 SDK 消失。"""
    before_guids = {item[2] for item in before}
    deadline = time.monotonic() + SDK_WAIT
    while time.monotonic() < deadline:
        remaining = {item[2] for item in list_target_steps(project_name)}
        deleted = sorted(before_guids - remaining)
        if deleted:
            return deleted
        time.sleep(0.3)
    return []


def test_locate_step_help_icon() -> None:
    """查看能否定位到 Step 标题右侧的问号。"""
    print(f"步骤标题模板：{BARCODE_TITLE_TEMPLATE}")
    print(f"问号模板：{HELP_ICON_TEMPLATE}")

    maximize_mech_vision()

    title_match, help_match, screenshot, origin = locate_step_help_icon(
        BARCODE_TITLE_TEMPLATE,
        HELP_ICON_TEMPLATE,
        threshold=0.8,
        timeout=15,
    )
    save_match_preview(help_match, screenshot, origin, HELP_PREVIEW_PATH)

    print("问号定位成功")
    print(f"标题相似度：{title_match.score:.3f}  中心：{title_match.center}")
    print(f"问号相似度：{help_match.score:.3f}  中心：{help_match.center}")
    print(f"问号屏幕坐标：{help_match.box}")
    print(f"预览图：{HELP_PREVIEW_PATH}")

    # 鼠标放到问号上停留 2 秒，截取含 Tooltip 的整屏
    print("鼠标悬停问号 2 秒...")
    hover_match(help_match, seconds=2.0)
    grab_full_screen(HELP_HOVER_PATH)
    print(f"悬停截图：{HELP_HOVER_PATH}")


def test_click_and_delete_ai_classify_step() -> None:
    """定位当前画布上的 Step → 点击 → Delete → 检查 SDK。"""
    print(f"使用模板：{TEMPLATE_PATH}")
    print(f"目标 Step：{STEP_NAME_PREFIX}")

    mmind_vision.initialize()
    try:
        all_names = {
            info.name for info in mmind_vision.Solution().get_all_projects_info()
        }
        current_project = get_current_project_name(all_names)
        print(f"当前打开的工程：{current_project or '未识别'}")

        before = list_target_steps(current_project)
        print("删除前，当前工程 SDK 中的目标 Step：")
        if before:
            for project_name, step_name, guid in before:
                print(f"  {project_name} / {step_name} / {guid}")
        else:
            raise RuntimeError(
                f"当前工程「{current_project}」没有「{STEP_NAME_PREFIX}」，"
                "无法截图定位删除。请打开包含该 Step 的工程，或更换模板。"
            )

        maximize_mech_vision()

        # 定位 Step 标题
        match, screenshot, origin = locate_template(
            TEMPLATE_PATH,
            threshold=0.8,
            timeout=15,
        )
        save_match_preview(match, screenshot, origin, PREVIEW_PATH)
        print("截图定位成功")
        print(f"相似度：{match.score:.3f}")
        print(f"中心点：{match.center}")

        # 点击标题左侧文字，避开右侧问号
        click_match(match, offset=(0.25, 0.5))
        time.sleep(0.5)
        print("已点击 Step")

        # 发送 Delete
        press_delete()
        time.sleep(1.0)
        print("已发送 Delete")

        deleted = wait_until_missing(before, current_project) if before else []
        if deleted:
            print("SDK 确认删除成功，已消失的 GUID：")
            for guid in deleted:
                print(f"  {guid}")
            return

        # SDK 没变化时，再看截图模板还在不在
        try:
            locate_template(TEMPLATE_PATH, threshold=0.8, timeout=3)
            raise RuntimeError(
                "Delete 后 SDK 中仍能看到该 Step，且截图仍能匹配到标题，删除失败"
            )
        except TimeoutError:
            print("截图已找不到该 Step 标题，界面上删除成功；SDK 未同步到删除结果")
    finally:
        mmind_vision.uninitialize()


if __name__ == "__main__":
    import sys

    if "help" in sys.argv:
        test_locate_step_help_icon()
    else:
        test_click_and_delete_ai_classify_step()
