# coding: utf-8
"""“误差分析”工具窗口 Page Object。"""

from __future__ import annotations

import re
import time

from pywinauto import Application

from utils.window_helper import (
    process_id_from_window,
    visible_process_windows,
    wait_window_hidden,
)


class _AnalysisSubPanel:
    """误差分析右侧 QStackedWidget 子页面公共基类。"""

    ROOT_CLASS = ""
    CARD_BUTTON_CLASS = "mmind::CustomizedButton"

    def __init__(self, page: AccuracyErrorAnalysisPage) -> None:
        self.page = page

    def root(self):
        """等待并返回当前子页面根容器。"""
        return self.page.wait_for_visible_class(self.ROOT_CLASS)

    def is_open(self) -> bool:
        """判断右侧当前可见子页面是否为本页面。"""
        return self.page.current_page_class() == self.ROOT_CLASS

    def scroll_area(self):
        """返回当前子页面下的 QScrollArea，若无则返回根容器。"""
        page_root = self.root()
        for control in page_root.descendants(control_type="Group"):
            if (
                control.element_info.class_name == "QScrollArea"
                and control.is_visible()
            ):
                return control
        return page_root

    def _find_visible(
        self,
        control_type: str,
        title: str | None = None,
        title_re: str | None = None,
        class_name: str | None = None,
        found_index: int = 0,
        container=None,
    ):
        """在指定容器内按条件查找可见控件。"""
        scope = self.root() if container is None else container
        pattern = re.compile(title_re) if title_re is not None else None
        deadline = time.monotonic() + self.page.timeout
        while time.monotonic() < deadline:
            matches = []
            for control in scope.descendants(control_type=control_type):
                if not control.is_visible():
                    continue
                text = control.window_text().strip()
                if title is not None and text != title:
                    continue
                if pattern is not None and not pattern.fullmatch(text):
                    continue
                if (
                    class_name is not None
                    and control.element_info.class_name != class_name
                ):
                    continue
                matches.append(control)
            if len(matches) > found_index:
                return matches[found_index]
            time.sleep(0.1)

        raise TimeoutError(
            f"{self.ROOT_CLASS} 中未找到控件："
            f"type={control_type!r}, title={title!r}, "
            f"title_re={title_re!r}, class_name={class_name!r}, "
            f"found_index={found_index}"
        )

    def text_label(self, title: str):
        """按文本内容定位子页面内可见的 Text 控件。"""
        return self._find_visible("Text", title=title)

    def card_buttons(self) -> list:
        """返回当前子页面内所有可见的检查项卡片按钮。"""
        return [
            control
            for control in self.root().descendants(control_type="Group")
            if control.element_info.class_name == self.CARD_BUTTON_CLASS
            and control.is_visible()
        ]

    def card_titles(self) -> list[str]:
        """返回当前子页面中每个检查项卡片的主标题列表。"""
        titles: list[str] = []
        for card in self.card_buttons():
            texts = [
                label.window_text().strip()
                for label in card.descendants(control_type="Text")
                if label.is_visible() and label.window_text().strip()
            ]
            if texts:
                titles.append(texts[0])
        return titles

    def card_button(self, title: str):
        """按主标题定位对应的检查项卡片按钮。"""
        labels = [
            control
            for control in self.root().descendants(control_type="Text")
            if control.is_visible()
            and control.window_text().strip() == title
        ]
        for label in labels:
            current = label
            while current is not None:
                try:
                    current = current.parent()
                except Exception:
                    break
                if (
                    current is not None
                    and current.element_info.class_name
                    == self.CARD_BUTTON_CLASS
                ):
                    return current
        raise RuntimeError(
            f"未找到标题为 {title!r} 的 {self.CARD_BUTTON_CLASS} 卡片"
        )


class ToolIntroductionPanel(_AnalysisSubPanel):
    """封装“工具介绍”右侧子页面。"""

    ROOT_CLASS = "mmind::ToolIntroductionPage"

    def intro_banner_text(self) -> str:
        """读取顶部蓝色说明横幅文本。"""
        label = self._find_visible(
            "Text",
            class_name="mmind::ElidedTextLabel",
        )
        return label.window_text().strip()

    def prompt_label(self):
        """定位现场情况选择提示文本。"""
        return self._find_visible(
            "Text",
            title="请根据现场实际情况进行如下选择：",
            container=self.scroll_area(),
        )

    def eih_same_position_option(self, choice: str):
        """定位第 1 题的“是”或“否”选项。"""
        if choice not in ("是", "否"):
            raise ValueError(f"不支持的选项：{choice!r}，可选 '是' / '否'")
        return self._find_visible(
            "CheckBox",
            title=choice,
            found_index=0,
            container=self.scroll_area(),
        )

    def workpiece_position_option(self, choice: str):
        """定位第 2 题的工件位置关系选项。"""
        valid = ("位置相近", "有明显的XYZ方向平移", "有明显的旋转")
        if choice not in valid:
            raise ValueError(f"不支持的选项：{choice!r}，可选 {valid!r}")
        return self._find_visible(
            "CheckBox",
            title=choice,
            container=self.scroll_area(),
        )

    def point_cloud_quality_option(self, choice: str):
        """定位第 3 题的“是”或“否”选项。"""
        if choice not in ("是", "否"):
            raise ValueError(f"不支持的选项：{choice!r}，可选 '是' / '否'")
        return self._find_visible(
            "CheckBox",
            title=choice,
            found_index=1,
            container=self.scroll_area(),
        )

    def evaluate_button(self):
        """定位“评估影响因素”或“重新评估影响因素”按钮。"""
        return self._find_visible(
            "Button",
            title_re=r"(重新)?评估影响因素",
            container=self.scroll_area(),
        )

    def suggested_check_label(self):
        """定位底部“建议检查”标题文本。"""
        return self._find_visible(
            "Text",
            title="建议检查",
            container=self.scroll_area(),
        )


