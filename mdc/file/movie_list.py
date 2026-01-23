import os
import re
import typing
from pathlib import Path
from mdc.config import config
from mdc.file.file_utils import file_modification_days
from mdc.utils.number_parser import get_number
from mdc.utils.logger import info as print, success, warn, error, debug


def movie_lists(source_folder: str, regexstr: str) -> typing.List[str]:
    conf = config.getInstance()
    main_mode = conf.main_mode()
    debug = conf.debug()
    nfo_skip_days = conf.nfo_skip_days()
    link_mode = conf.link_mode()
    file_type = conf.media_type().lower().split(",")
    trailerRE = re.compile(r"-trailer\.", re.IGNORECASE)
    cliRE = None
    if isinstance(regexstr, str) and len(regexstr):
        try:
            cliRE = re.compile(regexstr, re.IGNORECASE)
        except:
            pass
    failed_list_txt_path = Path(conf.failed_folder()).resolve() / "failed_list.txt"
    failed_set = set()
    if (main_mode == 3 or link_mode) and not conf.ignore_failed_list():
        try:
            flist = failed_list_txt_path.read_text(encoding="utf-8").splitlines()
            failed_set = set(flist)
            if (
                len(flist) != len(failed_set)
            ):  # 检查去重并写回，但是不改变failed_list.txt内条目的先后次序，重复的只保留最后的
                fset = failed_set.copy()
                for i in range(len(flist) - 1, -1, -1):
                    fset.remove(flist[i]) if flist[i] in fset else flist.pop(i)
                failed_list_txt_path.write_text(
                    "\n".join(flist) + "\n", encoding="utf-8"
                )
                assert len(fset) == 0 and len(flist) == len(failed_set)
        except:
            pass
    if not Path(source_folder).is_dir():
        print("[-]Source folder not found!")
        return []
    total = []
    source = Path(source_folder).resolve()
    skip_failed_cnt, skip_nfo_days_cnt = 0, 0
    escape_folder_set = set(re.split("[,，]", conf.escape_folder()))
    for full_name in source.glob(r"**/*"):
        if main_mode != 3 and set(full_name.parent.parts) & escape_folder_set:
            continue
        if not full_name.is_file():
            continue
        if full_name.suffix.lower() not in file_type:
            continue
        absf = str(full_name)
        if absf in failed_set:
            skip_failed_cnt += 1
            if debug:
                print(f"[!]Skip failed movie '{absf}'")
            continue
        if re.search(trailerRE, absf):
            if debug:
                print(f"[!]Skip trailer '{absf}'")
            continue
        if cliRE and not re.search(cliRE, absf):
            continue
        if main_mode != 3:
            nfo = full_name.with_suffix(".nfo")
            if not nfo.is_file():
                if debug:
                    print(f"[!]Metadata {nfo.name} not found for '{absf}'")
            elif nfo_skip_days > 0 and file_modification_days(nfo) <= nfo_skip_days:
                skip_nfo_days_cnt += 1
                if debug:
                    print(
                        f"[!]Skip movie by it's .nfo which modified within {nfo_skip_days} days: '{absf}'"
                    )
                continue
        total.append(absf)

    if skip_failed_cnt:
        print(
            f"[!]Skip {skip_failed_cnt} movies in failed list '{failed_list_txt_path}'."
        )
    if skip_nfo_days_cnt:
        print(
            f"[!]Skip {skip_nfo_days_cnt} movies in source folder '{source}' who's .nfo modified within {nfo_skip_days} days."
        )
    if nfo_skip_days <= 0 or not link_mode or main_mode == 3:
        return total
    # 软连接方式，已经成功削刮的也需要从成功目录中检查.nfo更新天数，跳过N天内更新过的
    skip_numbers = set()
    success_folder = Path(conf.success_folder()).resolve()
    for f in success_folder.glob(r"**/*"):
        if not re.match(r"\.nfo$", f.suffix, re.IGNORECASE):
            continue
        if file_modification_days(f) > nfo_skip_days:
            continue
        number = get_number(False, f.stem)
        if not number:
            continue
        skip_numbers.add(number.lower())

    rm_list = []
    for f in total:
        n_number = get_number(False, os.path.basename(f))
        if n_number and n_number.lower() in skip_numbers:
            rm_list.append(f)
    for f in rm_list:
        total.remove(f)
        if debug:
            print(
                f"[!]Skip file successfully processed within {nfo_skip_days} days: '{f}'"
            )
    if len(rm_list):
        print(
            f"[!]Skip {len(rm_list)} movies in success folder '{success_folder}' who's .nfo modified within {nfo_skip_days} days."
        )

    return total
