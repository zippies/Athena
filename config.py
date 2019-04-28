# -*- encoding:utf-8 -*-
import multiprocessing
import os

env = os.getenv("ENV")
print "current env:", env

bind = "0.0.0.0:8080"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
backlog = 2048
reload = True
debug = True


class Config(object):
    SECRET_KEY = "it's when i'm weak that i am strong"
    WTF_CSRF_SECRET_KEY = "i believe i can fly"
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_POOL_RECYCLE = 5
    ADMIN_LIST = [""]
    gitlab_url = "http://host:port"
    sonar_url = "http://host:port"
    staff_url = ""
    jenkins_user = "dataci"
    jenkins_passwd = "data2018"
    unexpected_branch_chars = ["/", "#"]

    def __init__(self):
        self.template_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "templates")
        self.report_template = self.__get_report_template()
        self.log_file = os.path.join(os.path.abspath(os.path.dirname(__file__)), "logs", "app.log")
        if "online" in env:
            self.__init_online_config()
        else:
            self.__init_offline_config()

    def __init_online_config(self):
        self.DEBUG = False
        self.SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'db', 'data.sqlite')
        self.CELERY_BROKER_URL = "redis://10.1.128.41:6379/11"
        self.CELERY_RESULT_BACKEND = "redis://10.1.128.41:6379/12"
        self.jenkins_url = "http://job_collection_url"
        self.runtime_host = "http://host"  # 用户报告内图片资源获取
        self.kafka_url = ""
        self.notify_url = ""
        self.notice_url = ""
        self.magazine_host = ""
        self.athena_host = ""

    def __init_offline_config(self):
        self.DEBUG = True
        self.SQLALCHEMY_DATABASE_URI = "mysql+pymysql://user:passwd@host:3306/athena?charset=utf8"
        self.CELERY_BROKER_URL = "redis://:6379/11"
        self.CELERY_RESULT_BACKEND = "redis://:6379/12"
        self.jenkins_url = "http://job_collection_url"
        self.runtime_host = ""  # 用户报告内图片资源获取
        self.kafka_url = ""
        self.notify_url = ""
        self.notice_url = ""
        self.magazine_host = ""
        self.athena_host = ""

    def __get_report_template(self):
        with open(os.path.join(self.template_path, "report_template.html"), "r") as f:
            return f.read()

    @staticmethod
    def init_app(app):
        pass