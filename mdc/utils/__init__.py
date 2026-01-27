# HTTP functions
from mdc.utils.http.request import (
    G_USER_AGENT,
    TimeoutHTTPAdapter,
    get_html,
    post_html,
    get_html_session,
    get_html_by_browser,
    get_html_by_form,
    get_html_by_scraper,
)

# Cookie functions
from mdc.utils.cookie.cookie import load_cookies

# String functions
from mdc.utils.string.string import cn_space

# HTML functions
from mdc.utils.html.xpath import get_xpath_single

# File functions
from mdc.file.common_utils import file_not_exist_or_empty

# Re-export all functions to maintain backward compatibility
__all__ = [
    # HTTP functions
    "G_USER_AGENT",
    "TimeoutHTTPAdapter",
    "get_html",
    "post_html",
    "get_html_session",
    "get_html_by_browser",
    "get_html_by_form",
    "get_html_by_scraper",
    # Cookie functions
    "load_cookies",
    # String functions
    "cn_space",
    # HTML functions
    "get_xpath_single",
    # File functions
    "file_not_exist_or_empty",
]
