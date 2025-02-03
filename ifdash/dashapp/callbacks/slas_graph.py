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

from ifdash.clients import checkmk, influxdb

import pprint
import datetime
import asyncio

from . import campuses
from . import slas

TIMEOUT = 15 * 60

SLA_COLOR_MAP = {
    "success": "green",
    "danger": "red",
    "warning": "yellow",
}


def get_bar_sla_graph(df, title, key, height=100):
    df = df.sort_index()
    df["color"] = df["sla"].apply(slas.set_sla_color_schema)
    fig = px.bar(
        df,
        y="sla",
        title=title,
        text_auto=".2f",
        labels={"index": "Day", "sla": "SLA"},
        template="plotly_dark",
        color="color",
        color_discrete_map=SLA_COLOR_MAP,
    )
    fig.update_layout(
        height=height,
        legend=dict(title_text=None),
        # xaxis=dict(type="category"),
    )
    fig.update_xaxes(dtick="D1", tickformat="%Y-%m-%d")
    fig.update_yaxes(
        range=(0, 100),
    )
    fig.update_traces(
        # textfont_size=12,
        # textangle=0,
        # textposition="outside",
        # cliponaxis=False,
        showlegend=False,
    )

    return dash.dcc.Graph(
        id=f"{key}-graph-content", figure=fig, config={"displayModeBar": False}
    )


@caches.cache.memoize(timeout=15 * 60)  # in seconds
def get_sla_by_periodic(
    groups,
    started_date,
    ended_date,
    periodic="month",
    enable_host=False,
    StateModel=None,
):
    sla_service = services.slas.SLAService(sync=True)

    results = sla_service.get_sla_granularity_by_groups_sync(
        groups,
        granularity="month",
        started_date=started_date,
        ended_date=ended_date,
        enable_host=enable_host,
        StateModel=StateModel,
        timezone="Asia/Bangkok",
    )
    return results


@caches.cache.memoize(timeout=6 * 60 * 60)  # in seconds
def get_summarize_sla_by_periodic(
    groups,
    started_date,
    ended_date,
    type="host",
    periodic="month",
    enable_host=False,
):
    sla_service = services.sla_summarizers.SLASummarizerService(sync=True)

    results = sla_service.get_sla_sumarization_granularity_by_groups_sync(
        groups,
        granularity=periodic,
        started_date=started_date,
        ended_date=ended_date,
        enable_host=enable_host,
        type=type,
        timezone="Asia/Bangkok",
    )

    return results


@caches.cache.memoize(timeout=12 * 60 * 60)  # in seconds
def get_summarize_group_sla_by_periodic(
    groups,
    started_date,
    ended_date,
    type="host",
    periodic="month",
):
    sla_service = services.sla_summarizers.SLASummarizerService(sync=True)

    results = sla_service.get_group_sla_sumarization_granularity_sync(
        groups,
        granularity=periodic,
        started_date=started_date,
        ended_date=ended_date,
        type=type,
        timezone="Asia/Bangkok",
    )

    return results


def combine_results(results, new_results):
    for group_name, values in results.items():
        # print(">>", group_name, values)
        if group_name not in new_results:
            new_results[group_name] = values
            continue

        for host_name, date_values in values.items():
            # print(host_name, date_values)
            if host_name not in new_results[group_name]:
                new_results[group_name][host_name] = date_values
                continue

            new_results[group_name][host_name].update(date_values)


