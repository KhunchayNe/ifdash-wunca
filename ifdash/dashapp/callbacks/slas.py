import dash

# from dash import callback, Input, Output, dash_table, dcc, State, Patch
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from flask import current_app, session
from flask_login import login_user, logout_user, current_user
from ifdash import models, services
from ifdash.web import caches
from ifdash.dashapp import managers

from ifdash.clients import checkmk

import pprint
import datetime
import asyncio


from .. import redis_caches

TIMEOUT = 60

METRICS = {
    "outside-psu": "internet",
    "ISP": "psu-isp",
    "PSU-CORE-NETWORK": "psu-core",
    "PSU-HDY-NETWORK": "psu-hat-yai-campus",
    "PSU-HDY-Backbone": "psu-hat-yai-campus-backbone",
    "PSU-HDY-Wireless": "psu-hat-yai-campus-wireless",
    "PSU-HDY-All-Unit": "psu-hat-yai-campus-all-unit",
    "AD": "psu-ad",
    "HTTP": "psu-web",
}


def set_sla_color_schema(sla):
    color = "success"

    if sla < 99.671:
        color = "danger"
    elif sla < 99.982:
        color = "warning"

    return color


def calculate_sla(data, response):
    for key in METRICS.values():
        if key not in data:
            # print("key:", key)
            data[key] = dict()

    for k, v in METRICS.items():
        if k not in response:
            continue

        data[v] = response[k]
        amount = data[v]["up"] + data[v]["down"] + data[v]["unreach"]
        data[v]["sla"] = 0

        if amount > 0:
            sla = (data[v]["up"] + data[v]["unreach"]) / amount * 100
            data[v]["sla"] = sla


@caches.cache.memoize(timeout=TIMEOUT)
def get_current_state_slas():
    data = dict()

    for name in METRICS:
        response = redis_caches.redis_client.get(f"ifdash:sla:group:{name}")
        if not response:
            print(name, "not found")
            continue

        new_bucket = METRICS.get(name)
        data[new_bucket] = response

    return data


@dash.callback(
    dash.Output("current-sla-memory", "data"),
    dash.Input("get-sla-interval", "n_intervals"),
    # dash.State("current-sla-memory", "data"),
    background=True,
    manager=managers.background_callback_manager,
)
# @caches.cache.memoize(timeout=TIMEOUT)
def get_sla_data(n_intervals):
    print("get sla data:", datetime.datetime.now())
    data = get_current_state_slas()
    return data


@dash.callback(
    dash.Output("search-sla-memory", "data"),
    dash.Input("sla-date-range", "start_date"),
    dash.Input("sla-date-range", "end_date"),
    # dash.State("search-sla-memory", "data"),
    background=True,
    manager=managers.background_callback_manager,
)
def get_sla_by_date_data(started_date, ended_date):
    print("get sla by date data:", started_date, ended_date)
    data = data or dict()
    return data


def generate_metric_callback():
    for page in ["current", "search"]:
        for metric in METRICS.values():
            print("render matric callback", page, metric)

            @dash.callback(
                dash.Output(f"{page}-{metric}-sla-card", "class_name"),
                dash.Output(f"{page}-{metric}-sla", "children"),
                dash.Output(f"{page}-{metric}-up", "children"),
                dash.Output(f"{page}-{metric}-unreach", "children"),
                dash.Output(f"{page}-{metric}-down", "children"),
                dash.Output(f"{page}-{metric}-downtime", "children"),
                dash.Output(f"{page}-{metric}-total", "children"),
                dash.Input(f"{page}-sla-memory", "modified_timestamp"),
                dash.State(f"{page}-sla-memory", "data"),
            )
            def on_data(ts, data):
                if ts is None:
                    raise PreventUpdate

                # print("got", dash.callback_context.outputs_list)
                current_metric = ""
                for output_element in dash.callback_context.outputs_list:
                    if "-sla" == output_element["id"][-4:]:
                        current_metric = output_element["id"][
                            output_element["id"].index("-") + 1 : -4
                        ]
                        break

                store_data = {}
                if data and current_metric in data:
                    store_data = data.get(current_metric, {})

                # print(f"update {current_metric:30} -> {store_data}")
                metric_sla = 0
                up = 0
                down = 0
                unreach = 0
                downtime = 0
                total = 0
                if store_data:
                    metric_sla = store_data.get("sla", 0)
                    up = store_data.get("up", 0)
                    unreach = store_data.get("unreach", 0)
                    down = store_data.get("down", 0)
                    downtime = store_data.get("downtime", 0)
                    total = store_data.get("total", 0)

                color_sla = set_sla_color_schema(metric_sla)

                slas = [f"{metric_sla:.02f}", up, unreach, down, downtime, total]

                return [f"text-bg-{color_sla}"] + slas


generate_metric_callback()
