from flask import Blueprint, redirect

module = Blueprint("site", __name__)


@module.route("/")
def index():
    return redirect("/dashboard")
