import requests
from lxml import html
from pathlib import Path
import config

headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }


def download_subtitles(filepath, path, multi_part, number, part, leak_word, c_word, hack_word) -> bool:
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
        subtitle_links = tree.xpath('//table[@class="table sub-table"]//tr/td[contains(translate(., "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz"), "' + number.lower() + '")]/a/@href')
        if not subtitle_links:
            print("未找到字幕链接")
            return False
        for subtitle_link in subtitle_links:
            if open_download(subtitle_link,path,number,leak_word,c_word,hack_word):
                return True
        
        return False
        
    except Exception as e:
        print(f"错误: {e}")
        return False
    
def open_download(subtitle_link,path,number,leak_word,c_word,hack_word):
    print(f"找到字幕链接: {subtitle_link}")
    subtitle_page_url = f"https://subtitlecat.com/{subtitle_link}"
    config_proxy = config.getInstance().proxy()
    if config_proxy.enable:
        proxies = config_proxy.proxies()

        subtitle_response = requests.get(subtitle_page_url, headers=headers, proxies=proxies,verify=False)
    else:
        subtitle_response = requests.get(subtitle_page_url, headers=headers,verify=False)

    print(f"访问字幕页面: {subtitle_page_url}, 状态码: {subtitle_response.status_code}")
    if subtitle_response.status_code != 200:
        return False
    tree = html.fromstring(subtitle_response.content)
    ext = "zh-CN.srt"
    download_links = tree.xpath('//div[@class="sub-single"]/span/a[contains(@href, "zh-CN.srt")]/@href')
    if not download_links:
        print("未找到简体中文字幕下载链接")
        download_links = tree.xpath('//div[@class="sub-single"]/span/a[contains(@href, "zh-TW.srt")]/@href')
        ext = "zh-TW.srt"
    if not download_links:
        print("未找到繁体中文字幕下载链接")
        return False
    download_link = download_links[0]
    print(f"找到下载链接: {download_link}")
    subtitle_download_url = f"https://subtitlecat.com/{download_link}"
    if config_proxy.enable:
        proxies = config_proxy.proxies()
        subtitle_response = requests.get(subtitle_download_url, headers=headers, proxies=proxies)
    else:
        subtitle_response = requests.get(subtitle_page_url, headers=headers)
    print(f"下载字幕: {subtitle_download_url}, 状态码: {subtitle_response.status_code}")
    if subtitle_response.status_code != 200:
        return False
    if "404 未找到".encode('utf-8') in subtitle_response.content:
        print("字幕文件下载失败")
        return False
    sub_targetpath = Path(path) / f"{number}{leak_word}{c_word}{hack_word}.{ext}"
    print(f"保存字幕至: {sub_targetpath}")
    with open(sub_targetpath, "wb") as file:
        file.write(subtitle_response.content)
    return True
    

def test_download_subtitles():
    filepath = "./"
    path = "G:\\srt\\"
    multi_part = False
    number = "SSNI-813"
    part = 1
    leak_word = "_leak"
    c_word = "_c"
    hack_word = "_hack"

    print("执行测试用例...")
    result = download_subtitles(filepath, path, multi_part, number, part, leak_word, c_word, hack_word)

    assert result == True, "下载失败"

    expected_file_path = os.path.join(path, f"{number}{leak_word}{c_word}{hack_word}.srt")
    import os
    assert os.path.exists(expected_file_path), "字幕文件未找到"

def test_download_subtitles2():
    import os,re,sys,glob
    # 获取当前目录
    current_dir = os.getcwd()
    print(current_dir)
    # 将当前目录添加到系统路径
    sys.path.append(current_dir)
    from number_parser import get_number
    # 遍历目录
    for root, dirs, files in os.walk("Z:\\R-18\\"):
        for file in files:
            # 检查文件名是否包含'-C'
            if '-C' not in file:
                # 检查文件扩展名是否为视频文件
                if file.endswith(('.mp4', '.avi', '.mkv', '.flv', '.mov')):
                    # 检查目录中是否存在.srt或.ass文件
                    srt_files = glob.glob(root+'\\*.srt')
                    ass_files = glob.glob(root+'\\*.ass')
                    # 检查是否存在同名的srt或ass文件
                    if not (srt_files or ass_files):
                            filepath = os.path.join(root, file)
                            movie_path = filepath
                            number = get_number(True,filepath)
                            # 使用正则表达式查找匹配的位置
                            match = re.search(" (|'|, ", number)

                            # 如果找到了匹配
                            if match:
                                # 截取匹配位置之前的内容
                                substring = number[:match.start()]
                            leak_word=''
                            c_word =''
                            hack_word =''
                            if '流出' in movie_path or 'uncensored' in movie_path.lower():
                                leak_word = '-无码流出'  # 流出影片后缀

                            if 'hack'.upper() in str(movie_path).upper() or '破解' in movie_path:
                                hack_word = "-hack"
                            
                            if re.search(r'[-_]UC(\.\w+$|-\w+)', movie_path,
                                        re.I):
                                c_word = '-UC'  #
                                hack_word = "-UC"
                            # 调用你的函数
                            download_subtitles(filepath, root, None, number, None, leak_word, c_word, hack_word)


if __name__ == '__main__':
    test_download_subtitles2()