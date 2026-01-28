# build-in lib
import typing
from typing import Optional, Union, Tuple, Any

# third party lib
import requests
from requests.adapters import HTTPAdapter
import mechanicalsoup
from urllib3.util.retry import Retry
from cloudscraper import create_scraper

# project wide
from mdc.config import config

from mdc.utils.http.ssl_warnings import disable_insecure_request_warning


G_USER_AGENT = r"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.133 Safari/537.36"


class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        """
        初始化 TimeoutHTTPAdapter
        :param args: 位置参数
        :param kwargs: 关键字参数, 支持 timeout 参数
        """
        self.timeout = 10  # seconds
        if "timeout" in kwargs:
            self.timeout = kwargs["timeout"]
            del kwargs["timeout"]
        super().__init__(*args, **kwargs)

    def send(self, request, **kwargs) -> requests.Response:
        """
        发送请求
        :param request: PreparedRequest 对象
        :param kwargs: 关键字参数
        :return: Response 对象
        """
        timeout = kwargs.get("timeout")
        if timeout is None:
            kwargs["timeout"] = self.timeout
        return super().send(request, **kwargs)


def get(
    url: str,
    cookies: Optional[dict] = None,
    ua: Optional[str] = None,
    extra_headers: Optional[dict] = None,
    return_type: Optional[str] = None,
    encoding: Optional[str] = None,
    retry: Optional[int] = None,
    timeout: Optional[int] = None,
    proxies: Optional[dict] = None,
    verify: Optional[bool] = None,
) -> Union[requests.Response, bytes, str]:
    config_proxy = config.getInstance().proxy()
    errors = ""
    headers = {"User-Agent": ua or G_USER_AGENT}
    if extra_headers is not None:
        headers.update(extra_headers)
    retry = config_proxy.retry if retry is None else retry
    timeout = config_proxy.timeout if timeout is None else timeout

    for i in range(retry):
        try:
            effective_proxies = proxies
            effective_verify = verify
            if effective_proxies is None and config_proxy.enable:
                effective_proxies = config_proxy.proxies()
                if effective_verify is None:
                    disable_insecure_request_warning()
                    effective_verify = False
            result = requests.get(
                str(url),
                headers=headers,
                timeout=timeout,
                proxies=effective_proxies,
                verify=effective_verify,
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
            if config.getInstance().debug():
                print(f"[-]Connect: {url} retry {i + 1}/{retry}")
            errors = str(e)
    if config.getInstance().debug():
        if "getaddrinfo failed" in errors:
            print("[-]Connect Failed! Please Check your proxy config")
            print("[-]" + errors)
        else:
            print("[-]" + errors)
            print("[-]Connect Failed! Please check your Proxy or Network!")
    raise Exception("Connect Failed")


def post(
    url: str,
    data: Optional[dict] = None,
    files: Any = None,
    cookies: Optional[dict] = None,
    ua: Optional[str] = None,
    return_type: Optional[str] = None,
    encoding: Optional[str] = None,
    retry: Optional[int] = None,
    timeout: Optional[int] = None,
    proxies: Optional[dict] = None,
    verify: Optional[bool] = None,
) -> Union[requests.Response, bytes, str]:
    config_proxy = config.getInstance().proxy()
    errors = ""
    headers = {"User-Agent": ua or G_USER_AGENT}
    retry = config_proxy.retry if retry is None else retry
    timeout = config_proxy.timeout if timeout is None else timeout

    for i in range(retry):
        try:
            effective_proxies = proxies
            effective_verify = verify
            if effective_proxies is None and config_proxy.enable:
                effective_proxies = config_proxy.proxies()
                if effective_verify is None:
                    disable_insecure_request_warning()
                    effective_verify = False
            result = requests.post(
                str(url),
                data=data,
                files=files,
                headers=headers,
                timeout=timeout,
                proxies=effective_proxies,
                verify=effective_verify,
                cookies=cookies,
            )
            if return_type == "object":
                return result
            elif return_type == "content":
                return result.content
            elif return_type == "text":
                result.encoding = encoding or result.apparent_encoding
                return result.text
            else:
                return result
        except Exception as e:
            if config.getInstance().debug():
                print(f"[-]Connect: {url} retry {i + 1}/{retry}")
            errors = str(e)
    if config.getInstance().debug():
        if "getaddrinfo failed" in errors:
            print("[-]Connect Failed! Please Check your proxy config")
            print("[-]" + errors)
        else:
            print("[-]" + errors)
            print("[-]Connect Failed! Please check your Proxy or Network!")
    raise Exception("Connect Failed")


def get_html(
    url: str,
    cookies: Optional[dict] = None,
    ua: Optional[str] = None,
    return_type: Optional[str] = None,
    encoding: Optional[str] = None,
    json_headers: Optional[dict] = None,
) -> Union[requests.Response, bytes, str]:
    """
    网页请求核心函数

    :param url: 请求链接
    :param cookies: 请求cookies
    :param ua: 用户代理
    :param return_type: 返回类型 'object' | 'content' | None
    :param encoding: 编码格式
    :param json_headers: json头部信息
    :return: 响应对象 | 二进制内容 | 文本内容
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
                disable_insecure_request_warning()
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


def post_html(
    url: str, query: dict, headers: Optional[dict] = None
) -> requests.Response:
    """
    POST 请求提交数据

    :param url: 请求的 URL
    :param query: 提交的数据字典
    :param headers: 请求头
    :return: Response 对象
    """
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


def request_session(
    cookies: Optional[dict] = None,
    ua: Optional[str] = None,
    retry: Optional[int] = None,
    timeout: Optional[int] = None,
    proxies: Optional[dict] = None,
    verify: Optional[bool] = None,
) -> requests.Session:
    config_proxy = config.getInstance().proxy()
    retry = config_proxy.retry if retry is None else retry
    timeout = config_proxy.timeout if timeout is None else timeout

    session = requests.Session()
    retries = Retry(
        total=retry,
        connect=retry,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    session.mount(
        "https://",
        TimeoutHTTPAdapter(max_retries=retries, timeout=timeout),
    )
    session.mount(
        "http://",
        TimeoutHTTPAdapter(max_retries=retries, timeout=timeout),
    )
    if isinstance(cookies, dict) and len(cookies):
        requests.utils.add_dict_to_cookiejar(session.cookies, cookies)

    effective_proxies = proxies
    effective_verify = verify
    if effective_proxies is None and config_proxy.enable:
        effective_proxies = config_proxy.proxies()
        if effective_verify is None:
            disable_insecure_request_warning()
            effective_verify = False
    if effective_verify is not None:
        session.verify = effective_verify
    if effective_proxies is not None:
        session.proxies = effective_proxies

    session.headers = {"User-Agent": ua or G_USER_AGENT}
    return session


def get_html_session(
    url: Optional[str] = None,
    cookies: Optional[dict] = None,
    ua: Optional[str] = None,
    return_type: Optional[str] = None,
    encoding: Optional[str] = None,
) -> Union[
    requests.Session,
    requests.Response,
    bytes,
    str,
    Tuple[requests.Response, requests.Session],
    None,
]:
    """
    使用 Session 发送 GET 请求

    :param url: 请求的 URL. 如果为空, 返回 Session 对象
    :param cookies: Cookies 字典
    :param ua: User-Agent
    :param return_type: 返回类型 'object' | 'content' | 'session' | None
    :param encoding: 指定编码
    :return: Session | Response | 二进制内容 | 文本内容 | (Response, Session) | None
    """
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
    url: str,
    form_select: Optional[str] = None,
    fields: Optional[dict] = None,
    cookies: Optional[dict] = None,
    ua: Optional[str] = None,
    return_type: Optional[str] = None,
    encoding: Optional[str] = None,
    retry: Optional[int] = None,
    timeout: Optional[int] = None,
    proxies: Optional[dict] = None,
    verify: Optional[bool] = None,
) -> Union[
    requests.Response,
    bytes,
    str,
    Tuple[requests.Response, mechanicalsoup.StatefulBrowser],
    None,
]:
    """
    提交表单

    :param url: URL
    :param form_select: 表单选择器
    :param fields: 表单字段
    :param cookies: Cookies
    :param ua: User-Agent
    :param return_type: 返回类型 'object' | 'content' | 'browser' | None
    :param encoding: 编码
    :return: Response | 二进制内容 | 文本内容 | (Response, Browser) | None
    """
    config_proxy = config.getInstance().proxy()
    retry = config_proxy.retry if retry is None else retry
    timeout = config_proxy.timeout if timeout is None else timeout
    s = requests.Session()
    if isinstance(cookies, dict) and len(cookies):
        requests.utils.add_dict_to_cookiejar(s.cookies, cookies)
    retries = Retry(
        total=retry,
        connect=retry,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    s.mount(
        "https://",
        TimeoutHTTPAdapter(max_retries=retries, timeout=timeout),
    )
    s.mount(
        "http://", TimeoutHTTPAdapter(max_retries=retries, timeout=timeout)
    )
    if verify is not None:
        s.verify = verify
    elif config_proxy.enable:
        s.verify = config.getInstance().cacert_file()

    if proxies is not None:
        s.proxies = proxies
    elif config_proxy.enable:
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
    url: Optional[str] = None,
    cookies: Optional[dict] = None,
    ua: Optional[str] = None,
    return_type: Optional[str] = None,
    encoding: Optional[str] = None,
    retry: Optional[int] = None,
    timeout: Optional[int] = None,
    proxies: Optional[dict] = None,
    verify: Optional[bool] = None,
) -> Union[
    requests.Session,
    requests.Response,
    bytes,
    str,
    Tuple[requests.Response, requests.Session],
    None,
]:
    """
    使用 CloudScraper 发送请求

    :param url: URL
    :param cookies: Cookies
    :param ua: User-Agent
    :param return_type: 返回类型 'object' | 'content' | 'scraper' | None
    :param encoding: 编码
    :return: Scraper Session | Response | 二进制内容 | 文本内容 | (Response, Session) | None
    """
    config_proxy = config.getInstance().proxy()
    retry = config_proxy.retry if retry is None else retry
    timeout = config_proxy.timeout if timeout is None else timeout
    session = create_scraper(
        browser={
            "custom": ua or G_USER_AGENT,
        }
    )
    if isinstance(cookies, dict) and len(cookies):
        requests.utils.add_dict_to_cookiejar(session.cookies, cookies)
    retries = Retry(
        total=retry,
        connect=retry,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    session.mount(
        "https://",
        TimeoutHTTPAdapter(max_retries=retries, timeout=timeout),
    )
    session.mount(
        "http://", TimeoutHTTPAdapter(max_retries=retries, timeout=timeout)
    )
    if verify is not None:
        session.verify = verify
    elif config_proxy.enable:
        session.verify = config.getInstance().cacert_file()

    if proxies is not None:
        session.proxies = proxies
    elif config_proxy.enable:
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
