# coding: utf-8
"""Mech-Vision 的启动和关闭。"""

from pathlib import Path

from pywinauto import Application
from pywinauto.application import ProcessNotFoundError


EXE_PATH = Path(
    r"D:\project\Mech-Vision & Mech-Viz-2.2.2-dev-10-27\Mech-Vision\mmind_vision.exe"
)


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