class CameraIntrinsicCheckPanel(_AnalysisSubPanel):
    """封装点击“检查相机内参”后显示的检查步骤页面。"""

    ROOT_CLASS = "mmind::IntriCheckPage"

    def text_labels(self) -> list:
        """返回新页面内所有非空、可见的文本控件。"""
        return [
            control
            for control in self.root().descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]

    def text_contents(self) -> list[str]:
        """返回新页面内所有可见文本内容。"""
        return [
            control.window_text().strip()
            for control in self.text_labels()
        ]

    def step_texts(self, title: str) -> list[str]:
        """返回指定步骤卡片内的标题和说明文字。"""
        card = self.card_button(title)
        return [
            control.window_text().strip()
            for control in card.descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]

    def step_description(self, title: str) -> str:
        """返回指定步骤卡片标题下方的说明文字。"""
        texts = self.step_texts(title)
        if len(texts) < 2:
            raise RuntimeError(f"{title!r} 卡片中未找到说明文字")
        return texts[1]

    def connect_camera_description(self) -> str:
        """返回“连接相机”步骤下方的说明文字。"""
        return self.step_description("连接相机")

    def open_intrinsic_tool_description(self) -> str:
        """返回“打开‘内参工具’”步骤下方的说明文字。"""
        return self.step_description("打开“内参工具”")

    def check_intrinsic_description(self) -> str:
        """返回“检查相机内参”步骤下方的说明文字。"""
        return self.step_description("检查相机内参")

    def view_result_description(self) -> str:
        """返回“查看检查结果”步骤下方的说明文字。"""
        return self.step_description("查看检查结果")

    def step_descriptions(self) -> dict[str, str]:
        """返回四个检查步骤及其说明文字。"""
        return {
            title: self.step_description(title)
            for title in self.card_titles()
        }

    def detailed_document_label(self):
        """定位“详细文档”文本控件。"""
        return self._find_visible("Text", title="详细文档")

    def open_viewer_button(self):
        """定位“打开”按钮。"""
        return self._find_visible("Button", title="打开")

    def previous_button(self):
        """定位底部“上一步”按钮。"""
        return self._find_visible(
            "Button",
            title="上一步",
            container=self.page.current_content_page(),
        )

    def page_elements(self) -> dict:
        """汇总新页面中已封装的文本和可交互元素。"""
        return {
            "texts": self.text_contents(),
            "card_titles": self.card_titles(),
            "step_descriptions": self.step_descriptions(),
            "detailed_document": self.detailed_document_label(),
            "open_button": self.open_viewer_button(),
            "previous_button": self.previous_button(),
        }

    def click_previous(self) -> "CameraAnalysisPanel":
        """点击“上一步”并返回相机入口页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = CameraAnalysisPanel(self.page)
        panel.root()
        return panel


class CameraAnalysisPanel(_AnalysisSubPanel):
    """封装“相机”右侧子页面。"""

    ROOT_CLASS = "mmind::CameraPage"

    def intrinsic_check_label(self):
        """定位“检查相机内参”文本控件。"""
        return self.text_label("检查相机内参")

    def intrinsic_check_button(self):
        """定位“检查相机内参”卡片按钮。"""
        return self.card_button("检查相机内参")

    def click_intrinsic_check(self) -> CameraIntrinsicCheckPanel:
        """点击“检查相机内参”并返回检查步骤页面。"""
        self.page.focus()
        self.intrinsic_check_button().click_input()
        panel = CameraIntrinsicCheckPanel(self.page)
        panel.root()
        return panel


class _RobotDetailPanel(_AnalysisSubPanel):
    """机器人检查入口打开后的二级页面公共封装。"""

    PAGE_TITLE = ""

    def root(self):
        """等待二级页面标志控件出现，并返回机器人右侧页面。"""
        self.page.wait_for_visible_class(self.ROOT_CLASS)
        return self.page.current_content_page()

    def is_open(self) -> bool:
        """判断当前是否已进入该机器人二级页面。"""
        try:
            self.page.wait_for_visible_class(self.ROOT_CLASS)
            return True
        except TimeoutError:
            return False

    def text_labels(self) -> list:
        """返回二级页面内所有非空、可见的文本控件。"""
        return [
            control
            for control in self.root().descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]

    def text_contents(self) -> list[str]:
        """返回二级页面内所有可见文本内容。"""
        return [
            control.window_text().strip()
            for control in self.text_labels()
        ]

    def title_label(self):
        """定位二级页面标题。"""
        return self._find_visible("Text", title=self.PAGE_TITLE)

    def detailed_document_label(self):
        """定位“详细文档”文本控件。"""
        return self._find_visible("Text", title="详细文档")

    def previous_button(self):
        """定位“上一步”按钮。"""
        return self._find_visible("Button", title="上一步")

    def next_button(self):
        """定位“下一步”按钮。"""
        return self._find_visible("Button", title="下一步")

    def has_next_button(self) -> bool:
        """判断当前二级页面是否包含“下一步”按钮。"""
        return any(
            control.is_visible()
            and control.window_text().strip() == "下一步"
            for control in self.root().descendants(control_type="Button")
        )

    def description_texts(self) -> list[str]:
        """返回除页面标题和“详细文档”外的说明文本。"""
        excluded = {self.PAGE_TITLE, "详细文档"}
        return [
            text
            for text in self.text_contents()
            if text not in excluded
        ]

    def page_elements(self) -> dict:
        """汇总当前二级页面中已定位的文本及按钮。"""
        elements = {
            "title": self.title_label(),
            "texts": self.text_contents(),
            "descriptions": self.description_texts(),
            "previous_button": self.previous_button(),
        }
        if self.has_next_button():
            elements["next_button"] = self.next_button()
        return elements

    def click_previous(self) -> "RobotAnalysisPanel":
        """点击“上一步”并返回机器人三个入口页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = RobotAnalysisPanel(self.page)
        panel.root()
        return panel


