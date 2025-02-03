import dash
from dash import html, dcc

import dash_bootstrap_components as dbc

from . import sla_layouts
from . import maps
import datetime

import dash_leaflet as dl

dash.register_page(__name__, path="/campuses")


current_date_interval = dcc.Interval(
    id="current-date-interval",
    interval=1000,  # in milliseconds
    n_intervals=0,
)

get_campuses_state_interval = dcc.Interval(
    id="get-campus-state-interval",
    interval=60 * 1000,  # in milliseconds
    n_intervals=0,
)

get_campuses_sla_interval = dcc.Interval(
    id="get-campus-sla-interval",
    interval=30 * 60 * 1000,  # in milliseconds
    n_intervals=0,
)


show_campuses_state_interval = dcc.Interval(
    id="show-campus-state-interval",
    interval=500,  # in milliseconds
    n_intervals=0,
)


def render_campus_contaniners():

    doms = []

    campus_titles = [
        ("ISP", "isp"),
        ("Hat Yai", "hatyai"),
        ("Pattani", "pattani"),
        ("Phuket", "phuket"),
        ("Suratthani", "suratthani"),
        ("Trang", "trang"),
    ]

    cols = []
    for name, doc_id in campus_titles:
        campus_dom = dbc.Col(
            [
                # html.H2([name]),
                html.Div(
                    [
                        dbc.Spinner(
                            color="primary",
                            spinner_style={
                                "width": "3rem",
                                "height": "3rem",
                            },
                        ),
                        f"{name} Loading...",
                    ],
                    id=f"{doc_id}-days-sla-graph",
                ),
            ],
            width=6,
        )
        cols.append(campus_dom)

    for i in range(0, len(cols), 2):
        row = dbc.Row(cols[i : i + 2])
        doms.append(row)
        doms.append(html.Br())

    return doms


def layout():
    dom = html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dl.Map(
                                [
                                    maps.tile_layer,
                                    # dl.TileLayer(),
                                    dl.LayerGroup(id="campus-links"),
                                    dl.LayerGroup(id="campus-marker-up"),
                                    dl.LayerGroup(id="campus-marker-down"),
                                    dl.LayerGroup(id="campus-marker-warning"),
                                    dl.LayerGroup(id="campus-marker-internet-up"),
                                    dl.LayerGroup(id="campus-marker-internet-down"),
                                ],
                                center=[8.7, 100.5],
                                zoom=7.5,
                                style={"height": "100vh"},
                                id="campus-map",
                            ),
                        ],
                        width=7,
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
                            html.Div(children=render_campus_contaniners()),
                            # sla_layouts.render_sla_card("Internet"),
                            # html.Br(),
                            # sla_layouts.render_sla_card("Hat Yai"),
                            # html.Br(),
                            # sla_layouts.render_sla_card("Pattani"),
                            # html.Br(),
                            # sla_layouts.render_sla_card("Phuket"),
                            # html.Br(),
                            # sla_layouts.render_sla_card("Suratthani"),
                            # html.Br(),
                            # sla_layouts.render_sla_card("Trang"),
                        ],
                        width=5,
                    ),
                ]
            ),
            dcc.Store(id="campus-state"),
            dcc.Store(id="campus-days-sla"),
            current_date_interval,
            get_campuses_state_interval,
            show_campuses_state_interval,
            get_campuses_sla_interval,
        ]
    )

    return dom
