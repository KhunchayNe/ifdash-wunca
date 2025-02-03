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
    Output("problem_events", "children"),
    Output("event_state_up", "children"),
    Output("event_state_down", "children"),
    Output("event_state_unreach", "children"),
    Output("total_event", "children"),
    Input("get-events-interval", "n_interval"),
)
def get_event_states(n_interval):
    print("xxx>>>")
    response = checkmk.client.events.get_events()

    print("yyy>>>", response)
    problem_events = []
    # pprint.pprint(response)

    event_state_counters = [0, 0, 0]
    for v in response.get("value", []):
        # pprint.pprint(v)
        data = v["extensions"]
        event_state_counters[data["state"]] += 1
        if data["state"] == 1:
            down_seconds = data["last_time_down"] - data["last_state_change"]
            down_timedelta = datetime.timedelta(seconds=down_seconds)

            problem_events.append(
                dict(
                    name=data["name"],
                    state=data["state"],
                    down_time=down_timedelta,
                    ip_address=data["address"],
                )
            )

    problem_events.sort(key=lambda data: (data["down_time"], data["name"]))

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
                for data in problem_events
            ]
        )
    ]
    event_table = dbc.Table(
        # using the same table as in the above example
        table_header + table_body,
        bordered=True,
        dark=True,
        hover=True,
        responsive=True,
        striped=True,
    )

    return (
        # f"{problem_events}",
        event_table,
        event_state_counters[0],
        event_state_counters[1],
        event_state_counters[2],
        sum(event_state_counters),
    )
