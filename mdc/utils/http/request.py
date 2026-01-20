# build-in lib
import typing

# third party lib
import requests
from requests.adapters import HTTPAdapter
import mechanicalsoup
from urllib3.util.retry import Retry
from cloudscraper import create_scraper

# project wide
from mdc.config import config


G_USER_AGENT = r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.133 Safari/537.36"


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.timeout = 10  # seconds
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs):
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def get_html(
    url,
    cookies: dict = None,
    ua: str = None,
    return_type: str = None,
    encoding: str = None,
    json_headers=None,
):
    """
    网页请求核心函数
    """
    verify = config.getInstance().cacert_file()
    config_proxy = config.getInstance().proxy()
    errors = ""

    headers = {"User-Agent": ua or G_USER_AGENT}  # noqa
    if json_headers is not None:
        headers.update(json_headers)

    for i in range(config_proxy.retry):
        try:
            if config_proxy.enable:
                proxies = config_proxy.proxies()
                result = requests.get(
                    str(url),
                    headers=headers,
                    timeout=config_proxy.timeout,
                    proxies=proxies,
                    verify=False,
                    cookies=cookies,
                )
            else:
                result = requests.get(
                    str(url),
                    headers=headers,
                    timeout=config_proxy.timeout,
                    cookies=cookies,
                )

            if return_type == "object":
                return result
            elif return_type == "content":
                return result.content
            else:
                result.encoding = encoding or result.apparent_encoding
                return result.text
        except Exception as e:
            print("[-]Connect retry {}/{}".format(i + 1, config_proxy.retry))
            errors = str(e)
    if "getaddrinfo failed" in errors:
        print("[-]Connect Failed! Please Check your proxy config")
        debug = config.getInstance().debug()
        if debug:
            print("[-]" + errors)
    else:
        print("[-]" + errors)
        print("[-]Connect Failed! Please check your Proxy or Network!")
    raise Exception("Connect Failed")


def post_html(url: str, query: dict, headers: dict = None) -> requests.Response:
    config_proxy = config.getInstance().proxy()
    errors = ""
    headers_ua = {"User-Agent": G_USER_AGENT}
    if headers is None:
        headers = headers_ua
    else:
        headers.update(headers_ua)

    for i in range(config_proxy.retry):
        try:
            if config_proxy.enable:
                proxies = config_proxy.proxies()
                result = requests.post(
                    url,
                    data=query,
                    proxies=proxies,
                    headers=headers,
                    timeout=config_proxy.timeout,
                )
            else:
                result = requests.post(
                    url, data=query, headers=headers, timeout=config_proxy.timeout
                )
            return result
        except Exception as e:
            print("[-]Connect retry {}/{}".format(i + 1, config_proxy.retry))
            errors = str(e)
    print("[-]Connect Failed! Please check your Proxy or Network!")
    print("[-]" + errors)
    raise Exception("Connect Failed")


