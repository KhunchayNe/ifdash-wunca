import pprint
import datetime
import asyncio
import pandas

import plotly.express as px
import dash
import dash_bootstrap_components as dbc
import random

from flask import current_app, session
from flask_login import login_user, logout_user, current_user
from ifdash import models, services

import dash_leaflet as dl
import plotly.express as px


from ifdash.clients import checkmk
from ifdash.web import caches
from ifdash.dashapp import managers

from . import slas
from . import slas_graph
from .. import redis_caches


COLOR_STATE_MAPPERS = dict(up="green", down="red", warning="yellow", unknow="gray")


def get_icon(type_, color, title=""):
    color_map = dict(
        red="text-bg-danger",
        green="text-bg-success",
        yellow="text-bg-warning",
        gray="text-bg-dark",
    )
    icon = dict(
        html=f"""
        <div class="badge rounded-circle {color_map[color]}" style="position:absolute;left:-0.7rem; top:-1.6rem;">
            <i class="fa-solid fa-network-wired" style="font-size: 1rem;"></i>
        </div>
        """,
        className=f"dummy",
    )

    if type_.lower() in ["wifi", "ap"]:
        icon = dict(
            html=f"""
            <div class="badge rounded-circle {color_map[color]}" style="position:absolute;left:-0.7rem; top:-1.6rem;">
                <i class="bi bi-wifi" style="font-size: 1rem;"></i>
            </div>
            """,
            className="dummy",
            # className=f"rounded-circle badge text-bg-success text-lg text-center",
            # iconSize=[140, 110],
        )

    return icon


@caches.cache.memoize(timeout=60 * 60)  # in seconds
def get_equipment_by_host_id(host_id):
    equipment_service = services.equipments.EquipmentService(sync=True)
    equipment = equipment_service.get_equipment_by_host_id_sync(host_id)

    return equipment


@dash.callback(
    dash.Output("hatyai-line-state", "data"),
    dash.Input("get-hatyai-line-state-interval", "n_intervals"),
    background=True,
    manager=managers.background_callback_manager,
)
def get_hatyai_line_states(n_intervals):
    group_names = ["PSU-HDY-Backbone", "PSU-HDY-All-Unit"]
    results = dict()
    for group_name in group_names:
        group_key = f"ifdash:sla:group:{group_name}"
        result = redis_caches.redis_client.get(group_key)

        if not result:
            continue

        results[group_name] = dict()
        for host_id in result.get("hosts", []):
            host_key = f"ifdash:state:{host_id}"
            host = redis_caches.redis_client.get(host_key)
            if host:
                results[group_name][host_id] = host

    return results


@dash.callback(
    dash.Output("hatyai-line-days-slas", "data"),
    dash.Input("get-hatyai-line-days-sla-interval", "n_intervals"),
    background=True,
    manager=managers.background_callback_manager,
)
def get_hatyai_line_days_sla(n_intervals):

    group_names = ["PSU-HDY-Backbone", "PSU-HDY-All-Unit"]
    results = slas_graph.get_sla_day(group_names, type="host", days=7)
    print(">>> line", datetime.datetime.now(), group_names)
    return results


@dash.callback(
    dash.Output("hatyai-wifi-state", "data"),
    dash.Input("get-hatyai-wifi-state-interval", "n_intervals"),
    background=True,
    manager=managers.background_callback_manager,
)
def get_hatyai_wifi_states(n_intervals):
    group_names = ["PSU-HDY-Wireless"]
    results = dict()
    for group_name in group_names:
        group_key = f"ifdash:sla:group:{group_name}"
        result = redis_caches.redis_client.get(group_key)

        if not result:
            continue

        results[group_name] = dict()
        for host_id in result.get("hosts", []):
            host_key = f"ifdash:state:{host_id}"
            host = redis_caches.redis_client.get(host_key)
            if host:
                results[group_name][host_id] = host

    return results


@dash.callback(
    dash.Output("hatyai-wifi-days-slas", "data"),
    dash.Input("get-hatyai-wifi-days-sla-interval", "n_intervals"),
    background=True,
    manager=managers.background_callback_manager,
)
def get_hatyai_wifi_days_sla(n_intervals):
    group_names = ["PSU-HDY-Wireless"]
    ap_results = slas_graph.get_sla_day(group_names, type="ap", days=7)
    host_results = slas_graph.get_sla_day(group_names, type="host", days=7)
    results = dict(ap=ap_results, host=host_results)
    print(">>> wifi", datetime.datetime.now(), group_names)
    return results


