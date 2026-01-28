# -*- coding: utf-8 -*-

import re
from difflib import SequenceMatcher

from .parser import Parser


class Airav(Parser):
    source = "airav"

    expr_title = "//div[@class='video-title my-3']/h1/text()"
    expr_number = (
        "//div[@class='info-list my-2']/ul/li[contains(text(),'番號')]/span/text()"
    )
    expr_studio = (
        "//div[@class='info-list my-2']/ul/li[contains(text(),'廠商')]/a/text()"
    )
    expr_release = "//div[@class='video-item']/div[contains(@class,'me-4')]/text()"
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
        def _norm(s: str) -> str:
            if not isinstance(s, str):
                return ""
            return re.sub(r"[^A-Za-z0-9]+", "", s).upper()

        def _extract_number(text: str) -> str:
            if not isinstance(text, str) or not text.strip():
                return ""
            t = text.upper()
            m = re.search(r"([A-Z0-9]{2,12}(?:-[A-Z0-9]{1,12})*-\d{2,8})", t)
            return m.group(1) if m else ""

        queryUrl = "https://airav.io/search_result?kw=" + number
        queryTree = self.getHtmlTree(queryUrl)
        if queryTree == 404:
            return ""
        results = self.getTreeAll(
            queryTree, '//div[contains(@class,"oneVideo") and contains(@class,"col")]'
        )

        target_norm = _norm(number)
        candidates = []
        for node in results:
            href = self.getTreeElement(
                node, './/div[contains(@class,"oneVideo-top")]//a/@href'
            )
            if not href:
                continue
            title = " ".join(
                t.strip()
                for t in node.xpath(
                    './/div[contains(@class,"oneVideo-body")]//h5//text()'
                )
                if isinstance(t, str) and t.strip()
            )
            cand_num = _extract_number(title)
            cand_norm = _norm(cand_num) if cand_num else ""

            is_mosaic = "馬賽克破解版" in title or "馬賽克破壞版" in title

            if cand_norm and cand_norm == target_norm and not is_mosaic:
                return "https://airav.io" + href
            candidates.append((href, cand_norm, cand_num, is_mosaic))

        best_href = ""
        best_score = -1.0
        for href, cand_norm, cand_num, is_mosaic in candidates:
            score = 0.0
            if cand_norm:
                score = SequenceMatcher[str](None, target_norm, cand_norm).ratio()

            if is_mosaic:
                score -= 0.001

            if score > best_score:
                best_score = score
                best_href = href

        if best_href:
            return "https://airav.io" + best_href
        for node in results:
            href = self.getTreeElement(
                node, './/div[contains(@class,"oneVideo-top")]//a/@href'
            )
            if href:
                return "https://airav.io" + href
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
