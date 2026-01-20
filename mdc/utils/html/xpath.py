# third party lib
from lxml import etree


def get_xpath_single(html_code: str, xpath):
    html = etree.fromstring(html_code, etree.HTMLParser())
    result1 = str(html.xpath(xpath)).strip(" ['']")
    return result1