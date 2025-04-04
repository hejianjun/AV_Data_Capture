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

def migrate_files(src_dir: Path, new_actor_dir: str):
    """迁移整个影片目录到新路径"""
    # 构建新路径
    base_path = src_dir.parent.parent  # 原路径的祖父目录
    movie_id = src_dir.name  # 影片ID
    dest_dir = base_path / new_actor_dir / movie_id
    
    # 创建目标目录
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 移动所有文件
    for src_file in src_dir.glob('*'):
        if src_file.is_file():
            dest_file = dest_dir / src_file.name
            # 仅当目标不存在时才复制（防止覆盖）
            if not dest_file.exists():
                shutil.copy2(src_file, dest_file)
    
    # 删除原目录（谨慎操作！测试时可注释掉）
    # shutil.rmtree(src_dir)

def process_movie_dir(movie_dir: Path):
    """处理单个影片目录"""
    nfo_files = list(movie_dir.glob('*.nfo'))
    if not nfo_files:
        return
    
    # 处理主NFO文件
    main_nfo = nfo_files[0]
    new_content, new_actors, modified = modify_nfo_content(main_nfo)
    
    if not modified and len(new_actors) == 0:
        return
    
    # 生成新演员目录名
    new_actor_dir = ','.join(new_actors)
    
    # 获取原演员目录
    original_actor_dir = movie_dir.parent.name
    if new_actor_dir == original_actor_dir:
        return  # 无需修改
    
    # 写入修改后的NFO内容
    with open(main_nfo, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # 迁移文件到新路径
    migrate_files(movie_dir, new_actor_dir)

def main(base_path: str = r"Z:\破解"):
    """主处理流程"""
    root = Path(base_path)
    if not root.exists():
        raise FileNotFoundError(f"路径不存在: {base_path}")
    
    # 收集所有影片目录
    processed = set()
    for nfo_file in root.rglob('*.nfo'):
        movie_dir = nfo_file.parent
        if movie_dir not in processed:
            processed.add(movie_dir)
            process_movie_dir(movie_dir)

if __name__ == "__main__":
    main()
