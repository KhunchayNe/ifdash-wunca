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
    Output("problem_hosts", "children"),
    Output("host_state_up", "children"),
    Output("host_state_down", "children"),
    Output("host_state_unreach", "children"),
    Output("total_host", "children"),
    Input("get-hosts-interval", "n_interval"),
)
def get_host_states(n_interval):
    response = checkmk.client.hosts.get_hosts()

    problem_hosts = []
    # pprint.pprint(response)

    host_state_counters = [0, 0, 0]
    for v in response.get("value"):
        # pprint.pprint(v)
        data = v["extensions"]
        host_state_counters[data["state"]] += 1
        if data["state"] == 1:
            down_seconds = data["last_time_down"] - data["last_state_change"]
            down_timedelta = datetime.timedelta(seconds=down_seconds)

            problem_hosts.append(
                dict(
                    name=data["name"],
                    state=data["state"],
                    down_time=down_timedelta,
                    ip_address=data["address"],
                )
            )

    problem_hosts.sort(key=lambda data: (data["down_time"], data["name"]))

    table_header = table_header = [
        html.Thead(html.Tr([html.Th("Name"), html.Th("IP"), html.Th("Diff")]))
    ]
    table_body = [
        html.Tbody(
            [
                html.Tr(
                    [
                        html.Td(data["name"]),
                        html.Td(data["ip_address"]),
                        html.Td(str(data["down_time"])),
                    ]
                )
                for data in problem_hosts
            ]
        )
    ]
    host_table = dbc.Table(
        # using the same table as in the above example
        table_header + table_body,
        bordered=True,
        dark=True,
        hover=True,
        responsive=True,
        striped=True,
    )

    return (
        # f"{problem_hosts}",
        host_table,
        host_state_counters[0],
        host_state_counters[1],
        host_state_counters[2],
        sum(host_state_counters),
    )
