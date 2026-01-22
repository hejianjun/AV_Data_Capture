# -*- coding: utf-8 -*-

from .parser import Parser


class Airav(Parser):
    source = "airav"

    expr_title = "//div[@class='video-title my-3']/h1/text()"
    expr_number = (
        "//div[@class='info-list my-2']/ul/li[contains(text(),'番號')]/span/text()"
    )
    expr_studio = "//div[class='video-item']/div[class='me-4']/text()"
    expr_release = "//div[@class='video-title my-3']/h1/text()"
    expr_outline = "/html/head/meta[@property='og:description']/@content"
    expr_actor = (
        "//div[@class='info-list my-2']/ul/li[contains(text(),'女優')]/a/text()"
    )
    expr_cover = "/html/head/meta[@property='og:image']/@content"
    expr_tags = "//div[@class='info-list my-2']/ul/li[contains(text(),'標籤')]/a/text()"

    def extraInit(self):
        # for javbus
        self.specifiedSource = None
        self.addtion_Javbus = False
        self.allow_number_change = False

    def queryNumberUrl(self, number):
        queryUrl = "https://airav.io/search_result?kw=" + number
        queryTree = self.getHtmlTree(queryUrl)
        results = self.getTreeAll(queryTree, '//div[contains(@class,"oneVideo-top")]/a')
        for i in results:
            return "https://airav.io" + i.attrib["href"]
        return ""

    def getTitle(self, htmltree):
        title = self.getTreeElement(htmltree, self.expr_title)
        if title is None:
            return ""
        return title.split(" ", 1)[1]

    def getStudio(self, htmltree):
        if self.addtion_Javbus:
            result = self.javbus.get("studio")
            if isinstance(result, str) and len(result):
                return result
        return super().getStudio(htmltree)

    def getRuntime(self, htmltree):
        if self.addtion_Javbus:
            result = self.javbus.get("runtime")
            if isinstance(result, str) and len(result):
                return result
        return ""

    def getDirector(self, htmltree):
        if self.addtion_Javbus:
            result = self.javbus.get("director")
            if isinstance(result, str) and len(result):
                return result
        return ""

    def getSeries(self, htmltree):
        if self.addtion_Javbus:
            result = self.javbus.get("series")
            if isinstance(result, str) and len(result):
                return result
        return ""

    def getNum(self, htmltree):
        number = self.getTreeElement(htmltree, self.expr_number)
        if number is None:
            return ""
        return number
