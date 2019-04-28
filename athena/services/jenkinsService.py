# -*- encoding:utf-8 -*-
from athena import js, config
from jinja2 import Template


def parse_build_info(request):
    project_id = request.json.get("project_id")
    project_name = request.json.get("project_name")
    branch = request.json.get("branch")
    commiter = request.json.get("commiter")
    gitlab_url = request.json.get("gitlab_url")
    sub_modules = request.json.get("sub_modules")
    submit_id = request.json.get("submit_id")
    namespace = request.json.get("namespace", "diamond-ci")
    receivers = request.json.get("receivers", "")
    return project_id, project_name, branch, commiter, gitlab_url, sub_modules, submit_id, namespace, receivers


def start_build(project_id, project_name, branch, commiter, gitlab_url, sub_modules, submit_id, namespace, receivers, magazine_id):
    valid_branch = branch
    for ec in config.unexpected_branch_chars:
        valid_branch = valid_branch.replace(ec, "_")
    job_name = project_name + "__" + valid_branch
    job_template_xml = js.get_job_config("job_model")
    job_template = Template(job_template_xml).render(
        project_name=project_name,
        branch=branch,
        gitlab_url=gitlab_url,
        sub_modules=sub_modules,
        project_id=project_id,
        submit_id=submit_id,
        commiter=commiter,
        namespace=namespace,
        receivers=receivers,
        magazine_id=magazine_id,
        magazine_host=config.magazine_host,
        athena_host=config.athena_host
    )
    try:
        js.assert_job_exists(job_name)
        js.reconfig_job(job_name, job_template)
    except:
        js.create_job(job_name, job_template)

    params = {
        "project_name": project_name,
        "branch": branch,
        "project_id": project_id,
        "gitlab_url": gitlab_url,
        "sub_modules": sub_modules,
        "submit_id": submit_id,
        "commiter": commiter,
        "namespace": namespace,
        "receivers": receivers,
        "magazine_id": magazine_id,
        "athena_host": config.athena_host,
        "magazine_host": config.magazine_host
    }
    build_id = js.get_job_info(job_name)['nextBuildNumber']
    js.build_job(job_name, parameters=params)

    return build_id


if __name__ == "__main__":
    import json
    print json.dumps(js.get_build_info("job_model_bak", 4), ensure_ascii=False, indent=4)