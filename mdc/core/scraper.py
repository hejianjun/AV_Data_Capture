# build-in lib
import json
import secrets
import typing
import re
import importlib
import traceback
from functools import lru_cache
from pathlib import Path

# third party lib
import opencc

# project wide definitions
from mdc.config import config
from mdc.utils.actor_mapping import (
    get_actor_mapping,
    get_info_mapping,
    process_special_actor_name,
    process_text_mappings,
)
from mdc.utils.translation import translate

from mdc.utils.cookie import load_cookies
from mdc.utils.number_parser import is_number_equivalent
from mdc.file.file_utils import file_modification_days
from mdc.scraping.parser import Parser
from mdc.scraping.custom_exceptions import QueryError


class Scraping:
    """ """

    adult_full_sources = [
        "javlibrary",
        "javdb",
        "javbus",
        "airav",
        "fanza",
        "xcity",
        "jav321",
        "mgstage",
        "fc2",
        "avsox",
        "dlsite",
        "carib",
        "madou",
        "msin",
        "av123",
        "getchu",
        "gcolle",
        "javday",
        "pissplay",
        "javmenu",
        "pcolle",
        "caribpr",
        "madouji",
    ]

    general_full_sources = ["tmdb", "imdb"]

    debug = False

    proxies = None
    verify = None
    specifiedSource = None
    specifiedUrl = None

    dbcookies = None
    dbsite = None
    # 使用storyline方法进一步获取故事情节
    morestoryline = False
    # 新增方法：根据爬虫名称加载对应cookie

    def load_cookies_for_source(self, source, dbsite):
        """统一cookie加载逻辑"""
        # 特殊处理javdb多站点逻辑
        if source == "javdb":
            cookie_file = f"{dbsite}.json"
        else:
            cookie_file = f"{source}.json"
        cookies_dict, cookies_path = load_cookies(cookie_file)
        if not isinstance(cookies_dict, dict):
            return None
        # 有效期验证
        cdays = file_modification_days(cookies_path)
        if cdays < 7:
            if self.debug:
                print(f"[Cookie] 加载有效cookie文件: {cookies_path}")
            return cookies_dict

        return None

    def search(
        self,
        number,
        sources=None,
        proxies=None,
        verify=None,
        type="adult",
        specifiedSource=None,
        specifiedUrl=None,
        dbsite=None,
        morestoryline=False,
        debug=False,
    ):
        self.debug = debug
        self.proxies = proxies
        self.verify = verify
        self.specifiedSource = specifiedSource
        self.specifiedUrl = specifiedUrl
        self.morestoryline = morestoryline
        # 动态加载各爬虫的cookie
        valid_cookies = {}
        if sources:
            for source in sources:
                if source_cookies := self.load_cookies_for_source(source, dbsite):
                    valid_cookies[source] = source_cookies

        # 构造爬虫配置
        self.dbsite = dbsite
        self.dbcookies = valid_cookies  # 改为字典结构存储多爬虫cookie

        print(f"当前爬虫sources: {sources}")
        if type == "adult":
            return self.searchAdult(number, tuple(sources) if sources else ())
        else:
            return self.searchGeneral(number, tuple(sources) if sources else ())

    @lru_cache(maxsize=None)
    def searchGeneral(self, name, sources):
        """查询电影电视剧
        imdb,tmdb
        """
        if self.specifiedSource:
            sources = [self.specifiedSource]
        else:
            sources = self.checkGeneralSources(sources, name)
        json_data = {}
        for source in sources:
            try:
                if self.debug:
                    print("[+]select", source)
                try:
                    module = importlib.import_module("." + source, "mdc.scraping")
                    parser_type = getattr(module, source.capitalize())
                    parser: Parser = parser_type()
                    data = parser.scrape(name, self)
                    if data == 404:
                        continue
                    json_data = json.loads(data)
                except QueryError as e:
                    print(f"[!] 查询异常: {str(e)}")
                except BaseException as e:
                    if self.debug:
                        traceback.print_exception(e)
                # if any service return a valid return, break
                if self.get_data_state(json_data):
                    if self.debug:
                        print(f"[+]Find movie [{name}] metadata on website '{source}'")
                    break
            except Exception:
                continue

        # Return if data not found in all sources
        if not json_data or json_data.get("title") == "":
            return None

        # If actor is anonymous, Fill in Anonymous
        if len(json_data.get("actor", [])) == 0:
            if config.getInstance().anonymous_fill():
                if (
                    "zh_" in config.getInstance().get_target_language()
                    or "ZH" in config.getInstance().get_target_language()
                ):
                    json_data["actor"] = "佚名"
                else:
                    json_data["actor"] = "Anonymous"

        return json_data

    @lru_cache(maxsize=None)
    def searchAdult(self, number, sources):
        if self.specifiedSource:
            sources = [self.specifiedSource]
        elif len(sources) > 1:
            pass
        else:
            sources = self.checkAdultSources(sources, number)
        json_data = {}
        for source in sources:
            try:
                if self.debug:
                    print("[+]select", source)
                try:
                    module = importlib.import_module("." + source, "mdc.scraping")
                    parser_type = getattr(module, source.capitalize())
                    parser: Parser = parser_type()
                    data = parser.scrape(number, self)
                    if data == 404:
                        continue
                    json_data = json.loads(data)
                except QueryError as e:
                    print(f"[!] 查询异常: {str(e)}")
                except BaseException as e:
                    if self.debug:
                        traceback.print_exception(e)
                    # json_data = self.func_mapping[source](number, self)
                # if any service return a valid return, break
                if self.get_data_state(json_data):
                    if self.debug:
                        print(
                            f"[+]Find movie [{number}] metadata on website '{source}'"
                        )
                    break
            except Exception:
                continue

        # javdb的封面有水印，如果可以用其他源的封面来替换javdb的封面
        if "source" in json_data and json_data["source"] == "javdb":
            # If cover not found in other source, then skip using other sources using javdb cover instead
            try:
                # search other sources
                if "javdb" in sources:
                    other_sources = sources[sources.index("javdb") + 1 :]
                    # 避免空列表导致无限递归
                    if other_sources:
                        other_json_data = self.searchAdult(number, other_sources)
                        if (
                            other_json_data is not None
                            and "cover" in other_json_data
                            and other_json_data["cover"] != ""
                        ):
                            json_data["cover"] = other_json_data["cover"]
                            if self.debug:
                                print(
                                    f"[+]Replace javdb cover with {other_json_data['source']} cover"
                                )
            except Exception:
                pass

        # Return if data not found in all sources
        if not json_data or json_data.get("title") == "":
            return None

        # If actor is anonymous, Fill in Anonymous
        if len(json_data.get("actor", [])) == 0:
            if config.getInstance().anonymous_fill():
                if (
                    "zh_" in config.getInstance().get_target_language()
                    or "ZH" in config.getInstance().get_target_language()
                ):
                    json_data["actor"] = "佚名"
                else:
                    json_data["actor"] = "Anonymous"

        return json_data

    def checkGeneralSources(self, sources, name):
        sources = list(sources)
        # check sources in func_mapping
        todel = []
        for s in sources:
            if s not in self.general_full_sources:
                print("[!] Source Not Exist : " + s)
                todel.append(s)
        for d in todel:
            print("[!] Remove Source : " + s)
            sources.remove(d)
        return sources

    def checkAdultSources(self, sources, file_number):
        # Convert tuple to list since we need to modify the order
        sources = list(sources)

        def insert(sources, source):
            if source in sources:
                sources.insert(0, sources.pop(sources.index(source)))
            return sources

        if len(sources) <= len(self.adult_full_sources):
            # if the input file name matches certain rules,
            # move some web service to the beginning of the list
            lo_file_number = file_number.lower()
            if "carib" in sources:
                sources = insert(sources, "caribpr")
                sources = insert(sources, "carib")
            elif "item" in file_number or "GETCHU" in file_number.upper():
                sources = ["getchu"]
            elif "rj" in lo_file_number or "vj" in lo_file_number:
                sources = ["dlsite"]
            elif re.search(r"[\u3040-\u309F\u30A0-\u30FF]+", file_number):
                sources = ["dlsite", "getchu"]
            elif "pcolle" in sources and "pcolle" in lo_file_number:
                sources = ["pcolle"]
            elif "fc2" in lo_file_number:
                sources = ["av123", "javdb", "fc2", "avsox", "msin"]
            elif re.search(r"\d+\D+-", file_number) or "siro" in lo_file_number:
                if "mgstage" in sources:
                    sources = insert(sources, "mgstage")
            elif "gcolle" in sources and (re.search(r"\d{6}", file_number)):
                sources = insert(sources, "gcolle")
            elif (
                re.search(r"^\d{5,}", file_number)
                or (re.search(r"^\d{6}-\d{3}", file_number))
                or "heyzo" in lo_file_number
            ):
                sources = [
                    "airav",
                    "avsox",
                    "carib",
                    "caribpr",
                    "javbus",
                    "xcity",
                    "javdb",
                ]
            elif re.search(r"^[a-z0-9]{3,}$", lo_file_number):
                if "xcity" in sources:
                    sources = insert(sources, "xcity")
                if "madou" in sources:
                    sources = insert(sources, "madou")

        # check sources in func_mapping
        todel = []
        for s in sources:
            if s not in self.adult_full_sources and config.getInstance().debug():
                print("[!] Source Not Exist : " + s)
                todel.append(s)
        for d in todel:
            if config.getInstance().debug():
                print("[!] Remove Source : " + d)
            sources.remove(d)
        return sources

    def get_data_state(self, data: dict) -> bool:  # 元数据获取失败检测
        if "title" not in data or "number" not in data:
            return False
        if data["title"] is None or data["title"] == "" or data["title"] == "null":
            return False
        if data["number"] is None or data["number"] == "" or data["number"] == "null":
            return False
        if (
            data.get("cover") is None
            or data.get("cover") == ""
            or data.get("cover") == "null"
        ) and (
            data.get("cover_small") is None
            or data.get("cover_small") == ""
            or data.get("cover_small") == "null"
        ):
            return False
        return True


