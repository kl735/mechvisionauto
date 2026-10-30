# coding: utf-8
"""连接或启动 Mech-Vision，并处理欢迎页。"""

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import win32con  # pyright: ignore[reportMissingModuleSource]
import win32gui  # pyright: ignore[reportMissingModuleSource]
from pages import WelcomePage
from pywinauto import Application, Desktop
from pywinauto.application import ProcessNotFoundError, process_get_modules


EXE_PATH = Path(
    r"D:\project\Mech-Vision & Mech-Viz-2.2.2-dev-10-27\Mech-Vision\mmind_vision.exe"
)
STARTUP_TIMEOUT = 60


@dataclass
class MechVisionApp:
    """记录测试会话中的主窗口和进程归属。"""

    main_window: Any
    initial_process_ids: set[int]

    @property
    def started_by_tests(self) -> bool:
        """Mech-Vision 是否由本次测试会话启动。"""
        return not self.initial_process_ids


# def vision_process_ids() -> list[int]:
#     """列出全部 mmind_vision.exe。界面可能运行在新进程中。"""
#     executable = str(EXE_PATH).lower()
#     return [
#         process
#         for process, name, _cmdline in process_get_modules()
#         if name and executable in name.lower()
#     ]


def find_main_native_window(process_id: int):
    """等待 Mech-Vision 主窗口出现，排除 Qt 弹层。"""
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while True:
        process_ids = vision_process_ids()
        if process_id not in process_ids:
            process_ids.append(process_id)

        pool = []
        for current_process_id in process_ids:
            windows = Desktop(backend="win32").windows(
                process=current_process_id,
                title_re=r".*Mech-Vision.*",
            )
            candidates = [
                window
                for window in windows
                if "QWindowPopup" not in window.class_name()
            ]
            icon_windows = [
                window
                for window in candidates
                if window.class_name() == "Qt5152QWindowIcon"
            ]
            pool.extend(icon_windows or candidates)

        if pool:
            return max(
                pool,
                key=lambda window: (
                    window.rectangle().width() * window.rectangle().height()
                ),
            )
        if time.monotonic() >= deadline:
            raise RuntimeError("未找到 Mech-Vision 主窗口")
        time.sleep(0.5)


def attach_main_window(process_id: int):
    """按进程定位主窗口，并切到 UIA。"""
    native_window = find_main_native_window(process_id)
    app = Application(backend="uia").connect(handle=native_window.handle)
    main_window = app.window(handle=native_window.handle)
    main_window.wait("exists", timeout=STARTUP_TIMEOUT)
    return main_window


def open_blank_solution(main_window):
    """欢迎页点击新建空白方案，再连接新的主窗口。"""
    welcome_page = WelcomePage(main_window, timeout=STARTUP_TIMEOUT)

    if not welcome_page.exists(timeout=5):
        print("未出现欢迎页，使用当前主窗口")
        return main_window

    welcome_page.create_empty_solution()
    print("已点击：新建空白方案")

    welcome_window = Desktop(backend="win32").window(
        title="欢迎使用Mech-Vision",
    )
    welcome_window.wait_not("exists", timeout=STARTUP_TIMEOUT)

    app = Application(backend="win32").connect(
        path=str(EXE_PATH),
        timeout=STARTUP_TIMEOUT,
    )
    main_window = attach_main_window(app.process)
    print("新窗口定位成功：", main_window.window_text())
    return main_window


def connect_mech_vision():
    """已运行则连接，否则启动，并在欢迎页新建空白方案。"""
    return start_mech_vision().main_window


def start_mech_vision() -> MechVisionApp:
    """连接或启动 Mech-Vision，并返回可用于关闭的会话信息。"""
    try:
        app = Application(backend="win32").connect(
            path=str(EXE_PATH),
            timeout=5,
        )
    except ProcessNotFoundError:
        app = Application(backend="win32").start(
            f'"{EXE_PATH}"',
            work_dir=str(EXE_PATH.parent),
            timeout=STARTUP_TIMEOUT,
            wait_for_idle=False,
        )

    main_window = attach_main_window(app.process)
    print("窗口定位成功：", main_window.window_text())
    main_window = open_blank_solution(main_window)
    return MechVisionApp(
        main_window=main_window,
        initial_process_ids=initial_process_ids,
    )


def discard_unsaved_changes(timeout: float = 3) -> bool:
    """退出时若出现保存确认框，点击“放弃”继续关闭。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            for window in Desktop(backend="win32").windows():
                discard_button = window.child_window(title="放弃", class_name="Button")
                if discard_button.exists(timeout=0):
                    discard_button.click_input()
                    print("已放弃退出时的未保存更改")
                    return True
        except Exception:
            # 窗口可能正在关闭，继续重试。
            pass
        time.sleep(0.2)
    return False


def force_kill_processes(process_ids: set[int]) -> None:
    """强制结束残留的 Mech-Vision 进程，避免 kill() 等待卡死。"""
    for process_id in process_ids:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(process_id)],
            capture_output=True,
            check=False,
            timeout=5,
        )


def close_mech_vision(app_session: MechVisionApp) -> None:
    """关闭本次测试启动的 Mech-Vision，不影响测试前已有的进程。"""
    if not app_session.started_by_tests:
        print("Mech-Vision 在测试前已运行，测试结束后保持打开")
        return

    try:
        win32gui.PostMessage(
            app_session.main_window.handle,
            win32con.WM_CLOSE,
            0,
            0,
        )
    except Exception:
        # 关闭窗口失败时，下面仍会清理本次测试产生的残留进程。
        pass

    discard_unsaved_changes()

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        remaining = set(vision_process_ids()) - app_session.initial_process_ids
        if not remaining:
            print("Mech-Vision 已关闭")
            return
        time.sleep(0.5)

    # UI 关闭可能被“是否保存”对话框阻塞，强制清理测试创建的进程。
    remaining = set(vision_process_ids()) - app_session.initial_process_ids
    force_kill_processes(remaining)
    print("Mech-Vision 已关闭")