class DhParametersCheckPanel(_RobotDetailPanel):
    """封装“DH参数检查”二级页面。"""

    ROOT_CLASS = "mmind::DHParametersCheckPage"
    PAGE_TITLE = "DH参数检查"

    def explanation(self) -> str:
        """返回 DH 参数检查页面的完整说明文字。"""
        descriptions = self.description_texts()
        if not descriptions:
            raise RuntimeError("DH参数检查页面未找到说明文字")
        return descriptions[0]


class RobotAbsoluteAccuracyCheckPanel(_RobotDetailPanel):
    """封装“机器人绝对精度检查”二级页面。"""

    ROOT_CLASS = "mmind::ZeroPointCheckPage"
    PAGE_TITLE = "机器人绝对精度检查"

    def instruction(self) -> str:
        """返回机器人零点检查说明。"""
        descriptions = self.description_texts()
        if not descriptions:
            raise RuntimeError("机器人绝对精度检查页面未找到说明文字")
        return descriptions[0]

    def click_next(self) -> "RobotMoveDistanceCheckPanel":
        """点击“下一步”进入移动距离检查页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = RobotMoveDistanceCheckPanel(self.page)
        panel.root()
        return panel


class RobotMoveDistanceCheckPanel(_RobotDetailPanel):
    """封装绝对精度检查的“移动距离检查”页面。"""

    ROOT_CLASS = "mmind::MoveDistanceCheckPage"
    PAGE_TITLE = "机器人绝对精度检查"

    def instruction(self) -> str:
        """返回移动距离检查说明。"""
        descriptions = self.description_texts()
        if not descriptions:
            raise RuntimeError("移动距离检查页面未找到说明文字")
        return descriptions[0]

    def click_previous(
        self,
    ) -> RobotAbsoluteAccuracyCheckPanel:
        """返回机器人零点检查页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = RobotAbsoluteAccuracyCheckPanel(self.page)
        panel.root()
        return panel

    def click_next(self) -> "RobotPointRotationCheckPanel":
        """进入围绕尖点旋转检查页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = RobotPointRotationCheckPanel(self.page)
        panel.root()
        return panel


class RobotPointRotationCheckPanel(_RobotDetailPanel):
    """封装绝对精度检查的“围绕尖点旋转”页面。"""

    ROOT_CLASS = "mmind::PointRotationCheckPage"
    PAGE_TITLE = "机器人绝对精度检查"

    def check_method_label(self):
        """定位“使用围绕尖点旋转法进行检测”文本。"""
        return self._find_visible(
            "Text",
            title="使用围绕尖点旋转法进行检测",
        )

    def operation_method_label(self):
        """定位“操作方法”文本。"""
        return self._find_visible("Text", title="操作方法")

    def operation_steps(self) -> str:
        """返回围绕尖点旋转法的完整操作步骤。"""
        excluded = {
            "使用围绕尖点旋转法进行检测",
            "操作方法",
        }
        descriptions = [
            text
            for text in self.description_texts()
            if text not in excluded
        ]
        if not descriptions:
            raise RuntimeError("围绕尖点旋转页面未找到操作步骤")
        return descriptions[0]

    def click_previous(self) -> RobotMoveDistanceCheckPanel:
        """返回移动距离检查页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = RobotMoveDistanceCheckPanel(self.page)
        panel.root()
        return panel

    def click_next(
        self,
    ) -> "RobotAbsoluteAccuracyRecommendationsPanel":
        """进入机器人绝对精度建议页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = RobotAbsoluteAccuracyRecommendationsPanel(self.page)
        panel.root()
        return panel


class RobotAbsoluteAccuracyRecommendationsPanel(_RobotDetailPanel):
    """封装机器人绝对精度检查的最终建议页面。"""

    ROOT_CLASS = "mmind::RecommendationsPage"
    PAGE_TITLE = "机器人绝对精度检查"

    def recommendation_texts(self) -> list[str]:
        """返回最终页面的影响说明与处理建议。"""
        return self.description_texts()

    def click_previous(self) -> RobotPointRotationCheckPanel:
        """返回围绕尖点旋转检查页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = RobotPointRotationCheckPanel(self.page)
        panel.root()
        return panel


