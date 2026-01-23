# -*- coding: utf-8 -*-

from functools import lru_cache
import re
import json

from .custom_exceptions import QueryError
from .parser import Parser
from mdc.config import config
import importlib
import traceback
from mdc.utils.cookie import load_cookies
from mdc.file.file_utils import file_modification_days
from mdc.utils.logger import info as print, success, warn, error, debug


def search(number, sources: str = None, **kwargs):
    """根据`番号/电影`名搜索信息

    :param number: number/name  depends on type
    :param sources: sources string with `,` Eg: `avsox,javbus`
    :param type: `adult`, `general`
    """
    sc = Scraping()
    return sc.search(number, sources, **kwargs)


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
        for source in sources:
            if source_cookies := self.load_cookies_for_source(source, dbsite):
                valid_cookies[source] = source_cookies

        # 构造爬虫配置
        self.dbsite = dbsite
        self.dbcookies = valid_cookies  # 改为字典结构存储多爬虫cookie

        print(f"当前爬虫sources: {sources}")
        if type == "adult":
            return self.searchAdult(number, tuple(sources))
        else:
            return self.searchGeneral(number, tuple(sources))

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
        if not json_data or json_data["title"] == "":
            return None

        # If actor is anonymous, Fill in Anonymous
        if len(json_data["actor"]) == 0:
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
        if not json_data or json_data["title"] == "":
            return None

        # If actor is anonymous, Fill in Anonymous
        if len(json_data["actor"]) == 0:
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
            elif "gcolle" in sources and (re.search("\d{6}", file_number)):
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
            data["cover"] is None or data["cover"] == "" or data["cover"] == "null"
        ) and (
            data["cover_small"] is None
            or data["cover_small"] == ""
            or data["cover_small"] == "null"
        ):
            return False
        return True
