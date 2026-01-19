import os
import re
import time
import shutil
import requests
from pathlib import Path
import config
from ADC_function import get_html, parallel_download_files
from file_utils import moveFailedFolder, file_not_exist_or_empty


def download_file_with_filename(url, filename, path, filepath, json_headers=None):
    conf = config.getInstance()
    configProxy = conf.proxy()

    for i in range(configProxy.retry):
        try:
            if not os.path.exists(path):
                try:
                    os.makedirs(path)
                except:
                    print(f"[-]Fatal error! Can not make folder '{path}'")
                    os._exit(0)
            r = get_html(url=url, return_type="content", json_headers=json_headers)
            if r == "":
                print("[-]Movie Download Data not found!")
                return
            with open(os.path.join(path, filename), "wb") as code:
                code.write(r)
            return
        except requests.exceptions.ProxyError:
            i += 1
            print(
                "[-]Image Download : Proxy error "
                + str(i)
                + "/"
                + str(configProxy.retry)
            )
        except Exception as e:
            print("[-]Image Download :Error", e)
    print("[-]Connect Failed! Please check your Proxy or Network!")
    moveFailedFolder(filepath)
    return


def trailer_download(trailer, leak_word, c_word, hack_word, number, path, filepath):
    if (
        download_file_with_filename(
            trailer,
            number + leak_word + c_word + hack_word + "-trailer.mp4",
            path,
            filepath,
        )
        == "failed"
    ):
        return
    configProxy = config.getInstance().proxy()
    for i in range(configProxy.retry):
        if file_not_exist_or_empty(
            path + "/" + number + leak_word + c_word + hack_word + "-trailer.mp4"
        ):
            print("[!]Video Download Failed! Trying again. [{}/3]", i + 1)
            download_file_with_filename(
                trailer,
                number + leak_word + c_word + hack_word + "-trailer.mp4",
                path,
                filepath,
            )
            continue
        else:
            break
    if file_not_exist_or_empty(
        path + "/" + number + leak_word + c_word + hack_word + "-trailer.mp4"
    ):
        return
    print(
        "[+]Video Downloaded!",
        path + "/" + number + leak_word + c_word + hack_word + "-trailer.mp4",
    )


def actor_photo_download(actors, save_dir, number):
    if not isinstance(actors, dict) or not len(actors) or not len(save_dir):
        return
    save_dir = Path(save_dir)
    if not save_dir.is_dir():
        return
    conf = config.getInstance()
    actors_dir = save_dir / ".actors"
    download_only_missing_images = conf.download_only_missing_images()
    dn_list = []
    for actor_name, url in actors.items():
        res = re.match(r"^http.*(\.\w+)$", url, re.A)
        if not res:
            continue
        ext = res.group(1)
        pic_fullpath = actors_dir / f"{actor_name}{ext}"
        if download_only_missing_images and not file_not_exist_or_empty(pic_fullpath):
            continue
        dn_list.append((url, pic_fullpath))
    if not len(dn_list):
        return
    parallel = min(len(dn_list), conf.extrafanart_thread_pool_download())
    if parallel > 100:
        print(
            "[!]Warrning: Parallel download thread too large may cause website ban IP!"
        )
    result = parallel_download_files(dn_list, parallel)
    failed = 0
    for i, r in enumerate(result):
        if not r:
            failed += 1
            print(
                f"[-]Actor photo '{dn_list[i][0]}' to '{dn_list[i][1]}' download failed!"
            )
    if failed:  # 非致命错误，电影不移入失败文件夹，将来可以用模式3补齐
        print(
            f"[-]Failed downloaded {failed}/{len(result)} actor photo for [{number}] to '{actors_dir}', you may retry run mode 3 later."
        )
    else:
        print(f"[+]Successfully downloaded {len(result)} actor photo.")


def extrafanart_download(data, path, number, filepath, json_data=None):
    if config.getInstance().extrafanart_thread_pool_download():
        return extrafanart_download_threadpool(data, path, number, json_data)
    extrafanart_download_one_by_one(data, path, filepath, json_data)


