# -*- encoding:utf-8 -*-
from athena.services.commonService import CommonLib
from athena.models import CodeScore, db, ProjectAutomationStatus, PushHistory
from pprint import pprint
from athena import config, app, log
import requests, json, traceback
from collections import Counter
from jinja2 import Template
import time
import sys
import os

reload(sys)
sys.setdefaultencoding("utf-8")


def parse_build_info(request):
    project_id = request.args.get("project_id")
    project_name = request.args.get("project_name")
    branch = request.args.get("branch")
    commiter = request.args.get("commiter")
    build_id = request.args.get("build_id")
    submit_id = request.args.get("submit_id", 0)
    receivers = request.args.get("receivers", "").split(",")
    sub_modules = request.args.get("sub_modules", "")
    error_msg = request.args.get("error_msg", "").strip("None").strip("null")
    error_type = request.args.get("error_type", "").strip("None").strip("null")
    CommonLib.pprint(
        project_id=project_id,
        project_name=project_name,
        branch=branch,
        commiter=commiter,
        build_id=build_id,
        submit_id=int(submit_id),
        receivers=receivers
    )
    return project_id, project_name, branch, commiter, build_id, int(submit_id), receivers, sub_modules, error_msg, error_type


def get_score(bugs, vulnerabilities, code_smells, ut_skipcount, ut_failcount, ut_line_cover, ut_class_cover,
              ut_branch_cover):
    """
    获取项目代码评分
    :param bugs: bug级别缺陷数
    :param vulnerabilities: 漏洞级别缺陷数
    :param code_smells: 坏味道级别缺陷数
    :param ut_skipcount: 单元测试跳过的case数
    :param ut_failcount: 单元测试失败的case数
    :param ut_line_cover: 单元测试行覆盖率
    :param ut_class_cover: 单元测试类覆盖率
    :param ut_branch_cover: 单元测试分支覆盖率
    :return:
    """
    score = 100
    static_minus = (bugs * 2 + vulnerabilities + code_smells * 0.5) * 0.1
    ut_minus = (ut_skipcount * 1 + ut_failcount * 5) * 0.45
    ut_cover_minus = ((10 - ut_line_cover / 10) + (10 - ut_class_cover / 10) + (10 - ut_branch_cover / 10)) * 0.45
    if sum([static_minus, ut_minus, ut_cover_minus]) > 100:
        score = 1
    else:
        score -= sum([static_minus, ut_minus, ut_cover_minus])

    log.info("静态代码扣分: %s\n单元测试扣分: %s\n单元测试覆盖率扣分: %s" % (static_minus, ut_minus, ut_cover_minus))
    return score


def get_group_email_list(project_id):
    user_list = list()
    page = 1
    while True:
        url_project = config.gitlab_url + "/api/v3/projects/{project_id}/members?private_token=Sqz4Lm-8nmy95f4tvCLE&page={page}".format(
            project_id=project_id, page=page)

        r_project = requests.get(url_project, timeout=(3, 10))
        if len(r_project.json()) == 0:
            break

        user_list.extend(r_project.json())
        page += 1
    # project_url = config.gitlab_url + "/api/v3/projects/{project_id}?private_token=Sqz4Lm-8nmy95f4tvCLE".format(
    #     project_id=project_id)
    # r = requests.get(project_url, timeout=(3, 10))
    # group_id = r.json().get("namespace").get("id")

    # url_group = config.gitlab_url + "/api/v3/groups/{group_id}/members?private_token=Sqz4Lm-8nmy95f4tvCLE".format(
    #     group_id=group_id
    # )
    # r_group = requests.get(url_group, timeout=(3, 10))
    # user_list.extend(r_group.json())

    return list(set([user.get("username") for user in user_list if user.get("access_level") >= 40]))


def get_judgement(branch_coverage, class_coverage, line_coverage):
    if branch_coverage >= 70 and class_coverage >= 85 and line_coverage >= 85:
        return "最强王者", "king"
    elif branch_coverage >= 50 and class_coverage >= 75 and line_coverage >= 75:
        return "超凡大师", "master"
    elif branch_coverage >= 40 and class_coverage >= 60 and line_coverage >= 60:
        return "璀璨钻石", "diamond"
    elif branch_coverage >= 30 and class_coverage >= 50 and line_coverage >= 50:
        return "华贵铂金", "platinum"
    elif branch_coverage >= 20 and class_coverage >= 40 and line_coverage >= 40:
        return "荣耀黄金", "gold"
    elif branch_coverage >= 10 and class_coverage >= 30 and line_coverage >= 30:
        return "不屈白银", "silver"
    return "英勇黄铜", "copper"


