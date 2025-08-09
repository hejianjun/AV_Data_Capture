# -*- coding: utf-8 -*-
import re
from lxml import etree
from .parser import Parser


class Madouqu(Parser):
    source = 'madouqu'

    expr_url = '/html/head/meta[@property="og:url"]/@content'
    expr_cover = '/html/head/meta[@property="og:image"]/@content'
    expr_title = '/html/head/meta[@property="og:title"]/@content'
    expr_outline = '/html/head/meta[@property="og:description"]/@content'
    expr_actor = '//a[@title="model"]/../text()'
    expr_tags = '//a[@rel="tag"]/text()'

    def extraInit(self):
        self.imagecut = 4
        self.uncensored = True
        self.allow_number_change = True

    def getNum(self, htmltree):
        title = self.getTreeElement(htmltree, self.expr_title)
        if title:
            num = re.search(r'^([A-Z]+-\d+)', title)
            if num:
                return num.group(1)
        return ''

    def getActors(self, htmltree) -> list:
        actor_text = self.getTreeElement(htmltree, self.expr_actor)
        if actor_text:
            # 从"麻豆女郎：苡若"中提取演员名
            actor = re.sub(r'：', '', actor_text)
            if actor:
                return [actor]
        return []

    def getTitle(self, htmltree):
        title = self.getTreeElement(htmltree, self.expr_title)
        if title:
            # 删除番号部分
            title = re.sub(r'^[A-Z]+-\d+\s+', '', title)
            return title.strip()
        return ''

    def getOutline(self, htmltree):
        outline = self.getTreeElement(htmltree, self.expr_outline)
        if outline:
            # 清理描述文本
            outline = re.sub(r'.{2}番號：.*?.{2}片名：', '', outline)
            outline = re.sub(r'.{2}女郎：.*?下載地址：.*$', '', outline)
            return outline.strip()
        return ''

    def search(self, number):
        self.number = number.strip().upper()
        if self.specifiedUrl:
            self.detailurl = self.specifiedUrl
        else:
            self.detailurl = f'https://madouqu.com/video/{number.lower()}/'
        
        self.htmlcode = self.getHtml(self.detailurl)
        if self.htmlcode == 404 or self.htmlcode == 403:
            return 404
            
        htmltree = etree.fromstring(self.htmlcode, etree.HTMLParser())
        result = self.dictformat(htmltree)
        return result 