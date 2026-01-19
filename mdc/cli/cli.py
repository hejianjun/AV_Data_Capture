import argparse
import typing
import os
from mdc.config import config
from pathlib import Path


def argparse_function(
    ver: str,
) -> typing.Tuple[str, str, str, str, bool, bool, str, str, str]:
    conf = config.getInstance()
    parser = argparse.ArgumentParser(epilog=f"Load Config file '{conf.ini_path}'.")
    parser.add_argument("file", default="", nargs="?", help="Single Movie file path.")
    parser.add_argument(
        "-p", "--path", default="", nargs="?", help="Analysis folder path."
    )
    parser.add_argument(
        "-m",
        "--main-mode",
        default="",
        nargs="?",
        help="Main mode. 1:Scraping 2:Organizing 3:Scraping in analysis folder",
    )
    parser.add_argument(
        "-n",
        "--number",
        default="",
        nargs="?",
        help="Custom file number of single movie file.",
    )
    parser.add_argument(
        "-L",
        "--link-mode",
        default="",
        nargs="?",
        help="Create movie file link. 0:moving movie file, do not create link 1:soft link 2:try hard link first",
    )
    default_logdir = str(Path.home() / ".mlogs")
    parser.add_argument(
        "-o",
        "--log-dir",
        dest="logdir",
        default=default_logdir,
        nargs="?",
        help=f"""Duplicate stdout and stderr to logfiles in logging folder, default on.
        default folder for current user: '{default_logdir}'. Change default folder to an empty file,
        or use --log-dir= to turn log off.""",
    )
    parser.add_argument(
        "-q",
        "--regex-query",
        dest="regexstr",
        default="",
        nargs="?",
        help="python re module regex filepath filtering.",
    )
    parser.add_argument(
        "-d",
        "--nfo-skip-days",
        dest="days",
        default="",
        nargs="?",
        help="Override nfo_skip_days value in config.",
    )
    parser.add_argument(
        "-c",
        "--stop-counter",
        dest="cnt",
        default="",
        nargs="?",
        help="Override stop_counter value in config.",
    )
    parser.add_argument(
        "-R",
        "--rerun-delay",
        dest="delaytm",
        default="",
        nargs="?",
        help="Delay (eg. 1h10m30s or 60 (second)) time and rerun, until all movies proceed. Note: stop_counter value in config or -c must none zero.",
    )
    parser.add_argument(
        "-i",
        "--ignore-failed-list",
        action="store_true",
        help="Ignore failed list '{}'".format(
            os.path.join(os.path.abspath(conf.failed_folder()), "failed_list.txt")
        ),
    )
    parser.add_argument(
        "-a",
        "--auto-exit",
        action="store_true",
        help="Auto exit after program complete",
    )
    parser.add_argument(
        "-g",
        "--debug",
        action="store_true",
        help="Turn on debug mode to generate diagnostic log for issue report.",
    )
    parser.add_argument(
        "-N",
        "--no-network-operation",
        action="store_true",
        help="No network query, do not get metadata, for cover cropping purposes, only takes effect when main mode is 3.",
    )
    parser.add_argument(
        "-w",
        "--website",
        dest="site",
        default="",
        nargs="?",
        help="Override [priority]website= in config.",
    )
    parser.add_argument(
        "-D",
        "--download-images",
        dest="dnimg",
        action="store_true",
        help="Override [common]download_only_missing_images=0 force invoke image downloading.",
    )
    parser.add_argument(
        "-C",
        "--config-override",
        dest="cfgcmd",
        action="append",
        nargs=1,
        help="Common use config override. Grammar: section:key=value[;[section:]key=value] eg. 'de:s=1' or 'debug_mode:switch=1' override[debug_mode]switch=1 Note:this parameters can be used multiple times",
    )
    parser.add_argument(
        "-z",
        "--zero-operation",
        dest="zero_op",
        action="store_true",
        help="""Only show job list of files and numbers, and **NO** actual operation
        is performed. It may help you correct wrong numbers before real job.""",
    )
    parser.add_argument("-v", "--version", action="version", version=ver)
    parser.add_argument("-s", "--search", default="", nargs="?", help="Search number")
    parser.add_argument(
        "-ss", "--specified-source", default="", nargs="?", help="specified Source."
    )
    parser.add_argument(
        "-su", "--specified-url", default="", nargs="?", help="specified Url."
    )

    args = parser.parse_args()

    def set_natural_number_or_none(sk, value):
        if isinstance(value, str) and value.isnumeric() and int(value) >= 0:
            conf.set_override(f"{sk}={value}")

    def set_str_or_none(sk, value):
        if isinstance(value, str) and len(value):
            conf.set_override(f"{sk}={value}")

    def set_bool_or_none(sk, value):
        if isinstance(value, bool) and value:
            conf.set_override(f"{sk}=1")

    set_natural_number_or_none("common:main_mode", args.main_mode)
    set_natural_number_or_none("common:link_mode", args.link_mode)
    set_str_or_none("common:source_folder", args.path)
    set_bool_or_none("common:auto_exit", args.auto_exit)
    set_natural_number_or_none("common:nfo_skip_days", args.days)
    set_natural_number_or_none("advenced_sleep:stop_counter", args.cnt)
    set_bool_or_none("common:ignore_failed_list", args.ignore_failed_list)
    set_str_or_none("advenced_sleep:rerun_delay", args.delaytm)
    set_str_or_none("priority:website", args.site)
    if isinstance(args.dnimg, bool) and args.dnimg:
        conf.set_override("common:download_only_missing_images=0")
    set_bool_or_none("debug_mode:switch", args.debug)
    if isinstance(args.cfgcmd, list):
        for cmd in args.cfgcmd:
            conf.set_override(cmd[0])

    no_net_op = False
    if conf.main_mode() == 3:
        no_net_op = args.no_network_operation
        if no_net_op:
            conf.set_override(
                "advenced_sleep:stop_counter=0;advenced_sleep:rerun_delay=0s;face:aways_imagecut=1"
            )

    return (
        args.file,
        args.number,
        args.logdir,
        args.regexstr,
        args.zero_op,
        no_net_op,
        args.search,
        args.specified_source,
        args.specified_url,
    )
