from pathlib import Path
from lxml import etree
import shutil
import sys
import re

# 全局映射缓存
_actor_mapping = None
_info_mapping = None

def load_mapping(mode,mapping_file: str) -> dict:
    """通用映射加载函数"""
    global_mapping = {}
    mapping_path = Path(__file__).parent / 'MappingTable' / mapping_file
    
    if not mapping_path.exists():
        raise FileNotFoundError(f"映射文件不存在: {mapping_path}")
    
    doc = etree.parse(str(mapping_path))
    
    for item in doc.xpath('//a'):
        if mode==1:
            lang = item.get('zh_cn')
        elif mode==2:
            lang = item.get('zh_tw')
        elif mode==3:
            lang = item.get('jp')
        if lang is None:
            continue
        
        # 收集所有可能的别名
        aliases = []
        if kw := item.get('keyword'):
            aliases.extend(kw.split(','))
        if jp := item.get('jp'):
            aliases.append(jp)
        if zh_tw := item.get('zh_tw'):
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
    global _actor_mapping
    if _actor_mapping is None:
        _actor_mapping = load_mapping(mode,'mapping_actor.xml')
    return _actor_mapping

def get_info_mapping(mode):
    """获取信息标签映射表"""
    global _info_mapping
    if _info_mapping is None:
        _info_mapping = load_mapping(mode,'mapping_info.xml')
    return _info_mapping

def process_text_mappings(json_data: dict, mapping: dict) -> dict:
    """处理文本映射"""
    if isinstance(json_data, list):
        newlists = []
        for text in json_data:
            normalized, should_delete = process_text_mapping(text, mapping)
            if not should_delete:
                newlists.append(normalized)
        return newlists
    return process_text_mappings(json_data, mapping)
    
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
    if ('（' not in original or '）' not in original) and ('(' not in original or ')' not in original) :
        return actor_mapping.get(original.lower(), original)

    # 处理全角括号
    match = re.match(r'(.*)[（|\(](.*)[）|\)]', original)
    if not match:
        return actor_mapping.get(original.strip().lower(), original)

    outer, inner = match.groups()
    norm_outer = actor_mapping.get(outer.strip().lower(), outer.strip())
    
    # 处理内层多个别名
    if '、' in inner:
        inner_parts = [p.strip() for p in inner.split('、')]
        norm_inner_parts = [actor_mapping.get(p.lower(), p) for p in inner_parts]
        
        if all(p == norm_outer for p in norm_inner_parts):
            return norm_outer
        return f"{norm_outer}({''.join(norm_inner_parts)})"
    
    norm_inner = actor_mapping.get(inner.strip().lower(), inner.strip())
    return f"{norm_outer}({norm_inner})" if norm_inner != norm_outer else norm_outer

def modify_nfo_content(nfo_path: Path) -> tuple:
    """修改NFO文件内容并返回新演员列表"""
    try:
        # 读取并解析文件
        with open(nfo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        root = etree.fromstring(content.encode('utf-8'))
        
        modified = False
        actor_mapping = get_actor_mapping(1)
        info_mapping = get_info_mapping(1)
        new_actors = []

        # 处理演员信息
        for actor in root.xpath('.//actor'):
            name_node = actor.find('name')
            # 使用更明确的检查方式
            if name_node is None or name_node.text is None or name_node.text.strip() == '':
                continue


            original = name_node.text.strip()
            normalized = process_special_actor_name(original, actor_mapping)
            
            # 冲突检测
            if '(' in normalized or '（' in normalized:
                print(f"ALERT: 演员名称映射冲突 {original} -> {normalized}", file=sys.stderr)
                return None, [], False

            if normalized != original:
                name_node.text = normalized
                modified = True

            clean_name = normalized.split('(')[0].strip()
            if clean_name not in new_actors:
                new_actors.append(clean_name)

        # 处理标签信息
        for node in root.xpath('.//tag | .//genre'):
            original = node.text.strip() if node.text else ""
            normalized, should_delete = process_text_mapping(original, info_mapping)
            
            if should_delete:
                node.getparent().remove(node)
                modified = True
            elif normalized and normalized != original:
                node.text = normalized
                modified = True

        # 生成最终内容
        if modified:
            new_content = etree.tostring(
                root, 
                encoding='utf-8', 
                pretty_print=True, 
                xml_declaration=True
            ).decode('utf-8')
            return new_content, new_actors, True
        
        return content, new_actors, False

    except Exception as e:
        print(f"ERROR处理文件 {nfo_path}: {str(e)}", file=sys.stderr)
        return None, [], False

# 以下函数保持原有实现，仅作示例保留
# (migrate_files, process_movie_dir, is_movie_dir, find_movie_dirs, safe_iterdir, main)

def migrate_files(src_dir: Path, new_actor_dir: str, reason: str):
    """优化后的文件迁移函数（添加了重试逻辑）"""
    base_path = src_dir.parent.parent
    dest_dir = base_path / new_actor_dir / src_dir.name
    
    print(f"\n【移动原因】{reason}")
    print(f"旧路径：{src_dir}\n新路径：{dest_dir}")
    
    try:
        dest_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_dir), str(dest_dir))
        print("└─ 状态：移动成功")
    except shutil.Error as e:
        print(f"└─ 状态：目录已存在 | 错误：{str(e)}", file=sys.stderr)
    except Exception as e:
        print(f"└─ 状态：移动失败 | 错误：{str(e)}", file=sys.stderr)

