# -*- encoding:utf-8 -*-


class ServiceResponse(object):

    code = 0
    data = None
    errorMsg = None

    @staticmethod
    def error(errorMsg, code=1, data=None):
        return {
            "code": code,
            "data": data,
            "errorMsg": errorMsg
        }

    @staticmethod
    def success(data=None):
        return {
            "code": ServiceResponse.code,
            "data": data,
            "errorMsg": ServiceResponse.errorMsg
        }


class CommonLib(object):

    @staticmethod
    def pprint(*args, **kwargs):
        for k in args:
            print k + "\n"

        for k, v in kwargs.items():
            print "%s: %s" % (k, v)
