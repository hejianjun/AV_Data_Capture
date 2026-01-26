import os.path
import pathlib
import shutil
import sys
import requests
import time
import re
import json

from PIL import Image
from io import BytesIO
from datetime import datetime
# from videoprops import get_video_properties

from mdc.utils import *
from mdc.core.scraper import get_data_from_json
from mdc.utils.number_parser import is_uncensored
from mdc.image.imgproc import cutImage
from mdc.download.subtitles import download_subtitles

# 导入拆分的模块
from mdc.file.file_utils import *
from mdc.download.downloader import *
from mdc.core.metadata import *
from mdc.file.file_utils import escape_path, moveFailedFolder, create_folder, get_info
from mdc.download.downloader import (
    download_file_with_filename,
    trailer_download,
    actor_photo_download,
    extrafanart_download,
    image_download,
    image_ext,
)
from mdc.core.metadata import small_cover_check, print_files
from mdc.utils.logger import info as print, success, warn, error, debug


# from WebCrawler import get_data_from_json


def add_mark(poster_path, thumb_path, cn_sub, leak, uncensored, hack, _4k, iso) -> None:
    """
    add watermark on poster or thumb for describe extra properties 给海报和缩略图加属性水印

    :poster_path 海报位置
    :thumb_path 缩略图位置
    :cn_sub: 中文字幕 可选值：1,"1" 或其他值
    :uncensored 无码 可选值：1,"1" 或其他值
    :hack 破解 可选值：1,"1" 或其他值
    :_4k Bool
    """
    mark_type = ""
    if cn_sub:
        mark_type += ",字幕"
    if leak:
        mark_type += ",无码流出"
    if uncensored:
        mark_type += ",无码"
    if hack:
        mark_type += ",破解"
    if _4k:
        mark_type += ",4k"
    if iso:
        mark_type += ",iso"
    if mark_type == "":
        return
    add_mark_thread(thumb_path, cn_sub, leak, uncensored, hack, _4k, iso)
    add_mark_thread(poster_path, cn_sub, leak, uncensored, hack, _4k, iso)
    print("[+]Add Mark:         " + mark_type.strip(","))


def add_mark_thread(pic_path, cn_sub, leak, uncensored, hack, _4k, iso):
    size = 9
    if not pic_path or not os.path.isfile(pic_path):
        return
    img_pic = None
    try:
        img_pic = Image.open(pic_path)
        # 获取自定义位置，取余配合pos达到顺时针添加的效果
        # 左上 0, 右上 1, 右下 2， 左下 3
        count = config.getInstance().watermark_type()
        if cn_sub:
            add_to_pic(pic_path, img_pic, size, count, 1)  # 添加
            count = (count + 1) % 4
        if leak:
            add_to_pic(pic_path, img_pic, size, count, 2)
            count = (count + 1) % 4
        if uncensored:
            add_to_pic(pic_path, img_pic, size, count, 3)
            count = (count + 1) % 4
        if hack:
            add_to_pic(pic_path, img_pic, size, count, 4)
            count = (count + 1) % 4
        if _4k:
            add_to_pic(pic_path, img_pic, size, count, 5)
            count = (count + 1) % 4
        if iso:
            add_to_pic(pic_path, img_pic, size, count, 6)
    except Exception as e:
        warn(f"[-]Skip add mark: {pic_path} ({type(e).__name__})")
    finally:
        if img_pic:
            try:
                img_pic.close()
            except Exception:
                pass


