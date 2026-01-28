import os


def file_not_exist_or_empty(filepath):
    if not os.path.exists(filepath):
        return True
    if os.path.isfile(filepath):
        return os.path.getsize(filepath) == 0
    return False