@dash.callback(
    dash.Output("hatyai-campus-line-network-up", "children"),
    dash.Output("hatyai-campus-line-network-down", "children"),
    dash.Output("hatyai-campus-line-network-warning", "children"),
    dash.Output("hatyai-campus-line-network-downtime", "children"),
    dash.Input("hatyai-line-state", "data"),
)
def show_hatyai_campus_line_state(data):
    group_names = ["PSU-HDY-Backbone", "PSU-HDY-All-Unit"]

    diis_coordinates = models.base.GeoObject(
        coordinates=[7.009021420820812, 100.49794949231915]
    )

    STATE_NAME = ["up", "down", "warning", "downtime"]

    state_up_markers = []
    state_down_markers = []
    state_warning_markers = []
    state_downtime_markers = []
    markers = dict(
        up=state_up_markers,
        down=state_down_markers,
        warning=state_warning_markers,
        unknow=state_downtime_markers,
    )
    for group_name in group_names:
        for host_id, host in data.get(group_name, {}).items():
            equipment = get_equipment_by_host_id(host_id=host_id)
            coordinates = diis_coordinates
            if equipment and equipment.coordinates.coordinates:
                coordinates = equipment.coordinates

            tooltip = dl.Tooltip(f'{host["name"]} - {host.get("state_name")}')
            # marker = dl.Marker(position=coordinates.coordinates)
            marker = dl.DivMarker(
                position=coordinates.coordinates,
                iconOptions=get_icon(
                    "host", COLOR_STATE_MAPPERS[host.get("state_name", "unknow")]
                ),
                children=tooltip,
            )
            markers[host.get("state_name", "unknow")].append(marker)

    return (
        state_up_markers,
        state_down_markers,
        state_warning_markers,
        state_downtime_markers,
    )


@dash.callback(
    dash.Output("hatyai-campus-wifi-network-up", "children"),
    dash.Output("hatyai-campus-wifi-network-down", "children"),
    dash.Output("hatyai-campus-wifi-network-warning", "children"),
    dash.Output("hatyai-campus-wifi-network-downtime", "children"),
    dash.Input("hatyai-wifi-state", "data"),
)
def show_hatyai_campus_wifi_state(data):
    # group_names = ["PSU-HDY-Wireless", "PSU-HDY-Wireless-Switch"]

    diis_coordinates = models.base.GeoObject(
        coordinates=[7.009021420820812, 100.49794949231915]
    )
    state_up_markers = []
    state_down_markers = []
    state_warning_markers = []
    state_downtime_markers = []
    markers = dict(
        up=state_up_markers,
        down=state_down_markers,
        warning=state_warning_markers,
        unknow=state_downtime_markers,
    )

    for group_name, hosts in data.items():
        for host_id, host in hosts.items():
            equipment = get_equipment_by_host_id(host_id=host_id)
            coordinates = diis_coordinates
            if equipment and equipment.coordinates.coordinates:
                coordinates = equipment.coordinates

            tooltip = dl.Tooltip(f'{host["name"]} - {host["state_name"]}')
            marker = dl.DivMarker(
                position=coordinates.coordinates,
                iconOptions=get_icon(
                    host.get("type"),
                    COLOR_STATE_MAPPERS[host.get("state_name", "unknow")],
                ),
                children=tooltip,
            )
            markers[host.get("state_name", "unknow")].append(marker)

    return (
        state_up_markers,
        state_down_markers,
        state_warning_markers,
        state_downtime_markers,
    )


@dash.callback(
    dash.Output("hatyai-backbone-days-sla-graph", "children"),
    dash.Output("hatyai-all-unit-days-sla-graph", "children"),
    dash.Input("hatyai-line-days-slas", "data"),
)
def show_hatyai_campus_line_days_slas(data):
    GRAPH_HEIGHT = 300
    graphs = []

    for key, values in data.items():
        day_slas = values.get("all", {})

        df = pandas.DataFrame.from_dict(day_slas).transpose()

        df = df[["sla"]]
        df = df.sort_index()

        df["color"] = df["sla"].apply(slas.set_sla_color_schema)

        fig = px.bar(
            df,
            x=df.index,
            y="sla",
            # title=title,
            text_auto=".2f",
            labels={"index": "Day", "sla": "SLA"},
            template="plotly_dark",
            color="color",
            color_discrete_map=slas_graph.SLA_COLOR_MAP,
        )
        fig.update_layout(
            height=GRAPH_HEIGHT,
            xaxis=dict(
                # type="category",
            ),
        )
        fig.update_xaxes(dtick="D1", tickformat="%Y-%m-%d")
        fig.update_yaxes(
            range=(0, 100),
        )
        fig.update_traces(
            #     textfont_size=12,
            #     textangle=0,
            #     textposition="outside",
            #     cliponaxis=False,
            showlegend=False,
        )

        content_id = f"web-{key}-sla-month-graph-content"

        graphs.append(dash.dcc.Graph(id=content_id, figure=fig))
    return graphs