def add_to_pic(pic_path, img_pic, size, count, mode):
    mark_pic_path = ""
    pngpath = ""
    if mode == 1:
        pngpath = "Img/SUB.png"
    elif mode == 2:
        pngpath = "Img/LEAK.png"
    elif mode == 3:
        pngpath = "Img/UNCENSORED.png"
    elif mode == 4:
        pngpath = "Img/HACK.png"
    elif mode == 5:
        pngpath = "Img/4K.png"
    elif mode == 6:
        pngpath = "Img/ISO.png"
    else:
        print("[-]Error: watermark image param mode invalid!")
        return
    # 先找pyinstaller打包的图片
    if hasattr(sys, "_MEIPASS") and os.path.isfile(
        os.path.join(getattr(sys, "_MEIPASS"), pngpath)
    ):
        mark_pic_path = os.path.join(getattr(sys, "_MEIPASS"), pngpath)
    # 再找py脚本所在路径的图片
    elif os.path.isfile(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), pngpath)
    ):
        mark_pic_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), pngpath
        )
    # 如果没有本地图片才通过网络下载
    else:
        mark_pic_path = BytesIO(
            get_html(
                "https://raw.githubusercontent.com/yoshiko2/AV_Data_Capture/master/"
                + pngpath,
                return_type="content",
            )
        )
    img_subt = Image.open(mark_pic_path)
    scroll_high = int(img_pic.height / size)
    scroll_wide = int(scroll_high * img_subt.width / img_subt.height)
    img_subt = img_subt.resize((scroll_wide, scroll_high), Image.Resampling.LANCZOS)
    r, g, b, a = img_subt.split()  # 获取颜色通道，保持png的透明性
    # 封面四个角的位置
    pos = [
        {"x": 0, "y": 0},
        {"x": img_pic.width - scroll_wide, "y": 0},
        {"x": img_pic.width - scroll_wide, "y": img_pic.height - scroll_high},
        {"x": 0, "y": img_pic.height - scroll_high},
    ]
    img_pic.paste(img_subt, (pos[count]["x"], pos[count]["y"]), mask=a)
    img_pic.save(pic_path, quality=95)


# ========================结束=================================


def paste_file_to_folder(
    filepath, path, multi_part, number, part, leak_word, c_word, hack_word
):  # 文件路径，番号，后缀，要移动至的位置
    filepath_obj = pathlib.Path(filepath)
    houzhui = filepath_obj.suffix
    try:
        targetpath = os.path.join(
            path, f"{number}{leak_word}{c_word}{hack_word}{houzhui}"
        )
        # 任何情况下都不要覆盖，以免遭遇数据源或者引擎错误导致所有文件得到同一个number，逐一
        # 同名覆盖致使全部文件损失且不可追回的最坏情况
        if os.path.exists(targetpath):
            raise FileExistsError(
                "File Exists on destination path, we will never overwriting."
            )
        link_mode = config.getInstance().link_mode()
        # 如果link_mode 1: 建立软链接 2: 硬链接优先、无法建立硬链接再尝试软链接。
        # 移除原先soft_link=2的功能代码，因默认记录日志，已经可追溯文件来源
        create_softlink = False
        action = None
        if link_mode not in (1, 2):
            shutil.move(filepath, targetpath)
            action = "Move"
        elif link_mode == 2:
            # 跨卷或跨盘符无法建立硬链接导致异常，回落到建立软链接
            try:
                os.link(filepath, targetpath, follow_symlinks=False)
                action = "Link"
            except:
                create_softlink = True
        if link_mode == 1 or create_softlink:
            # 先尝试采用相对路径，以便网络访问时能正确打开视频，失败则可能是因为跨盘符等原因无法支持
            # 相对路径径，改用绝对路径方式尝试建立软链接
            try:
                filerelpath = os.path.relpath(filepath, path)
                os.symlink(filerelpath, targetpath)
            except:
                os.symlink(str(filepath_obj.resolve()), targetpath)
            action = "Link"
        if action:
            print(f"[!]{action} =>          {path}")
        return

    except FileExistsError as fee:
        print(f"[-]FileExistsError: {fee}")
        moveFailedFolder(filepath)
        return
    except PermissionError:
        print("[-]Error! Please run as administrator!")
        return
    except OSError as oserr:
        print(f"[-]OS Error errno {oserr.errno}")
        return


