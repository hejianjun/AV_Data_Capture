import os
import re
import typing

from mdc.config import config

G_spat = re.compile(
    r"^\w+\.(cc|com|net|me|club|jp|tv|xyz|biz|wiki|info|tw|us|de)@|^22-sht\.me|"
    r"^(fhd|hd|sd|1080p|720p|4K)(-|_)|"
    r"(-|_)(fhd|hd|sd|1080p|720p|4K|x264|x265|uncensored|hack|leaked|leak|uc|u)",
    re.IGNORECASE,
)


def get_number(debug: bool, file_path: str) -> str:
    """
    从文件路径中提取番号 from number_parser import get_number
    >>> get_number(False, "/Users/Guest/AV_Data_Capture/snis-829.mp4")
    'snis-829'
    >>> get_number(False, "/Users/Guest/AV_Data_Capture/snis-829-C.mp4")
    'snis-829'
    >>> get_number(False, "/Users/Guest/AV_Data_Capture/[脸肿字幕组][PoRO]牝教師4～穢された教壇～ 「生意気ドジっ娘女教師・美結～高飛車ハメ堕ち2濁金」[720p][x264_aac].mp4")
    '牝教師4～穢された教壇～ 「生意気ドジっ娘女教師・美結～高飛車ハメ堕ち2濁金」'
    >>> get_number(False, "C:\\Users\\Guest\\snis-829.mp4")
    'snis-829'
    >>> get_number(False, "C:\\Users\\Guest\\snis-829-C.mp4")
    'snis-829'
    >>> get_number(False, "./snis-829.mp4")
    'snis-829'
    >>> get_number(False, "./snis-829-C.mp4")
    'snis-829'
    >>> get_number(False, ".\\snis-829.mp4")
    'snis-829'
    >>> get_number(False, ".\\snis-829-C.mp4")
    'snis-829'
    >>> get_number(False, "snis-829.mp4")
    'snis-829'
    >>> get_number(False, "snis-829-C.mp4")
    'snis-829'
    """
    filepath = os.path.basename(str(file_path).replace("\\", "/"))
    # debug True 和 False 两块代码块合并，原因是此模块及函数只涉及字符串计算，没有IO操作，debug on时输出导致异常信息即可
    try:
        # 先对自定义正则进行匹配
        if config.getInstance().number_regexs().split().__len__() > 0:
            for regex in config.getInstance().number_regexs().split():
                try:
                    if re.search(regex, filepath):
                        return re.search(regex, filepath).group()
                except Exception as e:
                    print(f"[-]custom regex exception: {e} [{regex}]")

        file_number = get_number_by_dict(filepath)
        if file_number:
            return file_number
        elif "字幕组" in filepath or "SUB" in filepath.upper() or re.match(r"[\u30a0-\u30ff]+", filepath):
            filepath = G_spat.sub("", filepath)
            filepath = re.sub(r"\[.*?\]", "", filepath)
            filepath = filepath.replace(".chs", "").replace(".cht", "")
            file_number = str(re.findall(r"(.+?)\.", filepath)).strip(" [']")
            return file_number
        elif "-" in filepath or "_" in filepath:
            filepath = G_spat.sub("", filepath)
            filename = str(re.sub(r"\[\d{4}-\d{1,2}-\d{1,2}\] - ", "", filepath))
            lower_check = filename.lower()
            if "fc2" in lower_check:
                filename = lower_check.replace("--", "-").replace("_", "-").upper()
            filename = re.sub(r"[-_]cd\d{1,2}", "", filename, flags=re.IGNORECASE)
            if not re.search("-|_", filename):
                return str(re.search(r"\w+", filename[: filename.find(".")], re.A).group())
            file_number = os.path.splitext(filename)
            filename = re.search(r"[\w\-]{2,}", file_number[0], re.A)
            if filename:
                file_number = str(filename.group()).strip("-_ ")
            else:
                file_number = file_number[0]

            new_file_number = file_number
            if re.search("(-|_)c$", file_number, flags=re.IGNORECASE):
                new_file_number = re.sub("(-|_)c$", "", file_number, flags=re.IGNORECASE)
            elif re.search("(-|_)u$", file_number, flags=re.IGNORECASE):
                new_file_number = re.sub("(-|_)u$", "", file_number, flags=re.IGNORECASE)
            elif re.search("(-|_)uc$", file_number, flags=re.IGNORECASE):
                new_file_number = re.sub("(-|_)uc$", "", file_number, flags=re.IGNORECASE)
            elif re.search(r"\d+ch$", file_number, flags=re.I):
                new_file_number = file_number[:-2]

            return new_file_number.upper()
        else:
            oumei = re.search(r"[a-zA-Z]+\.\d{2}\.\d{2}\.\d{2}", filepath)
            if oumei:
                return oumei.group()
            try:
                return (
                    str(
                        re.findall(
                            r"(.+?)\.",
                            str(re.search(r'([^<>/\\|:"*?]+)\.\w+$', filepath).group()),
                        )
                    )
                    .strip("['']")
                    .replace("_", "-")
                )
            except Exception:
                return str(re.search(r"(.+?)\.", filepath)[0])
    except Exception as e:
        if debug:
            print(f"[-]Number Parser exception: {e} [{file_path}]")
        return None


