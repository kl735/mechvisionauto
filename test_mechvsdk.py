# coding: utf-8
"""打开 E:\\新版本读码 方案，并列出工程9的全部 Step。"""

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

        # Get solution information
        solution_info = solution.get_info()
        print("[方案信息]")
        print(f" 名称：{solution_info.name}")
        print(f" 路径：{solution_info.path}")
        print(f" 版本：{solution_info.version}")
        print(f" 未保存更改：{solution_info.has_changes}")
        print(f" 正在运行：{solution_info.is_running}")

        # 按名称获取工程
        project = Project(PROJECT_NAME)
        project_info = project.get_info()
        print("[工程信息]")
        print(f" 名称：{project_info.name}")
        print(f" 路径：{project_info.path}")
        print(f" ID：{project_info.id}")
        print(f" 未保存更改：{project_info.has_changes}")
        print(f" 正在运行：{project_info.is_running}")

        # 使用新版 SDK 列出工程下全部 Step
        steps = project.get_all_steps_info()
        print(f"[Step 信息] 共 {len(steps)} 个")
        for index, step_info in enumerate(steps, start=1):
            name = step_info.name
            print(f"\n{index}. {name}")
            print(f" GUID：{step_info.guid}")

            # 获取当前参数（与步骤参数面板对应）
            try:
                props_json = Step(name, PROJECT_NAME).get_properties_json("[]")
                print(" SDK 参数：")
                print(json.dumps(json.loads(props_json), ensure_ascii=False, indent=2))
            except VisionError as error:
                print(f" SDK 参数不可用：{error}")
    except VisionError as error:
        print(f"Error：{error}")


if __name__ == "__main__":
    mmind_vision.initialize()
    main()
    mmind_vision.uninitialize()
