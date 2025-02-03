from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    send_file,
    Response,
    request,
)
from flask_login import login_required, current_user

from ifdash import models

import beanie

from .. import forms
from .. import caches

import datetime


module = Blueprint("spaces", __name__, url_prefix="/spaces")


@module.route("/")
@login_required
def index():
    host_groups = get_all_groups()
    return render_template("/spaces/index.html", host_groups=host_groups)
