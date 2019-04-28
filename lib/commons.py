# -*- encoding:utf-8 -*-
import requests

def get_gitlab_projects(username, token):
    group_projects = []
    circle = 1
    while True:
        url = "http://git.caimi-inc.com/api/v3/projects?private_token=%s&sudo=%s&page=%s" %(token, username, circle)
        r = requests.get(url, timeout=(10, 30))
        if r.status_code == 200:
            if len(r.json()) == 0:
                break
            else:
                group_projects.extend([p.get("path_with_namespace") for p in r.json()])
        circle += 1

    group_projects = sorted(group_projects, key=lambda x:x.split("/")[0])

    return group_projects


def replace_week(string):
    return string.replace("Sunday", "周日").replace("Monday", "周一").replace("Tuesday", "周二").replace("Wednesday",
            "周三").replace("Thursday", "周四").replace("Friday", "周五").replace("Saturday", "周六")