def paste_file_to_folder_mode2(
    filepath, path, multi_part, number, part, leak_word, c_word, hack_word
):  # 文件路径，番号，后缀，要移动至的位置
    if multi_part == 1:
        number += part  # 这时number会被附加上CD1后缀
    filepath_obj = pathlib.Path(filepath)
    houzhui = filepath_obj.suffix
    targetpath = os.path.join(
        path, f"{number}{part}{leak_word}{c_word}{hack_word}{houzhui}"
    )
    if os.path.exists(targetpath):
        raise FileExistsError(
            "File Exists on destination path, we will never overwriting."
        )
    try:
        link_mode = config.getInstance().link_mode()
        create_softlink = False
        if link_mode not in (1, 2):
            shutil.move(filepath, targetpath)
            print("[!]Move =>          ", path)
            return
        elif link_mode == 2:
            try:
                os.link(filepath, targetpath, follow_symlinks=False)
            except:
                create_softlink = True
        if link_mode == 1 or create_softlink:
            try:
                filerelpath = os.path.relpath(filepath, path)
                os.symlink(filerelpath, targetpath)
            except:
                os.symlink(str(filepath_obj.resolve()), targetpath)
        print("[!]Link =>          ", path)
    except FileExistsError as fee:
        print(f"[-]FileExistsError: {fee}")
    except PermissionError:
        print("[-]Error! Please run as administrator!")
    except OSError as oserr:
        print(f"[-]OS Error errno  {oserr.errno}")


def linkImage(path, number, part, leak_word, c_word, hack_word, ext):
    """
    首先尝试为图片建立符合Jellyfin封面图文件名规则的硬连接以节省磁盘空间
    如果目标目录无法建立硬链接则将图片复制一份成为常规文件
    常规文件日期已经存在时，若修改日期比源文件更旧，则将被新的覆盖，否则忽略
    """
    if not all(len(v) for v in (path, number, part, ext)):
        return
    covers = ("-fanart", "-poster", "-thumb")
    normal_prefix = f"{number}{leak_word}{c_word}{hack_word}"
    multi_prefix = f"{number}{part}{leak_word}{c_word}{hack_word}"
    normal_pathes = (Path(path) / f"{normal_prefix}{c}{ext}" for c in covers)
    multi_pathes = (Path(path) / f"{multi_prefix}{c}{ext}" for c in covers)
    for normal_path, multi_path in zip(normal_pathes, multi_pathes):
        if not normal_path.is_file():
            continue
        mkLink = False
        if not multi_path.exists():
            mkLink = True
        elif multi_path.is_file():
            if multi_path.stat().st_nlink > 1:
                continue
            elif normal_path.stat().st_mtime <= multi_path.stat().st_mtime:
                continue
            mkLink = True
            multi_path.unlink(missing_ok=True)
        if not mkLink:
            continue
        try:
            os.link(str(normal_path), str(multi_path), follow_symlinks=False)
        except:
            shutil.copyfile(str(normal_path), str(multi_path))


def debug_print(data: json):
    try:
        print("[+] ------- DEBUG INFO -------")
        for i, v in data.items():
            if i == "outline":
                print("[+]  -", "%-19s" % i, ":", len(v), "characters")
                continue
            if i == "actor_photo" or i == "year":
                continue
            if i == "extrafanart":
                print("[+]  -", "%-19s" % i, ":", len(v), "links")
                continue
            print(f"[+]  - {i:<{cn_space(i, 19)}} : {v}")

        print("[+] ------- DEBUG INFO -------")
    except:
        pass


