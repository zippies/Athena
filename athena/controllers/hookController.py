# -*- encoding:utf-8 -*-
from flask import request, jsonify
from athena.controllers import url
from athena.services.jenkinsService import start_build
from athena.services.hookService import parse_push_info, is_supported_project
from athena.models import PushHistory, db
from athena import log
import traceback


@url.route("/athena/hook", methods=["POST"])
def push_event_hook():
    """
    该接口是配置在gitlab工程内的hook接口，用于获取提交代码的信息，触发ci构建
    """
    object_kind, project_id, project_name, branch, gitlab_url, sub_modules, ignore, commiter, full_message, receivers, namespace, magazine_id = parse_push_info(request)
    build_id = 0
    if not ignore and is_supported_project(project_id):
        try:
            build_id = start_build(project_id, project_name, branch, commiter, gitlab_url, sub_modules, 0, namespace, receivers, magazine_id)
            log.info("create job successfully: %s build_id: %s" % ("__".join([project_name, branch]), build_id))
        except Exception as e:
            log.error(traceback.format_exc())
    try:
        ph = PushHistory(object_kind, project_id, project_name, branch, gitlab_url, sub_modules, commiter, full_message, build_id, receivers, magazine_id)
        db.session.add(ph)
        db.session.commit()
        db.session.close()
    except Exception as e:
        log.error(traceback.format_exc())
    return "ok"


@url.route("/athena/history")
def push_event_history():
    phs = [ph.to_json() for ph in PushHistory.query.all()]
    return jsonify(phs)
