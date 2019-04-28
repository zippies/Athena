# -*- encoding:utf-8 -*-


def parse_build_info(request):
    project_id = str(request.form.get("project_id"))
    project_name = request.form.get("project_name")
    branch = request.form.get("branch")
    build_id = request.form.get("build_id")

    return project_id, project_name, branch, build_id
