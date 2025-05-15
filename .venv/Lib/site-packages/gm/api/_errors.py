import json
import sys

from gm.csdk.c_sdk import gmi_get_ext_errormsg, gmi_strerror


class GmError(Exception):
    """掘金SDK自定义错误"""

    def __init__(self, status, message, function):
        # type: (int, str, str) -> None
        self.status = status
        self.message = message
        self.function = function

    def __str__(self):
        return json.dumps(dict(
            status=self.status,
            message=self.message,
            function=self.function,
        ), ensure_ascii=False)


def check_gm_status(status):
    if status != 0:
        message = gmi_strerror(status).decode("utf8")
        ext_message = gmi_get_ext_errormsg().decode("utf8")
        if ext_message:
            message += "; " + ext_message
        function = sys._getframe().f_back.f_code.co_name
        raise GmError(status, message, function)

def send_custom_error(message):
    function = sys._getframe().f_back.f_code.co_name
    raise GmError(-1, message, function)