@dash.callback(
    dash.Output("hatyai-wifi-days-sla-graph", "children"),
    dash.Output("hatyai-wifi-switch-days-sla-graph", "children"),
    dash.Input("hatyai-wifi-days-slas", "data"),
)
def show_hatyai_campus_wifi_days_slas(data):
    GRAPH_HEIGHT = 300
    graphs = []
    if len(data) == 0:
        return dash.dcc.Graph(), dash.dcc.Graph()

    for state_host in ["ap", "host"]:
        for key, values in data[state_host].items():
            day_slas = values.get("all", {})

            df = pandas.DataFrame.from_dict(day_slas).transpose()

            df = df[["sla"]]
            df = df.sort_index()

            df["color"] = df["sla"].apply(slas.set_sla_color_schema)

            fig = px.bar(
                df,
                x=df.index,
                y="sla",
                # title=title,
                text_auto=".2f",
                labels={"index": "Day", "sla": "SLA"},
                template="plotly_dark",
                color="color",
                color_discrete_map=slas_graph.SLA_COLOR_MAP,
            )
            fig.update_layout(
                height=GRAPH_HEIGHT,
                xaxis=dict(
                    # type="category",
                ),
            )
            fig.update_xaxes(dtick="D1", tickformat="%Y-%m-%d")
            fig.update_yaxes(
                range=(0, 100),
            )
            fig.update_traces(
                #     textfont_size=12,
                #     textangle=0,
                #     textposition="outside",
                #     cliponaxis=False,
                showlegend=False,
            )

            content_id = f"web-{key}-sla-month-graph-content"

            graphs.append(dash.dcc.Graph(id=content_id, figure=fig))

    return graphs


@caches.cache.memoize(timeout=20 * 60)
def get_sla_month(group_names, type):
    # data = slas_graph.get_sla_month(group_names, type=type)
    data = slas_graph.get_sla_group_month(group_names, type=type)
    return data


@dash.callback(
    dash.Output("hatyai-core-sla-month-graph", "children"),
    dash.Output("hatyai-wireless-sla-month-graph", "children"),
    dash.Output("hatyai-all-unit-sla-month-graph", "children"),
    dash.Input("show-hatyai-sla-month-graph-interval", "n_intervals"),
)
def show_hatyai_sla_month_graph(n_intervals):
    GRAPH_HEIGHT = 450
    graph_titles = {
        "Hat Yai Backbone": "PSU-HDY-Backbone",
        "Hat Yai Wireless": "PSU-HDY-Wireless",
        "Hat Yai Central Division": "PSU-HDY-All-Unit",
    }

    results = get_sla_month(graph_titles.values(), type="host")
    ap_results = get_sla_month(["PSU-HDY-Wireless"], type="ap")
    slas_graph.combine_results(ap_results, results)
    # print("results", results)
    data = dict()
    for key, host_slas in results.items():
        if key not in data:
            data[key] = dict()

        for host_id, h_slas in host_slas.items():
            if host_id not in data[key]:
                data[key][host_id] = dict()

            for date, value in h_slas.items():
                data[key][host_id][date] = value["sla"]

    graphs = []

    for title, group in graph_titles.items():
        df = pandas.DataFrame.from_dict(data[group])
        df["sla"] = df[data[group].keys()].mean(axis=1)
        df = df.sort_index()

        df["color"] = df["sla"].apply(slas.set_sla_color_schema)

        fig = px.bar(
            df,
            y="sla",
            title=title,
            text_auto=".2f",
            labels={"index": "Month", "sla": "SLA"},
            template="plotly_dark",
            color="color",
            color_discrete_map=slas_graph.SLA_COLOR_MAP,
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

        graphs.append(dash.dcc.Graph(id="hatyai-core-sla-graph-content", figure=fig))

    return graphs
