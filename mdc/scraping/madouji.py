# -*- coding: utf-8 -*-
import re
from lxml import etree
from .parser import Parser
from .madou import change_number



class Madouji(Parser):
    source = "madouji"

    expr_url = '/html/head/meta[@property="og:url"]/@content'
    expr_cover = '/html/head/meta[@property="og:image"]/@content'
    expr_extrafanart = "//figure[2]/img/@src"
    expr_tags = '/html/head/meta[@name="keywords"]/@content'
    expr_title = "/html/head/title/text()"
    expr_outline = '//div[@class="intro"]/p/text()'
    expr_info = '//div[@class="info"]/span'
    infos = []

    def getNum(self, htmltree):
        for info in self.infos:
            num = re.search("番号：(.+)", info.text)
            if num:
                return (
                    num.group(1)
                    .replace("兔子先生", "")
                    .replace("皇家华人", "")
                    .replace("绝对领域", "")
                    .strip()
                )
        return ""

    def getActors(self, htmltree) -> list:
        for info in self.infos:
            num = re.search("女优/演员：", info.text)
            if num:
                return [actor.text for actor in info.getchildren()]
        return []

    def getRuntime(self, htmltree):
        for info in self.infos:
            num = re.search("时长：(\w+)", info.text)
            if num:
                return num.group(1)
        return ""

    def getSeries(self, htmltree):
        for info in self.infos:
            num = re.search("分类：(\w+)", info.text)
            if num:
                return num.group(1)
        return ""

    def extraInit(self):
        self.imagecut = 4
        self.uncensored = True
        self.allow_number_change = True

    def search(self, number):
        self.number = number.strip().upper()
        if self.specifiedUrl:
            self.detailurl = self.specifiedUrl
        else:
            number = "".join(item for item in change_number(number) if item)
            if self.number != number:
                print(number)
            self.detailurl = self.queryNumberUrl(number)
        if self.detailurl == None:
            return 404
        self.htmlcode = self.getHtml(self.detailurl)
        if self.htmlcode == 404 or self.htmlcode == 403:
            return 404
        htmltree = etree.fromstring(self.htmlcode, etree.HTMLParser())

        self.detailurl = self.getTreeElement(htmltree, self.expr_url)
        self.infos = htmltree.xpath(self.expr_info)

        result = self.dictformat(htmltree)
        return result

    def queryNumberUrl(self, number):
        keyword_url = "https://madouji.com/videos/keyword-" + number + ".html"
        qurySiteTree = self.getHtmlTree(keyword_url)
        site = self.getTreeElement(
            qurySiteTree,
            '//div[@class="videos"]/div[@class="item"]/div[@class="preview-container"]/a/@href',
        )
        if site == "" or site == "null" or site == "None":
            return None
        return "https://madouji.com" + site

    def getTitle(self, htmltree):
        title = super().getTitle(htmltree)
        # 删除番号
        try:
            title = str(re.sub("（.+?）( #\w+)*$", "", title, 1))
        except:
            title = title.replace("（" + self.number + "）", "")
        return title.strip()
