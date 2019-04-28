# -*- encoding:utf-8 -*-
from athena.services.commonService import ServiceResponse
from athena.models import db, ProjectAutomationStatus
from athena.controllers import url
from athena import log
from flask import request, jsonify
from datetime import datetime
from config import Config
import traceback
import requests


@url.route("/automation/<group>/<project>/update")
def project_branch_covered_update(group, project):
    try:
        pas = ProjectAutomationStatus.query.filter_by(group=group, project=project).first()
        covered_api_count = int(request.args.get("covered_count", 0))
        swagger_url = request.args.get("swagger_url", "")
        api_count = int(request.args.get("api_count", 0))
        log.info("[update project api info]api_count:%s covered_count:%s swagger:%s" % (api_count, covered_api_count, swagger_url))
        if pas:
            pas.covered_api = covered_api_count or pas.covered_api
            pas.swagger_url = swagger_url or pas.swagger_url
            pas.api_count = api_count or pas.api_count
            pas.updatedtime = datetime.now()
        else:
            pas = ProjectAutomationStatus(group, project, swagger_url, api_count, covered_api_count)
        db.session.add(pas)
        db.session.commit()
        db.session.close()
        return jsonify(ServiceResponse.success())
    except Exception as e:
        log.error("update project api info failed:" + traceback.format_exc())
        return jsonify(ServiceResponse.error(traceback.format_exc()))


@url.route("/automation/existscript")
def exist_script():
    gitlab_url = request.args.get("gitlab_url")
    group_name = gitlab_url.split(":")[1].split("/")[0]
    project_name = gitlab_url.split("/")[1].split(".git")[0].strip()
    r1 = requests.get(Config.gitlab_url + "/api/v3/projects/3564/repository/files?ref=master&file_path=case%2Fit%2F{ext_msg}%2F__init__%2Epy&private_token=Sqz4Lm-8nmy95f4tvCLE".format(
        ext_msg=project_name
    )).status_code
    r2 = requests.get(Config.gitlab_url + "/api/v3/projects/3564/repository/files?ref=master&file_path=case%2Fit%2F{ext_msg}%2F__init__%2Epy&private_token=Sqz4Lm-8nmy95f4tvCLE".format(
        ext_msg=project_name.replace("-", "_")
    )).status_code
    r3 = requests.get(Config.gitlab_url + "/api/v3/projects/3564/repository/files?ref=master&file_path=case%2Fit%2F{ext_msg}%2F__init__%2Epy&private_token=Sqz4Lm-8nmy95f4tvCLE".format(
        ext_msg="{group_name}%2F{project_name}".format(group_name=group_name.replace(".", "_"), project_name=project_name.replace("-", "_"))
    )).status_code
    r4 = requests.get(Config.gitlab_url + "/api/v3/projects/3564/repository/files?ref=master&file_path=case%2Fit%2F{ext_msg}%2F__init__%2Epy&private_token=Sqz4Lm-8nmy95f4tvCLE".format(
        ext_msg="{group_name}%2F{project_name}".format(group_name=group_name.replace(".", "_"), project_name=project_name)
    )).status_code
    if r1 == 200 or r2 == 200 or r3 == 200 or r4 == 200:
        return jsonify(ServiceResponse.success())
    else:
        return jsonify(ServiceResponse.error("no scripts found"))
