
from datetime import datetime, timedelta
from layout import app_layout
from dash_bootstrap_templates import load_figure_template
from dash_extensions.enrich import Output, Input
from callbacks import update_graph, download_excel
from config import KEY, SECRET, form_name
from data_handler import DataHandler
from utils import get_info_data

load_figure_template('LUX')

# TODO: Facebook ads api koppelen met gekozen vestiging
# TODO: Informatiebijeenkomst toevoegen als balkgrafiek aan algemene formulier
# TODO: Voor later misschien een zoekfunctie naar naam/email? Aan ellis vragen
# TODO: Activecampaign API Campagne grafieken


data = DataHandler(KEY, SECRET)
infobijeenkomst_form, info_name = get_info_data()

start_date_one_week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
end_date_today = datetime.today().strftime('%Y-%m-%d')
fig = data.get_entries("Brochure wonen", start_date_one_week_ago, end_date_today)
app = app_layout(fig, form_name, info_name)
test = data.get_info_forms()

app.callback(
    Output('graph-container', 'children'),
    Output('header-text', 'children'),
    Input('one', 'value'),
    Input('three', 'value'),
    Input('info_bijeenkomst', 'value'),
    Input('date_picker', 'start_date'),
    Input('date_picker', 'end_date')
)(update_graph)

app.callback(
    Output("download", "data"),
    Input("excel-button", "n_clicks"),
    Input('info_bijeenkomst', 'value'),
    prevent_initial_call=True
)(download_excel)

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
