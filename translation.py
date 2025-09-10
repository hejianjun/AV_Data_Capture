from pathlib import Path
import re
import uuid
import json
import time
import requests
import sys
from lxml import etree
import config
from ADC_function import get_html, post_html


def is_japanese(raw: str) -> bool:
    """
    日语简单检测
    """
    return bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\uFF66-\uFF9F]', raw, re.UNICODE))
def translate(
        src: str,
        target_language: str = config.getInstance().get_target_language(),
        engine: str = config.getInstance().get_translate_engine(),
        app_id: str = "",
        key: str = "",
        delay: int = 0,
) -> str:
    """
    translate japanese kana to simplified chinese
    翻译日语假名到简体中文
    :raises ValueError: Non-existent translation engine
    """
    trans_result = ""
    # 中文句子如果包含&等符号会被谷歌翻译截断损失内容，而且中文翻译到中文也没有意义，故而忽略，只翻译带有日语假名的
    if (is_japanese(src) == False) and ("zh_" in target_language):
        return src
    if engine == "google-free":
        gsite = config.getInstance().get_translate_service_site()
        if not re.match('^translate\.google\.(com|com\.\w{2}|\w{2})$', gsite):
            gsite = 'translate.google.cn'
        url = (
            f"https://{gsite}/translate_a/single?client=gtx&dt=t&dj=1&ie=UTF-8&sl=auto&tl={target_language}&q={src}"
        )
        result = get_html(url=url, return_type="object")
        if not result.ok:
            print('[-]Google-free translate web API calling failed.')
            return ''

        translate_list = [i["trans"] for i in result.json()["sentences"]]
        trans_result = trans_result.join(translate_list)
    elif engine == "azure":
        url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=" + target_language
        headers = {
            'Ocp-Apim-Subscription-Key': key,
            'Ocp-Apim-Subscription-Region': "global",
            'Content-type': 'application/json',
            'X-ClientTraceId': str(uuid.uuid4())
        }
        body = json.dumps([{'text': src}])
        result = post_html(url=url, query=body, headers=headers)
        translate_list = [i["text"] for i in result.json()[0]["translations"]]
        trans_result = trans_result.join(translate_list)
    elif engine == "deeplx":
        url = config.getInstance().get_translate_service_site()
        res = requests.post(f"{url}/translate", json={
            'text': src,
            'source_lang': 'auto',
            'target_lang': target_language,
        })
        if res.text.strip():
            trans_result = res.json().get('data')
    else:
        raise ValueError("Non-existent translation engine")

    time.sleep(delay)
    return trans_result

def modify_nfo_content(nfo_path: Path) -> tuple:
    """修改NFO文件内容并返回新演员列表"""
    try:
        # 读取并解析文件
        with open(nfo_path, 'r', encoding='utf-8') as f:
            content = f.read()
        root = etree.fromstring(content.encode('utf-8'))
        
        modified = False
        # 处理简介信息
        for outline in root.xpath('.//outline'):
            normalized = translate(outline.text)
            if normalized != outline.text:
                outline.text = normalized
                modified = True

        for plot in root.xpath('.//plot'):
            normalized = translate(plot.text)
            if normalized != plot.text:
                plot.text = normalized
                modified = True
        
        # 生成最终内容
        if modified:
            new_content = etree.tostring(
                root, 
                encoding='utf-8', 
                pretty_print=True, 
                xml_declaration=True
            ).decode('utf-8')
            return new_content, True
        return content, False

    except Exception as e:
        print(f"ERROR处理文件 {nfo_path}: {str(e)}", file=sys.stderr)
        return None, [], False

def process_movie_dir(movie_dir: Path):
    """处理单个影片目录（增强版）"""
    nfo_files = list(movie_dir.glob('*.nfo'))
    if not nfo_files:
        return
    
    main_nfo = nfo_files[0]
    new_content, modified = modify_nfo_content(main_nfo)
    
    # 只要NFO内容被修改（包含tag/genre的修改），就写入文件
    if modified and new_content is not None:
        with open(main_nfo, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"√ 已更新NFO文件：{main_nfo.name}")


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
    main("Z:\\破解\\JAV_output\\夏目彩春\\MIDE-064")