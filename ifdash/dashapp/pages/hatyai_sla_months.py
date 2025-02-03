import dash
from dash import html, dcc

import dash_bootstrap_components as dbc

from . import sla_layouts
import datetime

dash.register_page(__name__, path_template="/slas/months/hatyai")

current_date_interval = dcc.Interval(
    id="current-date-interval",
    interval=1000,  # in milliseconds
    n_intervals=0,
)


show_hatyai_sla_graph_interval = dcc.Interval(
    id="show-hatyai-sla-month-graph-interval",
    interval=15 * 60 * 1000,  # in milliseconds
    n_intervals=0,
)


def layout():
    dom = html.Div(
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(["PSU Hat Yai 12 Month SLAs"]),
                        ]
                    ),
                    dbc.Col(
                        [
                            html.Div(
                                id="current-date",
                                style={"textAlign": "right"},
                            ),
                        ]
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # html.Div([html.H2(["Hat Yai"])]),
                            html.Div(
                                [
                                    dbc.Spinner(
                                        color="primary",
                                        spinner_style={
                                            "width": "3rem",
                                            "height": "3rem",
                                        },
                                    ),
                                    "Loading...",
                                ],
                                id="hatyai-core-sla-month-graph",
                            ),
                        ]
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # html.Div([html.H2(["Hat Yai"])]),
                            html.Div(
                                [
                                    dbc.Spinner(
                                        color="primary",
                                        spinner_style={
                                            "width": "3rem",
                                            "height": "3rem",
                                        },
                                    ),
                                    "Loading...",
                                ],
                                id="hatyai-wireless-sla-month-graph",
                            ),
                        ]
                    ),
                    dbc.Col(
                        [
                            # html.Div([html.H2(["Hat Yai"])]),
                            html.Div(
                                [
                                    dbc.Spinner(
                                        color="primary",
                                        spinner_style={
                                            "width": "3rem",
                                            "height": "3rem",
                                        },
                                    ),
                                    "Loading...",
                                ],
                                id="hatyai-all-unit-sla-month-graph",
                            ),
                        ]
                    ),
                ],
                style=dict(paddingTop="1vh"),
            ),
            show_hatyai_sla_graph_interval,
            current_date_interval,
        ]
    )

    return dom
