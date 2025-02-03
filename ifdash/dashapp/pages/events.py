import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/events")

current_date_interval = dcc.Interval(
    id="current-date-interval",
    interval=1000,  # in milliseconds
    n_intervals=0,
)

get_events_interval = dcc.Interval(
    id="get-events-interval",
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
                                    [html.I(className="bi bi-heart-pulse-fill"), " UP"]
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="event_state_up",
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
                                    [html.I(className="bi bi-heartbreak-fill"), " DOWN"]
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="event_state_down",
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
                                        " UNREACH",
                                    ]
                                ),
                                dbc.CardBody(
                                    [
                                        html.Div(
                                            id="event_state_unreach",
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
                                            id="total_event",
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
        html.H1(children="This is our Home page"),
        html.Div(
            children="""
        This is our Home page content.
    """
        ),
        html.Div(id="current-date"),
        health_check_bar,
        html.Div(id="problem_events", style={"padding-top": "1em"}),
        # intervals
        current_date_interval,
        get_events_interval,
    ]
)
