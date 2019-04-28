# -*- encoding:utf-8 -*-
from athena.controllers import url


@url.route("/check_backend_active.html")
def check_backent_active():
    return "ok"