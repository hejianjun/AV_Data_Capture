import re
import typing
from pathlib import Path

from lxml import etree

# 全局映射缓存（按 mode 缓存）
_actor_mapping_by_mode: dict[int, dict] = {}
_info_mapping_by_mode: dict[int, dict] = {}


def load_mapping(mode, mapping_file: str) -> dict:
    """通用映射加载函数"""
    global_mapping = {}
    mapping_path = Path(__file__).parent.parent / "data" / "mapping" / mapping_file

    if not mapping_path.exists():
        raise FileNotFoundError(f"映射文件不存在: {mapping_path}")

    doc = etree.parse(str(mapping_path))

    for item in doc.xpath("//a"):
        if mode == 1:
            lang = item.get("zh_cn")
        elif mode == 2:
            lang = item.get("zh_tw")
        elif mode == 3:
            lang = item.get("jp")
        if lang is None:
            continue

        # 收集所有可能的别名
        aliases = []
        if kw := item.get("keyword"):
            aliases.extend(kw.split(","))
        if jp := item.get("jp"):
            aliases.append(jp)
        if zh_tw := item.get("zh_tw"):
            aliases.append(zh_tw)

        # 建立映射关系
        for alias in filter(None, aliases):
            normalized_alias = alias.strip().lower()
            global_mapping[normalized_alias] = lang

        # 建立中文名到自身的映射
        global_mapping[lang.lower()] = lang

    return global_mapping


def get_actor_mapping(mode):
    """获取演员映射表"""
    cached = _actor_mapping_by_mode.get(mode)
    if cached is None:
        cached = load_mapping(mode, "mapping_actor.xml")
        _actor_mapping_by_mode[mode] = cached
    return cached


def get_info_mapping(mode):
    """获取信息标签映射表"""
    cached = _info_mapping_by_mode.get(mode)
    if cached is None:
        cached = load_mapping(mode, "mapping_info.xml")
        _info_mapping_by_mode[mode] = cached
    return cached


def process_text_mappings(json_data: typing.Union[str, list, dict], mapping: dict) -> typing.Union[str, list, dict]:
    """处理文本映射"""
    if isinstance(json_data, list):
        newlists = []
        for text in json_data:
            normalized, should_delete = process_text_mapping(text, mapping)
            if not should_delete:
                newlists.append(normalized)
        return newlists
    elif isinstance(json_data, str):
        normalized, should_delete = process_text_mapping(json_data, mapping)
        return normalized if not should_delete else json_data
    return json_data


def process_text_mapping(text: str, mapping: dict) -> tuple:
    """
    处理文本映射
    返回：(处理后的文本, 是否需要删除)
    """
    original = text.strip()
    normalized = mapping.get(original.lower(), original)

    if normalized == "删除":
        return None, True
    return normalized, False


def process_special_actor_name(original: str, actor_mapping: dict) -> str:
    """处理带括号的特殊演员名称"""
    if ("（" not in original or "）" not in original) and ("(" not in original or ")" not in original):
        return actor_mapping.get(original.lower(), original)

    # 处理全角括号
    match = re.match(r"(.*)[（|\(](.*)[）|\)]", original)
    if not match:
        return actor_mapping.get(original.strip().lower(), original)

    outer, inner = match.groups()
    norm_outer = actor_mapping.get(outer.strip().lower(), outer.strip())

    # 处理内层多个别名
    if "、" in inner:
        inner_parts = [p.strip() for p in inner.split("、")]
        norm_inner_parts = [actor_mapping.get(p.lower(), p) for p in inner_parts]

        if all(p == norm_outer for p in norm_inner_parts):
            return norm_outer
        return f"{norm_outer}({','.join(norm_inner_parts)})"

    norm_inner = actor_mapping.get(inner.strip().lower(), inner.strip())
    return f"{norm_outer}({norm_inner})" if norm_inner != norm_outer else norm_outer


def normalize_nfo_xml(xml_content: str, actor_mapping: dict, info_mapping: dict) -> tuple[str, list[str], bool, bool]:
    modified = False
    new_actors: list[str] = []

    root = etree.fromstring(xml_content.encode("utf-8"))

    for actor in root.xpath(".//actor"):
        name_node = actor.find("name")
        if name_node is None or name_node.text is None or name_node.text.strip() == "":
            continue

        original = name_node.text.strip()
        normalized = process_special_actor_name(original, actor_mapping)

        if "(" in normalized or "（" in normalized:
            return xml_content, [], False, True

        if normalized != original:
            name_node.text = normalized
            modified = True

        clean_name = normalized.split("(")[0].strip()
        if clean_name and clean_name not in new_actors:
            new_actors.append(clean_name)

    for node in root.xpath(".//tag | .//genre"):
        original = node.text.strip() if node.text else ""
        normalized, should_delete = process_text_mapping(original, info_mapping)

        if should_delete:
            node.getparent().remove(node)
            modified = True
        elif normalized and normalized != original:
            node.text = normalized
            modified = True

    if modified:
        new_content = etree.tostring(root, encoding="utf-8", pretty_print=True, xml_declaration=True).decode("utf-8")
        return new_content, new_actors, True, False

    return xml_content, new_actors, False, False
