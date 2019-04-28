# -*- encoding:utf-8 -*-
import logging

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

def get_logger(name, level, logpath):
    """
    返回logger对象，与logging使用方法一致

    :param name: 为当前logger命名
    :param level: 日志等级 NOTSET、DEBUG、INFO、WARN、ERROR、FATAL
    :param logpath: 存放日志文件目录
    :return: logging对象
    """
    fh = logging.FileHandler(logpath)
    fh.setLevel(level)
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
