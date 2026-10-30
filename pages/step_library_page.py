# coding: utf-8
"""步骤库 Page：搜索步骤名，必要时展开父节点，再按 title 定位。"""

from __future__ import annotations

import time

from pywinauto import keyboard, mouse


DRAG_MOVE_STEPS = 40


class StepLibraryPage:
    """封装步骤库。树节点没有 auto_id，用搜索把目标拉进可视区后按 title 定位。"""

    def __init__(self, main_window, timeout: float = 60) -> None:
        self.main_window = main_window
        self.timeout = timeout

    def dock(self):
        """定位步骤库停靠窗口。"""
        library = self.main_window.child_window(
            title="步骤库",
            class_name="mmind::tailor_impl::TDockWidget",
        )
        library.wait("exists", timeout=self.timeout)
        return library

    def search_box(self):
        """定位步骤库搜索框。"""
        box = self.dock().child_window(control_type="Edit")
        box.wait("exists", timeout=10)
        return box

    def filter_checkbox(self, title: str):
        """定位全部 / 2D / 3D 过滤框。"""
        checkbox = self.dock().child_window(
            title=title,
            control_type="CheckBox",
        )
        checkbox.wait("exists", timeout=10)
        return checkbox

    def item(self, title: str, found_index: int = 0):
        """只封装定位条件，不搜索、不等待。同名时用 found_index。"""
        return self.dock().child_window(
            title=title,
            control_type="TreeItem",
            found_index=found_index,
        )

    def search(self, keyword: str) -> None:
        """在搜索框输入关键字，筛出匹配的步骤。"""
        box = self.search_box()
        box.click_input()
        box.set_edit_text(keyword)
        time.sleep(1.0)

    def expand(self, title: str, timeout: float = 10) -> bool:
        """选中树节点后按右方向键展开。UIA expand 对这棵 Qt 树无效。"""
        node = self.item(title)
        if not node.exists(timeout=timeout):
            return False
        node.click_input()
        time.sleep(0.3)
        keyboard.send_keys("{RIGHT}")
        time.sleep(0.5)
        return True

    def _expand_visible_parents(self, title: str) -> None:
        """搜索后若叶子还没出现，展开当前可见的父分类。"""
        library = self.dock()
        for _ in range(6):
            if self.item(title).exists(timeout=0.5):
                return
            parents = [
                row
                for row in library.descendants(control_type="TreeItem")
                if row.window_text().strip()
                and row.window_text().strip() != title
                and row.is_visible()
            ]
            if not parents:
                return
            for parent in parents:
                parent.click_input()
                time.sleep(0.2)
                keyboard.send_keys("{RIGHT}")
                time.sleep(0.4)
                if self.item(title).exists(timeout=0.5):
                    return

    def locate(self, title: str, found_index: int = 0):
        """搜索步骤名 → 必要时展开父节点 → 等待 TreeItem。"""
        self.search(title)
        node = self.item(title, found_index)
        if not node.exists(timeout=2):
            self._expand_visible_parents(title)
        node.wait("exists", timeout=10)
        return node

    def drag_item_to(
        self,
        item,
        destination: tuple[int, int],
        move_steps: int = DRAG_MOVE_STEPS,
    ) -> None:
        """把树节点拖到目标屏幕坐标。Qt 画布需要连续 DragMove。"""
        source_point = item.rectangle().mid_point()
        source = (source_point.x, source_point.y)
        mouse.move(coords=source)
        mouse.press(button="left", coords=source)
        time.sleep(0.5)
        for index in range(1, move_steps + 1):
            ratio = index / move_steps
            point = (
                round(source[0] + (destination[0] - source[0]) * ratio),
                round(source[1] + (destination[1] - source[1]) * ratio),
            )
            mouse.move(coords=point)
            time.sleep(0.03)
        time.sleep(0.5)
        mouse.release(button="left", coords=destination)
        time.sleep(1.0)
