# coding: utf-8
"""在教学示例下新增子分组，并验证本地配置。"""

from utils.solution_library_resources import (
    add_library_subgroup,
    library_categories,
)

GROUP_NAME = "教学示例"
SUBGROUP_NAME = "自动化新增子分组"


def main() -> None:
    subgroup_id = add_library_subgroup(GROUP_NAME, SUBGROUP_NAME)
    assert subgroup_id is not None, (
        f"新增失败或子分组已存在：{GROUP_NAME}/{SUBGROUP_NAME}"
    )

    category = next(
        item
        for item in library_categories()
        if item["name"] == GROUP_NAME
    )
    names = [item["name"] for item in category["subgroups"]]
    assert SUBGROUP_NAME in names, f"本地未写入新增子分组：{names}"
    print(
        f"新增成功：{GROUP_NAME}/{SUBGROUP_NAME}，"
        f"id={subgroup_id}"
    )


if __name__ == "__main__":
    main()
