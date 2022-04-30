class Result:
    code = "200"
    msg = "success"
    data = {}

    def __int__(self, code, msg, data):
        self.code = code
        self.msg = msg
        self.data = data

    def __str__(self):
        return {
            "code": self.code,
            "msg": self.msg,
            "data": self.data
        }
