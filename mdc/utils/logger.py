import logging

def get_logger():
    return logging.getLogger("MDC")

def _join(args, sep=" "):
    return sep.join(map(str, args))

def info(*args, sep=" "):
    get_logger().log(logging.INFO, "[*] " + _join(args, sep))

def success(*args, sep=" "):
    get_logger().log(logging.INFO, "[+] " + _join(args, sep))

def warn(*args, sep=" "):
    get_logger().log(logging.WARNING, "[!] " + _join(args, sep))

def error(*args, sep=" "):
    get_logger().log(logging.ERROR, "[-] " + _join(args, sep))

def debug(*args, sep=" "):
    get_logger().log(logging.DEBUG, "[D] " + _join(args, sep))
