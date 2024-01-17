from dash import dash_table
from datetime import datetime, timedelta
from layout import app_layout
import pandas as pd
from dash.exceptions import PreventUpdate
from dash_extensions.enrich import html, dcc
from config import KEY, SECRET, form_name
from data_handler import DataHandler
from utils import get_info_data

data = DataHandler(KEY, SECRET)
infobijeenkomst_form, info_name = get_info_data()

start_date_one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
end_date_today = datetime.today().strftime('%Y-%m-%d')
fig = data.get_entries("Brochure wonen", start_date_one_week_ago, end_date_today)
app = app_layout(fig, form_name, info_name)


def update_graph(value, selected_location, info_bijeenkomst, start_date, end_date):
    header_text = "Formulieren Dashboard"
    if selected_location:
        header_text = selected_location
        # If a location is selected, display a chart for that location
        px = data.get_entries_per_location(value, selected_location)
        px.update_layout(
            yaxis=dict(categoryorder='total descending'),
            title_x=0.5,
            xaxis_title='Date',
            yaxis_title='Occurrences',
            plot_bgcolor='#ecf0f1',
            paper_bgcolor='#ecf0f1'
        )
        px.update_traces(marker_color='#c4336d', hovertemplate='%{x}: %{y}')
    else:
        # If no location is selected, display a bar chart

        px = data.get_entries(value, start_date, end_date)

        px.update_layout(
            title_text=f'{value}',
            title_x=0.5,  # Center the chart title
            xaxis_title='Vestigingen',
            yaxis_title='Aantal',
            showlegend=False,  # Hide legend
            plot_bgcolor='#ecf0f1',  # Set plot background color
            paper_bgcolor='#ecf0f1',  # Set paper background color
            xaxis=dict(categoryorder='total descending')
        )
        px.update_traces(marker_color='#c4336d', hovertemplate='%{x}: %{y}')  # Set bar color
    if info_bijeenkomst:
        header_text = info_bijeenkomst
        df, df2 = data.get_infobijeenkomst(infobijeenkomst_form[info_bijeenkomst])
        return [html.Button(
            "Export naar Excel",
            id="excel-button",
            style={'margin-top': '10px'},
            className="export-button",
        ),
            dcc.Download(id="download"),
            html.Hr(),
            dash_table.DataTable(
                id='table',
                columns=[{'name': col, 'id': col} for col in df.columns],
                style_cell={'textAlign': 'left'},
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                style_table={'borderCollapse': 'collapse', 'overflowX': 'auto'},
                style_data={'whiteSpace': 'normal',
                            'height': 'auto'},
                style_cell_conditional=[
                    {
                        'if': {'column_id': c},
                        'border': '1px solid black',
                    } for c in df.columns
                ],

                data=df.to_dict('records')
            ),

        ], header_text

    return [dcc.Graph(id='graph1', figure=px)], header_text


def download_excel(n_clicks, info_bijeenkomst):
    if n_clicks is None or info_bijeenkomst is None:
        raise PreventUpdate

    # Assuming df is your DataFrame
    df, df2 = data.get_infobijeenkomst(infobijeenkomst_form[info_bijeenkomst])

    # Create an ExcelWriter object
    excel_writer = pd.ExcelWriter(info_bijeenkomst + ".xlsx", engine='xlsxwriter')

    # Write the DataFrame to Excel using ExcelWriter
    df.to_excel(excel_writer, index=False, sheet_name="Totaallijst" )
    df2.to_excel(excel_writer, index=False, sheet_name="Presentielijst")
    totaal_sheet = excel_writer.sheets["Totaallijst"]
    # Adjusting column width
    for column in df:
        column_length = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        totaal_sheet.set_column(col_idx, col_idx, column_length)

    presentie_sheet = excel_writer.sheets["Presentielijst"]
    for column in df2:
        column_length = max(df2[column].astype(str).map(len).max(), len(column))
        col_idx = df2.columns.get_loc(column)
        presentie_sheet.set_column(col_idx, col_idx, column_length)
    # Get the dimensions of the DataFrame
    num_rows, num_cols = df.shape

    # Create an Excel table
    totaal_sheet.add_table(0, 0, num_rows, num_cols - 1, {'columns': [{'header': col} for col in df.columns]})

    num_rows, num_cols = df2.shape
    presentie_sheet.add_table(0, 0, num_rows, num_cols - 1, {'columns': [{'header': col} for col in df.columns]})
    excel_writer.close()

    return dcc.send_file(info_bijeenkomst + ".xlsx")