def search(number, sources: str = None, **kwargs):
    """根据`番号/电影`名搜索信息

    :param number: number/name  depends on type
    :param sources: sources string with `,` Eg: `avsox,javbus`
    :param type: `adult`, `general`
    """
    sc = Scraping()
    return sc.search(number, sources, **kwargs)


def _build_search_kwargs(
    conf: config, specified_source: str, specified_url: str
) -> dict:
    """构造 search() 调用参数，集中处理代理、证书、javdb 站点等配置。"""
    proxies: dict = None
    config_proxy = conf.proxy()
    if config_proxy.enable:
        proxies = config_proxy.proxies()

    ca_cert = conf.cacert_file() or None

    javdb_sites = [site for site in conf.javdb_sites().split(",") if site]
    javdb_sites = [f"javdb{site}" for site in javdb_sites] or ["javdb"]

    return {
        "proxies": proxies,
        "verify": ca_cert,
        "dbsite": secrets.choice(javdb_sites),
        "morestoryline": conf.is_storyline(),
        "specifiedSource": specified_source,
        "specifiedUrl": specified_url,
        "debug": conf.debug(),
    }


def _is_number_change_allowed(file_number: str, json_data: dict) -> bool:
    """判断抓取到的番号是否允许与输入番号不一致。"""
    if is_number_equivalent(json_data.get("number"), file_number):
        return True

    try:
        return bool(json_data.get("allow_number_change"))
    except Exception:
        return False


