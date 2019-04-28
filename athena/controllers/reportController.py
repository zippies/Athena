# -*- encoding:utf-8 -*-
from flask import request, jsonify, redirect, url_for
from athena import js
from athena.controllers import url
from athena.models import PushHistory, CodeScore
from athena.services.commonService import ServiceResponse
from athena.services.reportService import parse_build_info, send_report, send_kafka
import traceback
import json


@url.route("/notify/report")
def notify_report():
    print request.args
    project_id, project_name, branch, commiter, build_id, submit_id, receivers, sub_modules, error_msg, error_type = parse_build_info(request)
    job_name = project_name + "__" + branch.replace("/", "_").replace("#", "_")
    try:
        print "job_name", job_name, build_id
        info = js.get_build_info(job_name, int(build_id))
        if info.get("result") not in ["ABORTED"]:
            send_report(project_id, project_name, branch, commiter, build_id, submit_id, receivers, sub_modules, error_type, error_msg)
            return jsonify(ServiceResponse.success())
        else:
            return jsonify(ServiceResponse.error("job interrupted"))
    except Exception as e:
        return jsonify(ServiceResponse.error(traceback.format_exc()))


@url.route("/judgement/<judgement>")
def get_jedgement_img(judgement):
    return redirect(url_for("static", filename="images/%s.png" % judgement))


@url.route("/images/link")
def get_link_img():
    return redirect(url_for("static", filename="images/link.png"))


@url.route("/images/reports")
def get_report_img():
    return redirect(url_for("static", filename="images/reports.png"))


@url.route("/grafana/sync")
def sync_grafana():
    pss = PushHistory.query.all()
    for ps in pss:
        scs = CodeScore.query.filter_by(history_id=ps.id).all()
        for sc in scs:
            params = {
                "topic": "red.alert",
                "message": json.dumps({
                    "database": "athena",
                    "measurement": "push-history-score",
                    "tags": {
                        "project_name": ps.project_name,
                        "branch": ps.branch,
                        "commiter": ps.commiter
                    },
                    "fields": {
                        "_project_name": ps.project_name,
                        "_branch": ps.branch,
                        "score": sc.score,
                        "_commiter": ps.commiter,
                        "code_lines": sc.code_lines,
                        "new_lines": sc.new_lines,
                        "bugs": sc.bugs,
                        "new_bugs": sc.new_bugs,
                        "vulnerabilities": sc.vulnerabilities,
                        "new_vulnerabilities": sc.new_vulnerabilities,
                        "code_smells": sc.code_smells,
                        "new_code_smells": sc.new_code_smells,
                        "violations": sc.violations,
                        "new_violations": sc.new_violations,
                        "rank_list": sc.rank_list,
                        "ut_report_url": sc.ut_report_url,
                        "ut_cover_report_url": sc.ut_cover_report_url,
                        "ut_failcount": sc.ut_failcount,
                        "ut_passcount": sc.ut_passcount,
                        "ut_skipcount": sc.ut_skipcount,
                        "ut_totalcount": sc.ut_totalcount,
                        "ut_judgement": sc.ut_judgement,
                        "ut_line_cover": sc.ut_line_cover,
                        "ut_class_cover": sc.ut_class_cover,
                        "ut_branch_cover": sc.ut_branch_cover,
                        "ctime": sc.createdtime.strftime("%Y-%m-%d %H:%M:%S")
                    }
                })
            }
            send_kafka(params)

    return "ok"