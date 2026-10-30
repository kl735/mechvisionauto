# coding: utf-8
"""打开工程9，列出全部 Step 并读取步骤参数。"""

import json
from pathlib import Path

import mmind_vision
from mmind_vision import Project, Solution, Step, VisionError


SOLUTION_PATH = r"E:\新版本读码"
PROJECT_NAME = "工程9"


def open_solution(solution: Solution, path: str) -> None:
    """已打开同一方案则复用，否则先关再开。"""
    try:
        current = solution.get_info()
        if current.path:
            if Path(current.path).resolve() == Path(path).resolve():
                return
            solution.close(ignore_changes=True)
    except VisionError:
        pass
    solution.open(path)


def main() -> None:
    try:
        solution = Solution()
        open_solution(solution, SOLUTION_PATH)
        print(f"已打开方案：{solution.get_info().path}")

        project = Project(PROJECT_NAME)
        project_info = project.get_info()
        print(f"工程：{project_info.name}  {project_info.path}")

        steps = project.get_all_steps_info()
        print(f"Step 数量：{len(steps)}")
        for step_info in steps:
            name = step_info.name
            print(f"\n[{name}]  guid={step_info.guid}")
            # [] 表示取该 Step 全部步骤参数
            props_json = Step(name, PROJECT_NAME).get_properties_json("[]")
            print(json.dumps(json.loads(props_json), ensure_ascii=False, indent=2))
    except VisionError as error:
        print(f"Error：{error}")


if __name__ == "__main__":
    mmind_vision.initialize()
    main()
    mmind_vision.uninitialize()
