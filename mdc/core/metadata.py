import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
from mdc.config import config
from lxml import etree
from mdc.file.file_utils import get_info



def small_cover_check(
    path: str,
    filename: str,
    cover_small: str,
    movie_path: str,
    json_headers: Optional[Dict[str, Any]] = None,
) -> None:
    """
    下载小封面（按配置可选择只补齐缺失图片）。

    Args:
        path: 目标目录
        filename: 图片文件名
        cover_small: 图片 URL
        movie_path: 影片路径（用于下载器日志/上下文）
        json_headers: 可选请求头字典，形如 {"headers": {...}}
    """
    full_filepath = Path(path) / filename
    if (
        config.getInstance().download_only_missing_images()
        and not file_not_exist_or_empty(str(full_filepath))
    ):
        return
    if json_headers is not None:
        download_file_with_filename(
            cover_small, filename, path, movie_path, json_headers["headers"]
        )
    else:
        download_file_with_filename(cover_small, filename, path, movie_path)
    print("[+]Image Downloaded! " + full_filepath.name)


def print_files(
    path: str,
    leak_word: str,
    c_word: str,
    naming_rule: str,
    part: str,
    cn_sub: bool,
    json_data: Dict[str, Any],
    filepath: str,
    tag: Sequence[str],
    actor_list: Sequence[str],
    liuchu: bool,
    uncensored: bool,
    hack: bool,
    hack_word: str,
    _4k: bool,
    fanart_path: str,
    poster_path: str,
    thumb_path: str,
    iso: bool,
) -> None:
    """
    写入影片元数据文件（主要是 NFO），并按配置下载/生成相关资源。

    模式3（不移动文件）下会尽量保留已有 NFO 中的部分字段，仅当新值非空时覆盖。

    Args:
        path: 输出目录（非模式3下用于拼接 NFO 路径）
        leak_word: 流出标记文本
        c_word: 中文字幕标记文本
        naming_rule: 用于写入 title/sorttitle 的命名结果
        part: 多文件分段后缀
        cn_sub: 是否为中文字幕
        json_data: 抓取到的结构化元数据
        filepath: 影片文件路径（模式3下 NFO 与其同名）
        tag: 需要写入的标签列表
        actor_list: 演员列表
        liuchu: 是否流出
        uncensored: 是否无码
        hack: 是否破解
        hack_word: 破解标记文本
        _4k: 是否 4K
        fanart_path: fanart 路径或 URL
        poster_path: poster 路径或 URL
        thumb_path: thumb 路径或 URL
        iso: 是否原盘
    """
    conf = config.getInstance()
    (
        title,
        studio,
        year,
        outline,
        runtime,
        director,
        actor_photo,
        release,
        number,
        cover,
        trailer,
        website,
        series,
        label,
    ) = get_info(json_data)
    main_mode = config.getInstance().main_mode()
    if main_mode == 3:
        nfo_path = str(Path(filepath).with_suffix(".nfo"))
    else:
        nfo_path = os.path.join(
            path, f"{number}{part}{leak_word}{c_word}{hack_word}.nfo"
        )
    try:
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                print(f"[-]Fatal error! can not make folder '{path}'")
                os._exit(0)

        old_nfo = None
        old_nfo_dict: Dict[str, str] = {}
        old_actor_list: List[str] = []
        try:
            if os.path.isfile(nfo_path):
                old_nfo = etree.parse(nfo_path)
                # 提取原有NFO中的所有元素值
                elements_to_check = [
                    "title",
                    "originaltitle",
                    "sorttitle",
                    "customrating",
                    "mpaa",
                    "set",
                    "studio",
                    "year",
                    "outline",
                    "plot",
                    "runtime",
                    "director",
                    "poster",
                    "thumb",
                    "fanart",
                    "maker",
                    "label",
                    "num",
                    "premiered",
                    "releasedate",
                    "release",
                    "cover",
                    "website",
                    "trailer",
                    "userrating",
                    "rating",
                    "criticrating",
                ]
                for elem in elements_to_check:
                    try:
                        old_value = old_nfo.xpath(f"//{elem}/text()")[0]
                        if old_value:
                            old_nfo_dict[elem] = old_value
                    except:
                        pass
                try:
                    old_actor_list = [
                        v.strip()
                        for v in old_nfo.xpath("//actor/name/text()")
                        if isinstance(v, str) and v.strip()
                    ]
                except:
                    old_actor_list = []
        except:
            pass

        if main_mode == 3:
            try:
                new_actor_list: List[str] = [
                    v.strip()
                    for v in (actor_list or [])
                    if isinstance(v, str) and v.strip()
                ]
                anonymous_names = {"佚名", "Anonymous"}
                new_is_anonymous_only = bool(new_actor_list) and all(
                    v in anonymous_names for v in new_actor_list
                )
                old_has_real_actor = bool(old_actor_list) and any(
                    v not in anonymous_names for v in old_actor_list
                )
                if new_is_anonymous_only and old_has_real_actor:
                    actor_list = old_actor_list
                else:
                    actor_list = new_actor_list
            except:
                pass

        # 模式3下，保留原有值，仅当新值非空时覆盖
        if main_mode == 3:
            # 处理outline和plot
            if not outline:
                if "outline" in old_nfo_dict:
                    outline = old_nfo_dict["outline"]
                # 对于plot，使用与outline相同的值
                plot_value = outline
            else:
                if json_data["source"] == "pissplay":
                    outline = f"{outline}"
                else:
                    outline = f"{number}#{outline}"
                plot_value = outline
        else:
            # 非模式3下的原有逻辑
            if not outline:
                pass
            elif json_data["source"] == "pissplay":
                outline = f"{outline}"
            else:
                outline = f"{number}#{outline}"
            plot_value = outline
        with open(nfo_path, "wt", encoding="UTF-8") as code:
            print('<?xml version="1.0" encoding="UTF-8" ?>', file=code)
            print("<movie>", file=code)

            # 处理标题相关元素
            if main_mode == 3:
                # 模式3下保留原有标题信息
                for elem in ["title", "originaltitle", "sorttitle"]:
                    if elem in old_nfo_dict and elem != "title":
                        if not config.getInstance().jellyfin():
                            print(
                                f"  <{elem}><![CDATA[{old_nfo_dict[elem]}]]></{elem}>",
                                file=code,
                            )
                        else:
                            print(f"  <{elem}>{old_nfo_dict[elem]}</{elem}>", file=code)
                    else:
                        # 原有标题不存在时使用新生成的
                        if elem == "title" or elem == "sorttitle":
                            value = naming_rule
                        else:
                            value = json_data["original_naming_rule"]
                        if not config.getInstance().jellyfin():
                            print(f"  <{elem}><![CDATA[{value}]]></{elem}>", file=code)
                        else:
                            print(f"  <{elem}>{value}</{elem}>", file=code)
            else:
                # 非模式3下的原有逻辑
                if not config.getInstance().jellyfin():
                    print("  <title><![CDATA[" + naming_rule + "]]></title>", file=code)
                    print(
                        "  <originaltitle><![CDATA["
                        + json_data["original_naming_rule"]
                        + "]]></originaltitle>",
                        file=code,
                    )
                    print(
                        "  <sorttitle><![CDATA[" + naming_rule + "]]></sorttitle>",
                        file=code,
                    )
                else:
                    print("  <title>" + naming_rule + "</title>", file=code)
                    print(
                        "  <originaltitle>"
                        + json_data["original_naming_rule"]
                        + "</originaltitle>",
                        file=code,
                    )
                    print("  <sorttitle>" + naming_rule + "</sorttitle>", file=code)

            # 处理customrating和mpaa
            print("  <customrating>JP-18+</customrating>", file=code)
            print("  <mpaa>JP-18+</mpaa>", file=code)

            # 处理set
            if main_mode == 3 and "set" in old_nfo_dict:
                print(f"  <set>{old_nfo_dict['set']}</set>", file=code)
            else:
                try:
                    print("  <set>" + series + "</set>", file=code)
                except:
                    print("  <set></set>", file=code)

            # 处理studio
            if main_mode == 3 and "studio" in old_nfo_dict and not studio:
                print(f"  <studio>{old_nfo_dict['studio']}</studio>", file=code)
            else:
                print("  <studio>" + studio + "</studio>", file=code)

            # 处理year
            if main_mode == 3 and "year" in old_nfo_dict and not year:
                print(f"  <year>{old_nfo_dict['year']}</year>", file=code)
            else:
                print("  <year>" + year + "</year>", file=code)

            # 处理outline和plot
            if not config.getInstance().jellyfin():
                print(f"  <outline><![CDATA[{outline}]]></outline>", file=code)
                print(f"  <plot><![CDATA[{plot_value}]]></plot>", file=code)
            else:
                print(f"  <outline>{outline}</outline>", file=code)
                print(f"  <plot>{plot_value}</plot>", file=code)

            # 处理runtime
            if main_mode == 3 and "runtime" in old_nfo_dict and not runtime:
                print(f"  <runtime>{old_nfo_dict['runtime']}</runtime>", file=code)
            else:
                print(
                    "  <runtime>" + str(runtime).replace(" ", "") + "</runtime>",
                    file=code,
                )

            # 处理director
            if main_mode == 3 and "director" in old_nfo_dict and not director:
                print(f"  <director>{old_nfo_dict['director']}</director>", file=code)
            elif False != conf.get_direct():
                print("  <director>" + director + "</director>", file=code)

            # 处理poster
            if main_mode == 3 and "poster" in old_nfo_dict:
                print(f"  <poster>{old_nfo_dict['poster']}</poster>", file=code)
            else:
                print("  <poster>" + poster_path + "</poster>", file=code)

            # 处理thumb
            if main_mode == 3 and "thumb" in old_nfo_dict:
                print(f"  <thumb>{old_nfo_dict['thumb']}</thumb>", file=code)
            else:
                print("  <thumb>" + thumb_path + "</thumb>", file=code)

            # 处理fanart
            if not config.getInstance().jellyfin():  # jellyfin 不需要保存fanart
                if main_mode == 3 and "fanart" in old_nfo_dict:
                    print(f"  <fanart>{old_nfo_dict['fanart']}</fanart>", file=code)
                else:
                    print("  <fanart>" + fanart_path + "</fanart>", file=code)

            # 处理actors
            try:
                for key in actor_list:
                    print("  <actor>", file=code)
                    print("    <name>" + key + "</name>", file=code)
                    try:
                        print(
                            "    <thumb>" + actor_photo.get(str(key)) + "</thumb>",
                            file=code,
                        )
                    except:
                        pass
                    print("  </actor>", file=code)
            except:
                pass

            # 处理maker
            if main_mode == 3 and "maker" in old_nfo_dict and not studio:
                print(f"  <maker>{old_nfo_dict['maker']}</maker>", file=code)
            else:
                print("  <maker>" + studio + "</maker>", file=code)

            # 处理label
            if main_mode == 3 and "label" in old_nfo_dict and not label:
                print(f"  <label>{old_nfo_dict['label']}</label>", file=code)
            else:
                print("  <label>" + label + "</label>", file=code)

            jellyfin = config.getInstance().jellyfin()
            if not jellyfin:
                if config.getInstance().actor_only_tag():
                    for key in actor_list:
                        try:
                            print("  <tag>" + key + "</tag>", file=code)
                        except:
                            pass
                else:
                    if cn_sub:
                        print("  <tag>中文字幕</tag>", file=code)
                    if liuchu:
                        print("  <tag>流出</tag>", file=code)
                    if uncensored:
                        print("  <tag>无码</tag>", file=code)
                    if hack:
                        print("  <tag>破解</tag>", file=code)
                    if _4k:
                        print("  <tag>4k</tag>", file=code)
                    if iso:
                        print("  <tag>原盘</tag>", file=code)
                    for i in tag:
                        try:
                            print("  <tag>" + i + "</tag>", file=code)
                        except:
                            pass

            print("</movie>", file=code)
    except Exception as e:
        print(f"[-]Error writing NFO file: {e}")
        moveFailedFolder(filepath)


# 由于这些函数在metadata.py中被调用但在其他模块中定义，需要从相应模块导入
from mdc.file.file_utils import file_not_exist_or_empty
from mdc.download.downloader import download_file_with_filename
from mdc.file.file_utils import moveFailedFolder