def get_chinese_flower_name(eng_flower_name):
    try:
        chinese_name = requests.get(config.staff_url + eng_flower_name).json().get("data").get("nicknameCN")
        return chinese_name
    except:
        return eng_flower_name


def get_sonar_data(project_name, branch):
    log.info("[get sonar_data] project_name:%s branch:%s" % (project_name, branch))
    code_lines = 0
    new_lines = 0
    bugs = 0
    new_bugs = 0
    vulnerabilities = 0
    new_vulnerabilities = 0
    code_smells = 0
    new_code_smells = 0
    violations = 0
    new_violations = 0
    rank_list = []

    try:
        params = {
            "additionalFields": "metrics,periods",
            "componentKey": "%s:%s" % (project_name, branch),
            "metricKeys": "lines,alert_status,violations,new_violations,quality_gate_details,bugs,new_bugs,reliability_rating,vulnerabilities,new_vulnerabilities,security_rating,code_smells,new_code_smells,sqale_rating,sqale_index,new_technical_debt,coverage,new_coverage,new_lines_to_cover,tests,duplicated_lines_density,new_duplicated_lines_density,duplicated_blocks,ncloc,ncloc_language_distribution,new_lines"
        }
        r = requests.get(config.sonar_url + "/api/measures/component", params=params)
        uuid = r.json().get("component").get("id")
        metrics = {}
        for metric in r.json().get("component").get("measures"):
            metrics[metric.get("metric")] = {
                "value": metric.get("value") or metric.get("periods")[0].get("value"),
                "periods": metric.get("periods")
            }
        pprint(metrics)
        code_lines = int(metrics.get("lines").get("value")) if metrics.get("lines", {}).get("value", 0) else 0
        new_lines = int(metrics.get("new_lines").get("value")) if metrics.has_key("new_lines") and metrics.get(
            "new_lines").get("value") else 0
        bugs = int(metrics.get("bugs").get("value")) if metrics.get("bugs").get("value") else 0
        new_bugs = int(metrics.get("new_bugs").get("value")) if metrics.has_key("new_bugs") and metrics.get(
            "new_bugs").get("value") else 0
        code_smells = int(metrics.get("code_smells").get("value")) if metrics.get("code_smells").get("value") else 0
        new_code_smells = int(metrics.get("new_code_smells").get("value")) if metrics.has_key(
            "new_code_smells") and metrics.get("new_code_smells").get("value") else 0
        vulnerabilities = int(metrics.get("vulnerabilities").get("value")) if metrics.get("vulnerabilities").get(
            "value") else 0
        new_vulnerabilities = int(metrics.get("new_vulnerabilities").get("value")) if metrics.has_key(
            "new_vulnerabilities") and metrics.get("new_vulnerabilities").get("value") else 0
        violations = int(metrics.get("violations").get("value")) if metrics.get("violations").get("value") else 0
        new_violations = int(metrics.get("new_violations").get("value")) if metrics.has_key(
            "new_violations") and metrics.get("new_violations").get("value") else 0

        issues_count = vulnerabilities + bugs + code_smells
        loop_count = issues_count / 100 if issues_count % 100 == 0 else issues_count / 100 + 1
        counter_author = []
        block_list = []
        critical_list = []
        minor_list = []
        major_list = []

        for loop in range(loop_count):
            params = {
                "p": loop + 1,
                "ps": 100,
                "componentUuids": uuid
            }
            r = requests.get(config.sonar_url + "/api/issues/search", params=params)
            if r.status_code == 200:
                issues = r.json().get("issues")
                for iss in issues:
                    author = iss.get("author").split("@")[0]
                    if iss.get("severity") == "BLOCKER":
                        block_list.append(author)
                    elif iss.get("severity") == "CRITICAL":
                        critical_list.append(author)
                    elif iss.get("severity") == "MAJOR":
                        major_list.append(author)
                    elif iss.get("severity") == "MINOR":
                        minor_list.append(author)
                    else:
                        pass
                    counter_author.append(iss.get("author").split("@")[0])

        author = Counter(counter_author)

        log.info("BLOCKER:%s" % len(block_list) + "CRITICAL:%s" % len(critical_list) + "MAJOR:%s" % len(major_list) + "MINOR:%s" % len(minor_list) + "负债数统计:%s" % json.dumps(dict(author)))

        for i, rank in enumerate(author.most_common()):
            rank_list.append({
                "rank": i + 1,
                "name": rank[0],
                "chinese_name": get_chinese_flower_name(rank[0]),
                "blocks": block_list.count(rank[0]),
                "criticals": critical_list.count(rank[0]),
                "majors": major_list.count(rank[0]),
                "minors": minor_list.count(rank[0]),
                "all": author.get(rank[0])
            })
    except Exception as e:
        log.error(traceback.format_exc())

    return code_lines, new_lines, bugs, new_bugs, vulnerabilities, new_vulnerabilities, code_smells, new_code_smells, violations, new_violations, rank_list


