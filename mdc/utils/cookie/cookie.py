# build-in lib
import os.path
import json
import typing
from pathlib import Path


def load_cookies(
    cookie_json_filename: str,
) -> typing.Tuple[typing.Optional[dict], typing.Optional[str]]:
    """
    加载cookie,用于以会员方式访问非游客内容

    :filename: cookie文件名。获取cookie方式：从网站登录后，通过浏览器插件(CookieBro或EdittThisCookie)或者直接在地址栏网站链接信息处都可以复制或者导出cookie内容，以JSON方式保存

    # 示例: FC2-755670 url https://javdb9.com/v/vO8Mn
    # json 文件格式
    # 文件名: 站点名.json，示例 javdb9.json
    # 内容(文件编码:UTF-8)：
    {
        "over18":"1",
        "redirect_to":"%2Fv%2FvO8Mn",
        "remember_me_token":"***********",
        "_jdb_session":"************",
        "locale":"zh",
        "__cfduid":"*********",
        "theme":"auto"
    }
    """
    filename = os.path.basename(cookie_json_filename)
    if not len(filename):
        return None, None
    path_search_order = (
        Path.cwd() / filename,
        Path.home() / filename,
        Path.home() / f".mdc/{filename}",
        Path.home() / f".local/share/mdc/{filename}",
    )
    cookies_filename = None
    try:
        for p in path_search_order:
            if p.is_file():
                cookies_filename = str(p.resolve())
                break
        if not cookies_filename:
            return None, None
        return json.loads(
            Path(cookies_filename).read_text(encoding="utf-8")
        ), cookies_filename
    except:
        return None, None
