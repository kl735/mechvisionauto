import time

from pages.character_recognition_config_page import (
    CharacterRecognitionConfigPage,
)
from pages.main_window_page import MainWindowPage
from pages.step_library_page import StepLibraryPage
from pages.welcome_page import WelcomePage
from pywinauto import Application
from pywinauto.application import ProcessNotFoundError
from utils.mech_vision_app import EXE_PATH, MechVisionApp

STEP_NAME = "AI分类（正反/有无）"

def test_mech_vision_app() -> MechVisionApp:
    """验证 MechVisionApp 能启动或连接 Mech-Vision。"""
    mech_vision = MechVisionApp().start()
    assert mech_vision.app is not None, "没有获得 pywinauto Application"
    assert mech_vision.app.is_process_running(), "Mech-Vision 进程未运行"
    print(f"[通过] MechVisionApp，进程 PID：{mech_vision.app.process}")
    return mech_vision


def test_welcome_page(mech_vision: MechVisionApp) -> WelcomePage:
    """验证 WelcomePage 能定位欢迎窗口及其核心控件。"""
    welcome = WelcomePage.attach(mech_vision.app)
    assert welcome.main_window.exists(), "没有定位到欢迎窗口"
    assert welcome.create_empty_solution_button().exists(
        timeout=5,
    ), "没有定位到“新建空白方案”按钮"
    print(f"[通过] WelcomePage，版本：{welcome.version_text()}")
    return welcome


def wait_for_main_window(timeout: float = 60) -> int:
    """用 Win32 Application 等待主窗口并返回句柄。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            app = Application(backend="win32").connect(
                path=str(EXE_PATH),
                timeout=2,
            )
            window = app.window(
                title="Mech-Vision",
                class_name="Qt5152QWindowIcon",
                top_level_only=True,
            )
            if window.exists(timeout=2) and window.is_visible():
                return window.handle
        except ProcessNotFoundError:
            pass
        time.sleep(0.2)
    raise TimeoutError(f"{timeout} 秒内未找到 Mech-Vision 主窗口")


def test_step_library_page(
    mech_vision: MechVisionApp,
    welcome: WelcomePage,
) -> StepLibraryPage:
    """进入空白方案并验证 StepLibraryPage 的核心控件。"""
    welcome.create_empty_solution()
    try:
        main_handle = wait_for_main_window(timeout=5)
    except TimeoutError:
        welcome.create_empty_solution_button().invoke()
        main_handle = wait_for_main_window(timeout=60)

    mech_vision.app = Application(backend="win32").connect(
        handle=main_handle,
    )
    main_page = MainWindowPage.attach(main_handle)
    step_library = main_page.step_library
    crema_node= step_library.locate("2D智能相机")
    crema_node.print_control_identifiers()
    
    assert step_library.dock().exists(), "没有定位到步骤库"
    assert step_library.search_box().exists(), "没有定位到步骤库搜索框"
    print("[通过] StepLibraryPage，步骤库和搜索框均已定位")
    return step_library

def locate_setup_wizard(timeout: float = 10):
    """连接正在运行的 Mech-Vision，定位已手动打开的配置向导。"""
    native_app = Application(backend="win32").connect(
        path=str(EXE_PATH),
        timeout=timeout,
    )
    print(f"[通过] native_app: {native_app}")
    
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        native_windows = native_app.windows(
            class_name="Qt5152QWindowIcon",
            visible_only=True,
        )
        for native_window in native_windows:
            if native_window.window_text() == "Mech-Vision":
                continue
            uia_app = Application(backend="uia").connect(
                handle=native_window.handle,
                timeout=2,
            )
            wizard = uia_app.window(handle=native_window.handle)
            info = wizard.element_info
            if (
                info.class_name == "mmind::Dialog"
                and info.automation_id == "mmind__Dialog"
            ):
                return wizard
        time.sleep(0.2)
    raise RuntimeError(
        "未定位到配置向导。请先手动展开配置向导，再运行 run.py"
    )


def test_setup_wizard() -> None:
    """验证当前已展开的配置向导能够被 UIA 定位。"""
    wizard = locate_setup_wizard()
    print(f"[通过] 配置向导窗口已定位：{wizard.window_text()!r}")
    wizard.print_control_identifiers()


def test_create_character_recognition_model() -> None:
    """新建模型、修改名称，并验证名称保存成功。"""
    wizard = locate_setup_wizard()
    config_page = CharacterRecognitionConfigPage(wizard)
    before_count, after_count = config_page.create_model()
    assert after_count == before_count + 1, (
        f"模型数量变化不符合预期：{before_count} -> {after_count}"
    )
    print(
        f"[通过] 模型创建成功，模型数量：{before_count} -> {after_count}"
    )
    expected_name = f"自动化测试模型{after_count}"
    actual_name = config_page.rename_model(expected_name)
    assert actual_name == expected_name, (
        f"模型名称修改失败：期望 {expected_name!r}，实际 {actual_name!r}"
    )
    print(f"[通过] 模型名称修改成功：{actual_name!r}")


def test_character_recognition_config_panel() -> None:
    """验证右侧 QStackedWidget 及其核心控件能够被定位。"""
    wizard = locate_setup_wizard()
    config_page = CharacterRecognitionConfigPage(wizard)
    panel = config_page.config_panel()
    controls = config_page.config_controls()

    assert panel.is_visible(), "没有定位到右侧 QStackedWidget 配置区域"
    assert controls, "右侧 QStackedWidget 下没有可见控件"
    assert config_page.target_region_edit_button().is_visible()
    assert config_page.confidence_spinner().is_visible()
    assert config_page.recognition_object_combo().is_visible()
    assert config_page.separator_combo().is_visible()
    assert config_page.single_capture_button().is_visible()
    assert config_page.continuous_capture_checkbox().is_visible()
    print(
        f"[通过] 右侧配置区域已定位，可见子控件数量：{len(controls)}"
    )


def test_delete_character_recognition_model() -> None:
    """删除最后一个模型并验证数量减少，随后恢复模型数量。"""
    wizard = locate_setup_wizard()
    config_page = CharacterRecognitionConfigPage(wizard)
    original_count = len(config_page.model_items())
    assert original_count > 1, "至少保留一个模型，当前不执行删除测试"

    before_count, after_count, message = config_page.delete_model(-1)
    assert before_count == original_count
    assert after_count == original_count - 1
    print(
        f"[通过] 模型删除成功，模型数量：{before_count} -> {after_count}，"
        f"提示：{message!r}"
    )
    restore_before, restore_after = config_page.create_model()
    assert restore_before == after_count
    assert restore_after == original_count
    print(f"[通过] 已恢复模型数量：{restore_before} -> {restore_after}")


def main() -> None:
    test_delete_character_recognition_model()


if __name__ == "__main__":
    main()