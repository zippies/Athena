# -*- encoding:utf-8 -*-
from athena.services.commonService import CommonLib
from config import Config
from athena import log
import requests
import json
import re


def parse_push_info(request):
    full_message = json.dumps(request.json, ensure_ascii=False, indent=4)
    receivers = request.args.get("receivers", "")
    namespace = request.args.get("namespace", "diamond-ci")
    magazine_id = request.args.get("magazine_id", 0)
    CommonLib.pprint(
        full_message=full_message,
        receivers=receivers,
        namespace=namespace,
        magazine_id=magazine_id
    )

    project_id = 0
    project_name = ""
    branch = ""
    gitlab_url = ""
    sub_modules = ""
    commiter = ""

    object_kind = request.json.get("object_kind")
    if request.json.get("repository", None):
        project_id = request.json.get("project_id", 0)
        project_name = request.json.get("repository", {}).get("name", "")
        branch = request.json.get("ref", "").split("refs/heads/")[-1]
        gitlab_url = request.json.get("repository", {}).get("git_ssh_url", "")
        commits = request.json.get("commits", [])

        if object_kind == "push" and len(commits) != 0:
            project_id = request.json.get("project_id", 0)
            project_name = request.json.get("repository", {}).get("name", "")
            branch = request.json.get("ref", "").split("refs/heads/")[-1]
            gitlab_url = request.json.get("repository", {}).get("git_ssh_url", "")
            latest_commit_message = request.json.get("commits", [{"message": ""}])[0]
            sub_modules, ignore = parse_commit_message(latest_commit_message.get("message"))
            # commiter = latest_commit_message.get("author", {}).get("email", "").split("@")[0] if request.json.get(
            #     "commits") else ""
            commiter = request.json.get("user_email").split("@")[0]
        else:
            ignore = True
    else:
        merge_msg = request.json.get("object_attributes", {})
        if object_kind == "merge_request" and merge_msg:
            project_id = merge_msg.get("source_project_id")
            project_name = merge_msg.get("source", {}).get("name", "")
            branch = merge_msg.get("source_branch", "")
            gitlab_url = merge_msg.get("source", {}).get("ssh_url", "")
            commiter = merge_msg.get("last_commit", {}).get("author", {}).get("email", "").split("@")[0]

        ignore = True

    return object_kind, project_id, project_name, branch, gitlab_url, sub_modules, ignore, commiter, full_message, receivers, namespace, magazine_id


def parse_commit_message(commit_message):
    sub_modules = []
    ignore = False
    for sub_modules_match_str in re.finditer("modules<(([^,>]+,? ?)+)>", commit_message):
        sms = sub_modules_match_str.groups()[0].split(",")
        sub_modules.extend([sm.strip() for sm in sms if sm.strip()])
        if "ignore" in sub_modules:
            ignore = True
            break

    return ",".join(sub_modules), ignore


def is_supported_project(project_id):
    try:
        r = requests.get(
            Config.gitlab_url + "/api/v3/projects/{project_id}/repository/files?ref=master&file_path=pom%2Exml&private_token=Sqz4Lm-8nmy95f4tvCLE".format(
                project_id=project_id
            )).status_code
        if r == 200:
            return True
        else:
            return False
    except:
        return False
