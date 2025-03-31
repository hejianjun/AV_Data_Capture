#首先定义业务专用异常（在类外部或模块级别定义）
class QueryError(Exception):
    """JavDB查询异常基类"""
    def __init__(self, number, message):
        self.number = number
        super().__init__(f"[{number}] {message}")
