from pathlib import Path
from lxml import etree
import shutil
import sys

# 全局演员映射缓存
_actor_mapping = None

def get_actor_mapping():
    """加载并缓存演员映射数据"""
    global _actor_mapping
    if _actor_mapping is None:
        mapping_path = Path(__file__).parent / 'MappingTable' / 'mapping_actor.xml'
        doc = etree.parse(str(mapping_path))
        
        _actor_mapping = {}
        for actor in doc.xpath('//a'):
            zh_cn = actor.get('zh_cn')
            # 收集所有可能的别名
            aliases = []
            if kw := actor.get('keyword'):
                aliases.extend(kw.split(','))
            if jp := actor.get('jp'):
                aliases.append(jp)
            if zh_tw := actor.get('zh_tw'):
                aliases.append(zh_tw)
                
            # 建立双向映射
            for alias in filter(None, aliases):
                _actor_mapping[alias.strip().lower()] = zh_cn
                # 同时建立中文名到自身的映射
                _actor_mapping[zh_cn.lower()] = zh_cn
    return _actor_mapping

def modify_nfo_content(nfo_path: Path) -> tuple:
    """修改NFO文件内容并返回新演员列表"""
    try:
        with open(nfo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        root = etree.fromstring(content.encode('utf-8'))
        modified = False
        mapping = get_actor_mapping()
        new_actors = []

        # 处理演员节点
        for actor in root.xpath('.//actor'):
            name_node = actor.find('name')
            if name_node is None:
                continue
            
            original = name_node.text.strip()
            # 标准化处理
            normalized = mapping.get(original.lower(), original)
            
            if normalized != original:
                name_node.text = normalized
                modified = True
            
            # 收集标准化后的名称
            if normalized not in new_actors:
                new_actors.append(normalized)

        return (
            etree.tostring(root, encoding='utf-8', pretty_print=True).decode('utf-8'),
            new_actors,
            True
        ) if modified else (content, new_actors, False)

    except Exception as e:
        print(f"ERROR处理文件 {nfo_path}: {str(e)}", file=sys.stderr)
        return None, [], False

def migrate_files(src_dir: Path, new_actor_dir: str, reason: str):
    """移动整个影片目录到新路径（带原因说明）"""
    base_path = src_dir.parent.parent
    movie_id = src_dir.name
    dest_dir = base_path / new_actor_dir / movie_id
    # 打印移动原因（在操作前输出）
    print(f"\n【移动原因】{reason}")
    print(f"旧路径：{src_dir}")
    print(f"新路径：{dest_dir}")
    # 创建目标父目录
    (base_path / new_actor_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        # 移动整个目录
        shutil.move(str(src_dir), str(dest_dir))
        print("└─ 状态：移动成功")
    except Exception as e:
        print(f"└─ 状态：移动失败 | 错误：{str(e)}", file=sys.stderr)


def process_movie_dir(movie_dir: Path):
    """处理单个影片目录（增强版）"""
    nfo_files = list(movie_dir.glob('*.nfo'))
    if not nfo_files:
        return
    
    main_nfo = nfo_files[0]
    new_content, new_actors, modified = modify_nfo_content(main_nfo)
    
    if not modified and len(new_actors) == 0:
        return
    
    new_actor_dir = ','.join(new_actors)
    original_actor_dir = movie_dir.parent.name
    
    # 构建变更说明
    if new_actor_dir != original_actor_dir:
        change_reason = (
            f"演员目录标准化转换：\n"
            f"原始名称：{original_actor_dir}\n"
            f"更新名称：{new_actor_dir}\n"
            f"影响文件：{main_nfo.name}"
        )
        
        # 写入修改后的NFO内容
        with open(main_nfo, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # 执行迁移（包含详细原因）
        migrate_files(movie_dir, new_actor_dir, change_reason)


def is_movie_dir(path: Path) -> bool:
    """判断是否为有效影片目录的标准"""
    return (
        path.is_dir() and 
        any(path.glob('*.nfo')) and  # 包含NFO文件
        not any(child.is_dir() for child in path.iterdir())  # 没有子目录
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
        if child.is_dir():
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
    main('Z:\日本\JAV_output')