def get_ut_data(ut_report_url, ut_cover_report_url):
    log.info("[get_ut_data]ut_report_url:%s ut_cover_report_url:%s" % (ut_report_url + "/api/json?pretty=true", ut_cover_report_url + "/api/json?pretty=true"))
    ut_failcount = ut_passcount = ut_skipcount = ut_totalcount = ut_elapsed = 0
    r = requests.get(ut_report_url + "/api/json?pretty=true")

    if r.status_code == 200:
        ut_failcount = r.json().get("failCount")
        ut_passcount = r.json().get("passCount")
        ut_skipcount = r.json().get("skipCount")
        ut_totalcount = r.json().get("skipCount") + r.json().get("failCount") + r.json().get("passCount")
        ut_elapsed = r.json().get("duration")
        log.info("失败数：%s 通过数：%s 跳过数：%s 总数：%s 运行时长：%s" % (ut_failcount, ut_passcount, ut_skipcount, ut_totalcount, ut_elapsed))
    else:
        log.error("获取单测数据异常, httpcode:%s url:%s" % (r.status_code, r.request.url))

    ut = requests.get(ut_cover_report_url + "/api/json?pretty=true")

    line_coverage = class_coverage = branch_coverage = 0
    if ut.status_code == 200:
        branch_coverage = ut.json().get("branchCoverage").get("percentage")
        class_coverage = ut.json().get("classCoverage").get("percentage")
        line_coverage = ut.json().get("lineCoverage").get("percentage")

    log.info("分支覆盖度：%s 类覆盖度：%s 行覆盖度：%s" % (branch_coverage, class_coverage, line_coverage))

    return ut_failcount, ut_passcount, ut_skipcount, ut_totalcount, ut_elapsed, branch_coverage, class_coverage, line_coverage


def get_it_data(it_report_url):
    log.info("[get_it_data]it_report_url:%s" % it_report_url)
    it_totalcount, it_passcount, it_skipcount, it_failcount, it_errorcount, it_elapsed = 0, 0, 0, 0, 0, 0
    try:
        r = requests.get(it_report_url)
        if r.status_code == 200:
            left, right = r.text.split(" tests ran in")
            it_totalcount = left.split("<p>")[-1]
            it_elapsed, right = right.split(" seconds. </p>")
            it_passcount, right = right.split("<span class=\"passed\">")[1].split(" passed</span>")
            it_skipcount, right = right.split("<span class=\"skipped\">")[1].split(" skipped</span>")
            it_failcount, right = right.split("<span class=\"failed\">")[1].split(" failed</span>")
            it_errorcount, right = right.split("<span class=\"error\">")[1].split(" errors</span>")
    except Exception as e:
        log.error("[get_it_data]failed:" + traceback.format_exc())

    return int(it_totalcount), int(it_passcount), int(it_skipcount), int(it_failcount), int(it_errorcount), float(it_elapsed)


def get_report_detail_data(detail_url):
    result = ""
    duration = 0.0
    r = requests.get(detail_url + "/api/json?pretty=true")
    if r.status_code == 200:
        result = r.json().get("result")
        duration = round(r.json().get("duration", 0.0) / 1000, 2)

    return result, duration


def report_send(project_name, branch, notifiers, build_id, report_content):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "toList": ",".join(["%s@{company}.com" % user if "@" not in user else user for user in notifiers if user.strip()]),
        "title": "[信贷数据CI]%s质量报告" % project_name,
        "type": 9,
        "content": report_content
    }
    log.info("[notifiers]" + data.get("toList"))
    try:
        r = requests.post(config.notify_url + "/notify/email", data=data, headers=headers, timeout=(1, 5))
        assert r.status_code == 200, "邮件发送失败"
        assert r.json().get("code") == 0, r.json().get("message")
        log.info(json.dumps(r.json(), ensure_ascii=False))
    except Exception as e:
        log.error(e)
    finally:
        with open(os.path.join(app.static_folder, "reports", "%s__%s_%s.html" % (project_name, branch.replace("/", "_").replace("#", "_"), build_id)), "wb") as f:
            f.write(report_content)