def get_html_session(
    url: str = None,
    cookies: dict = None,
    ua: str = None,
    return_type: str = None,
    encoding: str = None,
):
    config_proxy = config.getInstance().proxy()
    session = requests.Session()
    if isinstance(cookies, dict) and len(cookies):
        requests.utils.add_dict_to_cookiejar(session.cookies, cookies)
    retries = Retry(
        total=config_proxy.retry,
        connect=config_proxy.retry,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    session.mount(
        "https://",
        TimeoutHTTPAdapter(max_retries=retries, timeout=config_proxy.timeout),
    )
    session.mount(
        "http://", TimeoutHTTPAdapter(max_retries=retries, timeout=config_proxy.timeout)
    )
    if config_proxy.enable:
        session.verify = config.getInstance().cacert_file()
        session.proxies = config_proxy.proxies()
    headers = {"User-Agent": ua or G_USER_AGENT}
    session.headers = headers
    try:
        if isinstance(url, str) and len(url):
            result = session.get(str(url))
        else:  # 空url参数直接返回可重用session对象，无需设置return_type
            return session
        if not result.ok:
            return None
        if return_type == "object":
            return result
        elif return_type == "content":
            return result.content
        elif return_type == "session":
            return result, session
        else:
            result.encoding = encoding or "utf-8"
            return result.text
    except requests.exceptions.ProxyError:
        print("[-]get_html_session() Proxy error! Please check your Proxy")
    except requests.exceptions.RequestException:
        pass
    except Exception as e:
        print(f"[-]get_html_session() failed. {e}")
    return None


def get_html_by_browser(
    url: str = None,
    cookies: dict = None,
    ua: str = None,
    return_type: str = None,
    encoding: str = None,
    use_scraper: bool = False,
):
    config_proxy = config.getInstance().proxy()
    s = (
        create_scraper(
            browser={
                "custom": ua or G_USER_AGENT,
            }
        )
        if use_scraper
        else requests.Session()
    )
    if isinstance(cookies, dict) and len(cookies):
        requests.utils.add_dict_to_cookiejar(s.cookies, cookies)
    retries = Retry(
        total=config_proxy.retry,
        connect=config_proxy.retry,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    s.mount(
        "https://",
        TimeoutHTTPAdapter(max_retries=retries, timeout=config_proxy.timeout),
    )
    s.mount(
        "http://", TimeoutHTTPAdapter(max_retries=retries, timeout=config_proxy.timeout)
    )
    if config_proxy.enable:
        s.verify = config.getInstance().cacert_file()
        s.proxies = config_proxy.proxies()
    try:
        browser = mechanicalsoup.StatefulBrowser(
            user_agent=ua or G_USER_AGENT, session=s
        )
        if isinstance(url, str) and len(url):
            result = browser.open(url)
        else:
            return browser
        if not result.ok:
            return None

        if return_type == "object":
            return result
        elif return_type == "content":
            return result.content
        elif return_type == "browser":
            return result, browser
        else:
            result.encoding = encoding or "utf-8"
            return result.text
    except requests.exceptions.ProxyError:
        print("[-]get_html_by_browser() Proxy error! Please check your Proxy")
    except Exception as e:
        print(f"[-]get_html_by_browser() Failed! {e}")
    return None


def get_html_by_form(
    url,
    form_select: str = None,
    fields: dict = None,
    cookies: dict = None,
    ua: str = None,
    return_type: str = None,
    encoding: str = None,
):
    config_proxy = config.getInstance().proxy()
    s = requests.Session()
    if isinstance(cookies, dict) and len(cookies):
        requests.utils.add_dict_to_cookiejar(s.cookies, cookies)
    retries = Retry(
        total=config_proxy.retry,
        connect=config_proxy.retry,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    s.mount(
        "https://",
        TimeoutHTTPAdapter(max_retries=retries, timeout=config_proxy.timeout),
    )
    s.mount(
        "http://", TimeoutHTTPAdapter(max_retries=retries, timeout=config_proxy.timeout)
    )
    if config_proxy.enable:
        s.verify = config.getInstance().cacert_file()
        s.proxies = config_proxy.proxies()
    try:
        browser = mechanicalsoup.StatefulBrowser(
            user_agent=ua or G_USER_AGENT, session=s
        )
        result = browser.open(url)
        if not result.ok:
            return None
        form = (
            browser.select_form()
            if form_select is None
            else browser.select_form(form_select)
        )
        if isinstance(fields, dict):
            for k, v in fields.items():
                browser[k] = v
        response = browser.submit_selected()

        if return_type == "object":
            return response
        elif return_type == "content":
            return response.content
        elif return_type == "browser":
            return response, browser
        else:
            result.encoding = encoding or "utf-8"
            return response.text
    except requests.exceptions.ProxyError:
        print("[-]get_html_by_form() Proxy error! Please check your Proxy")
    except Exception as e:
        print(f"[-]get_html_by_form() Failed! {e}")
    return None


def get_html_by_scraper(
    url: str = None,
    cookies: dict = None,
    ua: str = None,
    return_type: str = None,
    encoding: str = None,
):
    config_proxy = config.getInstance().proxy()
    session = create_scraper(
        browser={
            "custom": ua or G_USER_AGENT,
        }
    )
    if isinstance(cookies, dict) and len(cookies):
        requests.utils.add_dict_to_cookiejar(session.cookies, cookies)
    retries = Retry(
        total=config_proxy.retry,
        connect=config_proxy.retry,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    session.mount(
        "https://",
        TimeoutHTTPAdapter(max_retries=retries, timeout=config_proxy.timeout),
    )
    session.mount(
        "http://", TimeoutHTTPAdapter(max_retries=retries, timeout=config_proxy.timeout)
    )
    if config_proxy.enable:
        session.verify = config.getInstance().cacert_file()
        session.proxies = config_proxy.proxies()
    try:
        if isinstance(url, str) and len(url):
            result = session.get(str(url))
        else:  # 空url参数直接返回可重用scraper对象，无需设置return_type
            return session
        if not result.ok:
            return None
        if return_type == "object":
            return result
        elif return_type == "content":
            return result.content
        elif return_type == "scraper":
            return result, session
        else:
            result.encoding = encoding or "utf-8"
            return result.text
    except requests.exceptions.ProxyError:
        print("[-]get_html_by_scraper() Proxy error! Please check your Proxy")
    except Exception as e:
        print(f"[-]get_html_by_scraper() failed. {e}")
    return None