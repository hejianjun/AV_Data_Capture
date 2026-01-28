# -*- coding: utf-8 -*-
import re
from lxml import etree
from .parser import Parser
from .madou import change_number


class Javday(Parser):
    source = "javday"

    expr_url = '/html/head/meta[@property="og:url"]/@content'
    expr_cover = '/html/head/meta[@property="og:image"]/@content'
    expr_tags = '/html/head/meta[@name="keywords"]/@content'
    expr_title = "/html/head/title/text()"
    expr_actor = "//span[@class='vod_actor']/a/text()"
    expr_studio = '//span[@class="producer"]/a/text()'
    expr_number = '//span[@class="jpnum"]/text()'

    def extraInit(self):
        self.imagecut = 4
        self.uncensored = True
        self.allow_number_change = True

    def search(self, number):
        self.number = number.strip().upper()
        if self.specifiedUrl:
            self.detailurl = self.specifiedUrl
        else:
            number = (
                "".join(item for item in change_number(number) if item)
                .replace("-", "")
                .upper()
            )
            if self.number != number:
                print(number)
            self.detailurl = "https://javday.tv/videos/" + number + "/"
        self.htmlcode = self.getHtml(self.detailurl)
        if self.htmlcode == 404:
            return 404
        htmltree = etree.fromstring(self.htmlcode, etree.HTMLParser())
        self.detailurl = self.getTreeElement(htmltree, self.expr_url)

        result = self.dictformat(htmltree)
        return result

    def getTitle(self, htmltree):
        title = super().getTitle(htmltree)
        # 删除番号和网站名
        try:
            title = str(re.sub("^[\w\-]+", "", title, 1))
            title = str(re.sub("[\w\.\-]+$", "", title, 1))
        except Exception:
            print("非标准标题" + title)
            title = title.replace(self.number, "")
            title = title.replace("JAVDAY.TV", "")
        return title.strip("- ")

    def getTags(self, htmltree) -> list:
        tags = super().getTags(htmltree)
        return [tag for tag in tags if "JAVDAY.TV" not in tag]