def _parse_actor_list(raw_actor: typing.Any) -> list[str]:
    """把抓取到的 actor 字段（可能是 list/str/None）规范化成字符串列表。"""
    if raw_actor is None:
        return []
    actor_list = str(raw_actor).strip("[ ]").replace("'", "").split(",")
    return [actor.strip() for actor in actor_list if actor.strip()]


def _parse_tag_list(raw_tag: typing.Any) -> list[str]:
    """把抓取到的 tag 字段规范化成字符串列表，并移除占位标签。"""
    if raw_tag is None:
        return []
    tag_list = (
        str(raw_tag)
        .strip("[ ]")
        .replace("'", "")
        .replace(" ", "")
        .split(",")
    )
    return [t for t in tag_list if t and t not in {"XXXX", "xxx"}]


def _normalize_and_update_json_data(json_data: dict, conf: config) -> str:
    """清洗字段并回写到 json_data，返回用于 title 本地字典的 number。"""
    title = json_data.get("title") or ""
    actor_list = _parse_actor_list(json_data.get("actor"))
    director = json_data.get("director")
    release = json_data.get("release") or ""
    number = json_data.get("number") or ""
    studio = json_data.get("studio")
    outline = json_data.get("outline")
    label = json_data.get("label")
    series = json_data.get("series")
    year = json_data.get("year")

    cover_small = json_data.get("cover_small") or ""
    trailer = json_data.get("trailer") or ""
    extrafanart = json_data.get("extrafanart") or ""
    tag = _parse_tag_list(json_data.get("tag"))

    if json_data.get("source") == "pissplay":
        actor = str(actor_list).strip("[ ]").replace("'", "")
    else:
        actor = str(actor_list).strip("[ ]").replace("'", "").replace(" ", "")

    actor = special_characters_replacement(actor)
    actor_list = [special_characters_replacement(a) for a in actor_list]
    title = special_characters_replacement(title)
    label = special_characters_replacement(label)
    outline = special_characters_replacement(outline)
    series = special_characters_replacement(series)
    studio = special_characters_replacement(studio)
    director = special_characters_replacement(director)
    tag = [special_characters_replacement(t) for t in tag]

    release = release.replace("/", "-")

    cover_small_first = cover_small.split(",")[0] if cover_small else ""
    cover_small = cover_small_first.strip('"').strip("'")

    if conf.number_uppercase():
        json_data["number"] = number.upper()

    json_data["title"] = title
    json_data["original_title"] = title
    json_data["actor"] = actor
    json_data["release"] = release
    json_data["cover_small"] = cover_small
    json_data["tag"] = tag
    json_data["year"] = year
    json_data["actor_list"] = actor_list
    json_data["trailer"] = trailer
    json_data["extrafanart"] = extrafanart
    json_data["label"] = label
    json_data["outline"] = outline
    json_data["series"] = series
    json_data["studio"] = studio
    json_data["director"] = director

    return number