@caches.cache.memoize(timeout=TIMEOUT)  # in seconds
def get_sla_month(groups, type="host", enable_host=False):
    sla_service = services.slas.SLAService(sync=True, client=models.beanie_client)
    now = datetime.datetime.now(datetime.timezone.utc)
    ended_date = now
    diff = now - datetime.timedelta(days=365)
    iter_date = datetime.datetime(year=diff.year, month=diff.month, day=1)
    before_date = datetime.datetime(year=now.year, month=now.month, day=1)

    results = dict()

    while iter_date < before_date:
        next_ended_date = iter_date + datetime.timedelta(days=31)
        next_ended_date = datetime.datetime(
            year=next_ended_date.year, month=next_ended_date.month, day=1
        )
        month_results = get_summarize_sla_by_periodic(
            groups,
            iter_date,
            next_ended_date,
            type=type,
            periodic="month",
            enable_host=enable_host,
        )

        # print(iter_date, next_ended_date, month_results)
        iter_date = next_ended_date
        combine_results(month_results, results)

    before_date = datetime.datetime(
        year=now.year, month=now.month, day=28
    ) + datetime.timedelta(days=7)
    before_date = datetime.datetime(
        year=before_date.year, month=before_date.month, day=1
    )
    month_results = sla_service.get_sla_granularity_by_groups_sync(
        groups,
        granularity="month",
        started_date=iter_date,
        ended_date=before_date,
        enable_host=enable_host,
        timezone="Asia/Bangkok",
    )
    # print(datetime.datetime.now(), groups, "get month sla", iter_date, before_date)
    combine_results(month_results, results)

    # import pprint

    # pprint.pprint(results)

    return results


@caches.cache.memoize(timeout=TIMEOUT)  # in seconds
def get_sla_day(groups, type="host", days=7, enable_host=False):
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - datetime.timedelta(days=days)
    iter_date = datetime.datetime(year=diff.year, month=diff.month, day=diff.day)
    ended_date = datetime.datetime(year=now.year, month=now.month, day=now.day)

    results = dict()
    while iter_date < ended_date:
        next_date = iter_date + datetime.timedelta(days=1)
        day_results = get_summarize_sla_by_periodic(
            groups,
            iter_date,
            next_date,
            type=type,
            periodic="day",
            enable_host=enable_host,
        )
        combine_results(day_results, results)
        iter_date = next_date

    # sla_service = services.slas.SLAService(sync=True, client=models.beanie_client)
    sla_service = services.slas.SLAService(sync=True)

    day_results = sla_service.get_sla_granularity_by_groups_sync(
        groups,
        started_date=iter_date,
        ended_date=now,
        enable_host=enable_host,
        granularity="day",
        timezone="Asia/Bangkok",
    )
    combine_results(day_results, results)

    # print(">>> day", datetime.datetime.now(), groups)
    return results


@caches.cache.memoize(timeout=TIMEOUT)  # in seconds
def get_sla_current_month(groups, type_):
    sla_service = services.slas.SLAService(sync=True, client=models.beanie_client)

    now = datetime.datetime.now()
    started_date = datetime.datetime(year=now.year, month=now.month, day=1)

    daily_results = get_summarize_group_sla_by_periodic(
        groups,
        started_date,
        now,
        type=type_,
        periodic="day",
    )

    started_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    this_day_slas = sla_service.get_sla_granularity_by_groups_sync(
        groups,
        granularity="day",
        started_date=started_date,
        ended_date=now,
        timezone="Asia/Bangkok",
    )

    results = dict()
    combine_results(daily_results, results)
    combine_results(this_day_slas, results)

    slas = dict()

    month_label = started_date.strftime("%Y-%m")
    for group_name, group_sla in results.items():
        day_counter = 0
        slas_sum = 0
        if group_name not in slas:
            slas[group_name] = dict(all={month_label: {}})

        for date_label, state in group_sla["all"].items():
            for k, v in state.items():
                if k not in slas[group_name]["all"][month_label]:
                    slas[group_name]["all"][month_label][k] = v
                elif type(v) in [int, float]:
                    slas[group_name]["all"][month_label][k] += v
            slas_sum += state["sla"]
            day_counter += 1

        if day_counter > 0:
            slas[group_name]["all"][month_label]["sla"] = slas_sum / day_counter

    return slas


