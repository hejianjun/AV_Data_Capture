import os
import shutil
import time
from pathlib import Path
from mdc.config import config
from datetime import datetime


def escape_path(path, escape_literals: str):  # Remove escape literals
    backslash = "\\"
    for literal in escape_literals:
        path = path.replace(backslash + literal, "")
    return path


def moveFailedFolder(filepath):
    conf = config.getInstance()
    failed_folder = conf.failed_folder()
    link_mode = conf.link_mode()
    # 模式3或软连接，改为维护一个失败列表，启动扫描时加载用于排除该路径，以免反复处理
    # 原先的创建软连接到失败目录，并不直观，不方便找到失败文件位置，不如直接记录该文件路径
    if conf.main_mode() == 3 or link_mode:
        ftxt = os.path.abspath(os.path.join(failed_folder, "failed_list.txt"))
        print("[-]Add to Failed List file, see '%s'" % ftxt)
        with open(ftxt, "a", encoding="utf-8") as flt:
            flt.write(f"{filepath}\n")
    elif conf.failed_move() and not link_mode:
        failed_name = os.path.join(failed_folder, os.path.basename(filepath))
        mtxt = os.path.abspath(
            os.path.join(failed_folder, "where_was_i_before_being_moved.txt")
        )
        print("'[-]Move to Failed output folder, see '%s'" % mtxt)
        with open(mtxt, "a", encoding="utf-8") as wwibbmt:
            tmstr = datetime.now().strftime("%Y-%m-%d %H:%M")
            wwibbmt.write(f"{tmstr} FROM[{filepath}]TO[{failed_name}]\n")
        try:
            if os.path.exists(failed_name):
                print("[-]File Exists while moving to FailedFolder")
                return
            shutil.move(filepath, failed_name)
        except:
            print("[-]File Moving to FailedFolder unsuccessful!")


def create_folder(json_data):  # 创建文件夹
    (title, studio, year, outline, runtime, director, actor_photo, release, number, 
     cover, trailer, website, series, label) = get_info(json_data)
    conf = config.getInstance()
    success_folder = conf.success_folder()
    actor = json_data.get("actor")
    location_rule = eval(conf.location_rule(), json_data)
    if "actor" in conf.location_rule() and len(actor) > 100:
        print(conf.location_rule())
        location_rule = eval(
            conf.location_rule().replace("actor", "'多人作品'"), json_data
        )
    maxlen = conf.max_title_len()
    if "title" in conf.location_rule() and len(title) > maxlen:
        shorttitle = title[0:maxlen]
        location_rule = location_rule.replace(title, shorttitle)
    # 当演员为空时，location_rule被计算为'/number'绝对路径，导致路径连接忽略第一个路径参数，因此添加./使其始终为相对路径
    path = os.path.join(success_folder, f"./{location_rule.strip()}")
    if not os.path.exists(path):
        path = escape_path(path, conf.escape_literals())
        try:
            os.makedirs(path)
        except:
            path = (
                success_folder
                + "/"
                + location_rule.replace("/[" + number + ")-" + title, "/number")
            )
            path = escape_path(path, conf.escape_literals())
            try:
                os.makedirs(path)
            except:
                print(f"[-]Fatal error! Can not make folder '{path}'")
                os._exit(0)

    return os.path.normpath(path)


def create_failed_folder(failed_folder: str) -> None:
    """
    Create failed folder
    """
    if not os.path.exists(failed_folder):
        try:
            os.makedirs(failed_folder)
        except:
            print(f"[-]Fatal error! Can not make folder '{failed_folder}'")
            os._exit(0)


def rm_empty_folder(path: str) -> None:
    abspath = os.path.abspath(path)
    deleted = set()
    for current_dir, subdirs, files in os.walk(abspath, topdown=False):
        try:
            still_has_subdirs = any(
                True
                for subdir in subdirs
                if os.path.join(current_dir, subdir) not in deleted
            )
            if (
                not any(files)
                and not still_has_subdirs
                and not os.path.samefile(path, current_dir)
            ):
                os.rmdir(current_dir)
                deleted.add(current_dir)
                print("[+]Deleting empty folder", current_dir)
        except:
            pass


def file_not_exist_or_empty(filepath):
    if not os.path.exists(filepath):
        return True
    if os.path.isfile(filepath):
        return os.path.getsize(filepath) == 0
    return False


def file_modification_days(filename: str) -> int:
    """
    文件修改时间距此时的天数
    """
    mfile = Path(filename)
    if not mfile.is_file():
        return 9999
    mtime = int(mfile.stat().st_mtime)
    now = int(time.time())
    days = int((now - mtime) / (24 * 60 * 60))
    if days < 0:
        return 9999
    return days

# 由于get_info函数被多个模块使用，暂时保留在file_utils.py中
def get_info(json_data):  # 返回json里的数据
    title = json_data.get("title")
    studio = json_data.get("studio")
    year = json_data.get("year")
    outline = json_data.get("outline")
    runtime = json_data.get("runtime")
    director = json_data.get("director")
    actor_photo = json_data.get("actor_photo", {})
    release = json_data.get("release")
    number = json_data.get("number")
    cover = json_data.get("cover")
    trailer = json_data.get("trailer")
    website = json_data.get("website")
    series = json_data.get("series")
    label = json_data.get("label", "")
    return (
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
    )
