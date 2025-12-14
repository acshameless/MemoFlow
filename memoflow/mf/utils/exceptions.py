"""Exception classes for MemoFlow"""


class MemoFlowError(Exception):
    """基础异常类"""
    pass


class HashCollisionError(MemoFlowError):
    """哈希冲突异常"""
    def __init__(self, message: str, matches: list = None):
        super().__init__(message)
        self.matches = matches or []


class InvalidPathError(MemoFlowError):
    """无效路径异常"""
    pass


class FileNotFoundError(MemoFlowError):
    """文件未找到异常（避免与内置异常冲突）"""
    pass


class SchemaValidationError(MemoFlowError):
    """Schema 验证异常"""
    pass


class GitOperationError(MemoFlowError):
    """Git 操作异常"""
    pass
