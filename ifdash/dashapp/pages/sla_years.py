import dash
from dash import html, dcc

import dash_bootstrap_components as dbc

from . import sla_layouts
import datetime

dash.register_page(__name__, path_template="/slas/years")


def layout():
    dom = html.Div(
        children=[
            html.H1(children=["PSU "]),
            # dbc.Row(
            #     children=[
            #         dbc.Col(
            #             children=[
            #                 dcc.DatePickerRange(
            #                     id="sla-date-range",
            #                     min_date_allowed=initial_date,
            #                     # max_date_allowed=date(2017, 9, 19),
            #                     initial_visible_month=started_date,
            #                     start_date=started_date,
            #                     end_date=ended_date,
            #                 ),
            #             ]
            #         )
            #     ]
            # ),
            # # sla_layouts.render_layout("Search"),
            # dcc.Store(id="search-sla-memory", storage_type="local"),
        ]
    )

    return dom