# 按javdb数据源的命名规范提取number
G_TAKE_NUM_RULES = {
    "tokyo.*hot": lambda x: str(re.search(r"(cz|gedo|k|n|red-|se)\d{2,4}", x, re.I).group()),
    "carib": lambda x: str(re.search(r"\d{6}(-|_)\d{3}", x, re.I).group()).replace("_", "-"),
    "1pon|mura|paco": lambda x: str(re.search(r"\d{6}(-|_)\d{3}", x, re.I).group()).replace("-", "_"),
    "10mu": lambda x: str(re.search(r"\d{6}(-|_)\d{2}", x, re.I).group()).replace("-", "_"),
    "x-art": lambda x: str(re.search(r"x-art\.\d{2}\.\d{2}\.\d{2}", x, re.I).group()),
    "xxx-av": lambda x: "".join(["xxx-av-", re.findall(r"xxx-av[^\d]*(\d{3,5})[^\d]*", x, re.I)[0]]),
    "heydouga": lambda x: "heydouga-" + "-".join(re.findall(r"(\d{4})[\-_](\d{3,4})[^\d]*", x, re.I)[0]),
    "heyzo": lambda x: "HEYZO-" + re.findall(r"heyzo[^\d]*(\d{4})", x, re.I)[0],
    "mdbk": lambda x: str(re.search(r"mdbk(-|_)(\d{4})", x, re.I).group()),
    "mdtm": lambda x: str(re.search(r"mdtm(-|_)(\d{4})", x, re.I).group()),
    "caribpr": lambda x: str(re.search(r"\d{6}(-|_)\d{3}", x, re.I).group()).replace("_", "-"),
}


def get_number_by_dict(filename: str) -> typing.Optional[str]:
    try:
        for k, v in G_TAKE_NUM_RULES.items():
            if re.search(k, filename, re.I):
                return v(filename)
    except Exception:
        pass
    return None


def _normalize_number_for_compare(number: typing.Optional[str]) -> str:
    return str(number or "").strip().upper()


def _strip_leading_numeric_prefix(number: str) -> str:
    number = _normalize_number_for_compare(number)
    return re.sub(r"^\d{3,}(?=[A-Z])", "", number)


def is_number_equivalent(a: typing.Optional[str], b: typing.Optional[str]) -> bool:
    """
    判断两个番号是否可视为同一影片。

    目前用于兼容部分站点返回的“3位以上数字前缀 + 原番号”形式（如 300MAAN-797）。
    """
    na = _normalize_number_for_compare(a)
    nb = _normalize_number_for_compare(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    sa = _strip_leading_numeric_prefix(na)
    sb = _strip_leading_numeric_prefix(nb)
    return sa == nb or sb == na


class Cache_uncensored_conf:
    prefix = None

    def is_empty(self):
        return bool(self.prefix is None)

    def set(self, v: list):
        if not v or not len(v) or not len(v[0]):
            raise ValueError("input prefix list empty or None")
        s = v[0]
        if len(v) > 1:
            for i in v[1:]:
                s += f"|{i}.+"
        self.prefix = re.compile(s, re.I)

    def check(self, number):
        if self.prefix is None:
            raise ValueError("No init re compile")
        return self.prefix.match(number)


G_cache_uncensored_conf = Cache_uncensored_conf()


# ========================================================================是否为无码
def is_uncensored(number) -> bool:
    if re.match(
        r"[\d-]{4,}|\d{6}_\d{2,3}|(cz|gedo|k|n|red-|se)\d{2,4}|heyzo.+|xxx-av-.+|heydouga-.+|x-art\.\d{2}\.\d{2}\.\d{2}",
        number,
        re.I,
    ):
        return True
    if G_cache_uncensored_conf.is_empty():
        G_cache_uncensored_conf.set(config.getInstance().get_uncensored().split(","))
    return bool(G_cache_uncensored_conf.check(number))