def process_movie_dir(movie_dir: Path):
    """处理单个影片目录（增强版）"""
    nfo_files = list(movie_dir.glob('*.nfo'))
    if not nfo_files:
        return
    
    main_nfo = nfo_files[0]
    new_content, new_actors, modified = modify_nfo_content(main_nfo)
    
    # 只要NFO内容被修改（包含tag/genre的修改），就写入文件
    if modified and new_content is not None:
        with open(main_nfo, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"√ 已更新NFO文件：{main_nfo.name}")

    # 仅在演员目录变化时执行迁移
    if len(new_actors) > 0:
        new_actor_dir = ','.join(new_actors)
        original_actor_dir = movie_dir.parent.name
        
        if new_actor_dir != original_actor_dir:
            change_reason = (
                f"演员目录标准化转换：\n"
                f"原始名称：{original_actor_dir}\n"
                f"更新名称：{new_actor_dir}\n"
                f"影响文件：{main_nfo.name}"
            )
            migrate_files(movie_dir, new_actor_dir, change_reason)


def is_movie_dir(path: Path) -> bool:
    """判断是否为有效影片目录的标准"""
    return (
        path.is_dir() and 
        any(path.glob('*.nfo')) and  # 包含NFO文件
        not any(child.is_dir() and child.name !='translated' for child in path.iterdir())  # 没有子目录
    )
def find_movie_dirs(root: Path) -> list[Path]:
    """智能递归查找所有符合条件的影片目录"""
    movie_dirs = []
    
    # 先检查当前目录本身是否符合条件
    if is_movie_dir(root):
        movie_dirs.append(root)
        return movie_dirs
    
    # 递归遍历子目录
    for child in safe_iterdir(root):
        if child.is_dir() and child.name !='translated':
            # 深度优先搜索
            movie_dirs.extend(find_movie_dirs(child))
    
    return movie_dirs
def safe_iterdir(path: Path) -> list[Path]:
    """带异常处理的目录遍历"""
    try:
        return list(path.iterdir())
    except (FileNotFoundError, PermissionError) as e:
        print(f"目录访问异常：{path} | {str(e)}")
        return []


def main(base_path: str = r"Z:\\破解\\JAV_output"):
    """增强安全性的主流程"""
    root = Path(base_path)
    
    # 新增路径存在性检查
    if not root.exists():
        raise FileNotFoundError(f"根目录不存在: {base_path}")
    processed_dirs = find_movie_dirs(root)
    # 批量处理已收集的目录
    for movie_dir in processed_dirs:
        # 新增处理前二次验证
        if not movie_dir.exists():
            print(f"跳过已移动目录：{movie_dir}")
            continue
            
        try:
            process_movie_dir(movie_dir)
        except Exception as e:
            print(f"处理失败：{movie_dir} | {str(e)}")


if __name__ == "__main__":
    main("W:\\JAV_output")
