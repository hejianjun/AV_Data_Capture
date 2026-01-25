def disable_insecure_request_warning() -> None:
    try:
        import urllib3
        from urllib3.exceptions import InsecureRequestWarning

        urllib3.disable_warnings(InsecureRequestWarning)
    except Exception:
        return
