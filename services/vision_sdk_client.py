# coding: utf-8
"""对 Mech-Vision Python SDK 的常用业务操作进行统一封装。"""

from pathlib import Path
from types import TracebackType

import mmind_vision
from mmind_vision import (
    Project,
    ProjectInfo,
    ProjectResult,
    ProjectRunWaitState,
    Solution,
    Step,
    StepInfo,
    StepOutput,
)


class VisionSdkClient:
    """管理 SDK 生命周期，并提供方案、工程和 Step 的常用操作。"""

    def __init__(self, config_file_path: str | Path = "") -> None:
        self._config_file_path = str(config_file_path)
        self._solution: Solution | None = None

    def __enter__(self) -> "VisionSdkClient":
        if self._solution is not None:
            raise RuntimeError("VisionSdkClient 已经初始化")

        mmind_vision.initialize(self._config_file_path)
        try:
            self._solution = Solution()
        except Exception:
            mmind_vision.uninitialize()
            raise
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._solution = None
        mmind_vision.uninitialize()

    def _get_solution(self) -> Solution:
        """返回当前 SDK 方案对象；未进入上下文时给出明确错误。"""
        if self._solution is None:
            raise RuntimeError("请使用 'with VisionSdkClient() as sdk:' 调用 SDK")
        return self._solution

    def open_solution(
        self,
        path: str | Path,
        username: str = "",
        password: str = "",
    ) -> None:
        """打开指定方案。"""
        self._get_solution().open(str(path), username, password)

    def save_solution(self, path: str | Path | None = None) -> None:
        """保存当前方案；传入路径时执行另存为。"""
        solution = self._get_solution()
        if path is None:
            solution.save()
        else:
            destination = Path(path)
            destination.mkdir(parents=True, exist_ok=True)
            solution.save_as(str(destination))

    def get_projects(self) -> list[ProjectInfo]:
        """获取当前方案中的全部工程信息。"""
        return self._get_solution().get_all_projects_info()

    def get_steps(self, project_name: str) -> list[StepInfo]:
        """获取指定工程中的全部 Step 信息。"""
        self._get_solution()
        return Project(project_name).get_all_steps_info()

    def get_step_names(self, project_name: str | None = None) -> list[str]:
        """获取指定工程或当前方案全部工程中的 Step 名称。"""
        if project_name is not None:
            return [step.name for step in self.get_steps(project_name)]

        return [
            step.name
            for project in self.get_projects()
            for step in self.get_steps(project.name)
        ]

    def run_project(
        self,
        project_name: str,
        wait_state: ProjectRunWaitState,
        request_id: str,
    ) -> ProjectResult:
        """运行指定工程并返回运行结果。"""
        self._get_solution()
        return Project(project_name).run(wait_state, request_id)

    def get_project_output(self, project_name: str) -> str:
        """获取指定工程的输出 JSON。"""
        self._get_solution()
        return Project(project_name).get_output()

    def get_step_output(
        self,
        project_name: str,
        step_name: str,
        port: int,
    ) -> StepOutput:
        """获取指定 Step 输出端口的数据。"""
        self._get_solution()
        return Step(step_name, project_name).get_output(port)
