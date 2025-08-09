# -*- coding: utf-8 -*-

import re
from lxml import etree
from . import httprequest
from .parser import Parser


class Av123(Parser):
    source = 'av123'
    # 标题
    expr_title = "/html/head/title/text()"
    # 封面
    expr_cover = "/html/head/meta[@name='og:image']/@content"
    # 简介
    expr_outline = "/html/head/meta[@name='og:description']/@content"
    # 番号
    expr_number = '//div[@class="details"]/div[@class="content"]/div[@class="detail-item"]/div/span/text()'
    # 演员
    expr_actor = ''
    # 标签
    expr_label = ''
    # 标签
    expr_tags = ''
    # 厂商
    expr_studio = ''
    # 出版年
    expr_release = ''
    # 时长
    expr_runtime = ''
    # 导演
    expr_series = ''

    def queryNumberUrl(self, number):
        """
        Returns the URL to query the number.
        """
        number = number.lower()
        return f'https://123av.ws/ja/v/{number}'