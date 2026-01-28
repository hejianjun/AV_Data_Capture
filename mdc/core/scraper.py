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


def getSupportedSources(tag="adult"):
    """
    :param tag: `adult`, `general`
    """
    sc = Scraping()
    if tag == "adult":
        return ",".join(sc.adult_full_sources)
    else:
        return ",".join(sc.general_full_sources)


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
            except:
                continue

        # Return if data not found in all sources
        if not json_data or json_data.get("title") == "":
            return None

        # If actor is anonymous, Fill in Anonymous
        if len(json_data.get("actor", [])) == 0:
            if config.getInstance().anonymous_fill() == True:
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
            except:
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
            except:
                pass

        # Return if data not found in all sources
        if not json_data or json_data.get("title") == "":
            return None

        # If actor is anonymous, Fill in Anonymous
        if len(json_data.get("actor", [])) == 0:
            if config.getInstance().anonymous_fill() == True:
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
            data.get("cover") is None or data.get("cover") == "" or data.get("cover") == "null"
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


def get_data_from_json(
    file_number: str, open_cc: opencc.OpenCC, specified_source: str, specified_url: str
) -> typing.Optional[dict]:
    """
    iterate through all services and fetch the data 从网站上查询片名解析JSON返回元数据
    :param file_number: 影片名称
    :param open_cc: 简繁转换器
    :param specified_source: 指定的媒体数据源
    :param specified_url: 指定的数据查询地址, 目前未使用
    :return 给定影片名称的具体信息
    """
    conf = config.getInstance()
    ccm = conf.cc_convert_mode()
    actor_mapping_data = get_actor_mapping(ccm)
    info_mapping_data = get_info_mapping(ccm)

    # default fetch order list, from the beginning to the end
    sources = conf.sources().split(",")
    # TODO 准备参数
    # - 清理 ADC_function, webcrawler
    proxies: dict = None
    config_proxy = conf.proxy()
    if config_proxy.enable:
        proxies = config_proxy.proxies()

    # javdb website logic
    # javdb have suffix
    javdb_sites = conf.javdb_sites().split(",")
    javdb_sites = [f"javdb{site}" for site in javdb_sites]
    ca_cert = None
    if conf.cacert_file():
        ca_cert = conf.cacert_file()

    json_data = search(
        file_number,
        sources,
        proxies=proxies,
        verify=ca_cert,
        dbsite=secrets.choice(javdb_sites),
        morestoryline=conf.is_storyline(),
        specifiedSource=specified_source,
        specifiedUrl=specified_url,
        debug=conf.debug(),
    )
    # Return if data not found in all sources
    if not json_data or not json_data.get("number"):
        print("[-]Movie Number not found!")
        return None

    # 增加number严格判断，避免提交任何number，总是返回"本橋実来 ADZ335"，这种返回number不一致的数据源故障
    # 目前选用number命名规则是javdb.com Domain Creation Date: 2013-06-19T18:34:27Z
    # 然而也可以跟进关注其它命名规则如airav.wiki Domain Creation Date: 2019-08-28T07:18:42.0Z
    # 如果将来javdb.com命名规则下不同Studio出现同名碰撞导致无法区分，可考虑更换规则，更新相应的number分析和抓取代码。
    if not is_number_equivalent(json_data.get("number"), file_number):
        try:
            if not json_data.get("allow_number_change"):
                print(
                    "[-]Movie number has changed! [{}]->[{}]".format(
                        file_number, str(json_data.get("number"))
                    )
                )
                return None
        except:
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

    title = json_data.get("title")
    actor_list = (
        str(json_data.get("actor")).strip("[ ]").replace("'", "").split(",")
    )  # 字符串转列表
    actor_list = [actor.strip() for actor in actor_list]  # 去除空白
    director = json_data.get("director")
    release = json_data.get("release")
    number = json_data.get("number")
    studio = json_data.get("studio")
    source = json_data.get("source")
    runtime = json_data.get("runtime")
    outline = json_data.get("outline")
    label = json_data.get("label")
    series = json_data.get("series")
    year = json_data.get("year")

    if json_data.get("cover_small"):
        cover_small = json_data.get("cover_small")
    else:
        cover_small = ""

    if json_data.get("trailer"):
        trailer = json_data.get("trailer")
    else:
        trailer = ""

    if json_data.get("extrafanart"):
        extrafanart = json_data.get("extrafanart")
    else:
        extrafanart = ""

    imagecut = json_data.get("imagecut")
    tag = (
        str(json_data.get("tag"))
        .strip("[ ]")
        .replace("'", "")
        .replace(" ", "")
        .split(",")
    )  # 字符串转列表 @
    while "XXXX" in tag:
        tag.remove("XXXX")
    while "xxx" in tag:
        tag.remove("xxx")
    if json_data["source"] == "pissplay":  # pissplay actor为英文名，不用去除空格
        actor = str(actor_list).strip("[ ]").replace("'", "")
    else:
        actor = str(actor_list).strip("[ ]").replace("'", "").replace(" ", "")

    # if imagecut == '3':
    #     DownloadFileWithFilename()

    # ====================处理异常字符====================== #\/:*?"<>|
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
    tmpArr = cover_small.split(",")
    if len(tmpArr) > 0:
        cover_small = tmpArr[0].strip('"').strip("'")
    # ====================处理异常字符 END================== #\/:*?"<>|

    # 处理大写
    if conf.number_uppercase():
        json_data["number"] = number.upper()

    # 返回处理后的json_data
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

    if conf.is_translate():
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
                        if number in title_dict:
                            json_data[translate_value] = title_dict[number]
                            continue
                    except Exception:
                        pass

            if conf.get_translate_engine() == "azure":
                t = translate(
                    json_data[translate_value],
                    target_language="zh-Hans",
                    engine=conf.get_translate_engine(),
                    key=conf.get_translate_key(),
                )
            else:
                if len(json_data[translate_value]):
                    if type(json_data[translate_value]) == str:
                        json_data[translate_value] = special_characters_replacement(
                            json_data[translate_value]
                        )
                        json_data[translate_value] = translate(
                            json_data[translate_value]
                        )
                    else:
                        for i in range(len(json_data[translate_value])):
                            json_data[translate_value][i] = (
                                special_characters_replacement(
                                    json_data[translate_value][i]
                                )
                            )
                        list_in_str = ",".join(json_data[translate_value])
                        json_data[translate_value] = translate(list_in_str).split(",")

    # 无论是否开启open_cc，都处理演员信息
    try:
        # 处理actor_list中的每个演员
        json_data["actor_list"] = [
            process_special_actor_name(actor, actor_mapping_data)
            for actor in json_data["actor_list"]
        ]
        # 重新生成actor字段，确保使用处理后的actor_list
        if json_data["source"] == "pissplay":
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

    # 处理tag和其他字段
    try:
        json_data["tag"] = process_text_mappings(json_data["tag"], info_mapping_data)
    except Exception as e:
        print(f"[-]处理标签信息失败: {e}")

    # 处理其他需要映射的字段
    mapping_fields = ["outline", "series", "studio", "title"]
    for field in mapping_fields:
        if field in json_data and json_data[field]:
            try:
                json_data[field] = process_text_mappings(
                    json_data[field], info_mapping_data
                )
            except Exception as e:
                print(f"[-]处理{field}信息失败: {e}")

    # 繁简转换
    if open_cc:
        cc_vars = conf.cc_convert_vars().split(",")
        for cc in cc_vars:
            if json_data.get(cc) is None or json_data[cc] == "" or len(json_data[cc]) == 0:
                continue
            try:
                if isinstance(json_data[cc], list):
                    json_data[cc] = [open_cc.convert(t) for t in json_data[cc]]
                else:
                    json_data[cc] = open_cc.convert(json_data[cc])
            except Exception as e:
                print(f"[-]繁简转换{cc}失败: {e}")

    naming_rule = ""
    original_naming_rule = ""
    for i in conf.naming_rule().split("+"):
        if i not in json_data:
            naming_rule += i.strip("'").strip('"')
            original_naming_rule += i.strip("'").strip('"')
        else:
            item = json_data.get(i)
            naming_rule += item if type(item) is not list else "&".join(item)
            # PATCH：处理[title]存在翻译的情况，后续NFO文件的original_name只会直接沿用naming_rule,这导致original_name非原始名
            # 理应在翻译处理 naming_rule和original_naming_rule
            if i == "title":
                item = json_data.get("original_title")
            original_naming_rule += item if type(item) is not list else "&".join(item)

    json_data["naming_rule"] = naming_rule
    json_data["original_naming_rule"] = original_naming_rule
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
