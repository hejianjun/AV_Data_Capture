import json
import os
import random
import sys
import time
import shutil
import itertools
import typing
import signal
import platform
from mdc.config import config
import logging


from datetime import datetime
from pathlib import Path
from opencc import OpenCC

from mdc.core.scraper import get_data_from_json
from mdc.utils.http import get_html
from mdc.utils.number_parser import get_number
from mdc.core.core import core_main, core_main_no_net_op, debug_print
from mdc.cli.cli import argparse_function
from mdc.file.movie_list import movie_lists
from mdc.file.file_utils import (
    moveFailedFolder,
    create_failed_folder,
    rm_empty_folder,
    mode3_should_execute_by_nfo,
)
from mdc.utils.system import WindowsInhibitor


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
        self.linebuf = ""

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.level, line.rstrip())

    def flush(self):
        pass


class ColorFormatter(logging.Formatter):
    def __init__(self, fmt="%(message)s", use_color=True):
        super().__init__(fmt)
        self.use_color = use_color

    def format(self, record):
        msg = super().format(record)
        if not self.use_color:
            return msg

        def _rgb(msg, r, g, b):
            return f"\x1b[38;2;{r};{g};{b}m{msg}\x1b[0m"

        prefix_color_map = {
            "[-]": (255, 107, 107),
            "[!]": (214, 214, 90),
            "[+]": (111, 211, 78),
            "[D]": (77, 163, 230),
            "[*]": (111, 211, 78),
        }

        msg_strip = msg.lstrip()
        for prefix, (r, g, b) in prefix_color_map.items():
            if msg_strip.startswith(prefix):
                return _rgb(msg, r, g, b)

        level_color_map = {
            logging.DEBUG: (77, 163, 230),
            logging.INFO: (111, 211, 78),
            logging.WARNING: (214, 214, 90),
            logging.ERROR: (255, 107, 107),
            logging.CRITICAL: (255, 107, 107),
        }
        rgb = level_color_map.get(record.levelno)
        return _rgb(msg, *rgb) if rgb else msg


def _enable_windows_vt_mode():
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        for handle_id in (-11, -12):
            handle = kernel32.GetStdHandle(handle_id)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        return


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
        except OSError:
            return

    if not log_dir.is_dir():
        return  # 通过将目录设为同名空文件来禁用日志

    # 创建日志文件路径
    log_tmstr = datetime.now().strftime("%Y%m%dT%H%M%S")
    LOG_FILE_PATH = log_dir / f"mdc_{log_tmstr}.txt"

    _enable_windows_vt_mode()
    debug_on = bool(config.getInstance().debug())

    # 配置根日志
    LOGGER = logging.getLogger("MDC")
    LOGGER.setLevel(logging.DEBUG if debug_on else logging.INFO)

    # 清除已有的handler
    for handler in LOGGER.handlers[:]:
        LOGGER.removeHandler(handler)

    # 创建文件handler
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG if debug_on else logging.INFO)

    # 创建控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if debug_on else logging.INFO)

    # 设置日志格式
    file_handler.setFormatter(logging.Formatter("%(message)s"))
    use_color = bool(
        getattr(console_handler.stream, "isatty", lambda: False)()
        and os.getenv("NO_COLOR") is None
    )
    console_handler.setFormatter(ColorFormatter("%(message)s", use_color=use_color))

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


def create_data_and_move(
    movie_path: str, zero_op: bool, no_net_op: bool, oCC: typing.Optional[OpenCC]
) -> None:
    # Normalized number, eg: 111xxx-222.mp4 -> xxx-222.mp4
    debug = config.getInstance().debug()
    n_number = get_number(debug, os.path.basename(movie_path))
    movie_path = os.path.abspath(movie_path)

    if debug is True:
        print(f"[!] [{n_number}] As Number Processing for '{movie_path}'")
        if zero_op:
            return
        if config.getInstance().main_mode() == 3 and not no_net_op:
            nfo_path = str(Path(movie_path).with_suffix(".nfo"))
            if not mode3_should_execute_by_nfo(nfo_path):
                print(f"[!]Skip by existing NFO: '{movie_path}'")
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
            if config.getInstance().main_mode() == 3 and not no_net_op:
                nfo_path = str(Path(movie_path).with_suffix(".nfo"))
                if not mode3_should_execute_by_nfo(nfo_path):
                    print(f"[!]Skip by existing NFO: '{movie_path}'")
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
    file_path: str,
    custom_number: str,
    oCC: typing.Optional[OpenCC],
    specified_source: str,
    specified_url: str,
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

    os_inhibitor = WindowsInhibitor()
    os_inhibitor.inhibit()

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
                ["Scraping", "Organizing", "Scraping in analysis folder"][
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
    except Exception:
        # some OS no OpenCC cpython, try opencc-python-reimplemented.
        # pip uninstall opencc && pip install opencc-python-reimplemented
        oCC = None if ccm == 0 else OpenCC("t2s" if ccm == 1 else "s2t")

    if not search == "":
        search_list = search.split(",")
        for i in search_list:
            json_data = get_data_from_json(i, oCC, None, None)
            debug_print(json_data)
            time.sleep(int(config.getInstance().sleep()))
        os_inhibitor.uninhibit()
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

        stop_count = conf.stop_counter()
        if stop_count < 1:
            stop_count = 999999
        movie_iter = movie_lists(folder_path, regexstr)
        peek_limit = 100
        peeked_movies = list(itertools.islice(movie_iter, peek_limit))
        movie_iter = itertools.chain(peeked_movies, movie_iter)

        count = 0
        count_all_int = None
        if stop_count != 999999:
            if len(peeked_movies) < stop_count:
                count_all_int = len(peeked_movies)
            elif stop_count <= peek_limit:
                count_all_int = stop_count
        elif len(peeked_movies) < peek_limit:
            count_all_int = len(peeked_movies)

        count_all = str(count_all_int) if count_all_int is not None else "99+"
        print("[+]Find", count_all, "movies.")
        print("[*]======================================================")

        for movie_path in movie_iter:  # 遍历电影列表 交给core处理
            count = count + 1
            if count_all_int:
                percentage = str(count / count_all_int * 100)[:4] + "%"
                progress_str = (
                    "- "
                    + percentage
                    + " ["
                    + str(count)
                    + "/"
                    + count_all
                    + "] -"
                )
            else:
                progress_str = "- [" + str(count) + "/" + count_all + "] -"
            print(
                "[!] {:>30}{:>21}".format(
                    progress_str,
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

    os_inhibitor.uninhibit()

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
