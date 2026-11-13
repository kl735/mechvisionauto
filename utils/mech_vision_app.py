# coding: utf-8
"""Mech-Vision 的启动和关闭。"""

from pathlib import Path
import time

from pywinauto import Application
from pywinauto.application import ProcessNotFoundError


EXE_PATH = Path(
    r"D:\project\Mech-Vision & Mech-Viz-2.2.2-dev-10-27\Mech-Vision\mmind_vision.exe"
)


def wait_for_main_window(timeout: float = 60) -> int:
    """等待可见的 Mech-Vision UIA 主窗口并返回原生句柄。"""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            app = Application(backend="win32").connect(
                path=str(EXE_PATH),
                timeout=2,
            )
            windows = app.windows(
                title="Mech-Vision",
                class_name="Qt5152QWindowIcon",
                top_level_only=True,
            )
            for window in windows:
                if not window.is_visible():
                    continue
                try:
                    uia_window = Application(
                        backend="uia",
                    ).connect(
                        handle=window.handle,
                    ).window(handle=window.handle)
                    if (
                        uia_window.element_info.automation_id
                        == "mainWindow"
                    ):
                        return window.handle
                except Exception:
                    continue
        except ProcessNotFoundError:
            pass
        time.sleep(0.2)
    raise TimeoutError(f"{timeout} 秒内未找到 Mech-Vision 主窗口")


class MechVisionApp:
    """管理 Mech-Vision 的启动和关闭。"""

    def __init__(self) -> None:
        self.app: Application | None = None
        # self.main_window = None

    def start(self) -> "MechVisionApp":
        """启动 Mech-Vision，并获取主窗口。"""
        if not EXE_PATH.is_file():
            raise FileNotFoundError(f"未找到 Mech-Vision：{EXE_PATH}")

        try:
            self.app = Application(backend="win32").connect(
                path=str(EXE_PATH),
                timeout=5,
            )
        except ProcessNotFoundError:
            self.app = Application(backend="win32").start(
                f'"{EXE_PATH}"',
                timeout=5,
                wait_for_idle=False,
            )
            
        return self

    def close(self) -> None:
        """关闭 Mech-Vision。"""
        if self.app is not None and self.app.is_process_running():
            self.app.kill()

        self.app = None
        # self.main_window = None
