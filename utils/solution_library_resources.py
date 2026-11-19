# coding: utf-8
"""案例库本地 online 资源的读取与清理。"""

from __future__ import annotations

import json
import os
import shutil
import stat
import uuid
from pathlib import Path


SOLUTION_LIBRARY_DIR = Path(
    r"C:\Users\Public\Documents\Mech-Mind\Mech-Vision-2.2.2"
    r"\resource\solution_library"
)
ONLINE_DIR = SOLUTION_LIBRARY_DIR / "online"
LIBRARY_GROUP_PATH = SOLUTION_LIBRARY_DIR / "library_group.json"
APPLICATION_TEMPLATE_GROUP_ID = "8abab4cb-94dc-4cef-883c-c1bd268ed0ca"
CURRENT_VERSION = (2, 2, 2)
# 教学示例卡片的难度排序权重
DIFFICULTY_ORDER = {
    "beginner": 0,
    "intermediate": 1,
    "professional": 2,
}


def _remove_readonly(func, path, _exc_info) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


def clear_online_resources() -> None:
    """删除本地 online 目录，不影响 library_group.json。"""
    if ONLINE_DIR.exists():
        shutil.rmtree(ONLINE_DIR, onexc=_remove_readonly)


def online_resource_dirs() -> list[Path]:
    """返回 online 下的 resource_* 目录。"""
    if not ONLINE_DIR.is_dir():
        return []
    return sorted(
        path
        for path in ONLINE_DIR.iterdir()
        if path.is_dir() and path.name.startswith("resource_")
    )


def count_online_resources() -> int:
    """返回已下载的 online 资源目录数量。"""
    return len(online_resource_dirs())


def parse_version(value) -> tuple[int, ...]:
    """把卡片 min_version 转成可比较的版本元组。"""
    if value is None or value == "":
        return (0,)
    if isinstance(value, (int, float)):
        text = str(int(value))
        if len(text) == 3:
            return (int(text[0]), int(text[1]), int(text[2]))
        return (int(value),)
    parts: list[int] = []
    for item in str(value).split("."):
        digits = "".join(ch for ch in item if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) if parts else (0,)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _group_parts(group: str) -> tuple[str, ...]:
    return tuple(
        item.strip()
        for item in (group or "").split(",")
        if item.strip()
    )


def library_categories() -> list[dict]:
    """读取 library_group.json，返回当前版本可见的一级/二级分类。"""
    data = _load_json(LIBRARY_GROUP_PATH)
    categories: list[dict] = []
    for group in data.get("group") or []:
        if parse_version(group.get("min_version")) > CURRENT_VERSION:
            continue
        subgroups: list[dict] = []
        for sub in group.get("subgroup") or []:
            if parse_version(sub.get("min_version")) > CURRENT_VERSION:
                continue
            subgroups.append(
                {
                    "id": sub["id"],
                    "name": str(sub.get("name_zh") or "").strip(),
                }
            )
        categories.append(
            {
                "id": group["id"],
                "name": str(group.get("name_zh") or "").strip(),
                "subgroups": subgroups,
            }
        )
    return categories


def remove_library_group(name: str) -> dict | None:
    """从 library_group.json 的 group 中删除指定中文分组。"""
    data = _load_json(LIBRARY_GROUP_PATH)
    groups = data.get("group") or []
    for index, group in enumerate(groups):
        if str(group.get("name_zh") or "").strip() != name:
            continue
        removed = groups.pop(index)
        LIBRARY_GROUP_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        return removed
    return None


def rename_library_group(old_name: str, new_name: str) -> bool:
    """修改 library_group.json 中指定分组的中文名称。"""
    data = _load_json(LIBRARY_GROUP_PATH)
    for group in data.get("group") or []:
        if str(group.get("name_zh") or "").strip() != old_name:
            continue
        group["name_zh"] = new_name
        LIBRARY_GROUP_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        return True
    return False


def rename_library_subgroup(
    group_name: str,
    old_name: str,
    new_name: str,
) -> bool:
    """修改指定一级分组下子分组的中文名称。"""
    data = _load_json(LIBRARY_GROUP_PATH)
    for group in data.get("group") or []:
        if str(group.get("name_zh") or "").strip() != group_name:
            continue
        for subgroup in group.get("subgroup") or []:
            if str(subgroup.get("name_zh") or "").strip() != old_name:
                continue
            subgroup["name_zh"] = new_name
            LIBRARY_GROUP_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=4),
                encoding="utf-8",
            )
            return True
        return False
    return False


