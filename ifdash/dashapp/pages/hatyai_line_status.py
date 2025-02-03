import dash
from dash import html, dcc

import dash_bootstrap_components as dbc

from . import sla_layouts
from . import maps
import datetime

import dash_leaflet as dl

dash.register_page(__name__, path="/campuses/hatyai/line")


current_date_interval = dcc.Interval(
    id="current-date-interval",
    interval=1000,  # in milliseconds
    n_intervals=0,
)

get_hatyai_line_state_interval = dcc.Interval(
    id="get-hatyai-line-state-interval",
    interval=2 * 60 * 1000,  # in milliseconds
    n_intervals=0,
)

get_hatyai_line_days_sla_interval = dcc.Interval(
    id="get-hatyai-line-days-sla-interval",
    interval=15 * 60 * 1000,  # in milliseconds
    n_intervals=0,
)


# show_hatyai_line_interval = dcc.Interval(
#     id="show-hatyai-line-state-interval",
#     interval=500,  # in milliseconds
#     n_intervals=0,
# )


def layout():
    dom = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dl.Map(
                                [
                                    # dl.TileLayer(),
                                    maps.tile_layer,
                                    dl.LayerGroup(id="hatyai-campus-line-network-up"),
                                    dl.LayerGroup(id="hatyai-campus-line-network-down"),
                                    dl.LayerGroup(
                                        id="hatyai-campus-line-network-warning"
                                    ),
                                    dl.LayerGroup(
                                        id="hatyai-campus-line-network-downtime"
                                    ),
                                ],
                                center=[7.007918327624404, 100.50051576195916],
                                zoom=16.4,
                                zoomDelta=0.2,
                                style={"height": "100vh"},
                                id="hatyai-campus-line-map",
                            ),
                        ],
                        width=9,
                    ),
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Div(["7 Days"]),
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
                            html.Br(),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H2(["Hatyai Campus Backbone"]),
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
                                                id="hatyai-backbone-days-sla-graph",
                                            ),
                                        ]
                                    )
                                ]
                            ),
                            html.Br(),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.H2(["Hatyai All Unit"]),
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
                                                id="hatyai-all-unit-days-sla-graph",
                                            ),
                                        ]
                                    )
                                ]
                            ),
                        ]
                    ),
                ]
            ),
            dcc.Store(id="hatyai-line-state"),
            dcc.Store(id="hatyai-line-days-slas"),
            current_date_interval,
            get_hatyai_line_state_interval,
            get_hatyai_line_days_sla_interval,
            # show_campuses_state_interval,
        ]
    )

    return dom
