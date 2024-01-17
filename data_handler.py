from collections import defaultdict
import pandas as pd
from locations import locations
import json
from datetime import datetime, timedelta
import plotly.express as px
import requests
from requests_oauthlib import OAuth1Session, OAuth1
from config import base_url, forms, form_field_id


class DataHandler:
    def __init__(self, consumer_key, client_secret):
        self.consumer_key = consumer_key
        self.client_secret = client_secret
        self.auth = OAuth1(client_key=consumer_key, client_secret=client_secret)

    def get_entries_per_location(self, form_name, selected_location):
        url = f'{base_url}/forms/{forms[form_name]}/entries'

        params = {
            'paging[page_size]': 500,
            'search': json.dumps({
                "field_filters": [
                    {"key": form_field_id[form_name], "value": locations[selected_location], "operator": "contains"}
                ]
            }),
        }

        response = requests.get(url, auth=self.auth, params=params)

        entries = response.json()
        # Count occurrences in each month
        monthly_counts = defaultdict(int)

        for request in entries['entries']:
            date_str = request['date_created']
            # Convert string to datetime object
            date_obj = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            # Format month as full month name
            month_name = date_obj.strftime('%B')
            # Extract year
            year = date_obj.strftime('%Y')
            # Combine month and year
            month_year = f'{month_name} {year}'
            # Increment count for the corresponding month
            monthly_counts[month_year] += 1

        # Create a dictionary with month names as keys and occurrences as values
        monthly_counts_dict = dict(monthly_counts)

        return px.bar(x=monthly_counts_dict.keys(), y=monthly_counts_dict.values(),
                      title=f"Inzendingen per maand voor {locations[selected_location]} - {form_name}")

    def get_entries(self, form_name, start_date, end_date):

        url = f'{base_url}/forms/{forms[form_name]}/entries'

        params = {
            'paging[page_size]': 500,
        }
        response = requests.get(url, auth=self.auth, params=params)

        entries = response.json()

        locations = []
        location_count = {}

        for entry in entries['entries']:

            if start_date <= entry['date_created'] <= end_date:
                id = str(form_field_id[form_name])
                locations.append(entry[id])

        for location in locations:
            location_count[location] = location_count.get(location, 0) + 1

        locations = list(location_count.keys())

        occurences = list(location_count.values())

        return px.bar(x=locations, y=occurences, title="Per vestiging")

    def get_infobijeenkomst(self, form_id):
        url = f'{base_url}/forms/{form_id}/entries'

        params = {
            'paging[page_size]': 50,
        }
        response = requests.get(url, auth=self.auth, params=params)
        entries = response.json()
        print(entries)
        data = entries['entries']
        df = pd.DataFrame(data)

        keep_columns = ['1', '2', '5', '17', '9', '8', '6']
        presentielijst = ['1']
        df2 = df[presentielijst]

        df = df[keep_columns]

        column_name_mapping = {
            '1': 'Naam',
            '2': 'Email',
            '5': 'Ik heb interesse in het Gastenhuis:',
            '17': 'Met hoeveel personen komt u?',
            '9': 'Waar zag of hoorde u over Het Gastenhuis?',
            '8': 'Telefoonnummer',
            '6': 'Eventuele toelichting'
            # Add more columns as needed
        }

        df.rename(columns=column_name_mapping, inplace=True)
        df2.rename(columns={'1': 'Naam'}, inplace=True)

        df.insert(0, 'Aantal', range(1, len(df) + 1))
        df2.insert(0, 'Aantal', range(1, len(df2) + 1))
        return df, df2

    def get_info_forms(self):
        url = f'{base_url}/forms/'

        params = {
            'paging[page_size]': 40,
        }
        response = requests.get(url, auth=self.auth, params=params)
        entries = response.json()

        # filter all informatiebijeenkomsten from forms
        filtered_data = {entry['title']: entry['id'] for entry_id, entry in entries.items() if
                         'informatiebijeenkomst' in entry['title'].lower()}

        return filtered_data
