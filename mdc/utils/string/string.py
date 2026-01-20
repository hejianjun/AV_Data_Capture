# build-in lib
from unicodedata import category


# print format空格填充对齐内容包含中文时的空格计算
def cn_space(v: str, n: int) -> int:
    return n - [category(c) for c in v].count("Lo")