def add_library_subgroup(
    group_name: str,
    subgroup_name: str,
) -> str | None:
    """在指定一级分组下新增子分组，返回新分组 UUID。"""
    data = _load_json(LIBRARY_GROUP_PATH)
    for group in data.get("group") or []:
        if str(group.get("name_zh") or "").strip() != group_name:
            continue
        subgroups = group.setdefault("subgroup", [])
        if any(
            str(item.get("name_zh") or "").strip() == subgroup_name
            for item in subgroups
        ):
            return None
        subgroup_id = str(uuid.uuid4())
        subgroups.append(
            {
                "id": subgroup_id,
                "name_zh": subgroup_name,
                "name_en": subgroup_name,
                "name_ja": subgroup_name,
                "name_ko": subgroup_name,
                "name_de": subgroup_name,
                "name_fr": subgroup_name,
                "name_es": subgroup_name,
                "name_it": subgroup_name,
                "name_pt": subgroup_name,
                "name_vi": subgroup_name,
                "introduction_zh": None,
                "introduction_en": None,
                "introduction_ja": None,
                "introduction_ko": None,
                "introduction_de": None,
                "introduction_fr": None,
                "introduction_es": None,
                "introduction_it": None,
                "introduction_pt": None,
                "introduction_vi": None,
                "features": [],
                "min_version": 200,
                "subgroup": [],
            }
        )
        LIBRARY_GROUP_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        return subgroup_id
    return None


def remove_library_subgroup(
    group_name: str,
    subgroup_name: str,
) -> dict | None:
    """从指定一级分组中删除子分组，并返回被删除的数据。"""
    data = _load_json(LIBRARY_GROUP_PATH)
    for group in data.get("group") or []:
        if str(group.get("name_zh") or "").strip() != group_name:
            continue
        subgroups = group.get("subgroup") or []
        for index, subgroup in enumerate(subgroups):
            if (
                str(subgroup.get("name_zh") or "").strip()
                != subgroup_name
            ):
                continue
            removed = subgroups.pop(index)
            LIBRARY_GROUP_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=4),
                encoding="utf-8",
            )
            return removed
        return None
    return None


def _visible_online_cards() -> list[dict]:
    cards: list[dict] = []
    for resource_dir in online_resource_dirs():
        config_path = resource_dir / "config" / "config_zh.json"
        package_path = resource_dir / "package.json"
        if not config_path.is_file() or not package_path.is_file():
            continue
        config = _load_json(config_path)
        if parse_version(config.get("min_version")) > CURRENT_VERSION:
            continue
        name = str(config.get("project_resource_translate_name") or "").strip()
        if not name:
            continue
        package = _load_json(package_path)
        cards.append(
            {
                "name": name,
                "pack_id": int(package.get("card_resource_pack_id") or 0),
                "difficulty": config.get("difficulty_level") or "",
                "group_parts": _group_parts(config.get("group", "")),
            }
        )
    return cards


def _sorted_card_names(cards: list[dict], by_difficulty: bool) -> list[str]:
    if by_difficulty:
        ordered = sorted(
            cards,
            key=lambda card: (
                DIFFICULTY_ORDER.get(str(card["difficulty"]), 99),
                card["pack_id"],
            ),
        )
    else:
        ordered = sorted(cards, key=lambda card: card["pack_id"])
    return [card["name"] for card in ordered]


def online_category_catalog() -> list[dict]:
    """按 library_group 结构汇总 online 中可见的分类、二级标题和方案名。"""
    buckets: dict[tuple[str, ...], list[dict]] = {}
    for card in _visible_online_cards():
        buckets.setdefault(card["group_parts"], []).append(card)

    catalog: list[dict] = []
    for category in library_categories():
        by_difficulty = category["name"] == "教学示例"
        if category["subgroups"]:
            subgroups = []
            for sub in category["subgroups"]:
                names = _sorted_card_names(
                    buckets.get((category["id"], sub["id"]), []),
                    by_difficulty,
                )
                subgroups.append(
                    {
                        "id": sub["id"],
                        "name": sub["name"],
                        "cards": names,
                    }
                )
            catalog.append(
                {
                    "id": category["id"],
                    "name": category["name"],
                    "subgroups": subgroups,
                    "cards": [],
                }
            )
            continue
        catalog.append(
            {
                "id": category["id"],
                "name": category["name"],
                "subgroups": [],
                "cards": _sorted_card_names(
                    buckets.get((category["id"],), []),
                    by_difficulty,
                ),
            }
        )
    return catalog


def application_template_names_from_online() -> list[str]:
    """按 card_resource_pack_id 排序，返回应用模板中文方案名。"""
    for category in online_category_catalog():
        if category["id"] == APPLICATION_TEMPLATE_GROUP_ID:
            return list(category["cards"])
    return []


def _card_name(resource_dir: Path) -> str:
    config_path = resource_dir / "config" / "config_zh.json"
    if not config_path.is_file():
        return ""
    return str(
        _load_json(config_path).get("project_resource_translate_name") or ""
    ).strip()


def remove_online_card(name: str) -> str | None:
    """从 online 删除指定卡片，找不到则返回 None。"""
    for resource_dir in online_resource_dirs():
        if _card_name(resource_dir) != name:
            continue
        shutil.rmtree(resource_dir, onexc=_remove_readonly)
        return resource_dir.name
    return None