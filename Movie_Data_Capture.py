import json
import os
import random
import sys
import time
import shutil
import typing
import urllib3
import signal
import platform
from mdc.config import config
import logging

from datetime import datetime, timedelta
from pathlib import Path
from opencc import OpenCC

from mdc.core.scraper import get_data_from_json
from mdc.file.file_utils import file_modification_days
from mdc.utils.http import get_html
from mdc.utils.number_parser import get_number
from mdc.core.core import core_main, core_main_no_net_op, debug_print
from mdc.cli.cli import argparse_function
from mdc.file.movie_list import movie_lists
from mdc.file.file_utils import moveFailedFolder, create_failed_folder, rm_empty_folder


# 日志配置
LOGGER = None
LOG_FILE_PATH = None


class StreamToLogger:
    """
    将流重定向到logger的类
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.linebuf = ''
    
    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())
    
    def flush(self):
        pass


def setup_logging(logdir):
    """
    配置logging系统
    """
    global LOGGER, LOG_FILE_PATH
    
    if not logdir or not isinstance(logdir, str):
        return
    
    log_dir = Path(logdir)
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except:
            return
            
    if not log_dir.is_dir():
        return  # 通过将目录设为同名空文件来禁用日志
    
    # 创建日志文件路径
    log_tmstr = datetime.now().strftime("%Y%m%dT%H%M%S")
    LOG_FILE_PATH = log_dir / f"mdc_{log_tmstr}.txt"
    
    # 配置根日志
    LOGGER = logging.getLogger('MDC')
    LOGGER.setLevel(logging.INFO)
    
    # 清除已有的handler
    for handler in LOGGER.handlers[:]:
        LOGGER.removeHandler(handler)
    
    # 创建文件handler
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    
    # 创建控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置日志格式
    formatter = logging.Formatter('%(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加handler
    LOGGER.addHandler(file_handler)
    LOGGER.addHandler(console_handler)
    
    # 重定向标准输出和标准错误
    sys.stdout = StreamToLogger(LOGGER, logging.INFO)
    sys.stderr = StreamToLogger(LOGGER, logging.ERROR)


def cleanup_logging(logdir):
    """
    清理日志系统
    """
    global LOGGER, LOG_FILE_PATH
    
    if not logdir or not isinstance(logdir, str) or not os.path.isdir(logdir):
        return None
    
    # 恢复标准输出和标准错误
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
    
    # 清除handler
    if LOGGER:
        for handler in LOGGER.handlers[:]:
            handler.close()
            LOGGER.removeHandler(handler)
    
    filepath = LOG_FILE_PATH
    
    if filepath:
        print(f"Log file '{filepath}' saved.")
    
    return filepath



def check_update(local_version: str) -> None:
    htmlcode = get_html(
        "https://api.github.com/repos/yoshiko2/Movie_Data_Capture/releases/latest"
    )
    data = json.loads(htmlcode)
    remote = int(data["tag_name"].replace(".", ""))
    local_version_int = int(local_version.replace(".", ""))
    if local_version_int < remote:
        print("[*]" + ("* New update " + str(data["tag_name"]) + " *").center(54))
        print("[*]" + "↓ Download ↓".center(54))
        print("[*]https://github.com/yoshiko2/Movie_Data_Capture/releases")
        print("[*]======================================================")



def signal_handler(*args) -> None:
    print("[!]Ctrl+C detected, Exit.")
    os._exit(9)



def sigdebug_handler(*args) -> None:
    conf = config.getInstance()
    conf.set_override(f"debug_mode:switch={int(not conf.debug())}")
    print(f"[!]Debug {('oFF', 'On')[int(conf.debug())]}")



def create_data_and_move(movie_path: str, zero_op: bool, no_net_op: bool, oCC: typing.Optional[OpenCC]) -> None:
    # Normalized number, eg: 111xxx-222.mp4 -> xxx-222.mp4
    debug = config.getInstance().debug()
    n_number = get_number(debug, os.path.basename(movie_path))
    movie_path = os.path.abspath(movie_path)

    if debug is True:
        print(f"[!] [{n_number}] As Number Processing for '{movie_path}'")
        if zero_op:
            return
        if n_number:
            if no_net_op:
                core_main_no_net_op(movie_path, n_number)
            else:
                core_main(movie_path, n_number, oCC)
        else:
            print("[-] number empty ERROR")
            moveFailedFolder(movie_path)
        print("[*]======================================================")
    else:
        try:
            print(f"[!] [{n_number}] As Number Processing for '{movie_path}'")
            if zero_op:
                return
            if n_number:
                if no_net_op:
                    core_main_no_net_op(movie_path, n_number)
                else:
                    core_main(movie_path, n_number, oCC)
            else:
                raise ValueError("number empty")
            print("[*]======================================================")
        except Exception as err:
            print(f"[-] [{movie_path}] ERROR:")
            print("[-]", err)

            try:
                moveFailedFolder(movie_path)
            except Exception as err:
                print("[!]", err)



def create_data_and_move_with_custom_number(
    file_path: str, custom_number: str, oCC: typing.Optional[OpenCC], specified_source: str, specified_url: str
) -> None:
    conf = config.getInstance()
    file_name = os.path.basename(file_path)
    try:
        print(
            "[!] [{1}] As Number Processing for '{0}'".format(file_path, custom_number)
        )
        if custom_number:
            core_main(file_path, custom_number, oCC, specified_source, specified_url)
        else:
            print("[-] number empty ERROR")
        print("[*]======================================================")
    except Exception as err:
        print("[-] [{}] ERROR:".format(file_path))
        print("[-]", err)

        if conf.link_mode() in (1, 2):
            print("[-]Link {} to failed folder".format(file_path))
            os.symlink(file_path, os.path.join(conf.failed_folder(), file_name))
        else:
            try:
                print("[-]Move [{}] to failed folder".format(file_path))
                shutil.move(file_path, os.path.join(conf.failed_folder(), file_name))
            except Exception as err:
                print("[!]", err)



def main(args: tuple) -> typing.Optional[Path]:
    (
        single_file_path,
        custom_number,
        logdir,
        regexstr,
        zero_op,
        no_net_op,
        search,
        specified_source,
        specified_url,
    ) = args
    conf = config.getInstance()
    main_mode = conf.main_mode()
    folder_path = ""
    if main_mode not in (1, 2, 3):
        print(
            f"[-]Main mode must be 1 or 2 or 3! You can run '{os.path.basename(sys.argv[0])} --help' for more help."
        )
        os._exit(4)

    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform == "win32":
        signal.signal(signal.SIGBREAK, sigdebug_handler)
    else:
        signal.signal(signal.SIGWINCH, sigdebug_handler)
    setup_logging(logdir)

    platform_total = str(
        " - "
        + platform.platform()
        + " \n[*] - "
        + platform.machine()
        + " - Python-"
        + platform.python_version()
    )

    print("[*]================= Movie Data Capture =================")
    print("[*]" + version.center(54))
    print("[*]======================================================")
    print("[*]" + platform_total)
    print("[*]======================================================")
    print("[*] - 严禁在墙内宣传本项目 - ")
    print("[*]======================================================")

    start_time = time.time()
    print("[+]Start at", time.strftime("%Y-%m-%d %H:%M:%S"))

    print(f"[+]Load Config file '{conf.ini_path}'.")
    if conf.debug():
        print("[+]Enable debug")
    if conf.link_mode() in (1, 2):
        print("[!]Enable {} link".format(("soft", "hard")[conf.link_mode() - 1]))
    if len(sys.argv) > 1:
        print("[!]CmdLine:", " ".join(sys.argv[1:]))
    print(
        "[+]Main Working mode ## {}: {} ## {}{}{}".format(
            *(
                main_mode,
                ["Scraping", "Organizing", "Scraping in analysis folder"]
                [
                    main_mode - 1
                ],
                "" if not conf.multi_threading() else ", multi_threading on",
                ""
                if conf.nfo_skip_days() == 0
                else f", nfo_skip_days={conf.nfo_skip_days()}",
                ""
                if conf.stop_counter() == 0
                else f", stop_counter={conf.stop_counter()}",
            )
            if not single_file_path
            else ("-", "Single File", "", "", "")
        )
    )

    create_failed_folder(conf.failed_folder())

    # create OpenCC converter
    ccm = conf.cc_convert_mode()
    try:
        oCC = None if ccm == 0 else OpenCC("t2s.json" if ccm == 1 else "s2t.json")
    except:
        # some OS no OpenCC cpython, try opencc-python-reimplemented.
        # pip uninstall opencc && pip install opencc-python-reimplemented
        oCC = None if ccm == 0 else OpenCC("t2s" if ccm == 1 else "s2t")

    if not search == "":
        search_list = search.split(",")
        for i in search_list:
            json_data = get_data_from_json(i, oCC, None, None)
            debug_print(json_data)
            time.sleep(int(config.getInstance().sleep()))
        os._exit(0)

    if not single_file_path == "":  # Single File
        print("[+]==================== Single File ====================")
        if custom_number == "":
            create_data_and_move_with_custom_number(
                single_file_path,
                get_number(conf.debug(), os.path.basename(single_file_path)),
                oCC,
                specified_source,
                specified_url,
            )
        else:
            create_data_and_move_with_custom_number(
                single_file_path, custom_number, oCC, specified_source, specified_url
            )
    else:
        folder_path = conf.source_folder()
        if not isinstance(folder_path, str) or folder_path == "":
            folder_path = os.path.abspath(".")

        movie_list = movie_lists(folder_path, regexstr)

        count = 0
        count_all = str(len(movie_list))
        print("[+]Find", count_all, "movies.")
        print("[*]======================================================")
        stop_count = conf.stop_counter()
        if stop_count < 1:
            stop_count = 999999
        else:
            count_all = str(min(len(movie_list), stop_count))

        for movie_path in movie_list:  # 遍历电影列表 交给core处理
            count = count + 1
            percentage = str(count / int(count_all) * 100)[:4] + "%"
            print(
                "[!] {:>30}{:>21}".format(
                    "- " + percentage + " [" + str(count) + "/" + count_all + "] -",
                    time.strftime("%H:%M:%S"),
                )
            )
            create_data_and_move(movie_path, zero_op, no_net_op, oCC)
            if count >= stop_count:
                print("[!]Stop counter triggered!")
                break
            sleep_seconds = random.randint(conf.sleep(), conf.sleep() + 2)
            time.sleep(sleep_seconds)

    end_time = time.time()
    print("[+]Finish at", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("[+]Total time: {:.2f}s".format(end_time - start_time))

    rm_empty_folder(conf.source_folder())

    if conf.auto_exit():
        print("[!]Auto exit after program complete")
    else:
        try:
            input("[*]Press Enter to exit...")
        except KeyboardInterrupt:
            pass

    logfile_path = cleanup_logging(logdir)
    return logfile_path


version = "5.6.9"


if __name__ == "__main__":
    args_tuple = argparse_function(version)
    main(args_tuple)
    if config.getInstance().auto_exit():
        os._exit(0)
