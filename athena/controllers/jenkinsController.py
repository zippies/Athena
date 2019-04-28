# -*- encoding:utf-8 -*-
from flask import request, jsonify
from athena.models import PushHistory, db
from athena.services.jenkinsService import parse_build_info, start_build
from athena.services.commonService import ServiceResponse
from athena.controllers import url
from athena import config, log, js
import traceback
import requests


@url.route("/jenkins/build", methods=["POST"])
def build_jenkins_job():
    """
    触发构建jenkins的评分job
    :param project_id: 项目id
    :param project: 项目名
    :param branch: 分支
    :param commiter: 代码提交者
    :param gitlab_url: 项目的ssh-url
    :param sub_modules: 指定修改的子module列表，逗号分隔
    :param submit_id: 提测工具触发时携带的id
    :param namespace: 如果运行自动化需要部署到哪个k2的namespace
    :param receivers:
    :return:
    """
    project_id, project_name, branch, commiter, gitlab_url, sub_modules, submit_id, namespace, receivers = parse_build_info(request)
    log.info("收到构建请求: project_id:%s project_name:%s branch:%s commiter:%s gitlab_url:%s submit_id:%s namespace:%s receivers:%s" % (project_id, project_name, branch, commiter, gitlab_url, submit_id, namespace, receivers))
    try:
        build_id = start_build(project_id, project_name, branch, commiter, gitlab_url, sub_modules, submit_id, namespace, receivers, 0)
        if submit_id:
            ph = PushHistory(
                "submit_test",
                project_id,
                project_name,
                branch,
                gitlab_url,
                sub_modules,
                commiter,
                "{}",
                build_id,
                receivers,
                0
            )
            db.session.add(ph)
            db.session.commit()
            db.session.close()
        return jsonify(ServiceResponse.success({"build_id": build_id, "project_name": project_name, "branch": branch}))
    except Exception as e:
        return jsonify(ServiceResponse.error(traceback.format_exc()))


@url.route("/jenkins/<job_name>/<int:build_id>")
def get_job_info(job_name, build_id):
    """
    获取某个job下某个build_id的构建状态
    :param job_name:
    :param build_id:
    :return:
    """
    try:
        info = js.get_build_info(job_name, build_id)

        return jsonify(ServiceResponse.success({
            "duration": info.get("duration"),
            "result": info.get("result"),
            "url": info.get("url")
        }))
    except Exception as e:
        return jsonify(ServiceResponse.error(traceback.format_exc()))


@url.route("/jenkins/job/status", methods=["GET", "POST"])
def query_job_status():
    status = {"ut": {"status": -1, "coverage": 0.0}, "cs": {"status": -1}, "it": {"status": -1}, "summary": {"finished": False, "reason": None} }
    try:
        if request.method == "GET":
            project_name = request.args.get("project_name")
            build_id = request.args.get("build_id")
            branch = request.args.get("branch")
        else:
            project_name = request.json.get("project_name")
            build_id = request.json.get("build_id")
            branch = request.json.get("branch")
            for ec in config.unexpected_branch_chars:
                branch = branch.replace(ec, "_")

        if not project_name or not build_id or not branch:
            return jsonify(ServiceResponse.error("缺少参数{project_name}/{branch}/{build_id}"))
        job_name = "%s__%s" % (project_name, branch.replace("/", "_"))
        detail_url = "{jenkins_url}/job/{job_name}".format(
            job_name=job_name, jenkins_url=config.jenkins_url
        )
        json_api_end = "/api/json?pretty=true"
        json_data = requests.get(detail_url + "/{build_id}/".format(build_id=build_id) + json_api_end).json()
        acs = json_data.get("actions")
        status["summary"]["finished"] = not json_data.get("building", False)
        for ac in acs:
            if ac.get("installationName", "") == "sonar" and not ac.get("skipped"):
                status["cs"]["status"] = 0

            if ac.get("_class") == "hudson.tasks.junit.TestResultAction" and ac.get("totalCount"):
                if ac.get("failCount") == 0:
                    status["ut"]["status"] = 0
                    try:
                        coverage = round(requests.get(detail_url + "/{build_id}/jacoco/".format(build_id=build_id) + json_api_end).json().get("lineCoverage", {}).get("percentageFloat", 0.0), 2)
                    except Exception as e:
                        coverage = 0.0
                    status["ut"]["coverage"] = coverage
                else:
                    status["ut"]["status"] = 1

        ph = PushHistory.query.filter_by(project_name=project_name, branch=branch, build_id=build_id).first()
        if ph:
            status["summary"]["reason"] = ph.error_msg
    except Exception as e:
        print traceback.format_exc()
        return jsonify(ServiceResponse.error(traceback.format_exc(), data=status))
    return jsonify(ServiceResponse.success(data=status))
