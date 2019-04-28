# -*- encoding:utf-8 -*-
from datetime import datetime
from athena import db


class PushHistory(db.Model):
    __tablename__ = "athena_push_history"

    id = db.Column(db.Integer, primary_key=True)
    object_kind = db.Column(db.String(32))
    project_id = db.Column(db.Integer)
    project_name = db.Column(db.String(64))
    branch = db.Column(db.String(64))
    gitlab_url = db.Column(db.String(256))
    sub_modules = db.Column(db.String(256))
    commiter = db.Column(db.String(32))
    full_message = db.Column(db.Text)
    build_id = db.Column(db.Integer)
    receivers = db.Column(db.String(256))
    magazine_id = db.Column(db.Integer)
    error_type = db.Column(db.Integer, default=0)
    error_msg = db.Column(db.String(64))
    duration = db.Column(db.Float, default=0.0)
    result = db.Column(db.String(32))
    createdtime = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, object_kind, project_id, project_name, branch, gitlab_url, sub_modules, commiter, full_message, build_id, receivers, magazine_id):
        self.object_kind = object_kind
        self.project_id = project_id
        self.project_name = project_name
        self.branch = branch
        self.gitlab_url = gitlab_url
        self.sub_modules = sub_modules
        self.commiter = commiter
        self.full_message = full_message
        self.build_id = build_id
        self.receivers = receivers
        self.magazine_id = magazine_id

    def to_json(self):
        return {
            "id": self.id,
            "object_kind": self.object_kind,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "branch": self.branch,
            "gitlab_url": self.gitlab_url,
            "sub_modules": self.sub_modules,
            "commiter": self.commiter,
            "full_message": self.full_message,
            "build_id": self.build_id,
            "receivers": self.receivers,
            "magazine_id": self.magazine_id,
            "createdtime": self.createdtime
        }

    def __repr__(self):
        return "<PushHistory:{commiter}_{project}_{branch}>".format(
            commiter=self.commiter, project=self.project, branch=self.branch
        )


class CodeScore(db.Model):
    __tablename__ = "athena_code_score"

    id = db.Column(db.Integer, primary_key=True)
    history_id = db.Column(db.Integer)
    code_lines = db.Column(db.Integer)
    new_lines = db.Column(db.Integer)
    bugs = db.Column(db.Integer)
    new_bugs = db.Column(db.Integer)
    vulnerabilities = db.Column(db.Integer)
    new_vulnerabilities = db.Column(db.Integer)
    code_smells = db.Column(db.Integer)
    new_code_smells = db.Column(db.Integer)
    violations = db.Column(db.Integer)
    new_violations = db.Column(db.Integer)
    rank_list = db.Column(db.PickleType)
    ut_report_url = db.Column(db.String(256))
    ut_cover_report_url = db.Column(db.String(256))
    ut_failcount = db.Column(db.Integer)
    ut_passcount = db.Column(db.Integer)
    ut_skipcount = db.Column(db.Integer)
    ut_totalcount = db.Column(db.Integer)
    ut_elapsed = db.Column(db.Float)
    ut_line_cover = db.Column(db.Float)
    ut_class_cover = db.Column(db.Float)
    ut_branch_cover = db.Column(db.Float)
    ut_judgement = db.Column(db.String(128))
    it_totalcount = db.Column(db.Integer)
    it_passcount = db.Column(db.Integer)
    it_skipcount = db.Column(db.Integer)
    it_failedcount = db.Column(db.Integer)
    it_failedrate = db.Column(db.Float)
    it_elapsed = db.Column(db.Float)
    score = db.Column(db.Float)
    createdtime = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, history_id, code_lines, new_lines, bugs, new_bugs, vulnerabilities, new_vulnerabilities,
                 code_smells, new_code_smells, violations, new_violations, rank_list, ut_report_url,
                 ut_cover_report_url, ut_failcount, ut_passcount, ut_skipcount, ut_totalcount, ut_elapsed,
                 ut_line_cover, ut_class_cover, ut_branch_cover, ut_judgement, it_totalcount, it_passcount,
                 it_skipcount, it_failedcount, it_failedrate, it_elapsed, score):
        self.history_id = history_id
        self.code_lines = code_lines
        self.new_lines = new_lines
        self.bugs = bugs
        self.new_bugs = new_bugs
        self.vulnerabilities = vulnerabilities
        self.new_vulnerabilities = new_vulnerabilities
        self.code_smells = code_smells
        self.new_code_smells = new_code_smells
        self.violations = violations
        self.new_violations = new_violations
        self.rank_list = rank_list
        self.ut_report_url = ut_report_url
        self.ut_cover_report_url = ut_cover_report_url
        self.ut_failcount = ut_failcount
        self.ut_passcount = ut_passcount
        self.ut_skipcount = ut_skipcount
        self.ut_totalcount = ut_totalcount
        self.ut_elapsed = ut_elapsed
        self.ut_line_cover = ut_line_cover
        self.ut_class_cover = ut_class_cover
        self.ut_branch_cover = ut_branch_cover
        self.ut_judgement = ut_judgement
        self.it_totalcount = it_totalcount
        self.it_passcount = it_passcount
        self.it_skipcount = it_skipcount
        self.it_failedcount = it_failedcount
        self.it_failedrate = it_failedrate
        self.it_elapsed = it_elapsed
        self.score = score


class ProjectAutomationStatus(db.Model):
    __tablename__ = "athena_automation_status"

    id = db.Column(db.Integer, primary_key=True)
    group = db.Column(db.String(64))
    project = db.Column(db.String(64))
    swagger_url = db.Column(db.String(256))
    api_count = db.Column(db.Integer)
    covered_api = db.Column(db.Integer)
    createdtime = db.Column(db.DateTime, default=datetime.now)
    updatedtime = db.Column(db.DateTime, default=datetime.now)

    def __init__(self, group, project, swagger_url, api_count, covered_api):
        self.group = group
        self.project = project
        self.swagger_url = swagger_url
        self.api_count = api_count
        self.covered_api = covered_api