def _maybe_translate(json_data: dict, conf: config, title_lookup_number: str) -> None:
    """按配置翻译字段；title 会优先查本地番号字典缓存。"""
    if not conf.is_translate():
        return

    translate_values = conf.translate_values().split(",")
    for translate_value in translate_values:
        if json_data.get(translate_value) is None or json_data[translate_value] == "":
            continue

        if translate_value == "title":
            title_dict = {}
            title_file = Path.home() / ".local" / "share" / "mdc" / "c_number.json"
            if title_file.exists():
                try:
                    title_dict = json.loads(title_file.read_text(encoding="utf-8"))
                    if title_lookup_number in title_dict:
                        json_data[translate_value] = title_dict[title_lookup_number]
                        continue
                except Exception:
                    pass

        if conf.get_translate_engine() == "azure":
            translate(
                json_data[translate_value],
                target_language="zh-Hans",
                engine=conf.get_translate_engine(),
                key=conf.get_translate_key(),
            )
            continue

        if not len(json_data[translate_value]):
            continue

        if isinstance(json_data[translate_value], str):
            json_data[translate_value] = special_characters_replacement(
                json_data[translate_value]
            )
            json_data[translate_value] = translate(json_data[translate_value])
            continue

        for i in range(len(json_data[translate_value])):
            json_data[translate_value][i] = special_characters_replacement(
                json_data[translate_value][i]
            )
        list_in_str = ",".join(json_data[translate_value])
        json_data[translate_value] = translate(list_in_str).split(",")


def _apply_actor_mapping(json_data: dict, actor_mapping_data: dict) -> None:
    """应用演员别名映射，并重新生成 actor 展示字段。"""
    try:
        json_data["actor_list"] = [
            process_special_actor_name(actor, actor_mapping_data)
            for actor in json_data["actor_list"]
        ]
        if json_data.get("source") == "pissplay":
            json_data["actor"] = (
                str(json_data["actor_list"]).strip("[ ]").replace("'", "")
            )
        else:
            json_data["actor"] = (
                str(json_data["actor_list"])
                .strip("[ ]")
                .replace("'", "")
                .replace(" ", "")
            )
    except Exception as e:
        print(f"[-]处理演员信息失败: {e}")


def _apply_info_mappings(json_data: dict, info_mapping_data: dict) -> None:
    """应用标签/文本字段映射（例如同义词替换）。"""
    try:
        json_data["tag"] = process_text_mappings(json_data["tag"], info_mapping_data)
    except Exception as e:
        print(f"[-]处理标签信息失败: {e}")

    mapping_fields = ["outline", "series", "studio", "title"]
    for field in mapping_fields:
        if field in json_data and json_data[field]:
            try:
                json_data[field] = process_text_mappings(
                    json_data[field], info_mapping_data
                )
            except Exception as e:
                print(f"[-]处理{field}信息失败: {e}")


def _apply_opencc(open_cc: opencc.OpenCC, conf: config, json_data: dict) -> None:
    """对配置指定的字段做繁简转换；支持 list[str] / str。"""
    if not open_cc:
        return

    cc_vars = conf.cc_convert_vars().split(",")
    for cc in cc_vars:
        if (
            json_data.get(cc) is None
            or json_data[cc] == ""
            or len(json_data[cc]) == 0
        ):
            continue
        try:
            if isinstance(json_data[cc], list):
                json_data[cc] = [open_cc.convert(t) for t in json_data[cc]]
            else:
                json_data[cc] = open_cc.convert(json_data[cc])
        except Exception as e:
            print(f"[-]繁简转换{cc}失败: {e}")


