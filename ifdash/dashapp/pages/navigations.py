from dash import html
import dash_bootstrap_components as dbc


def render_simple_menu():
    return html.Div(
        [
            dbc.Nav(
                [
                    dbc.NavLink(
                        "Overview",
                        href="/dashboard",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "Web",
                        href="/dashboard/slas/months/web",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "Campus SLA Month",
                        href="/dashboard/slas/months/campuses",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "Hat Yai Line Network",
                        href="/dashboard/campuses/hatyai/line",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "Hat Yai Campus SLA Month",
                        href="/dashboard/slas/months/hatyai",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "PSU Service",
                        href="/dashboard/slas/months/service",
                        external_link=True,
                    ),
                ]
            )
        ]
    )
