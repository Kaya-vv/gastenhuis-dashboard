import dash_auth
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from datetime import date, datetime, timedelta
import dash
from locations import locations

start_date_one_week_ago = datetime.now() - timedelta(days=7)
def app_layout(fig, form_name, info_bijeenkomst):
    # SiDEBAR
    location_names = list(locations.keys())
    SIDEBAR_STYLE = {
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "max-width": '27%',
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
        "zIndex": 999,
        'overflowY': 'auto'
    }

    sidebar = html.Div(
        [
            html.H2("Formulieren"),
            html.Hr(),
            html.P(
                "Algemene formulieren", className="lead"
            ),
            dbc.Nav(
                [
                    dcc.Dropdown(form_name, 'Brochure wonen', id='one'),
                    html.Br(),
                    dcc.DatePickerRange(
                        month_format='MMMM Y',
                        end_date_placeholder_text='MMMM Y',
                        start_date=start_date_one_week_ago,
                        end_date=datetime.today(),
                        id='date_picker',
                        display_format='DD/MM/YYYY'
                    )
                ],
                vertical=True,
                pills=True,
            ),
            html.Hr(),
            html.P(
                "Per vestiging", className="lead"
            ),
            dbc.Nav(
                [
                    dcc.Dropdown(location_names, '', id='three')

                ],
                vertical=True,
                pills=True,
            ),
            html.Hr(),
            html.P(
                "Informatiebijeenkomsten", className="lead"
            ),
            dbc.Nav(
                [
                    dcc.Dropdown(info_bijeenkomst, '', id='info_bijeenkomst')

                ],
                vertical=True,
                pills=True,
            ),
        ],
        style=SIDEBAR_STYLE,
    )

    # Initialize Dash app

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX, 'assets/styles.css'], suppress_callback_exceptions=True)

    app.layout = html.Div(style={'overflowY': 'auto', 'display': 'flex', 'height': '100vh'}, children=[
        html.Div(sidebar, style={'flex': '0 0 25%', 'background': '#f8f9fa', 'padding': '25px'}),
        html.Div(style={'display': 'flex', 'flexDirection': 'column', 'flex': '1', 'padding': '10px'}, children=[
            html.H1('Formulieren dashboard', id="header-text", style={'margin-top': '7px', 'margin-left': '15px'}),
            html.Div(id='graph-container', style={'margin-top': '7px', 'margin-left': '15px'}),
        ]),
    ])

    return app