class RobotRepeatabilityCheckPanel(_RobotDetailPanel):
    """封装“机器人重复精度检查”二级页面。"""

    ROOT_CLASS = "mmind::RobotPrecisionWizard"
    PAGE_TITLE = "机器人重复精度检查"

    def step_texts(self, title: str) -> list[str]:
        """返回指定工程搭建步骤的标题和说明文字。"""
        card = self.card_button(title)
        return [
            control.window_text().strip()
            for control in card.descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]

    def step_description(self, title: str) -> str:
        """返回指定工程搭建步骤的说明文字。"""
        texts = self.step_texts(title)
        if len(texts) < 2:
            raise RuntimeError(f"{title!r} 卡片中未找到说明文字")
        return texts[1]

    def step_descriptions(self) -> dict[str, str]:
        """返回工程搭建页面的全部步骤及说明。"""
        return {
            title: self.step_description(title)
            for title in self.card_titles()
        }

    def eih_photo_position_label(self):
        """定位“EIH拍照点位置检测”选项。"""
        return self._find_visible(
            "Text",
            title="EIH拍照点位置检测",
        )

    def fixed_grasp_point_label(self):
        """定位“固定抓取点检测”选项。"""
        return self._find_visible(
            "Text",
            title="固定抓取点检测",
        )

    def page_elements(self) -> dict:
        """汇总重复精度检查页面中的文本、步骤及控件。"""
        elements = super().page_elements()
        elements.update(
            {
                "card_titles": self.card_titles(),
                "step_descriptions": self.step_descriptions(),
                "eih_photo_position": self.eih_photo_position_label(),
                "fixed_grasp_point": self.fixed_grasp_point_label(),
            }
        )
        return elements

    def click_next(
        self,
    ) -> "RobotRepeatabilityOperationStepsPanel":
        """进入机器人移动与拍照操作步骤页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = RobotRepeatabilityOperationStepsPanel(self.page)
        panel.root()
        return panel


class RobotRepeatabilityOperationStepsPanel(_RobotDetailPanel):
    """封装重复精度检查的拍照操作步骤页面。"""

    ROOT_CLASS = "mmind::OperationStepsPage"
    PAGE_TITLE = "机器人重复精度检查"

    def method_title_label(self):
        """定位“机器人携带相机从不同位置拍摄标定板”。"""
        return self._find_visible(
            "Text",
            title="机器人携带相机从不同位置拍摄标定板",
        )

    def operation_method_label(self):
        """定位“操作方法”文本。"""
        return self._find_visible("Text", title="操作方法")

    def operation_steps(self) -> str:
        """返回移动、拍照及记录标定板位姿的操作步骤。"""
        excluded = {
            "机器人携带相机从不同位置拍摄标定板",
            "操作方法",
            "EIH拍照点位置检测",
            "固定抓取点检测",
        }
        descriptions = [
            text
            for text in self.description_texts()
            if text not in excluded
        ]
        if not descriptions:
            raise RuntimeError("重复精度操作页面未找到操作步骤")
        return descriptions[0]

    def click_previous(self) -> RobotRepeatabilityCheckPanel:
        """返回搭建工程获取标定板位姿页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = RobotRepeatabilityCheckPanel(self.page)
        panel.root()
        return panel

    def click_next(self) -> "RobotRepeatabilityEvaluationPanel":
        """进入机器人重复精度评估页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = RobotRepeatabilityEvaluationPanel(self.page)
        panel.root()
        return panel


class RobotRepeatabilityEvaluationPanel(_RobotDetailPanel):
    """封装机器人重复精度的位姿数据评估页面。"""

    ROOT_CLASS = "mmind::EvaluationErrorPage"
    PAGE_TITLE = "机器人重复精度检查"

    def pose_data_label(self):
        """定位“位姿数据”文本。"""
        return self._find_visible("Text", title="位姿数据")

    def pose_table(self):
        """定位标定板位姿数据表格。"""
        return self._find_visible("Table")

    def result_label(self):
        """定位“评估结果：”文本。"""
        return self._find_visible("Text", title="评估结果：")

    def evaluate_error_button(self):
        """定位“评估误差”按钮。"""
        return self._find_visible("Button", title="评估误差")

    def table_header_names(self) -> list[str]:
        """返回位姿数据表格的列标题。"""
        return [
            control.window_text().strip()
            for control in self.root().descendants(control_type="Header")
            if control.is_visible() and control.window_text().strip()
        ]

    def page_elements(self) -> dict:
        """汇总位姿数据评估页面中的关键控件。"""
        elements = super().page_elements()
        elements.update(
            {
                "pose_data": self.pose_data_label(),
                "pose_table": self.pose_table(),
                "table_headers": self.table_header_names(),
                "result": self.result_label(),
                "evaluate_error_button": self.evaluate_error_button(),
            }
        )
        return elements

    def click_previous(
        self,
    ) -> RobotRepeatabilityOperationStepsPanel:
        """返回机器人移动与拍照操作步骤页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = RobotRepeatabilityOperationStepsPanel(self.page)
        panel.root()
        return panel