def _build_naming_rules(conf: config, json_data: dict) -> None:
    """根据配置拼接命名规则；original_naming_rule 用于保留原始标题。"""
    naming_rule = ""
    original_naming_rule = ""
    for i in conf.naming_rule().split("+"):
        if i not in json_data:
            naming_rule += i.strip("'").strip('"')
            original_naming_rule += i.strip("'").strip('"')
            continue

        item = json_data.get(i)
        naming_rule += item if type(item) is not list else "&".join(item)

        if i == "title":
            item = json_data.get("original_title")
        original_naming_rule += item if type(item) is not list else "&".join(item)

    json_data["naming_rule"] = naming_rule
    json_data["original_naming_rule"] = original_naming_rule


def get_data_from_json(
    file_number: str, open_cc: opencc.OpenCC, specified_source: str, specified_url: str
) -> typing.Optional[dict]:
    """
    从网站抓取并标准化元数据。

    这个函数会：
    1) 通过多数据源查询得到 json_data；
    2) 对番号/title/演员/标签等做清洗与字符替换（避免路径非法字符）；
    3) 可选：翻译、演员别名映射、字段映射、繁简转换；
    4) 生成 naming_rule / original_naming_rule，供后续文件命名与 NFO 使用。
    """
    conf = config.getInstance()
    ccm = conf.cc_convert_mode()
    actor_mapping_data = get_actor_mapping(ccm)
    info_mapping_data = get_info_mapping(ccm)

    # 数据源顺序从配置读取；search() 会依次尝试直到有结果
    sources = conf.sources().split(",")
    json_data = search(file_number, sources, **_build_search_kwargs(conf, specified_source, specified_url))

    # Return if data not found in all sources
    if not json_data or not json_data.get("number"):
        print("[-]Movie Number not found!")
        return None

    # 增加number严格判断，避免提交任何number，总是返回"本橋実来 ADZ335"，这种返回number不一致的数据源故障
    # 目前选用number命名规则是javdb.com Domain Creation Date: 2013-06-19T18:34:27Z
    # 然而也可以跟进关注其它命名规则如airav.wiki Domain Creation Date: 2019-08-28T07:18:42.0Z
    # 如果将来javdb.com命名规则下不同Studio出现同名碰撞导致无法区分，可考虑更换规则，更新相应的number分析和抓取代码。
    if not _is_number_change_allowed(file_number, json_data):
        print(
            "[-]Movie number has changed! [{}]->[{}]".format(
                file_number, str(json_data.get("number"))
            )
        )
        return None

    # ================================================网站规则添加结束================================================

    if json_data.get("title") == "":
        print("[-]Movie Number or Title not found!")
        return None

    title_lookup_number = _normalize_and_update_json_data(json_data, conf)
    _maybe_translate(json_data, conf, title_lookup_number)
    _apply_actor_mapping(json_data, actor_mapping_data)
    _apply_info_mappings(json_data, info_mapping_data)
    _apply_opencc(open_cc, conf, json_data)
    _build_naming_rules(conf, json_data)
    return json_data


def special_characters_replacement(text) -> str:
    if not isinstance(text, str):
        return text
    return (
        text.replace("\\", "∖")
        .  # U+2216 SET MINUS @ Basic Multilingual Plane
        replace("/", "∕")
        .  # U+2215 DIVISION SLASH @ Basic Multilingual Plane
        replace(":", "꞉")
        .  # U+A789 MODIFIER LETTER COLON @ Latin Extended-D
        replace("*", "∗")
        .  # U+2217 ASTERISK OPERATOR @ Basic Multilingual Plane
        replace("?", "？")
        .  # U+FF1F FULLWIDTH QUESTION MARK @ Basic Multilingual Plane
        replace('"', "＂")
        .  # U+FF02 FULLWIDTH QUOTATION MARK @ Basic Multilingual Plane
        replace("<", "ᐸ")
        .  # U+1438 CANADIAN SYLLABICS PA @ Basic Multilingual Plane
        replace(">", "ᐳ")
        .  # U+1433 CANADIAN SYLLABICS PO @ Basic Multilingual Plane
        replace("|", "ǀ")
        .  # U+01C0 LATIN LETTER DENTAL CLICK @ Basic Multilingual Plane
        replace("&lsquo;", "‘")
        .  # U+02018 LEFT SINGLE QUOTATION MARK
        replace("&rsquo;", "’")
        .  # U+02019 RIGHT SINGLE QUOTATION MARK
        replace("&hellip;", "…")
        .replace("&amp;", "＆")
        .replace("&", "＆")
    )
