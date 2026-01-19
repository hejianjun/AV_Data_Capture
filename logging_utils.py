import sys
import os
import typing
import re
from datetime import datetime, timedelta
from pathlib import Path


class OutLogger(object):
    def __init__(self, logfile) -> None:
        self.term = sys.stdout
        self.log = open(logfile, "w", encoding="utf-8", buffering=1)
        self.filepath = logfile

    def __del__(self):
        self.close()

    def __enter__(self):
        pass

    def __exit__(self, *args):
        self.close()

    def write(self, msg):
        self.term.write(msg)
        self.log.write(msg)

    def flush(self):
        if "flush" in dir(self.term):
            self.term.flush()
        if "flush" in dir(self.log):
            self.log.flush()
        if "fileno" in dir(self.log):
            os.fsync(self.log.fileno())

    def close(self):
        if self.term is not None:
            sys.stdout = self.term
            self.term = None
        if self.log is not None:
            self.log.close()
            self.log = None


class ErrLogger(OutLogger):
    def __init__(self, logfile) -> None:
        self.term = sys.stderr
        self.log = open(logfile, "w", encoding="utf-8", buffering=1)
        self.filepath = logfile

    def close(self):
        if self.term is not None:
            sys.stderr = self.term
            self.term = None

        if self.log is not None:
            self.log.close()
            self.log = None



def dupe_stdout_to_logfile(logdir: str) -> None:
    if not isinstance(logdir, str) or len(logdir) == 0:
        return
    log_dir = Path(logdir)
    if not log_dir.exists():
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except:
            pass
    if not log_dir.is_dir():
        return  # Tips for disabling logs by change directory to a same name empty regular file
    abslog_dir = log_dir.resolve()
    log_tmstr = datetime.now().strftime("%Y%m%dT%H%M%S")
    logfile = abslog_dir / f"mdc_{log_tmstr}.txt"
    errlog = abslog_dir / f"mdc_{log_tmstr}_err.txt"

    sys.stdout = OutLogger(logfile)
    sys.stderr = ErrLogger(errlog)



def close_logfile(logdir: str) -> typing.Optional[Path]:
    if not isinstance(logdir, str) or len(logdir) == 0 or not os.path.isdir(logdir):
        return None
    # Save log file path before closing
    filepath = None
    try:
        filepath = sys.stdout.filepath
    except:
        pass
    sys.stdout.close()
    sys.stderr.close()
    log_dir = Path(logdir).resolve()
    if isinstance(filepath, Path):
        print(f"Log file '{filepath}' saved.")
        assert filepath.parent.samefile(log_dir)
    # 清理空文件
    for f in log_dir.glob(r"*_err.txt"):
        if f.stat().st_size == 0:
            try:
                f.unlink(missing_ok=True)
            except:
                pass
    # 合并日志 只检测日志目录内的文本日志，忽略子目录。三天前的日志，按日合并为单个日志，三个月前的日志，
    # 按月合并为单个月志，去年及以前的月志，今年4月以后将之按年合并为年志
    today = datetime.today()
    # 第一步，合并到日。3天前的日志，文件名是同一天的合并为一份日志
    for i in range(1):
        txts = [
            f
            for f in log_dir.glob(r"*.txt")
            if re.match(r"^mdc_\d{8}T\d{6}$", f.stem, re.A)
        ]
        if not txts or not len(txts):
            break
        e = [f for f in txts if "_err" in f.stem]
        txts.sort()
        tmstr_3_days_ago = (today.replace(hour=0) - timedelta(days=3)).strftime(
            "%Y%m%dT99"
        )
        deadline_day = f"mdc_{tmstr_3_days_ago}"
        day_merge = [f for f in txts if f.stem < deadline_day]
        if not day_merge or not len(day_merge):
            break
        cutday = len("T235959.txt")  # cut length mdc_20201201|T235959.txt
        for f in day_merge:
            try:
                day_file_name = str(f)[:-cutday] + ".txt"  # mdc_20201201.txt
                with open(day_file_name, "a", encoding="utf-8") as m:
                    m.write(f.read_text(encoding="utf-8"))
                f.unlink(missing_ok=True)
            except:
                pass
    # 第二步，合并到月
    for i in range(1):  # 利用1次循环的break跳到第二步，避免大块if缩进或者使用goto语法
        txts = [
            f for f in log_dir.glob(r"*.txt") if re.match(r"^mdc_\d{8}$", f.stem, re.A)
        ]
        if not txts or not len(txts):
            break
        txts.sort()
        tmstr_3_month_ago = (today.replace(day=1) - timedelta(days=3 * 30)).strftime(
            "%Y%m32"
        )
        deadline_month = f"mdc_{tmstr_3_month_ago}"
        month_merge = [f for f in txts if f.stem < deadline_month]
        if not month_merge or not len(month_merge):
            break
        tomonth = len("01.txt")  # cut length mdc_202012|01.txt
        for f in month_merge:
            try:
                month_file_name = str(f)[:-tomonth] + ".txt"  # mdc_202012.txt
                with open(month_file_name, "a", encoding="utf-8") as m:
                    m.write(f.read_text(encoding="utf-8"))
                f.unlink(missing_ok=True)
            except:
                pass
    # 第三步，月合并到年
    for i in range(1):
        if today.month < 4:
            break
        mons = [
            f for f in log_dir.glob(r"*.txt") if re.match(r"^mdc_\d{6}$", f.stem, re.A)
        ]
        if not mons or not len(mons):
            break
        mons.sort()
        deadline_year = f"mdc_{today.year - 1}13"
        year_merge = [f for f in mons if f.stem < deadline_year]
        if not year_merge or not len(year_merge):
            break
        toyear = len("12.txt")  # cut length mdc_2020|12.txt
        for f in year_merge:
            try:
                year_file_name = str(f)[:-toyear] + ".txt"  # mdc_2020.txt
                with open(year_file_name, "a", encoding="utf-8") as y:
                    y.write(f.read_text(encoding="utf-8"))
                f.unlink(missing_ok=True)
            except:
                pass
    return filepath