class RobotAnalysisPanel(_AnalysisSubPanel):
    """封装“机器人”右侧子页面。"""

    ROOT_CLASS = "mmind::RobotPage"

    def dh_parameter_check_button(self):
        """定位“DH参数检查”卡片按钮。"""
        return self.card_button("DH参数检查")

    def absolute_accuracy_check_button(self):
        """定位“机器人绝对精度检查”卡片按钮。"""
        return self.card_button("机器人绝对精度检查")

    def repeatability_check_button(self):
        """定位“机器人重复精度检查”卡片按钮。"""
        return self.card_button("机器人重复精度检查")

    def click_dh_parameter_check(self) -> DhParametersCheckPanel:
        """点击“DH参数检查”并返回二级页面。"""
        self.page.focus()
        self.dh_parameter_check_button().click_input()
        panel = DhParametersCheckPanel(self.page)
        panel.root()
        return panel

    def click_absolute_accuracy_check(
        self,
    ) -> RobotAbsoluteAccuracyCheckPanel:
        """点击“机器人绝对精度检查”并返回二级页面。"""
        self.page.focus()
        self.absolute_accuracy_check_button().click_input()
        panel = RobotAbsoluteAccuracyCheckPanel(self.page)
        panel.root()
        return panel

    def click_repeatability_check(
        self,
    ) -> RobotRepeatabilityCheckPanel:
        """点击“机器人重复精度检查”并返回二级页面。"""
        self.page.focus()
        self.repeatability_check_button().click_input()
        panel = RobotRepeatabilityCheckPanel(self.page)
        panel.root()
        return panel


class _ExtrinsicDetailPanel(_AnalysisSubPanel):
    """EIH/ETH 外参误差分析向导页面公共封装。"""

    PAGE_TITLE = ""

    def root(self):
        """等待页面标志类出现，并返回外参右侧页面。"""
        self.page.wait_for_visible_class(self.ROOT_CLASS)
        return self.page.current_content_page()

    def is_open(self) -> bool:
        """判断当前是否位于该外参向导页面。"""
        try:
            self.page.wait_for_visible_class(self.ROOT_CLASS)
            return True
        except TimeoutError:
            return False

    def text_contents(self) -> list[str]:
        """返回当前页面内全部非空可见文本。"""
        return [
            control.window_text().strip()
            for control in self.root().descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]

    def title_label(self):
        """定位 EIH 或 ETH 外参误差分析标题。"""
        return self._find_visible("Text", title=self.PAGE_TITLE)

    def detailed_document_label(self):
        """定位“详细文档”文本。"""
        return self._find_visible("Text", title="详细文档")

    def previous_button(self):
        """定位“上一步”按钮。"""
        return self._find_visible("Button", title="上一步")

    def next_button(self):
        """定位“下一步”按钮。"""
        return self._find_visible("Button", title="下一步")

    def has_next_button(self) -> bool:
        """判断当前页面是否包含“下一步”按钮。"""
        return any(
            control.is_visible()
            and control.window_text().strip() == "下一步"
            for control in self.root().descendants(control_type="Button")
        )

    def description_texts(self) -> list[str]:
        """返回页面标题与“详细文档”之外的内容文本。"""
        excluded = {self.PAGE_TITLE, "详细文档"}
        return [
            text
            for text in self.text_contents()
            if text not in excluded
        ]

    def card_step_texts(self, title: str) -> list[str]:
        """返回指定步骤卡片中的标题与说明。"""
        card = self.card_button(title)
        return [
            control.window_text().strip()
            for control in card.descendants(control_type="Text")
            if control.is_visible() and control.window_text().strip()
        ]

    def card_step_description(self, title: str) -> str:
        """返回指定步骤卡片中的说明文字。"""
        texts = self.card_step_texts(title)
        if len(texts) < 2:
            raise RuntimeError(f"{title!r} 卡片中未找到说明文字")
        return texts[1]

    def card_step_descriptions(self) -> dict[str, str]:
        """返回当前页面全部步骤卡片及说明。"""
        return {
            title: self.card_step_description(title)
            for title in self.card_titles()
        }

    def page_elements(self) -> dict:
        """汇总当前页面的文本和导航按钮。"""
        elements = {
            "title": self.title_label(),
            "texts": self.text_contents(),
            "descriptions": self.description_texts(),
            "previous_button": self.previous_button(),
        }
        if self.has_next_button():
            elements["next_button"] = self.next_button()
        return elements


