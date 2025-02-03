import dash

# from dash import callback, Input, Output, dash_table, dcc, State, Patch
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import current_app, session
from flask_login import login_user, logout_user, current_user
from ifdash import models
from ifdash.web import caches
from ifdash.dashapp import managers

from ifdash.clients import checkmk, influxdb

import pprint
import datetime

TIMEOUT = 60


def transform(response) -> dict():
    data = data or dict()
    return data


@dash.callback(
    dash.Output("current-state-memory", "data"),
    dash.State("current-state-memory", "data"),
    dash.Input("get-sla-interval", "n_intervals"),
    background=True,
)
@caches.cache.memoize(timeout=TIMEOUT)  # in seconds
def get_data(n_intervals, data):
    response = influxdb.client.hosts.get_current_state()
    print("response", response)

    # calculate_sla(data, response)
    data = transform(response)

    return data
