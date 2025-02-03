import dash
from dash import html, dcc

import dash_bootstrap_components as dbc


# current_date_interval = dcc.Interval(
#     id="current-date-interval",
#     interval=1000,  # in milliseconds
#     n_intervals=0,
# )

# get_sla_interval = dcc.Interval(
#     id="get-sla-interval",
#     interval=60 * 1000,  # in milliseconds
#     n_intervals=0,
# )


def render_sla_card(title, icon="bi bi-globe"):
    name_id = title.lower().replace(" ", "-")
    return dbc.Card(
        id=f"{name_id}-month-sla-card",
        class_name="text-bg-success",
        children=[
            dbc.CardHeader(
                [
                    html.H4(
                        [
                            html.I(className=f"{icon}"),
                            f" {title}",
                        ]
                    )
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        id=f"{name_id}-month-sla",
                        style={
                            "fontSize": "3vh",
                            "textAlign": "center",
                        },
                    ),
                ]
            ),
            # dbc.CardFooter(
            #     [],
            # ),
        ],
    )


def sla_card(title, icon="bi bi-globe"):
    name_id = title.lower().replace(" ", "-")
    return dbc.Card(
        id=f"{name_id}-sla-card",
        class_name="text-bg-success",
        children=[
            dbc.CardHeader(
                [
                    html.H1(
                        [
                            html.I(className=f"{icon}"),
                            f" {title}",
                        ],
                        style=dict(fontSize="2vh"),
                    )
                ]
            ),
            dbc.CardBody(
                [
                    html.Div(
                        id=f"{name_id}-sla",
                        style={
                            "fontSize": "5vh",
                            "textAlign": "center",
                        },
                    ),
                ]
            ),
            dbc.CardFooter(
                [
                    dbc.Badge(
                        [
                            html.I(className="bi bi-caret-up"),
                            html.Span(id=f"{name_id}-up"),
                        ],
                        color="success",
                    ),
                    dbc.Badge(
                        [
                            html.I(className="bi bi-caret-up"),
                            html.Span(id=f"{name_id}-unreach"),
                        ],
                        color="warning",
                    ),
                    dbc.Badge(
                        [
                            html.I(className="bi bi-caret-down"),
                            html.Span(id=f"{name_id}-down"),
                        ],
                        color="danger",
                    ),
                    dbc.Badge(
                        [
                            html.I(className="bi bi-exclamation-triangle"),
                            html.Span(id=f"{name_id}-downtime"),
                        ],
                        color="dark",
                    ),
                    dbc.Badge(
                        [
                            html.I(className="bi bi-diagram-3-fill"),
                            html.Span(id=f"{name_id}-total"),
                        ],
                        color="grey",
                    ),
                ],
            ),
        ],
    )


def render_layout(page):
    dom = html.Div(
        children=[
            html.H2(children="PSU SLA"),
            html.Div(
                id="host-sla",
                children=[
                    dbc.Row(
                        [
                            dbc.Col([sla_card(f"{page} Internet")]),
                            dbc.Col([sla_card(f"{page} PSU ISP")]),
                            dbc.Col(
                                [
                                    sla_card(
                                        f"{page} PSU CORE", icon="bi bi-diagram-3-fill"
                                    )
                                ]
                            ),
                        ]
                    ),
                ],
            ),
            html.H2(
                children="PSU Hat Yai Campus SLA",
                style={"padding-top": "1em"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [sla_card(f"{page} PSU Hat Yai Campus", "bi bi-diagram-3-fill")]
                    ),
                    dbc.Col(
                        [
                            sla_card(
                                f"{page} PSU Hat Yai Campus Backbone",
                                "bi bi-diagram-3-fill",
                            )
                        ]
                    ),
                    dbc.Col(
                        [sla_card(f"{page} PSU Hat Yai Campus Wireless", "bi bi-wifi")]
                    ),
                    dbc.Col(
                        [
                            sla_card(
                                f"{page} PSU Hat Yai Campus All Unit",
                                "bi bi-diagram-3-fill",
                            )
                        ]
                    ),
                ]
            ),
            html.H2(children="PSU Service SLA", style={"padding-top": "1em"}),
            html.Div(
                id="serice-sla",
                children=[
                    dbc.Row(
                        [
                            dbc.Col(
                                [sla_card(f"{page} PSU Web", "bi bi-browser-chrome")]
                            ),
                            dbc.Col([sla_card(f"{page} PSU AD", "bi bi-server")]),
                        ]
                    ),
                ],
            ),
            # current_date_interval,
            # dcc.Store(id="memory"),
            # get_sla_interval,
        ]
    )

    return dom
