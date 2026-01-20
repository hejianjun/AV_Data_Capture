# build-in lib
import os
import typing
from pathlib import Path

# third party lib
import requests
from concurrent.futures import ThreadPoolExecutor

# project wide
from mdc.config import config
from mdc.utils.http.request import get_html


def download_file_with_filename(url: str, filename: str, path: str) -> None:
    """
    download file save to give path with given name from given url
    """
    conf = config.getInstance()
    config_proxy = conf.proxy()

    for i in range(config_proxy.retry):
        try:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except:
                    print(f"[-]Fatal error! Can not make folder '{path}'")
                    os._exit(0)
            r = get_html(url=url, return_type="content")
            if r == "":
                print("[-]Movie Download Data not found!")
                return
            with open(os.path.join(path, filename), "wb") as code:
                code.write(r)
            return
        except requests.exceptions.ProxyError:
            i += 1
            print(
                "[-]Download :  Connect retry " + str(i) + "/" + str(config_proxy.retry)
            )
        except requests.exceptions.ConnectTimeout:
            i += 1
            print(
                "[-]Download :  Connect retry " + str(i) + "/" + str(config_proxy.retry)
            )
        except requests.exceptions.ConnectionError:
            i += 1
            print(
                "[-]Download :  Connect retry " + str(i) + "/" + str(config_proxy.retry)
            )
        except requests.exceptions.RequestException:
            i += 1
            print(
                "[-]Download :  Connect retry " + str(i) + "/" + str(config_proxy.retry)
            )
        except IOError:
            raise ValueError(f"[-]Create Directory '{path}' failed!")
            return
    print("[-]Connect Failed! Please check your Proxy or Network!")
    raise ValueError("[-]Connect Failed! Please check your Proxy or Network!")
    return


def download_one_file(args) -> str:
    """
    download file save to given path from given url
    wrapped for map function
    """

    (url, save_path, json_headers) = args
    if json_headers is not None:
        filebytes = get_html(
            url, return_type="content", json_headers=json_headers["headers"]
        )
    else:
        filebytes = get_html(url, return_type="content")
    if isinstance(filebytes, bytes) and len(filebytes):
        with save_path.open("wb") as fpbyte:
            if len(filebytes) == fpbyte.write(filebytes):
                return str(save_path)


def parallel_download_files(
    dn_list: typing.Iterable[typing.Sequence], parallel: int = 0, json_headers=None
):
    """
    download files in parallel 多线程下载文件

    用法示例: 2线程同时下载两个不同文件，并保存到不同路径，路径目录可未创建，但需要具备对目标目录和文件的写权限
    parallel_download_files([
    ('https://site1/img/p1.jpg', 'C:/temp/img/p1.jpg'),
    ('https://site2/cover/n1.xml', 'C:/tmp/cover/n1.xml')
    ])

    :dn_list: 可以是 tuple或者list: ((url1, save_fullpath1),(url2, save_fullpath2),) fullpath可以是str或Path
    :parallel: 并行下载的线程池线程数，为0则由函数自己决定
    """
    mp_args = []
    for url, fullpath in dn_list:
        if (
            url
            and isinstance(url, str)
            and url.startswith("http")
            and fullpath
            and isinstance(fullpath, (str, Path))
            and len(str(fullpath))
        ):
            fullpath = Path(fullpath)
            fullpath.parent.mkdir(parents=True, exist_ok=True)
            mp_args.append((url, fullpath, json_headers))
    if not len(mp_args):
        return []
    if not isinstance(parallel, int) or parallel not in range(1, 200):
        parallel = min(5, len(mp_args))
    with ThreadPoolExecutor(parallel) as pool:
        results = list(pool.map(download_one_file, mp_args))
    return results