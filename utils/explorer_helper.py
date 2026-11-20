from __future__ import annotations

import time
import win32gui  # pyright: ignore[reportMissingModuleSource]


from pywinauto import Application
from utils.window_helper import wait_window_hidden

def visible_explorer_windows() -> list[int]:
    """返回所有可见的文件资源管理器窗口句柄。"""
    handles = []
    def collect(hwnd: int, _: object) -> bool:
        if (
            win32gui.IsWindowVisible(hwnd)
            and win32gui.GetClassName(hwnd) == ExplorerWindow.CLASS_NAME
        ):
            handles.append(hwnd)
        return True
    win32gui.EnumWindows(collect, None)
    return handles


class ExplorerWindow:
    CLASS_NAME = "CabinetWClass"
    TITLE_SUFFIX = "文件资源管理器"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout

    @classmethod
    def wait_for_open(
        cls,
        folder_name: str | None = None,
        timeout: float = 10,
    ) -> "ExplorerWindow":
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for hwnd in visible_explorer_windows():
                title = win32gui.GetWindowText(hwnd)
                if cls.TITLE_SUFFIX not in title:
                    continue
                if folder_name and not title.startswith(folder_name):
                    continue
                app = Application(backend="uia").connect(handle=hwnd)
                return cls(app.window(handle=hwnd), timeout)
            time.sleep(0.2)
        raise TimeoutError("未弹出文件夹窗口")


    def title(self) -> str:
        return self.window.window_text()


    def folder_name(self) -> str:
        return self.title().removesuffix(
            f" - {self.TITLE_SUFFIX}"
        ).strip()

        
    def close_button(self):
        """定位资源管理器标题栏关闭按钮。"""
        button = self.window.child_window(
            title="关闭",
            control_type="Button",
        )
        button.wait("exists enabled", timeout=self.timeout)
        return button

    def close(self) -> None:
        hwnd = self.window.handle
        self.close_button().invoke()
        wait_window_hidden(hwnd, timeout=self.timeout)