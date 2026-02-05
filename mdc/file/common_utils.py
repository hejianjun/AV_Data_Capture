import os
from pathlib import Path


def file_not_exist_or_empty(filepath):
    if not os.path.exists(filepath):
        return True
    if os.path.isfile(filepath):
        return os.path.getsize(filepath) == 0
    return False


def windows_long_path(path: Path) -> Path:
    if os.name != "nt":
        return path
    try:
        p = str(path)
        if p.startswith("\\\\?\\"):
            return path
        lp = "\\\\?\\" + p
        return Path(lp) if Path(lp).exists() else path
    except Exception:
        return path
