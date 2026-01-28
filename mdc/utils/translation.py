from pathlib import Path
import re
import uuid
import json
import time
import requests
import sys
from lxml import etree
from mdc.config import config
from mdc.utils.http import get_html, post_html



def is_japanese(raw: str) -> bool:
    """
    日语简单检测，仅检测日语特有的假名字符
    """
    if not isinstance(raw, str) or not raw:
        return False
    # 仅检测日语假名（平假名、片假名、半宽假名、语音扩展）
    # \u3040-\u30ff: Hiragana and Katakana
    # \u31f0-\u31ff: Katakana Phonetic Extensions
    # \uff66-\uff9f: Halfwidth Katakana
    return bool(
        re.search(r"[\u3040-\u30ff\u31f0-\u31ff\uff66-\uff9f]", raw, re.UNICODE)
    )


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
    if not src:
        return src

    is_jp = is_japanese(src)

    # 中文句子如果包含&等符号会被谷歌翻译截断损失内容，而且中文翻译到中文也没有意义，故而忽略，只翻译带有日语的
    if (is_jp == False) and ("zh_" in target_language):
        return src

    if engine == "google-free":
        gsite = config.getInstance().get_translate_service_site()
        if not re.match(r"^translate\.google\.(com|com\.\w{2}|\w{2})$", gsite):
            gsite = "translate.google.cn"
        url = f"https://{gsite}/translate_a/single?client=gtx&dt=t&dj=1&ie=UTF-8&sl=auto&tl={target_language}&q={src}"
        result = get_html(url=url, return_type="object")
        if not result.ok:
            print("[-]Google-free translate web API calling failed.")
            return ""

        try:
            json_data = result.json()
            translate_list = [i["trans"] for i in json_data["sentences"]]
            trans_result = trans_result.join(translate_list)
        except Exception:
            return ""
    elif engine == "azure":
        url = (
            "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to="
            + target_language
        )
        headers = {
            "Ocp-Apim-Subscription-Key": key,
            "Ocp-Apim-Subscription-Region": "global",
            "Content-type": "application/json",
            "X-ClientTraceId": str(uuid.uuid4()),
        }
        body = json.dumps([{"text": src}])
        result = post_html(url=url, query=body, headers=headers)
        try:
            json_data = result.json()
            translate_list = [i["text"] for i in json_data[0]["translations"]]
            trans_result = trans_result.join(translate_list)
        except Exception:
            return ""
    elif engine == "deeplx":
        url = config.getInstance().get_translate_service_site()
        res = requests.post(
            f"{url}/translate",
            json={
                "text": src,
                "source_lang": "auto",
                "target_lang": target_language,
            },
        )
        if res.text.strip():
            try:
                json_data = res.json()
                trans_result = json_data.get("data")
            except Exception:
                return ""
    else:
        raise ValueError("Non-existent translation engine")

    time.sleep(delay)
    return trans_result


def modify_nfo_content(nfo_path: Path) -> tuple:
    """修改NFO文件内容并返回新演员列表"""
    try:
        # 读取并解析文件
        with open(nfo_path, "r", encoding="utf-8") as f:
            content = f.read()
        root = etree.fromstring(content.encode("utf-8"))

        modified = False
        # 处理简介信息：合并去重，仅保留一个 plot，且空内容安全处理
        outlines = root.xpath(".//outline")
        plots = root.xpath(".//plot")

        plot_node = plots[0] if len(plots) else outlines[0]

        # 翻译：仅对最终保留下来的唯一 plot 非空内容执行一次翻译
        if plot_node is not None:
            original = plot_node.text
            if original:  # 仅处理非空内容
                original = original.strip()
                normalized = translate(original)
                if normalized and normalized != original:
                    plot_node.text = normalized
                    modified = True
            else:
                print(f"WARNING: 跳过空内容：{nfo_path}")

        # 生成最终内容
        if modified:
            new_content = etree.tostring(
                root, encoding="utf-8", pretty_print=True, xml_declaration=True
            ).decode("utf-8")
            return new_content, True
        return content, False

    except Exception as e:
        print(f"ERROR处理文件 {nfo_path}: {str(e)}", file=sys.stderr)
        return content, False


def process_movie_dir(movie_dir: Path):
    """处理单个影片目录（增强版）"""
    nfo_files = list(movie_dir.glob("*.nfo"))
    if not nfo_files:
        return

    main_nfo = nfo_files[0]
    new_content, modified = modify_nfo_content(main_nfo)

    # 只要NFO内容被修改（包含tag/genre的修改），就写入文件
    if modified and new_content is not None:
        with open(main_nfo, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"√ 已更新NFO文件：{main_nfo.name}")


def is_movie_dir(path: Path) -> bool:
    """判断是否为有效影片目录的标准"""
    return (
        path.is_dir()
        and any(path.glob("*.nfo"))  # 包含NFO文件
        and not any(
            child.is_dir() and child.name != "translated" for child in path.iterdir()
        )  # 没有子目录
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
        if child.is_dir() and child.name != "translated":
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