def core_main_no_net_op(movie_path, number):
    conf = config.getInstance()
    part = ""
    leak_word = ""
    leak = False
    c_word = ""
    cn_sub = False
    hack = False
    hack_word = ""
    _4k = False
    iso = False
    imagecut = 1
    multi = False
    part = ""
    path = str(Path(movie_path).parent)

    if re.search("[-_]CD\d+", movie_path, re.IGNORECASE):
        part = re.findall("[-_]CD\d+", movie_path, re.IGNORECASE)[0].upper()
        multi = True
    if (
        re.search(r"[-_]C(\.\w+$|-\w+)|\d+ch(\.\w+$|-\w+)", movie_path, re.I)
        or "中文" in movie_path
        or "字幕" in movie_path
        or ".chs" in movie_path
        or ".cht" in movie_path
    ):
        cn_sub = True
        c_word = "-C"  # 中文字幕影片后缀
    uncensored = True if is_uncensored(number) else 0
    if "流出" in movie_path or "uncensored" in movie_path.lower():
        leak_word = "-无码流出"  # 无码流出影片后缀
        leak = True

    if "hack".upper() in str(movie_path).upper() or "破解" in movie_path:
        hack = True
        hack_word = "-hack"

    if "4k".upper() in str(movie_path).upper() or "4k" in movie_path:
        _4k = True

    if ".iso".upper() in str(movie_path).upper() or ".iso" in movie_path:
        iso = True
    # try:

    #     props = get_video_properties(movie_path)  # 判断是否为4K视频
    #     if props['width'] >= 4096 or props['height'] >= 2160:
    #         _4k = True
    # except:
    #     pass
    prestr = f"{number}{leak_word}{c_word}{hack_word}"

    full_nfo = Path(path) / f"{prestr}{part}.nfo"
    if full_nfo.is_file():
        if full_nfo.read_text(encoding="utf-8").find(r"<tag>无码</tag>") >= 0:
            uncensored = True
        try:
            nfo_xml = etree.parse(full_nfo)
            nfo_fanart_path = nfo_xml.xpath("//fanart/text()")[0]
            ext = Path(nfo_fanart_path).suffix
        except:
            return
    else:
        return
    fanart_path = f"fanart{ext}"
    poster_path = f"poster{ext}"
    thumb_path = f"thumb{ext}"
    if config.getInstance().image_naming_with_number():
        fanart_path = f"{prestr}-fanart{ext}"
        poster_path = f"{prestr}-poster{ext}"
        thumb_path = f"{prestr}-thumb{ext}"
    full_fanart_path = os.path.join(path, fanart_path)
    full_poster_path = os.path.join(path, poster_path)
    full_thumb_path = os.path.join(path, thumb_path)

    if not all(os.path.isfile(f) for f in (full_fanart_path, full_thumb_path)):
        return

    cutImage(
        imagecut,
        path,
        fanart_path,
        poster_path,
        bool(conf.face_uncensored_only() and not uncensored),
    )
    if conf.is_watermark():
        add_mark(
            full_poster_path, full_thumb_path, cn_sub, leak, uncensored, hack, _4k, iso
        )

    if multi and conf.jellyfin_multi_part_fanart():
        linkImage(path, number, part, leak_word, c_word, hack_word, ext)


def move_subtitles(
    filepath, path, multi_part, number, part, leak_word, c_word, hack_word
) -> bool:
    filepath_obj = pathlib.Path(filepath)
    link_mode = config.getInstance().link_mode()
    sub_res = config.getInstance().sub_rule()
    result = False
    for subfile in filepath_obj.parent.glob("**/*"):
        if subfile.is_file() and subfile.suffix.lower() in sub_res:
            if multi_part and part.lower() not in subfile.name.lower():
                continue
            if (
                filepath_obj.stem.split(".")[0].lower()
                != subfile.stem.split(".")[0].lower()
            ):
                continue
            sub_targetpath = (
                Path(path)
                / f"{number}{leak_word}{c_word}{hack_word}{''.join(subfile.suffixes)}"
            )
            if link_mode not in (1, 2):
                shutil.move(str(subfile), str(sub_targetpath))
                print(f"[+]Sub Moved!        {sub_targetpath.name}")
                result = True
            else:
                shutil.copyfile(str(subfile), str(sub_targetpath))
                print(f"[+]Sub Copied!       {sub_targetpath.name}")
                result = True
            if result:
                break
    return result


