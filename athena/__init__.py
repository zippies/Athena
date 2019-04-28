# -*- encoding: utf-8 -*-
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from lib.logger import get_logger
from jenkins import Jenkins

app = Flask(__name__)
db = SQLAlchemy()
config = Config()
log = get_logger("athena", "INFO", config.log_file)
js = Jenkins(config.jenkins_url, username=config.jenkins_user, password=config.jenkins_passwd)


def create_app():
    app.config.from_object(config)
    db.init_app(app)
    from athena.controllers import url as BluePrint
    app.register_blueprint(BluePrint)

    return(app)