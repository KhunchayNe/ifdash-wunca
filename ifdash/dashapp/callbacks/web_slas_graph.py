import dash
import pandas

pandas.options.mode.copy_on_write = True

# from dash import callback, Input, Output, dash_table, dcc, State, Patch
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

import plotly.express as px
import plotly.graph_objects as go

from flask import current_app, session
from flask_login import login_user, logout_user, current_user
from ifdash import models, services
from ifdash.web import caches
from ifdash.dashapp import managers

from ifdash.clients import checkmk

import pprint
import datetime
import asyncio

from . import campuses
from . import slas
from . import slas_graph

TIMEOUT = 5 * 60

GROUP_WEB_MAPER = {
    "google": "Google",
    "facebook": "Facebook",
    "github": "github",
}


@caches.cache.memoize(timeout=TIMEOUT)  # in seconds
def get_web_30days_sla(groups, enable_host=True):
    # sla_service = services.slas.SLAService(sync=True, client=models.beanie_client)
    sla_service = services.slas.SLAService(sync=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    ended_date = now
    diff = now - datetime.timedelta(days=30)
    started_date = datetime.datetime(year=diff.year, month=diff.month, day=diff.day)
    results = sla_service.get_sla_by_groups_sync(
        groups,
        started_date=started_date,
        ended_date=ended_date,
        enable_host=True,
        timezone="Asia/Bangkok",
    )

    return results


@caches.cache.memoize(timeout=TIMEOUT)  # in seconds
def get_service_30days_sla(groups, enable_host=True):
    # sla_service = services.slas.SLAService(sync=True, client=models.beanie_client)
    sla_service = services.slas.SLAService(sync=True)
    now = datetime.datetime.now(datetime.timezone.utc)
    ended_date = now
    diff = now - datetime.timedelta(days=30)
    started_date = datetime.datetime(year=diff.year, month=diff.month, day=diff.day)
    results = sla_service.get_sla_by_groups_sync(
        groups,
        started_date=started_date,
        ended_date=ended_date,
        enable_host=True,
        timezone="Asia/Bangkok",
    )

    return results


@dash.callback(
    dash.Output("web-sla-30days-graph", "children"),
    dash.Output("web-google-sla-month-graph", "children"),
    dash.Output("web-facebook-sla-month-graph", "children"),
    dash.Output("web-github-sla-month-graph", "children"),
    dash.Input("show-web-sla-month-graph-interval", "n_intervals"),
)
def show_web_sla_month_graph(n_intervals):
    CAMPUS_GRAPH_HEIGHT = 300

    graphs = []
    now = datetime.datetime.now()

    group_name = "Service"
    results = get_web_30days_sla([group_name], enable_host=True)

    df = pandas.DataFrame.from_dict(results.get(group_name, {}))
    df = df.transpose()
    down_record = {
        "host_name": "Down",
        "down": df["down"].sum() if "down" in df else 0,
        "sla": 500 - df["sla"].sum() if "sla" in df else 0,
    }

    df = df._append(down_record, ignore_index=True)

    fig = px.pie(
        df,
        values="sla",
        names="host_name",
        hole=0.3,
        template="plotly_dark",
        color="host_name",
        color_discrete_map={
            "Down": "red",
            "Google": "#009CDE",
            "Facebook": "#315DAE",
            "Github": "#0085AD",
        },
    )
    graphs.append(dash.dcc.Graph(id="web-sla-30days-graph-content", figure=fig))

    results = slas_graph.get_sla_month([group_name], type="service", enable_host=True)

    for key, title in GROUP_WEB_MAPER.items():
        print(key, title)
        values = dict()
        for host_id, values in results.get(group_name, {}).items():
            index = list(values.keys())[0]
            data = values[index]

            if key in data["host_name"].lower():
                process_host_id = key
                break

        df = pandas.DataFrame()
        if values:
            df = pandas.DataFrame.from_dict(values).transpose()
        else:
            values = [dict(sla=0)]
            df = pandas.DataFrame.from_dict(values)

        df = df[["sla"]]
        df = df.sort_index()

        df["color"] = df["sla"].apply(slas.set_sla_color_schema)

        fig = px.bar(
            df,
            x=df.index,
            y="sla",
            title=title,
            text_auto=".2f",
            labels={"index": "Month", "sla": "SLA"},
            template="plotly_dark",
            color="color",
            color_discrete_map=slas_graph.SLA_COLOR_MAP,
        )
        fig.update_layout(
            height=CAMPUS_GRAPH_HEIGHT,
        )

        fig.update_xaxes(dtick="M1", tickformat="%Y-%m")

        fig.update_yaxes(
            range=(0, 100),
        )
        fig.update_traces(
            textfont_size=12,
            textangle=0,
            textposition="outside",
            cliponaxis=False,
            showlegend=False,
        )

        content_id = f"web-{key}-sla-month-graph-content"

        graphs.append(dash.dcc.Graph(id=content_id, figure=fig))
    return graphs


@dash.callback(
    dash.Output("service-sla-month-graph", "children"),
    dash.Input("show-service-sla-month-graph-interval", "n_intervals"),
    # prevent_initial_call=True,
)
# @caches.cache.cached(timeout=TIMEOUT)  # in seconds
def show_web_sla_month_graph(n_intervals):
    CAMPUS_GRAPH_HEIGHT = 300

    graphs = []
    now = datetime.datetime.now()

    group_names = [
        "Service",
    ]
    results = slas_graph.get_sla_group_month(group_names, type="service")
    for group_name in group_names:
        group_sla = results.get(group_name)
        values = group_sla.get("all")

        df = pandas.DataFrame()
        if values:
            df = pandas.DataFrame.from_dict(values).transpose()
        else:
            values = [dict(sla=0)]
            df = pandas.DataFrame.from_dict(values)

        title = group_name

        df = df[["sla"]]
        df = df.sort_index()

        df["color"] = df["sla"].apply(slas.set_sla_color_schema)

        fig = px.bar(
            df,
            x=df.index,
            y="sla",
            title=title,
            text_auto=".2f",
            labels={"index": "Month", "sla": "SLA"},
            template="plotly_dark",
            color="color",
            color_discrete_map=slas_graph.SLA_COLOR_MAP,
        )
        fig.update_layout(
            height=CAMPUS_GRAPH_HEIGHT,
        )
        fig.update_xaxes(dtick="M1", tickformat="%Y-%m")
        fig.update_yaxes(
            range=(0, 100),
        )
        fig.update_traces(
            textfont_size=12,
            textangle=0,
            textposition="outside",
            cliponaxis=False,
            showlegend=False,
        )
        key = group_name.replace(" ", "-")
        content_id = f"web-{key}-sla-month-graph-content"

        graphs.append(dash.dcc.Graph(id=content_id, figure=fig))
    return graphs
