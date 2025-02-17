import dash
from dash import html, dcc

import dash_bootstrap_components as dbc

from . import sla_layouts
import datetime

dash.register_page(__name__, path_template="/slas/months/campuses")


current_date_interval = dcc.Interval(
    id="current-date-interval",
    interval=1000,  # in milliseconds
    n_intervals=0,
)

show_sla_graph_interval = dcc.Interval(
    id="show-campus-sla-month-graph-interval",
    interval=30 * 60 * 1000,  # in milliseconds
    n_intervals=0,
)


def layout():
    dom = html.Div(
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(["PSU 12 Month SLAs"]),
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
                            # html.Div([html.H2(["Internet"])]),
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
                                id="internet-sla-month-graph",
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
                                id="hatyai-sla-month-graph",
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            # html.Div([html.H2(["Pattani"])]),
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
                                id="pattani-sla-month-graph",
                            ),
                        ],
                        width=6,
                    ),
                ],
                style=dict(paddingTop="1vh"),
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            # html.Div([html.H2(["Phuket"])]),
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
                                id="phuket-sla-month-graph",
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            # html.Div([html.H2(["Suratthani"])]),
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
                                id="suratthani-sla-month-graph",
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            # html.Div([html.H2(["Trang"])]),
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
                                id="trang-sla-month-graph",
                            ),
                        ],
                        width=4,
                    ),
                ],
                style=dict(paddingTop="1vh"),
            ),
            # # sla_layouts.render_layout("Search"),
            # dcc.Store(id="month-slas", storage_type="local"),
            show_sla_graph_interval,
            current_date_interval,
        ]
    )

    return dom