class EihProjectPanel(_ExtrinsicDetailPanel):
    """封装 EIH 外参分析的工程搭建页面。"""

    ROOT_CLASS = "mmind::EihProjectPage"
    PAGE_TITLE = "EIH外参误差分析"

    def step_descriptions(self) -> dict[str, str]:
        """返回 EIH 工程搭建步骤及说明。"""
        return self.card_step_descriptions()

    def click_previous(self) -> "ExtrinsicParametersPanel":
        """返回外参分析入口页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = ExtrinsicParametersPanel(self.page)
        panel.root()
        return panel

    def click_next(self) -> "EihOperationPanel":
        """进入 EIH 标定板位姿采集页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = EihOperationPanel(self.page)
        panel.root()
        return panel


class EihOperationPanel(_ExtrinsicDetailPanel):
    """封装 EIH 外参分析的位姿采集操作页面。"""

    ROOT_CLASS = "mmind::EihOperationPage"
    PAGE_TITLE = "EIH外参误差分析"

    def instruction(self) -> str:
        """返回 EIH 位姿采集操作说明。"""
        descriptions = self.description_texts()
        if not descriptions:
            raise RuntimeError("EIH操作页面未找到说明文字")
        return descriptions[0]

    def click_previous(self) -> EihProjectPanel:
        """返回 EIH 工程搭建页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = EihProjectPanel(self.page)
        panel.root()
        return panel

    def click_next(self) -> "EihEvaluationPanel":
        """进入 EIH 外参误差评估页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = EihEvaluationPanel(self.page)
        panel.root()
        return panel


class EihEvaluationPanel(_ExtrinsicDetailPanel):
    """封装 EIH 外参误差的位姿数据评估页面。"""

    ROOT_CLASS = "mmind::EihEvaluationPage"
    PAGE_TITLE = "EIH外参误差分析"

    def pose_data_label(self):
        """定位“位姿数据”文本。"""
        return self._find_visible("Text", title="位姿数据")

    def pose_table(self):
        """定位 EIH 标定板位姿数据表格。"""
        return self._find_visible("Table")

    def result_label(self):
        """定位“评估结果：”文本。"""
        return self._find_visible("Text", title="评估结果：")

    def evaluate_error_button(self):
        """定位“评估误差”按钮。"""
        return self._find_visible("Button", title="评估误差")

    def table_header_names(self) -> list[str]:
        """返回 EIH 位姿表格列标题。"""
        return [
            control.window_text().strip()
            for control in self.root().descendants(control_type="Header")
            if control.is_visible() and control.window_text().strip()
        ]

    def click_previous(self) -> EihOperationPanel:
        """返回 EIH 位姿采集操作页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = EihOperationPanel(self.page)
        panel.root()
        return panel


class EthProjectPanel(_ExtrinsicDetailPanel):
    """封装 ETH 外参分析的工程搭建页面。"""

    ROOT_CLASS = "mmind::EthProjectPage"
    PAGE_TITLE = "ETH外参误差分析"

    def step_descriptions(self) -> dict[str, str]:
        """返回 ETH 工程搭建步骤及说明。"""
        return self.card_step_descriptions()

    def click_previous(self) -> "ExtrinsicParametersPanel":
        """返回外参分析入口页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = ExtrinsicParametersPanel(self.page)
        panel.root()
        return panel

    def click_next(self) -> "EthPointCloudPanel":
        """进入 ETH 场景点云获取页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = EthPointCloudPanel(self.page)
        panel.root()
        return panel


class _EthOperationPanel(_ExtrinsicDetailPanel):
    """ETH 外参分析操作步骤页面公共封装。"""

    def operation_title(self) -> str:
        """返回当前操作页面的操作主题。"""
        descriptions = self.description_texts()
        if not descriptions:
            raise RuntimeError("ETH操作页面未找到操作主题")
        return descriptions[0]

    def operation_method_label(self):
        """定位“操作方法”文本。"""
        return self._find_visible("Text", title="操作方法")

    def operation_steps(self) -> str:
        """返回当前页面的完整操作步骤。"""
        descriptions = [
            text
            for text in self.description_texts()
            if text not in {self.operation_title(), "操作方法"}
        ]
        if not descriptions:
            raise RuntimeError("ETH操作页面未找到操作步骤")
        return descriptions[0]


class EthPointCloudPanel(_EthOperationPanel):
    """封装 ETH 获取标定板场景点云页面。"""

    ROOT_CLASS = "mmind::PointCloudPage"
    PAGE_TITLE = "ETH外参误差分析"

    def click_previous(self) -> EthProjectPanel:
        """返回 ETH 工程搭建页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = EthProjectPanel(self.page)
        panel.root()
        return panel

    def click_next(self) -> "EthVirtualTcpPanel":
        """进入创建标定板虚拟 TCP 页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = EthVirtualTcpPanel(self.page)
        panel.root()
        return panel


class EthVirtualTcpPanel(_EthOperationPanel):
    """封装 ETH 创建标定板虚拟 TCP 页面。"""

    ROOT_CLASS = "mmind::VirtualTcpPage"
    PAGE_TITLE = "ETH外参误差分析"

    def click_previous(self) -> EthPointCloudPanel:
        """返回 ETH 场景点云获取页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = EthPointCloudPanel(self.page)
        panel.root()
        return panel

    def click_next(self) -> "EthOtherAreaPanel":
        """进入工作区域内其他位置外参评估页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = EthOtherAreaPanel(self.page)
        panel.root()
        return panel


class EthOtherAreaPanel(_EthOperationPanel):
    """封装 ETH 工作区域其他位置外参评估页面。"""

    ROOT_CLASS = "mmind::OtherAreaPage"
    PAGE_TITLE = "ETH外参误差分析"

    def click_previous(self) -> EthVirtualTcpPanel:
        """返回创建标定板虚拟 TCP 页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = EthVirtualTcpPanel(self.page)
        panel.root()
        return panel

    def click_next(self) -> "EthRecommendationsPanel":
        """进入 ETH 外参误差处理建议页面。"""
        self.page.focus()
        self.next_button().click_input()
        panel = EthRecommendationsPanel(self.page)
        panel.root()
        return panel


