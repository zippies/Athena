# -*- encoding:utf-8 -*-
from flask import request, jsonify
from athena.controllers import url
from athena.models import db, PushHistory
from athena.services import projectService
from athena import log
from config import Config
import json
import requests


@url.route("/springboot/analyze/submodule", methods=["POST"])
def analyze_module():
    info = {"modules": ""}
    project_id, project_name, branch, build_id = projectService.parse_build_info(request)
    ph = PushHistory.query.filter_by(project_id=project_id, branch=branch, build_id=build_id).first()
    commit_ids = [commit.get("id") for commit in json.loads(ph.full_message).get("commits", [])]
    edits = list()
    for commit_id in commit_ids:
        r = requests.get(Config.gitlab_url + "/api/v3/projects/" + project_id + "/repository/commits/" + commit_id + "/diff?private_token=Sqz4Lm-8nmy95f4tvCLE")
        edits.extend([path.get("new_path").split("/")[0] for path in r.json() if "/" in path.get("new_path")])

    file = request.files["file"]
    pomlist = [f.strip() for f in file.stream.readlines() if f.count("/") == 1]
    submodules = [p.split("/")[0] for p in pomlist]
    edit_submodules = ",".join([module for module in set(edits) if module in submodules])
    log.info(
        "[analyze submodule]project_id:%s project_name:%s branch:%s build_id:%s submodules:%s edit_submodules:%s" % (
        project_id, project_name, branch, build_id, submodules, edit_submodules)
    )
    ph.sub_modules = edit_submodules
    db.session.add(ph)
    db.session.commit()
    db.session.close()
    info["modules"] = edit_submodules

    return jsonify(info)
