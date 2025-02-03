import dash
from dash import callback, html, Input, Output, dash_table, dcc, State
import dash_bootstrap_components as dbc
from flask import current_app, session
from flask_login import login_user, logout_user, current_user
from ifdash import models

from ifdash.clients import checkmk

import pprint
import datetime


from dataclasses import dataclass


@dash.callback(
    Output("problem_services", "children"),
    Output("service_state_ok", "children"),
    Output("service_state_warning", "children"),
    Output("service_state_critical", "children"),
    Output("service_state_unknow", "children"),
    Output("total_service", "children"),
    Input("get-services-interval", "n_interval"),
)
def get_service_states(n_interval):
    response = checkmk.client.services.get_services()

    problem_services = []
    # pprint.pprint(response)

    service_state_counters = [0, 0, 0, 0]
    for v in response.get("value"):
        # pprint.pprint(v)
        data = v["extensions"]
        service_state_counters[data["state"]] += 1
        if data["state"] == 2:
            down_seconds = data["last_time_critical"] - data["last_state_change"]
            down_timedelta = datetime.timedelta(seconds=down_seconds)

            problem_services.append(
                dict(
                    name=data["host_name"],
                    state=data["state"],
                    description=data["description"],
                    down_time=down_timedelta,
                    ip_address=data["host_address"],
                )
            )

    problem_services.sort(key=lambda data: (data["down_time"], data["name"]))

    table_header = table_header = [
        html.Thead(
            html.Tr(
                [
                    html.Th("Name"),
                    html.Th("IP"),
                    html.Th("Description"),
                    html.Th("Diff"),
                ]
            )
        )
    ]
    table_body = [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(data["name"]),
                        html.Td(data["ip_address"]),
                        html.Td(data["description"]),
                        html.Td(str(data["down_time"])),
                    ]
                )
                for data in problem_services
            ]
        )
    ]

    service_table = dbc.Table(
        # using the same table as in the above example
        table_header + table_body,
        bordered=True,
        dark=True,
        hover=True,
        responsive=True,
        striped=True,
    )

    return (
        # f"{problem_services}",
        service_table,
        service_state_counters[0],
        service_state_counters[1],
        service_state_counters[2],
        service_state_counters[3],
        sum(service_state_counters),
    )