class EthRecommendationsPanel(_ExtrinsicDetailPanel):
    """封装 ETH 外参误差分析最终建议页面。"""

    ROOT_CLASS = "mmind::EthRecommendationsPage"
    PAGE_TITLE = "ETH外参误差分析"

    def recommendation_texts(self) -> list[str]:
        """返回 ETH 外参误差处理建议。"""
        return self.description_texts()

    def click_previous(self) -> EthOtherAreaPanel:
        """返回工作区域内其他位置外参评估页面。"""
        self.page.focus()
        self.previous_button().click_input()
        panel = EthOtherAreaPanel(self.page)
        panel.root()
        return panel


class ExtrinsicParametersPanel(_AnalysisSubPanel):
    """封装“外参”右侧入口页面。"""

    ROOT_CLASS = "mmind::ExtriPage"

    def eih_extrinsic_analysis_button(self):
        """定位“EIH外参误差分析”卡片按钮。"""
        return self.card_button("EIH外参误差分析")

    def eth_extrinsic_analysis_button(self):
        """定位“ETH外参误差分析”卡片按钮。"""
        return self.card_button("ETH外参误差分析")

    def click_eih_extrinsic_analysis(self) -> EihProjectPanel:
        """点击“EIH外参误差分析”并返回工程搭建页面。"""
        self.page.focus()
        self.eih_extrinsic_analysis_button().click_input()
        panel = EihProjectPanel(self.page)
        panel.root()
        return panel

    def click_eth_extrinsic_analysis(self) -> EthProjectPanel:
        """点击“ETH外参误差分析”并返回工程搭建页面。"""
        self.page.focus()
        self.eth_extrinsic_analysis_button().click_input()
        panel = EthProjectPanel(self.page)
        panel.root()
        return panel


