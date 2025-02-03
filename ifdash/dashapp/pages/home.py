import dash
from dash import html, dcc

import dash_bootstrap_components as dbc

from . import sla_layouts
from . import navigations

dash.register_page(__name__, path="")

current_date_interval = dcc.Interval(
    id="current-date-interval",
    interval=1000,  # in milliseconds
    n_intervals=0,
)

get_sla_interval = dcc.Interval(
    id="get-sla-interval",
    interval=60 * 1000,  # in milliseconds
    n_intervals=0,
)


def layout():
    dom = html.Div(
        children=[
            html.H1(children=["PSU ", html.Span(id="current-date")]),
            sla_layouts.render_layout("Current"),
            navigations.render_simple_menu(),
            dcc.Store(id="current-sla-memory"),
            current_date_interval,
            get_sla_interval,
        ]
    )

    return dom
