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
                        "Campus",
                        href="/dashboard/campuses",
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
                        "Hat Yai WiFi Network",
                        href="/dashboard/campuses/hatyai/wifi",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "Hat Yai Campus SLA Month",
                        href="/dashboard/slas/months/hatyai",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "PSU Web",
                        href="/dashboard/slas/months/psu-web",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "PSU Service",
                        href="/dashboard/slas/months/psu-service",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "Host",
                        href="/dashboard/hosts",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "Service",
                        href="/dashboard/services",
                        external_link=True,
                    ),
                    dbc.NavLink(
                        "Event",
                        href="/dashboard/events",
                        external_link=True,
                    ),
                ]
            )
        ]
    )