def send_kafka(params):
    try:
        log.info("[send kafka]url:%s params:%s" % (config.kafka_url, params))
        r = requests.post(config.kafka_url, params=params, timeout=(4, 10))
        assert r.status_code == 200, r.reason
        assert r.content == "ok", r.content
    except Exception as e:
        log.error("[send kafka failed]" + str(e))


def send_report(project_id, project_name, branch, commiter, build_id, submit_id, receivers, sub_modules, error_type, error_msg):
    assert project_id is not None
    assert project_name is not None
    assert branch is not None
    assert commiter is not None
    assert build_id is not None

    code_lines, new_lines, bugs, new_bugs, vulnerabilities, new_vulnerabilities, code_smells, new_code_smells, violations, new_violations, rank_list = get_sonar_data(
        project_name, branch.replace("#", "_"))

    report_detail_url = "{jenkins_url}/job/{project_name}__{branch}".format(
        project_name=project_name, branch=branch.replace("/", "_").replace("#", "_"), jenkins_url=config.jenkins_url
    )

    console_url = report_detail_url + "/{build_id}/console".format(build_id=build_id)

    ut_report_url = "{report_detail_url}/{build_id}/testReport".format(
        report_detail_url=report_detail_url, build_id=build_id)

    ut_cover_report_url = "{report_detail_url}/{build_id}/jacoco".format(
        report_detail_url=report_detail_url, build_id=build_id)

    ut_failcount, ut_passcount, ut_skipcount, ut_totalcount, ut_elapsed, branch_coverage, class_coverage, line_coverage = get_ut_data(
        ut_report_url, ut_cover_report_url)

    score = get_score(bugs, vulnerabilities, code_smells, ut_skipcount, ut_failcount, line_coverage, class_coverage,
                      branch_coverage)

    it_report_url = "{report_detail_url}/{build_id}/HTML_Report/test_report.html".format(
        report_detail_url=report_detail_url, build_id=build_id
    )

    it_totalcount, it_passcount, it_skipcount, it_failcount, it_errorcount, it_elapsed = get_it_data(it_report_url)

    ut_judgement = get_judgement(int(branch_coverage), int(class_coverage), int(line_coverage))

    result, duration = get_report_detail_data(detail_url=report_detail_url)

    report_content = Template(config.report_template).render(
        project_name=project_name,
        branch=branch,
        score=score,
        commiter=commiter,
        sub_modules=sub_modules,
        build_id=build_id,
        code_lines=code_lines,
        new_lines=new_lines,
        bugs=bugs,
        new_bugs=new_bugs,
        vulnerabilities=vulnerabilities,
        new_vulnerabilities=new_vulnerabilities,
        code_smells=code_smells,
        new_code_smells=new_code_smells,
        violations=violations,
        new_violations=new_violations,
        rank_list=rank_list,
        console_url=console_url,
        ut_report_url=ut_report_url,
        ut_cover_report_url=ut_cover_report_url,
        ut_failcount=ut_failcount,
        ut_passcount=ut_passcount,
        ut_skipcount=ut_skipcount,
        ut_totalcount=ut_totalcount,
        ut_judgement=ut_judgement,
        ut_line_cover=line_coverage,
        ut_class_cover=class_coverage,
        ut_branch_cover=branch_coverage,
        it_totalcount=it_totalcount,
        it_passcount=it_passcount,
        it_skipcount=it_skipcount,
        it_failedcount=it_failcount + it_errorcount,
        it_failedrate=round((it_failcount + it_errorcount) / float(it_totalcount) * 100, 2) if it_totalcount else 0.0,
        it_elapsed=it_elapsed,
        it_report_url=it_report_url,
        runtime_host=config.runtime_host,
        sonar_url=config.sonar_url,
        error_msg=error_msg
    )

    notify_list = config.ADMIN_LIST
    # if branch == "master":
    #     notify_list.extend(get_group_email_list(project_id))

    notifiers = notify_list + [commiter] + receivers
    report_send(project_name, branch, notifiers, build_id, report_content)

    if error_msg:
        try:
            send_wechat_notice(project_name, branch, commiter, build_id, error_msg, report_detail_url, notifiers)
        except Exception as e:
            log.error("[send wechat failed]" + str(e))

    with app.app_context():
        api_count = 0
        covered_count = 0
        ph = None
        try:
            ph = PushHistory.query.filter_by(project_id=project_id, branch=branch, build_id=build_id).first()
            if ph:
                ph.error_type = error_type
                ph.error_msg = error_msg
                ph.result = result
                ph.duration = duration
                db.session.add(ph)
                db.session.commit()
            group = ph.gitlab_url.split(":")[1].split("/")[0]
            pas = ProjectAutomationStatus.query.filter_by(group=group, project=project_name).first()
            if pas:
                api_count = pas.api_count
                covered_count = pas.covered_count
        except Exception as e:
            log.error("[update db failed]" + traceback.format_exc())
        params = {
            "topic": "red.alert",
            "message": json.dumps({
                "database": "athena-monitor",
                "measurement": "push-history-score",
                "tags": {
                    "project_name": project_name,
                    "branch": branch,
                    "commiter": commiter
                },
                "fields": {
                    "_project_name": project_name,
                    "_branch": branch,
                    "score": score,
                    "_commiter": commiter,
                    "code_lines": code_lines,
                    "new_lines": new_lines,
                    "bugs": bugs,
                    "new_bugs": new_bugs,
                    "vulnerabilities": vulnerabilities,
                    "new_vulnerabilities": new_vulnerabilities,
                    "code_smells": code_smells,
                    "new_code_smells": new_code_smells,
                    "violations": violations,
                    "new_violations": new_violations,
                    "rank_list": rank_list,
                    "ut_report_url": ut_report_url,
                    "ut_cover_report_url": ut_cover_report_url,
                    "ut_failcount": ut_failcount,
                    "ut_passcount": ut_passcount,
                    "ut_skipcount": ut_skipcount,
                    "ut_totalcount": ut_totalcount,
                    "ut_judgement": ut_judgement,
                    "ut_line_cover": line_coverage,
                    "ut_class_cover": class_coverage,
                    "ut_branch_cover": branch_coverage,
                    "it_totalcount": it_totalcount,
                    "it_passcount": it_passcount,
                    "it_skipcount": it_skipcount,
                    "it_failedcount": it_failcount + it_errorcount,
                    "it_failedrate": round((it_failcount + it_errorcount) / float(it_totalcount) * 100, 2) if it_totalcount else 0.0,
                    "it_elapsed": it_elapsed,
                    "api_count": api_count,
                    "covered_count": covered_count,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            })
        }

        send_kafka(params)

        try:
            cs = CodeScore(
                history_id=ph.id if ph else 0,
                code_lines=code_lines,
                new_lines=new_lines,
                bugs=bugs,
                new_bugs=new_bugs,
                vulnerabilities=vulnerabilities,
                new_vulnerabilities=new_vulnerabilities,
                code_smells=code_smells,
                new_code_smells=new_code_smells,
                violations=violations,
                new_violations=new_violations,
                rank_list=rank_list,
                ut_report_url=ut_report_url,
                ut_cover_report_url=ut_cover_report_url,
                ut_failcount=ut_failcount,
                ut_passcount=ut_passcount,
                ut_skipcount=ut_skipcount,
                ut_totalcount=ut_totalcount,
                ut_elapsed=ut_elapsed,
                ut_line_cover=line_coverage,
                ut_class_cover=class_coverage,
                ut_branch_cover=branch_coverage,
                ut_judgement=str(ut_judgement),
                it_totalcount=it_totalcount,
                it_passcount=it_passcount,
                it_skipcount=it_skipcount,
                it_failedcount=it_failcount + it_errorcount,
                it_failedrate=round((it_failcount + it_errorcount) / float(it_totalcount) * 100, 2) if it_totalcount else 0.0,
                it_elapsed=it_elapsed,
                score=score
            )
            db.session.add(cs)
            db.session.commit()
            db.session.close()
        except Exception as e:
            log.error("update db error: %s" % traceback.format_exc())


def send_wechat_notice(project, branch, commiter, build_id, errorMsg, errorDetail, notifiers):
    content_message = [
        "项目: %s" % project,
        "分支: %s" % branch,
        "提交人: %s" % commiter,
        "构建Id: %s" % build_id
    ]
    if errorMsg:
        content_message.append("异常: %s" % errorMsg)
        content_message.append("详情: %s" % errorDetail)
    data = {
        "touser" : ",".join(notifiers),
        "from" : "Athena质量监控",
        "type" : "wechat",
        "content" : "\n" + "\n".join(content_message)
    }
    r = requests.post(config.notice_url, json=data)
    log.info("[send wechat result]httpcode:%s response:%s" % (r.status_code, r.json()))
