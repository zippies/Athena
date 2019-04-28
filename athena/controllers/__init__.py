# -*- coding: utf-8 -*-
from flask import Blueprint

url = Blueprint('controller', __name__)

from . import jenkinsController, hookController, reportController, automationController, projectController, checkBackendController