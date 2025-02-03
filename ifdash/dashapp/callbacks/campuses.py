import dash
import dash_bootstrap_components as dbc
import random

from flask import current_app, session
from flask_login import login_user, logout_user, current_user
from ifdash import models, services
import dash_leaflet as dl

from ifdash.clients import checkmk
from ifdash.web import caches
from ifdash.dashapp import managers

import pprint
import datetime
import asyncio

import pandas

from . import slas
from . import slas_graph
from .. import redis_caches


from dataclasses import dataclass

hatyai_point = [7.0088874802665915, 100.49806371302826]
phuket_point = [7.894564705888285, 98.35290977608172]
trang_point = [7.518666341422261, 99.57878006786918]
suratthani_point = [9.094400682569859, 99.3565026781295]
pattani_point = [6.8776576423880424, 101.23676949266853]

uninet_point = [10, 100.5]
link1_point = [10, 101.5]
link2_point = [10, 102.5]

campus_links = [
    [pattani_point, hatyai_point],
    [phuket_point, hatyai_point],
    [suratthani_point, hatyai_point],
    [trang_point, hatyai_point],
    [uninet_point, hatyai_point],
    [link1_point, hatyai_point],
    [link2_point, hatyai_point],
]

campus_markers = dict(
    hatyai=hatyai_point,
    pattani=pattani_point,
    phuket=phuket_point,
    trang=trang_point,
    suratthani=suratthani_point,
    Uninet=uninet_point,
    NT=link1_point,
    link2=link2_point,
)
campus_markers["3BB"] = link2_point

ISP_NAMES = ["Uninet", "NT", "3BB"]


CAMPUS_NAME_PREFIXS = dict(
    hatyai="HDY",
    pattani="PTN",
    phuket="PKT",
    suratthani="SRT",
    trang="TRG",
)

DISPLAY_NAMES = dict(
    hatyai="Hat Yai",
    pattani="Pattani",
    phuket="Phuket",
    suratthani="Surattani",
    trang="Trang",
    Uninet="Uninet",
    NT="NT",
)
DISPLAY_NAMES["3BB"] = "3BB"


def get_icon(type_, color, title=""):
    color_map = dict(
        red="text-bg-danger",
        green="text-bg-success",
        yellow="text-bg-warning",
        gray="text-bg-primary",
    )
    icon = dict(
        html=f"""
        <h3><i class="fa-solid fa-network-wired"></i></h3>
    """,
        className=f"badge {color_map[color]} text-lg",
        iconSize=[50, 40],
    )

    if type_ == "internet":
        icon = dict(
            html=f"""
        <h1>{title}</h1><h1><i class="fa-solid fa-cloud"></i></h1>
    """,
            className=f"badge {color_map[color]} text-lg text-center",
            iconSize=[140, 110],
        )

    return icon


@dash.callback(
    dash.Output("campus-state", "data"),
    dash.Input("get-campus-state-interval", "n_intervals"),
    # dash.State("campus-state", "data"),
    background=True,
    manager=managers.background_callback_manager,
)
def get_campuses_states(n_intervals):
    campus_key = "ifdash:campus:state"
    result = redis_caches.redis_client.get(campus_key)
    return result or dict()


@dash.callback(
    dash.Output("campus-days-sla", "data"),
    dash.Input("get-campus-sla-interval", "n_intervals"),
    # dash.State("campus-month-sla", "data"),
    background=True,
    manager=managers.background_callback_manager,
)
def get_campuses_days_sla(n_intervals):

    group_names = ["ISP", "PSU-CORE-NETWORK"]
    results = slas_graph.get_sla_day(group_names, type="host", days=7, enable_host=True)

    key = "ISP"
    data = {"isp": dict()}
    isp_data = data["isp"]
    for host_name, daily_datas in results.get(key, {}).items():
        for date_key, value in daily_datas.items():
            if date_key not in isp_data:
                isp_data[date_key] = value["sla"]
            elif isp_data[date_key] < value["sla"]:
                isp_data[date_key] = value["sla"]

    key = "PSU-CORE-NETWORK"
    for host_name, daily_datas in results.get(key, {}).items():

        campus = None
        for campus_name, prefix in CAMPUS_NAME_PREFIXS.items():
            if prefix in host_name:
                campus = campus_name
                break

        if "CSW" == host_name:
            campus = "hatyai"

        if not campus:
            continue

        if campus not in data:
            data[campus] = dict()

        campus_data = data[campus]

        for date_key, value in daily_datas.items():
            if date_key not in campus_data:
                campus_data[date_key] = value["sla"]
            elif campus_data[date_key] < value["sla"]:
                campus_data[date_key] = value["sla"]

    return data


@dash.callback(
    dash.Output("campus-links", "children"),
    dash.Output("campus-marker-up", "children"),
    dash.Output("campus-marker-down", "children"),
    dash.Output("campus-marker-warning", "children"),
    dash.Output("campus-marker-internet-up", "children"),
    dash.Output("campus-marker-internet-down", "children"),
    # dash.Input("campus-state", "modified_timestamp"),
    dash.Input("show-campus-state-interval", "n_intervals"),
    dash.State("campus-state", "data"),
)
def show_campus_states(n_intervals, current_states):
    current_states = current_states or dict()

    colors = ["green", "red", "yellow", "gray"]

    links = [dl.Polyline(positions=link) for link in campus_links]

    # dl.Circle(center=marker, radius=10000, color=random.choice(colors))
    points = [[], [], []]
    internet_points = [[], []]

    for campus, state in current_states.items():
        color = colors[state]

        type_ = "net"
        if campus in ISP_NAMES:
            type_ = "internet"

        marker = dl.DivMarker(
            position=campus_markers.get(campus),
            iconOptions=get_icon(type_, color, DISPLAY_NAMES[campus]),
        )

        if type_ == "internet":
            internet_points[state].append(marker)
        else:
            points[state].append(marker)

    return (
        links,
        points[0],
        points[1],
        points[2],
        internet_points[0],
        internet_points[1],
    )


@dash.callback(
    dash.Output("isp-days-sla-graph", "children"),
    dash.Output("hatyai-days-sla-graph", "children"),
    dash.Output("pattani-days-sla-graph", "children"),
    dash.Output("phuket-days-sla-graph", "children"),
    dash.Output("suratthani-days-sla-graph", "children"),
    dash.Output("trang-days-sla-graph", "children"),
    dash.Input("campus-days-sla", "data"),
)
def show_campus_month_sla(data):
    GRAPH_HEIGHT = 300
    keys = [
        ("isp", "ISP"),
        ("hatyai", "Hat Yai"),
        ("pattani", "Pattani"),
        ("phuket", "Phuket"),
        ("suratthani", "Suratthani"),
        ("trang", "Trang"),
    ]
    # for key in keys:
    #     results.append(f"{data.get(key):.2f}")
    #     color = slas.set_sla_color_schema(data.get(key, 0))
    #     color_classes.append(f"text-bg-{color}")

    graphs = []
    campus_df = pandas.DataFrame.from_dict(data)

    for key, title in keys:
        df = campus_df[[key]]
        df.columns = ["sla"]
        graph = slas_graph.get_bar_sla_graph(df, title, key, GRAPH_HEIGHT)

        graphs.append(graph)

    return graphs
