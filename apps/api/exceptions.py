from rest_framework.exceptions import APIException
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR


class ServerError(APIException):
    status_code = HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = ("Something with the server went wrong."
                      " Please try again later.")
    default_code = "server_error"
