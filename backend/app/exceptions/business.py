class BusinessError(Exception):
    def __init__(self, code: int, message: str, detail: str = None):
        self.code = code
        self.message = message
        self.detail = detail
        super().__init__(message)
