import dash
from dash import html, dcc

import dash_bootstrap_components as dbc

from . import sla_layouts
import datetime

dash.register_page(__name__, path_template="/slas/months/service")

show_service_sla_graph_interval = dcc.Interval(
    id="show-service-sla-month-graph-interval",
    interval=5 * 60 * 1000,  # in milliseconds
    n_intervals=0,
)

current_date_interval = dcc.Interval(
    id="current-date-interval",
    interval=1000,  # in milliseconds
    n_intervals=0,
)


def layout():

    dom = html.Div(
        children=[
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.H1(["Service 12 Month SLAs"]),
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
                            # html.Div([html.H2(["Campus Web SLA"])]),
                            html.Div(
                                [
                                    # html.Div([html.H3(["PSU Primary Web"])]),
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
                                        id="service-sla-month-graph",
                                    ),
                                ],
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            # html.Div([html.H2(["Campus Web SLA"])]),
                            html.Div(
                                [
                                    # html.Div([html.H3(["PSU Primary Web"])]),
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
                                        # id="web-psu-student-eila-sla-month-graph",
                                    ),
                                ],
                            ),
                        ],
                        width=6,
                    ),
                ]
            ),
            html.Div(style=dict(paddingTop="1vh")),
            # dcc.Store(id="month-slas", storage_type="local"),
            show_service_sla_graph_interval,
            current_date_interval,
        ]
    )

    return dom
