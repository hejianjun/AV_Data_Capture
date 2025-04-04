from pathlib import Path
from lxml import etree
import sys

# 全局缓存演员映射字典
_actor_mapping_cache = None

def get_actor_mapping():
    """获取演员映射字典（缓存优化版）"""
    global _actor_mapping_cache
    if _actor_mapping_cache is None:
        mapping_path = Path(__file__).parent / 'MappingTable' / 'mapping_actor.xml'
        actor_mapping_data = etree.parse(str(mapping_path))
        
        mapping_dict = {}
        for actor in actor_mapping_data.xpath('//a'):
            zh_cn = actor.get('zh_cn')
            keywords = []
            
            # 合并所有关键字
            if actor.get('keyword'):
                keywords.extend(actor.get('keyword').split(','))
            if actor.get('zh_tw'):
                keywords.append(actor.get('zh_tw'))
            if actor.get('jp'):
                keywords.append(actor.get('jp'))
                
            # 建立双向映射
            for kw in filter(None, keywords):  # 过滤空值
                mapping_dict[kw.strip().lower()] = zh_cn  # 统一小写去重
                
        _actor_mapping_cache = mapping_dict
    return _actor_mapping_cache

def parse_nfo_file(nfo_path: Path) -> dict:
    """增强版解析函数，包含别名检测"""
    try:
        with open(nfo_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        root = etree.fromstring(content.encode("utf-8"))
        movie_name = root.findtext(".//movie/title") or root.findtext(".//title")
        
        raw_actors = []
        for actor in root.xpath(".//actor"):
            if name := actor.findtext("name"):
                raw_actors.append(name.strip())
        
        # 标准化处理
        actor_mapping = get_actor_mapping()
        normalized_actors = {a.lower() for a in raw_actors}
        
        # 检测非中文别名
        non_zh_aliases = []
        for raw_name in raw_actors:
            lower_name = raw_name.lower()
            if zh_cn := actor_mapping.get(lower_name):
                # 如果中文名不在演员列表中
                if zh_cn.lower() not in normalized_actors:
                    non_zh_aliases.append({
                        'alias': raw_name,
                        'zh_cn': zh_cn
                    })
        
        return {
            "file_path": str(nfo_path),
            "movie": movie_name.strip() if movie_name else None,
            "actors": raw_actors,
            "non_zh_actors": non_zh_aliases
        }
        
    except Exception as e:
        print(f"解析失败 [{nfo_path}]: {str(e)}", file=sys.stderr)
        return None

def read_nfo(base_path: str = r"Z:\破解"):
    """生成器模式遍历处理"""
    path = Path(base_path)
    if not path.exists():
        raise FileNotFoundError(f"路径不存在: {base_path}")
    
    for nfo_file in path.rglob("*.nfo"):
        if result := parse_nfo_file(nfo_file):
            if result['non_zh_actors']:  # 只返回存在问题的记录
                yield result

if __name__ == "__main__":
    for movie in read_nfo():
        print(f"发现非中文演员使用：{movie['movie']}")
        print(f"文件路径：{movie['file_path']}")
        for item in movie['non_zh_actors']:
            print(f"  ├─ 使用别名：{item['alias']}")
            print(f"  └─ 标准中文名：{item['zh_cn']}")
        print("═" * 60)
