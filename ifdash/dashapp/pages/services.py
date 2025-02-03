import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/services")

current_date_interval = dcc.Interval(
    id="current-date-interval",
    interval=1000,  # in milliseconds
    n_intervals=0,
)

get_services_interval = dcc.Interval(
    id="get-services-interval",
    interval=1000,  # in milliseconds
    n_intervals=0,
)


health_check_bar = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            class_name="text-bg-success",
                            children=[
                                dbc.CardHeader(
                                    [html.I(className="bi bi-heart-pulse-fill"), " OK"]
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="service_state_ok",
                                            style={
                                                "font-size": "5vw",
                                                "text-align": "center",
                                            },
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ]
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            class_name="text-bg-danger",
                            children=[
                                dbc.CardHeader(
                                    [
                                        html.I(className="bi bi-heartbreak-fill"),
                                        " Critical",
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="service_state_critical",
                                            style={
                                                "font-size": "5vw",
                                                "text-align": "center",
                                            },
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ]
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            class_name="text-bg-warning",
                            children=[
                                dbc.CardHeader(
                                    [
                                        html.I(className="bi bi-heart-pulse-fill"),
                                        " ",
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="service_state_warning",
                                            style={
                                                "font-size": "5vw",
                                                "text-align": "center",
                                            },
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ]
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            class_name="text-bg-secondary",
                            children=[
                                dbc.CardHeader(
                                    [
                                        html.I(className="bi bi-heart-pulse-fill"),
                                        " ",
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="service_state_unknow",
                                            style={
                                                "font-size": "5vw",
                                                "text-align": "center",
                                            },
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ]
                ),
                dbc.Col(
                    [
                        dbc.Card(
                            class_name="text-bg-info",
                            children=[
                                dbc.CardHeader(
                                    [
                                        html.I(className="bi bi-heart-pulse-fill"),
                                        " TOTAL",
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="total_service",
                                            style={
                                                "font-size": "5vw",
                                                "text-align": "center",
                                            },
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ]
                ),
            ],
        ),
    ]
)


layout = html.Div(
    children=[
        html.H1(children="Service"),
        html.Div(id="current-date"),
        health_check_bar,
        html.Div(id="problem_services", style={"padding-top": "1em"}),
        # intervals
        current_date_interval,
        get_services_interval,
    ]
)
