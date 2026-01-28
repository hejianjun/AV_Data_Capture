# -*- coding: utf-8 -*-

import re
from ssl import SSLError
from urllib.parse import urljoin
from lxml import etree

from .custom_exceptions import QueryError
from mdc.utils.http.request import request_session
from .parser import Parser

from mdc.utils.http.ssl_warnings import disable_insecure_request_warning


class Javdb(Parser):
    source = "javdb"

    expr_number = '//strong[contains(text(),"番號")]/../span/text()'
    expr_number2 = '//strong[contains(text(),"番號")]/../span/a/text()'
    expr_title = "/html/head/title/text()"
    expr_title_no = '//*[contains(@class,"movie-list")]/div/a/div[contains(@class, "video-title")]/strong/text()'
    expr_runtime = '//strong[contains(text(),"時長")]/../span/text()'
    expr_runtime2 = '//strong[contains(text(),"時長")]/../span/a/text()'
    expr_uncensored = '//strong[contains(text(),"類別")]/../span/a[contains(@href,"/tags/uncensored?") or contains(@href,"/tags/western?")]'
    expr_actor = '//span[@class="value"]/a[contains(@href,"/actors/")]/text()'
    expr_actor2 = (
        '//span[@class="value"]/a[contains(@href,"/actors/")]/../strong/@class'
    )
    expr_release = '//strong[contains(text(),"日期")]/../span/text()'
    expr_release_no = (
        '//*[contains(@class,"movie-list")]/div/a/div[contains(@class, "meta")]/text()'
    )
    expr_studio = '//strong[contains(text(),"片商")]/../span/a/text()'
    expr_studio2 = '//strong[contains(text(),"賣家:")]/../span/a/text()'
    expr_director = '//strong[contains(text(),"導演")]/../span/text()'
    expr_director2 = '//strong[contains(text(),"導演")]/../span/a/text()'
    expr_cover = "//div[contains(@class, 'column-video-cover')]/a/img/@src"
    expr_cover2 = "//div[contains(@class, 'column-video-cover')]/img/@src"
    expr_cover_no = '//*[contains(@class,"movie-list")]/div/a/div[contains(@class, "cover")]/img/@src'
    expr_trailer = '//span[contains(text(),"預告片")]/../../video/source/@src'
    expr_extrafanart = "//article[@class='message video-panel']/div[@class='message-body']/div[@class='tile-images preview-images']/a[contains(@href,'/samples/')]/@href"
    expr_tags = '//strong[contains(text(),"類別")]/../span/a/text()'
    expr_tags2 = '//strong[contains(text(),"類別")]/../span/text()'
    expr_series = '//strong[contains(text(),"系列")]/../span/text()'
    expr_series2 = '//strong[contains(text(),"系列")]/../span/a/text()'
    expr_label = '//strong[contains(text(),"系列")]/../span/text()'
    expr_label2 = '//strong[contains(text(),"系列")]/../span/a/text()'
    expr_userrating = '//span[@class="score-stars"]/../text()'
    expr_uservotes = '//span[@class="score-stars"]/../text()'
    expr_actorphoto = (
        '//strong[contains(text(),"演員:")]/../span/a[starts-with(@href,"/actors/")]'
    )

    def extraInit(self):
        self.fixstudio = False
        self.noauth = False

    def updateCore(self, core):
        if core.proxies:
            self.proxies = core.proxies
        if core.verify:
            self.verify = core.verify
        if core.morestoryline:
            self.morestoryline = True
        if core.specifiedSource == self.source:
            self.specifiedUrl = core.specifiedUrl
        # special
        if core.dbsite:
            self.dbsite = core.dbsite
        else:
            self.dbsite = "javdb"
        if core.dbcookies:
            self.cookies = core.dbcookies.get(
                self.source, {"over18": "1", "theme": "auto", "locale": "zh"}
            )
        else:
            self.cookies = {"over18": "1", "theme": "auto", "locale": "zh"}

    def search(self, number: str):
        self.number = number
        number = number.upper()
        if "FC2-PPV" in number or "FC2PPV" in number:
            number = number.replace("FC2-PPV", "FC2").replace("FC2PPV", "FC2")
            print(number)
            self.allow_number_change = True
            self.uncensored = True
        self.session = request_session(
            cookies=self.cookies, proxies=self.proxies, verify=self.verify
        )
        if self.specifiedUrl:
            self.detailurl = self.specifiedUrl
        else:
            self.detailurl = self.queryNumberUrl(number)
        self.deatilpage = self.session.get(self.detailurl).text
        if (
            "此內容需要登入才能查看或操作" in self.deatilpage
            or "需要VIP權限才能訪問此內容" in self.deatilpage
            or "開通VIP" in self.deatilpage
        ):
            self.noauth = True
            self.imagecut = 0
            result = self.dictformat(self.querytree)
        else:
            htmltree = etree.fromstring(self.deatilpage, etree.HTMLParser())
            result = self.dictformat(htmltree)
        return result

    def queryNumberUrl(self, number):
        javdb_url = f"https://{self.dbsite}.com/search?q={number}&f=all"
        try:
            print(f"搜索的URL: {javdb_url}")
            disable_insecure_request_warning()
            resp = self.session.get(
                javdb_url,
                cookies=self.cookies,
                proxies=False,
                verify=False,
                timeout=(3.05, 10),  # 连接超时3.05秒，读取超时10秒
            )
            print(f"访问JavDB: {javdb_url}, 状态码: {resp.status_code}")
        except SSLError as e:
            print(f"SSL错误: {e}")
        except BaseException as e:
            raise QueryError(number, f"[!] {self.number}: 访问JavDB时出错 - {str(e)}")
        if "由於版權限制" in resp.text:
            raise QueryError(number, "JavDB: 该影片由于版权限制无法访问")
        print(f"搜索的URL: {javdb_url}")
        print(f"搜索的番号: {number}")
        self.querytree = etree.fromstring(resp.text, etree.HTMLParser())
        urls = self.getTreeAll(
            self.querytree, '//*[contains(@class,"movie-list")]/div/a/@href'
        )
        ids = self.getTreeAll(self.querytree, self.expr_title_no)
        print(f"提取的ID列表: {ids}")
        print(f"提取的URL列表: {urls}")
        if not ids:
            raise QueryError(number, f"番号 {number} 在JavDB中未找到{resp.text}")
        try:
            self.queryid = ids.index(number)
            correct_url = urls[self.queryid]
        except ValueError:
            # 如果精确匹配失败，检查是否为部分匹配或格式差异
            for idx, _id in enumerate(ids):
                if _id.upper().replace(" ", "") == number.upper().replace(" ", ""):
                    self.queryid = idx
                    correct_url = urls[idx]
                    break
            else:
                raise QueryError(
                    number, f"精确匹配失败{resp.text}，但可能找到近似结果：{ids[0]}"
                )
        return urljoin(resp.url, correct_url)

    def getNum(self, htmltree):
        if self.noauth:
            return self.number
        # 番号被分割开，需要合并后才是完整番号
        part1 = self.getTreeElement(htmltree, self.expr_number)
        part2 = self.getTreeElement(htmltree, self.expr_number2)
        dp_number = part2 + part1
        # 检测番号是否为空
        if not dp_number:
            raise Exception(f"[!] {self.number}: found empty number in javdb")
        # 转换为大写进行比较
        original_upper = self.number.upper()
        dp_upper = dp_number.upper()
        # 去除原番号开头的所有数字
        stripped_original = original_upper.lstrip("0123456789")
        # 检查是否完全匹配或存在数字前缀且剩余部分匹配
        if original_upper == dp_upper or (
            stripped_original == dp_upper
            and len(stripped_original) < len(original_upper)
        ):
            self.number = dp_number
        else:
            raise Exception(
                f"[!] {self.number}: find [{dp_number}] in javdb, not match"
            )
        return self.number

    def getTitle(self, htmltree):
        if self.noauth:
            return self.getTreeElement(htmltree, self.expr_title_no, self.queryid)
        browser_title = super().getTitle(htmltree)
        title = browser_title[: browser_title.find(" | JavDB")].strip()
        return title.replace(self.number, "").strip()

    def getCover(self, htmltree):
        if self.noauth:
            return self.getTreeElement(htmltree, self.expr_cover_no, self.queryid)
        return super().getCover(htmltree)

    def getRelease(self, htmltree):
        if self.noauth:
            return self.getTreeElement(
                htmltree, self.expr_release_no, self.queryid
            ).strip()
        return super().getRelease(htmltree)

    def getDirector(self, htmltree):
        return self.getTreeElementbyExprs(
            htmltree, self.expr_director, self.expr_director2
        )

    def getSeries(self, htmltree):
        # NOTE 不清楚javdb是否有一部影片多个series的情况，暂时保留
        results = self.getTreeAllbyExprs(htmltree, self.expr_series, self.expr_series2)
        result = "".join(results)
        if not result and self.fixstudio:
            result = self.getStudio(htmltree)
        return result

    def getLabel(self, htmltree):
        results = self.getTreeAllbyExprs(htmltree, self.expr_label, self.expr_label2)
        result = "".join(results)
        if not result and self.fixstudio:
            result = self.getStudio(htmltree)
        return result

    def getActors(self, htmltree):
        actors = self.getTreeAll(htmltree, self.expr_actor)
        genders = self.getTreeAll(htmltree, self.expr_actor2)
        r = []
        idx = 0
        # NOTE only female, we dont care others
        actor_gendor = "female"
        for act in actors:
            if (
                (actor_gendor == "all")
                or (
                    actor_gendor == "both"
                    and genders[idx] in ["symbol female", "symbol male"]
                )
                or (actor_gendor == "female" and genders[idx] == "symbol female")
                or (actor_gendor == "male" and genders[idx] == "symbol male")
            ):
                r.append(act)
            idx = idx + 1
        if re.match(r"FC2-[\d]+", self.number, re.A) and not r:
            r = "素人"
            self.fixstudio = True
        return r

    def getOutline(self, htmltree):
        if self.morestoryline:
            from .storyline import getStoryline

            return getStoryline(
                self.number,
                self.getUncensored(htmltree),
                proxies=self.proxies,
                verify=self.verify,
            )
        return ""

    def getTrailer(self, htmltree):
        video = super().getTrailer(htmltree)
        # 加上数组判空
        if video:
            if "https:" not in video:
                video_url = "https:" + video
            else:
                video_url = video
        else:
            video_url = ""
        return video_url

    def getTags(self, htmltree):
        return self.getTreeAllbyExprs(htmltree, self.expr_tags, self.expr_tags2)

    def getUserRating(self, htmltree):
        try:
            numstrs = self.getTreeElement(htmltree, self.expr_userrating)
            nums = re.findall("[0-9.]+", numstrs)
            return float(nums[0])
        except Exception:
            return ""

    def getUserVotes(self, htmltree):
        try:
            result = self.getTreeElement(htmltree, self.expr_uservotes)
            v = re.findall("[0-9.]+", result)
            return int(v[1])
        except Exception:
            return ""

    def getaphoto(self, url, session):
        html_page = session.get(url, proxies=self.proxies, verify=self.verify).text
        img_url = re.findall(
            r"<span class\=\"avatar\" style\=\"background\-image\: url\((.*?)\)",
            html_page,
        )
        return img_url[0] if img_url else ""

    def getActorPhoto(self, htmltree):
        actorall = self.getTreeAll(htmltree, self.expr_actorphoto)
        if not actorall:
            return {}
        actors = self.getActors(htmltree)
        actor_photo = {}
        for i in actorall:
            x = re.findall(r"/actors/(.*)", i.attrib["href"], re.A)
            if not len(x) or not len(x[0]) or i.text not in actors:
                continue
            # NOTE: https://c1.jdbstatic.com 会经常变动，直接使用页面内的地址获取
            # actor_id = x[0]
            # pic_url = f"https://c1.jdbstatic.com/avatars/{actor_id[:2].lower()}/{actor_id}.jpg"
            # if not self.session.head(pic_url).ok:
            try:
                pic_url = self.getaphoto(
                    urljoin("https://javdb.com", i.attrib["href"]), self.session
                )
                if len(pic_url):
                    actor_photo[i.text] = pic_url
            except Exception:
                pass
        return actor_photo