def extrafanart_download_one_by_one(data, path, filepath, json_data=None):
    tm_start = time.perf_counter()
    j = 1
    conf = config.getInstance()
    path = os.path.join(path, conf.get_extrafanart())
    configProxy = conf.proxy()
    download_only_missing_images = conf.download_only_missing_images()
    for url in data:
        jpg_filename = f"extrafanart-{j}.jpg"
        jpg_fullpath = os.path.join(path, jpg_filename)
        if download_only_missing_images and not file_not_exist_or_empty(jpg_fullpath):
            continue
        if (
            download_file_with_filename(url, jpg_filename, path, filepath, json_data)
            == "failed"
        ):
            moveFailedFolder(filepath)
            return
        for i in range(configProxy.retry):
            if file_not_exist_or_empty(jpg_fullpath):
                print(f"[!]Image Download Failed! Trying again. [{i + 1}/3]")
                download_file_with_filename(
                    url, jpg_filename, path, filepath, json_data
                )
                continue
            else:
                break
        if file_not_exist_or_empty(jpg_fullpath):
            return
        print("[+]Image Downloaded!", Path(jpg_fullpath).name)
        j += 1
    if conf.debug():
        print(
            f"[!]Extrafanart download one by one mode runtime {time.perf_counter() - tm_start:.3f}s"
        )


def extrafanart_download_threadpool(url_list, save_dir, number, json_data=None):
    tm_start = time.perf_counter()
    conf = config.getInstance()
    extrafanart_dir = Path(save_dir) / conf.get_extrafanart()
    download_only_missing_images = conf.download_only_missing_images()
    dn_list = []
    for i, url in enumerate(url_list, start=1):
        jpg_fullpath = extrafanart_dir / f"extrafanart-{i}.jpg"
        if download_only_missing_images and not file_not_exist_or_empty(jpg_fullpath):
            continue
        dn_list.append((url, jpg_fullpath))
    if not len(dn_list):
        return
    parallel = min(len(dn_list), conf.extrafanart_thread_pool_download())
    if parallel > 100:
        print(
            "[!]Warrning: Parallel download thread too large may cause website ban IP!"
        )
    result = parallel_download_files(dn_list, parallel, json_data)
    failed = 0
    for i, r in enumerate(result, start=1):
        if not r:
            failed += 1
            print(f"[-]Extrafanart {i} for [{number}] download failed!")
    if failed:  # 非致命错误，电影不移入失败文件夹，将来可以用模式3补齐
        print(
            f"[-]Failed downloaded {failed}/{len(result)} extrafanart images for [{number}] to '{extrafanart_dir}', you may retry run mode 3 later."
        )
    else:
        print(f"[+]Successfully downloaded {len(result)} extrafanarts.")
    if conf.debug():
        print(
            f"[!]Extrafanart download ThreadPool mode runtime {time.perf_counter() - tm_start:.3f}s"
        )


def image_ext(url):
    try:
        ext = os.path.splitext(url)[-1]
        if ext in {".jpg", ".jpge", ".bmp", ".png", ".gif"}:
            return ext
        return ".jpg"
    except:
        return ".jpg"


def image_download(cover, fanart_path, thumb_path, path, filepath, json_headers=None):
    full_filepath = os.path.join(path, thumb_path)
    if (
        config.getInstance().download_only_missing_images()
        and not file_not_exist_or_empty(full_filepath)
    ):
        return
    if json_headers != None:
        if (
            download_file_with_filename(
                cover, thumb_path, path, filepath, json_headers["headers"]
            )
            == "failed"
        ):
            moveFailedFolder(filepath)
            return
    else:
        if download_file_with_filename(cover, thumb_path, path, filepath) == "failed":
            moveFailedFolder(filepath)
            return

    configProxy = config.getInstance().proxy()
    for i in range(configProxy.retry):
        if file_not_exist_or_empty(full_filepath):
            print(f"[!]Image Download Failed! Trying again. [{i + 1}/3]")
            if json_headers != None:
                download_file_with_filename(
                    cover, thumb_path, path, filepath, json_headers["headers"]
                )
            else:
                download_file_with_filename(cover, thumb_path, path, filepath)
            continue
        else:
            break
    if file_not_exist_or_empty(full_filepath):
        return
    print("[+]Image Downloaded!", Path(full_filepath).name)
    if not config.getInstance().jellyfin():
        shutil.copyfile(full_filepath, os.path.join(path, fanart_path))
