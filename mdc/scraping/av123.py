# -*- coding: utf-8 -*-

from .parser import Parser


class Av123(Parser):
    source = "av123"
    # 标题
    expr_title = "/html/head/title/text()"
    # 封面
    expr_cover = "/html/head/meta[@property='og:image']/@content"
    # 简介
    expr_outline = "/html/head/meta[@property='og:description']/@content"
    # 番号（定位"コード:"后的相邻span）
    expr_number = '//span[text()="コード:"]/following-sibling::span[1]/text()'
    # 演员（HTML中无演员信息）
    expr_actor = '//span[text()="女優:"]/following-sibling::span[1]/a/text()'
    # 标签
    expr_label = '//span[text()="ジャンル:"]/following-sibling::span[1]/a/text()'
    # 标签
    expr_tags = '//span[text()="ジャンル:"]/following-sibling::span[1]/a/text()'
    # 厂商（定位"メーカー:"后的a标签文本）
    expr_studio = '//span[text()="メーカー:"]/following-sibling::span[1]/a/text()'
    # 出版年（定位"リリース日:"后的span文本）
    expr_release = '//span[text()="リリース日:"]/following-sibling::span[1]/text()'
    # 时长（定位"再生時間:"后的span文本）
    expr_runtime = '//span[text()="再生時間:"]/following-sibling::span[1]/text()'

    def queryNumberUrl(self, number):
        """
        Returns the URL to query the number.
        """
        self.number = number.lower()
        if not self.number.startswith("fc2-ppv-"):
            self.number = self.number.replace("fc2-", "fc2-ppv-").replace(
                "fc2ppv-", "fc2-ppv-"
            )
        return f"https://123av.ws/ja/v/{self.number}"

    def getTitle(self, htmltree):
        title = self.getTreeElement(htmltree, self.expr_title).strip()
        if title.endswith(" - 123AV"):
            title = title[: -len(" - 123AV")].strip()
        if title.startswith(self.number.upper()):
            title = title[len(self.number) :].strip()
        return title