@caches.cache.memoize(timeout=TIMEOUT)  # in seconds
def get_sla_group_month(groups, type="host"):
    sla_service = services.slas.SLAService(sync=True, client=models.beanie_client)
    sla_summarizer_service = services.sla_summarizers.SLASummarizerService(
        sync=True, client=models.beanie_client
    )
    now = datetime.datetime.now(datetime.timezone.utc)
    ended_date = now
    diff = now - datetime.timedelta(days=365)
    iter_date = datetime.datetime(year=diff.year, month=diff.month, day=1)
    before_date = datetime.datetime(year=now.year, month=now.month, day=1)

    results = dict()
    month_results = get_summarize_group_sla_by_periodic(
        groups,
        iter_date,
        before_date,
        type=type,
        periodic="month",
    )

    combine_results(month_results, results)

    month_results = get_sla_current_month(
        groups,
        type,
    )

    combine_results(month_results, results)
    return results


@dash.callback(
    dash.Output("internet-sla-month-graph", "children"),
    dash.Output("hatyai-sla-month-graph", "children"),
    dash.Output("pattani-sla-month-graph", "children"),
    dash.Output("phuket-sla-month-graph", "children"),
    dash.Output("suratthani-sla-month-graph", "children"),
    dash.Output("trang-sla-month-graph", "children"),
    dash.Input("show-campus-sla-month-graph-interval", "n_intervals"),
    # dash.State("month-slas", "data"),
    # background=True,
    # manager=managers.background_callback_manager,
)
def show_campus_sla_month_graph(n_intervals):
    GRAPH_HEIGHT = 250
    results = get_sla_month(["ISP", "PSU-CORE-NETWORK"], enable_host=True)
    data = dict()
    for key, host_slas in results.items():
        if key not in data:
            data[key] = dict()

        for host_id, h_slas in host_slas.items():
            if host_id not in data[key]:
                data[key][host_id] = dict()

            for date, value in h_slas.items():
                data[key][host_id][date] = value["sla"]

    df = pandas.DataFrame.from_dict(data["ISP"])
    df["sla"] = df[data["ISP"].keys()].max(axis=1)
    df = df.sort_index()

    graphs = []
    df["color"] = df["sla"].apply(slas.set_sla_color_schema)
    fig = px.bar(
        df,
        y="sla",
        title="Internet",
        text_auto=".2f",
        labels={"index": "Month", "internet": "SLA"},
        template="plotly_dark",
        color="color",
        color_discrete_map=SLA_COLOR_MAP,
    )
    fig.update_layout(
        height=GRAPH_HEIGHT,
        xaxis=dict(
            # type="category",
        ),
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

    graphs.append(dash.dcc.Graph(id="isp-graph-content", figure=fig))

    df = pandas.DataFrame.from_dict(data["PSU-CORE-NETWORK"])

    # graphs.append(dash.dcc.Graph(id="hatyai-graph-content", figure=fig))
    for campus, prefix in campuses.CAMPUS_NAME_PREFIXS.items():
        # print(campus, prefix)
        if prefix == "HDY":
            campus_df = df[["CSW"]]
            campus_df = campus_df.rename(columns={"CSW": "sla"})
        else:
            campus_df = df[df.columns[pandas.Series(df.columns).str.startswith(prefix)]]
            campus_df["sla"] = campus_df.max(axis=1)

        campus_df = campus_df.sort_index()
        campus_df["color"] = campus_df["sla"].apply(slas.set_sla_color_schema)
        fig = px.bar(
            campus_df,
            y="sla",
            title=campus.title(),
            text_auto=".2f",
            labels={"index": "Month", "sla": "SLA"},
            template="plotly_dark",
            color="color",
            color_discrete_map=SLA_COLOR_MAP,
        )
        fig.update_layout(
            height=GRAPH_HEIGHT,
            xaxis=dict(
                # type="category"
            ),
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

        graphs.append(dash.dcc.Graph(id=f"{campus}-graph-content", figure=fig))

    return graphs
