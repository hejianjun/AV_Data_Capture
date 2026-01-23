import logging

def get_logger():
    return logging.getLogger("MDC")

def _join(args, sep=" "):
    return sep.join(map(str, args))

def _is_prefixed_message(message: str) -> bool:
    if not isinstance(message, str):
        return False
    s = message.lstrip()
    if len(s) < 3:
        return False
    if s[0] != "[" or s[2] != "]":
        return False
    return s[1] in "*+!-D"

def _with_prefix(prefix: str, message: str) -> str:
    return message if _is_prefixed_message(message) else prefix + message

def info(*args, sep=" "):
    msg = _join(args, sep)
    get_logger().log(logging.INFO, _with_prefix("[*] ", msg))

def success(*args, sep=" "):
    msg = _join(args, sep)
    get_logger().log(logging.INFO, _with_prefix("[+] ", msg))

def warn(*args, sep=" "):
    msg = _join(args, sep)
    get_logger().log(logging.WARNING, _with_prefix("[!] ", msg))

def error(*args, sep=" "):
    msg = _join(args, sep)
    get_logger().log(logging.ERROR, _with_prefix("[-] ", msg))

def debug(*args, sep=" "):
    msg = _join(args, sep)
    get_logger().log(logging.DEBUG, _with_prefix("[D] ", msg))