def has_subtitles(filepath, path, multi_part, number, part, leak_word, c_word, hack_word):
    filepath_obj = pathlib.Path(filepath)
    sub_res = config.getInstance().sub_rule()
    prefix = f"{number}{leak_word}{c_word}{hack_word}".lower()
    for subfile in Path(path).glob("*"):
        if not subfile.is_file():
            continue
        if subfile.suffix.lower() not in sub_res:
            continue
        if multi_part and part and part.lower() not in subfile.name.lower():
            continue
        if subfile.name.lower().startswith(prefix):
            return True
    for subfile in filepath_obj.parent.glob("**/*"):
        if subfile.is_file() and subfile.suffix.lower() in sub_res:
            if multi_part and part.lower() not in subfile.name.lower():
                continue
            if (
                filepath_obj.stem.split(".")[0].lower()
                != subfile.stem.split(".")[0].lower()
            ):
                continue
            return True
    return False


def core_main(movie_path, number_th, oCC, specified_source=None, specified_url=None):
    conf = config.getInstance()
    # =======================================================================初始化所需变量
    multi_part = False
    part = ""
    leak_word = ""
    c_word = ""
    cn_sub = False
    liuchu = False
    hack = False
    hack_word = ""
    _4k = False
    iso = False

    # 下面被注释的变量不需要
    # rootpath = os.getcwd
    number = number_th
    json_data = get_data_from_json(
        number, oCC, specified_source, specified_url
    )  # 定义番号

    # Return if blank dict returned (data not found)
    if not json_data:
        moveFailedFolder(movie_path)
        return

    if json_data["number"] != number:
        # fix issue #119
        # the root cause is we normalize the search id
        # print_files() will use the normalized id from website,
        # but paste_file_to_folder() still use the input raw search id
        # so the solution is: use the normalized search id
        number = json_data["number"]
    imagecut = json_data.get("imagecut")
    tag = json_data.get("tag")
    # =======================================================================判断-C,-CD后缀
    if re.search("[-_]CD\d+", movie_path, re.IGNORECASE):
        multi_part = True
        part = re.findall("[-_]CD\d+", movie_path, re.IGNORECASE)[0].upper()
    if (
        re.search(r"[-_]C(\.\w+$|-\w+)|\d+ch(\.\w+$|-\w+)", movie_path, re.I)
        or "中文" in movie_path
        or "字幕" in movie_path
    ):
        cn_sub = True
        c_word = "-C"  # 中文字幕影片后缀

    if re.search(r"[-_]UC(\.\w+$|-\w+)", movie_path, re.I):
        cn_sub = True
        c_word = "-UC"  #
        hack = True
        hack_word = "-UC"

    if re.search(r"[-_]U(\.\w+$|-\w+)", movie_path, re.I):  #
        hack = True
        hack_word = "-U"

    # 判断是否无码
    unce = json_data.get("无码")
    uncensored = int(unce) if isinstance(unce, bool) else int(is_uncensored(number))

    if "流出" in movie_path or "uncensored" in movie_path.lower():
        liuchu = "流出"
        leak = True
        leak_word = "-无码流出"  # 流出影片后缀
    else:
        leak = False

    if "hack".upper() in str(movie_path).upper() or "破解" in movie_path:
        hack = True
        hack_word = "-hack"

    if "4k".upper() in str(movie_path).upper() or "4k" in movie_path:
        _4k = True

    if ".iso".upper() in str(movie_path).upper() or ".iso" in movie_path:
        iso = True

    # 判断是否4k
    if "4K" in tag:
        tag.remove("4K")  # 从tag中移除'4K'

    # 判断是否为无码破解
    if "无码破解" in tag:
        tag.remove("无码破解")  # 从tag中移除'无码破解'

    # try:
    #     props = get_video_properties(movie_path)  # 判断是否为4K视频
    #     if props['width'] >= 4096 or props['height'] >= 2160:
    #         _4k = True
    # except:
    #     pass

    # 调试模式检测
    if conf.debug():
        debug_print(json_data)

    # 创建文件夹
    # path = create_folder(rootpath + '/' + conf.success_folder(),  json_data.get('location_rule'), json_data)

    cover = json_data.get("cover")
    ext = image_ext(cover)

    fanart_path = f"fanart{ext}"
    poster_path = f"poster{ext}"
    thumb_path = f"thumb{ext}"
    if config.getInstance().image_naming_with_number():
        fanart_path = f"{number}{leak_word}{c_word}{hack_word}-fanart{ext}"
        poster_path = f"{number}{leak_word}{c_word}{hack_word}-poster{ext}"
        thumb_path = f"{number}{leak_word}{c_word}{hack_word}-thumb{ext}"

    # main_mode
    #  1: 刮削模式 / Scraping mode
    #  2: 整理模式 / Organizing mode
    #  3：不改变路径刮削
    if conf.main_mode() == 1:
        # 创建文件夹
        path = create_folder(json_data)
        if multi_part == 1:
            number += part  # 这时number会被附加上CD1后缀

        # 检查小封面, 如果image cut为3，则下载小封面
        if imagecut == 3:
            if "headers" in json_data:
                small_cover_check(
                    path,
                    poster_path,
                    json_data.get("cover_small"),
                    movie_path,
                    json_data,
                )
            else:
                small_cover_check(
                    path, poster_path, json_data.get("cover_small"), movie_path
                )

        # creatFolder会返回番号路径
        if "headers" in json_data:
            image_download(cover, fanart_path, thumb_path, path, movie_path, json_data)
        else:
            image_download(cover, fanart_path, thumb_path, path, movie_path)

        if not multi_part or part.lower() == "-cd1":
            try:
                # 下载预告片
                if conf.is_trailer() and json_data.get("trailer"):
                    trailer_download(
                        json_data.get("trailer"),
                        leak_word,
                        c_word,
                        hack_word,
                        number,
                        path,
                        movie_path,
                    )

                # 下载剧照 data, path, filepath
                if conf.is_extrafanart() and json_data.get("extrafanart"):
                    if "headers" in json_data:
                        extrafanart_download(
                            json_data.get("extrafanart"),
                            path,
                            number,
                            movie_path,
                            json_data,
                        )
                    else:
                        extrafanart_download(
                            json_data.get("extrafanart"), path, number, movie_path
                        )

                # 下载演员头像 KODI .actors 目录位置
                if conf.download_actor_photo_for_kodi():
                    actor_photo_download(json_data.get("actor_photo"), path, number)
            except:
                pass

        # 裁剪图
        cutImage(
            imagecut,
            path,
            thumb_path,
            poster_path,
            bool(conf.face_uncensored_only() and not uncensored),
        )

        # 兼容Jellyfin封面图文件名规则
        if multi_part and conf.jellyfin_multi_part_fanart():
            linkImage(path, number_th, part, leak_word, c_word, hack_word, ext)

        # 移动电影
        paste_file_to_folder(
            movie_path, path, multi_part, number, part, leak_word, c_word, hack_word
        )

        # Move subtitles
        move_status = move_subtitles(
            movie_path, path, multi_part, number, part, leak_word, c_word, hack_word
        )
        if move_status:
            cn_sub = True
        else:
            cn_sub = cn_sub or download_subtitles(
                movie_path, path, multi_part, number, part, leak_word, c_word, hack_word
            )
        # 添加水印
        if conf.is_watermark():
            add_mark(
                os.path.join(path, poster_path),
                os.path.join(path, thumb_path),
                cn_sub,
                leak,
                uncensored,
                hack,
                _4k,
                iso,
            )

        # 最后输出.nfo元数据文件，以完成.nfo文件创建作为任务成功标志
        print_files(
            path,
            leak_word,
            c_word,
            json_data.get("naming_rule"),
            part,
            cn_sub,
            json_data,
            movie_path,
            tag,
            json_data.get("actor_list"),
            liuchu,
            uncensored,
            hack,
            hack_word,
            _4k,
            fanart_path,
            poster_path,
            thumb_path,
            iso,
        )

    elif conf.main_mode() == 2:
        # 创建文件夹
        path = create_folder(json_data)
        # 移动文件
        paste_file_to_folder_mode2(
            movie_path, path, multi_part, number, part, leak_word, c_word, hack_word
        )

        # Move subtitles
        move_subtitles(
            movie_path, path, multi_part, number, part, leak_word, c_word, hack_word
        ) or download_subtitles(
            movie_path, path, multi_part, number, part, leak_word, c_word, hack_word
        )

    elif conf.main_mode() == 3:
        path = str(Path(movie_path).parent)
        if multi_part == 1:
            number += part  # 这时number会被附加上CD1后缀

        # 检查小封面, 如果image cut为3，则下载小封面
        if imagecut == 3:
            if "headers" in json_data:
                small_cover_check(
                    path,
                    poster_path,
                    json_data.get("cover_small"),
                    movie_path,
                    json_data,
                )
            else:
                small_cover_check(
                    path, poster_path, json_data.get("cover_small"), movie_path
                )

        # creatFolder会返回番号路径
        if "headers" in json_data:
            image_download(cover, fanart_path, thumb_path, path, movie_path, json_data)
        else:
            image_download(cover, fanart_path, thumb_path, path, movie_path)

        if not multi_part or part.lower() == "-cd1":
            try:
                # 下载预告片
                if conf.is_trailer() and json_data.get("trailer"):
                    trailer_download(
                        json_data.get("trailer"),
                        leak_word,
                        c_word,
                        hack_word,
                        number,
                        path,
                        movie_path,
                    )

                # 下载剧照 data, path, filepath
                if conf.is_extrafanart() and json_data.get("extrafanart"):
                    if "headers" in json_data:
                        extrafanart_download(
                            json_data.get("extrafanart"),
                            path,
                            number,
                            movie_path,
                            json_data,
                        )
                    else:
                        extrafanart_download(
                            json_data.get("extrafanart"), path, number, movie_path
                        )

                # 下载演员头像 KODI .actors 目录位置
                if conf.download_actor_photo_for_kodi():
                    actor_photo_download(json_data.get("actor_photo"), path, number)
            except:
                pass

        # 裁剪图
        cutImage(
            imagecut,
            path,
            fanart_path,
            poster_path,
            bool(conf.face_uncensored_only() and not uncensored),
        )

        if not cn_sub and has_subtitles(
            movie_path, path, multi_part, number, part, leak_word, c_word, hack_word
        ):
            cn_sub = True
        if not cn_sub:
            cn_sub = cn_sub or download_subtitles(
                movie_path, path, multi_part, number, part, leak_word, c_word, hack_word
            )

        # 添加水印
        if conf.is_watermark():
            add_mark(
                os.path.join(path, poster_path),
                os.path.join(path, fanart_path),
                cn_sub,
                leak,
                uncensored,
                hack,
                _4k,
                iso,
            )

        # 兼容Jellyfin封面图文件名规则
        if multi_part and conf.jellyfin_multi_part_fanart():
            linkImage(path, number_th, part, leak_word, c_word, hack_word, ext)

        # 最后输出.nfo元数据文件，以完成.nfo文件创建作为任务成功标志
        print_files(
            path,
            leak_word,
            c_word,
            json_data.get("naming_rule"),
            part,
            cn_sub,
            json_data,
            movie_path,
            tag,
            json_data.get("actor_list"),
            liuchu,
            uncensored,
            hack,
            hack_word,
            _4k,
            fanart_path,
            poster_path,
            thumb_path,
            iso,
        )
