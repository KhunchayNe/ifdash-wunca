import dash
from dash import callback, html, Input, Output, dash_table, dcc, State
import dash_bootstrap_components as dbc
from flask import current_app, session
from flask_login import login_user, logout_user, current_user
from ifdash import models

# from ifdash.clients.rezource import RezourceClient


@dash.callback(
    Output("login-output-state", "children"),
    [
        Input("login-button", "n_clicks"),
        State("username", "value"),
        State("password", "value"),
    ],
)
def login(n_clicks, username, password):
    if not username or not password:
        return "กรุณาเข้าสู่ระบบ"

    client = RezourceClient(
        username,
        password,
        base_api_url=current_app.config.get("REZOURCE_BASE_API_URL"),
        verify_ssl=current_app.config.get("REZOURCE_API_VERIFY_SSL", False),
    )

    tokens = client.login()

    if not tokens:
        return "เข้าสู่ระบบไม่สำเร็จ"

    session["tokens"] = tokens.to_dict()
    me = client.get_me()
    user = models.users.User(me)
    login_user(user, remember=True)
    session["me"] = me

    return dcc.Location(pathname="/dashboard", id="redirect-dashboard")


@dash.callback(Output("logout", "data"), Input("logout-button", "n_clicks"))
def logout(n_clicks):
    if current_user.is_authenticated:
        logout_user()
        session.clear()

    return dcc.Location(pathname="/accounts/login", id="redirect-dashboard")