class AccuracyErrorAnalysisPage:
    """封装“精度误差分析工具”打开的“误差分析”窗口。"""

    TITLE = "误差分析"
    CLASS_NAME = "mmind::Dialog"
    AUTOMATION_ID = "mmind__Dialog"
    WIZARD_CLASS = "mmind::ErrorAnalysisWizard"

    def __init__(self, window, timeout: float = 10) -> None:
        self.window = window
        self.timeout = timeout
        self._validate_window()
        self.tool_introduction = ToolIntroductionPanel(self)
        self.camera = CameraAnalysisPanel(self)
        self.robot = RobotAnalysisPanel(self)
        self.extrinsic_parameters = ExtrinsicParametersPanel(self)

    @classmethod
    def wait_for_open(
        cls,
        reference_hwnd: int,
        timeout: float = 10,
    ) -> "AccuracyErrorAnalysisPage":
        """等待同一进程中的“误差分析”窗口出现。"""
        process_id = process_id_from_window(reference_hwnd)
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            for hwnd in visible_process_windows(process_id):
                if hwnd == reference_hwnd:
                    continue
                try:
                    app = Application(backend="uia").connect(handle=hwnd)
                    window = app.window(handle=hwnd)
                    info = window.element_info
                    if (
                        info.name == cls.TITLE
                        and info.class_name == cls.CLASS_NAME
                        and info.automation_id == cls.AUTOMATION_ID
                    ):
                        return cls(window, timeout)
                except Exception:
                    continue
            time.sleep(0.1)

        raise TimeoutError(f"未出现窗口：{cls.TITLE}")

    def _validate_window(self) -> None:
        """确认传入窗口确实是“误差分析”窗口。"""
        info = self.window.element_info
        actual = (
            info.name,
            info.class_name,
            info.automation_id,
        )
        expected = (
            self.TITLE,
            self.CLASS_NAME,
            self.AUTOMATION_ID,
        )
        if actual != expected:
            raise ValueError(
                "传入窗口不是误差分析窗口："
                f"期望 {expected!r}，实际 {actual!r}"
            )

    @property
    def handle(self) -> int:
        """返回误差分析窗口原生句柄。"""
        return self.window.handle

    @property
    def element_info(self):
        """返回误差分析窗口 UIA 元素信息。"""
        return self.window.element_info

    def exists(self, timeout: float = 1) -> bool:
        """误差分析窗口是否存在。"""
        return self.window.exists(timeout=timeout)

    def is_visible(self) -> bool:
        """误差分析窗口当前是否可见。"""
        return self.exists() and self.window.is_visible()

    def focus(self) -> None:
        """通过 Win32 句柄将误差分析窗口置于前台，避免被其他窗口遮挡。"""
        Application(backend="win32").connect(
            handle=self.handle,
        ).window(handle=self.handle).set_focus()

    def print_control_identifiers(self) -> None:
        """打印误差分析窗口完整控件树。"""
        self.window.print_control_identifiers()

    def close_button(self):
        """定位右上角关闭按钮。"""
        button = self.window.child_window(
            auto_id="mmind__Dialog.dialogFrame.titleBarWidget.closeBtn",
            control_type="Button",
        )
        button.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        return button

    def navigation_item(self, title: str):
        """按名称定位左侧导航项（工具介绍、相机、机器人等）。"""
        label = self.window.child_window(
            title=title,
            control_type="Text",
        )
        label.wait("exists visible", timeout=self.timeout)
        return label.wrapper_object().parent()

    def select_navigation(self, title: str) -> None:
        """点击左侧指定导航项。"""
        self.focus()
        self.navigation_item(title).click_input()

    def content_stack(self):
        """定位误差分析向导右侧顶层 QStackedWidget。"""
        wizard = self.window.child_window(
            class_name=self.WIZARD_CLASS,
            control_type="Window",
        )
        wizard.wait("exists visible", timeout=self.timeout)
        for child in wizard.wrapper_object().children():
            if child.element_info.class_name == "QStackedWidget":
                return child
        raise RuntimeError(
            f"{self.WIZARD_CLASS} 下未找到右侧 QStackedWidget"
        )

    def current_content_page(self):
        """返回右侧当前可见的子页面容器。"""
        visible_pages = [
            child
            for child in self.content_stack().children()
            if child.is_visible()
        ]
        if not visible_pages:
            raise RuntimeError("误差分析右侧没有可见内容子页面")
        return visible_pages[0]

    def current_page_class(self) -> str:
        """返回右侧当前可见子页面的 Qt 类名。"""
        return self.current_content_page().element_info.class_name or ""

    def wait_for_page_class(self, expected_class: str):
        """等待右侧切换为指定类名的子页面。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            try:
                page = self.current_content_page()
                if page.element_info.class_name == expected_class:
                    return page
            except RuntimeError:
                pass
            time.sleep(0.1)
        raise TimeoutError(
            f"误差分析右侧未切换到：{expected_class!r}，"
            f"当前页面：{self.current_page_class()!r}"
        )

    def wait_for_visible_class(self, expected_class: str):
        """在右侧当前页面及其子控件中等待指定 Qt 类名。"""
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            page = self.current_content_page()
            if (
                page.element_info.class_name == expected_class
                and page.is_visible()
            ):
                return page
            for control in page.descendants():
                if (
                    control.element_info.class_name == expected_class
                    and control.is_visible()
                ):
                    return control
            time.sleep(0.1)
        raise TimeoutError(
            f"误差分析右侧未找到可见控件类：{expected_class!r}"
        )

    def content_scroll_area(self):
        """定位当前右侧子页面下的 QScrollArea。"""
        page = self.current_content_page()
        for control in page.descendants(control_type="Group"):
            if (
                control.element_info.class_name == "QScrollArea"
                and control.is_visible()
            ):
                return control
        return page

    def click_tool_introduction(self) -> ToolIntroductionPanel:
        """点击“工具介绍”并返回对应面板。"""
        self.select_navigation("工具介绍")
        self.tool_introduction.root()
        return self.tool_introduction

    def click_camera(self) -> CameraAnalysisPanel:
        """点击“相机”并返回对应面板。"""
        self.select_navigation("相机")
        self.camera.root()
        return self.camera

    def click_robot(self) -> RobotAnalysisPanel:
        """点击“机器人”并返回对应面板。"""
        self.select_navigation("机器人")
        self.robot.root()
        return self.robot

    def click_extrinsic_parameters(self) -> ExtrinsicParametersPanel:
        """点击“外参”并返回对应面板。"""
        self.select_navigation("外参")
        self.extrinsic_parameters.root()
        return self.extrinsic_parameters

    def option_button(self, title: str, found_index: int = 0):
        """按文字和索引定位当前页面中的选项按钮。"""
        option = self.window.child_window(
            title=title,
            control_type="CheckBox",
            found_index=found_index,
        )
        option.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        return option

    def evaluate_button(self):
        """定位“评估影响因素”或“重新评估影响因素”按钮。"""
        button = self.window.child_window(
            title_re=r"(重新)?评估影响因素",
            control_type="Button",
        )
        button.wait(
            "exists visible enabled ready",
            timeout=self.timeout,
        )
        return button

    def close(self) -> None:
        """关闭误差分析窗口并等待窗口隐藏。"""
        if not self.is_visible():
            return
        hwnd = self.handle
        self.close_button().invoke()
        wait_window_hidden(hwnd, self.timeout)
