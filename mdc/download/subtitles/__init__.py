import requests
from lxml import html
from pathlib import Path
from mdc.config import config
from mdc.utils.logger import info as print, success, warn, error, debug
from mdc.utils.http.ssl_warnings import disable_insecure_request_warning

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
}


def download_subtitles(
    filepath, path, multi_part, number, part, leak_word, c_word, hack_word
) -> bool:
    try:
        print(f"开始搜索{number}字幕...")
        search_url = f"https://subtitlecat.com/index.php?search={number}"
        config_proxy = config.getInstance().proxy()
        if config_proxy.enable:
            proxies = config_proxy.proxies()
            response = requests.get(search_url, headers=headers, proxies=proxies)
        else:
            response = requests.get(search_url, headers=headers)
        print(f"搜索URL: {search_url}, 状态码: {response.status_code}")
        if response.status_code != 200:
            return False

        tree = html.fromstring(response.content)
        subtitle_links = tree.xpath(
            '//table[@class="table sub-table"]//tr/td[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "'
            + number.lower()
            + '")]/a/@href'
        )
        if not subtitle_links:
            print("未找到字幕链接")
            return False
        for subtitle_link in subtitle_links:
            if open_download(subtitle_link, path, number, leak_word, c_word, hack_word):
                return True

        return False

    except Exception as e:
        print(f"错误: {e}")
        return False


def open_download(subtitle_link, path, number, leak_word, c_word, hack_word):
    print(f"找到字幕链接: {subtitle_link}")
    subtitle_page_url = f"https://subtitlecat.com/{subtitle_link}"
    config_proxy = config.getInstance().proxy()
    disable_insecure_request_warning()
    if config_proxy.enable:
        proxies = config_proxy.proxies()

        subtitle_response = requests.get(
            subtitle_page_url, headers=headers, proxies=proxies, verify=False
        )
    else:
        subtitle_response = requests.get(
            subtitle_page_url, headers=headers, verify=False
        )

    print(f"访问字幕页面: {subtitle_page_url}, 状态码: {subtitle_response.status_code}")
    if subtitle_response.status_code != 200:
        return False
    tree = html.fromstring(subtitle_response.content)
    ext = "zh-CN.srt"
    download_links = tree.xpath(
        '//div[@class="sub-single"]/span/a[contains(@href, "zh-CN.srt")]/@href'
    )
    if not download_links:
        print("未找到简体中文字幕下载链接")
        download_links = tree.xpath(
            '//div[@class="sub-single"]/span/a[contains(@href, "zh-TW.srt")]/@href'
        )
        ext = "zh-TW.srt"
    if not download_links:
        print("未找到繁体中文字幕下载链接")
        return False
    download_link = download_links[0]
    print(f"找到下载链接: {download_link}")
    subtitle_download_url = f"https://subtitlecat.com/{download_link}"
    if config_proxy.enable:
        proxies = config_proxy.proxies()
        subtitle_response = requests.get(
            subtitle_download_url, headers=headers, proxies=proxies
        )
    else:
        subtitle_response = requests.get(subtitle_page_url, headers=headers)
    print(f"下载字幕: {subtitle_download_url}, 状态码: {subtitle_response.status_code}")
    if subtitle_response.status_code != 200:
        return False
    if "404 未找到".encode("utf-8") in subtitle_response.content:
        print("字幕文件下载失败")
        return False
    sub_targetpath = Path(path) / f"{number}{leak_word}{c_word}{hack_word}.{ext}"
    print(f"保存字幕至: {sub_targetpath}")
    with open(sub_targetpath, "wb") as file:
        file.write(subtitle_response.content)
    return True
