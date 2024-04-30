from collections import defaultdict
import pandas as pd
from locations import locations
import json
from datetime import datetime, timedelta
import plotly.express as px
import requests
from requests_oauthlib import OAuth1Session, OAuth1
from config import base_url, forms, form_field_id
pd.set_option('display.max_colwidth', None)


pd.set_option('display.max_columns', None)

class DataHandler:
    def __init__(self, consumer_key, client_secret, access_token, account_id):
        self.consumer_key = consumer_key
        self.client_secret = client_secret
        self.access_token = access_token
        self.auth = OAuth1(client_key=consumer_key, client_secret=client_secret)
        self.account_id = account_id

    def get_ad_spending(self, start_date, end_date):
        # Define the endpoint and parameters
        start_date = start_date[:10]
        end_date = end_date[:10]
        # Convert to datetime object
        start_obj = datetime.strptime(start_date, "%Y-%m-%d")
        end_obj = datetime.strptime(end_date, "%Y-%m-%d")
        # Convert to YYYY-MM-DD format
        start_date = start_obj.strftime("%Y-%m-%d")
        end_date = end_obj.strftime("%Y-%m-%d")
        base_url = f"https://graph.facebook.com/v19.0/act_{self.account_id}/insights"
        params = {
            "access_token": self.access_token,
            "level": "adset",
            "fields": "spend,adset_name,campaign_name",
            "time_range": json.dumps({"since": start_date, "until": end_date})
        }

        # Initialize list to store data
        all_data = []
        excluded_keywords = ['Kandidaatwerving', "SDIM", 'Interesses', 'Zorgwerving']
        # Function to fetch a page
        def fetch_page(url, params):
            response = requests.get(url, params=params)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f"Error: {response.status_code} - {response.text}")

        # Fetch first page
        data = fetch_page(base_url, params)
        all_data.extend(data["data"])

        # Handle pagination
        while "paging" in data and "next" in data["paging"]:
            next_url = data["paging"]["next"]
            data = fetch_page(next_url, params=None)  # No params needed as they're included in the URL
            all_data.extend(data["data"])

        # Convert to a DataFrame
        df = pd.DataFrame(all_data)

        # Convert spend column to float if necessary
        df["uitgave"] = df["spend"].astype(float)

        # Define the list of locations
        locaties = list(locations.keys())
        print(locaties)
        # Map ad sets to locations
        def map_location(adset_name, locaties):
            adset_name_lower = adset_name.lower()
            for location in locaties:
                if location.lower() in adset_name_lower:
                    return location
            return None

        df["locatie"] = df["adset_name"].apply(lambda x: map_location(x, locaties))

        # Function to filter out rows with specific keywords

        # Function to filter out rows with specific keywords
        def filter_keywords(adset_name, keywords):
            adset_name_lower = adset_name.lower()
            for keyword in keywords:
                if keyword.lower() in adset_name_lower:
                    return False
            return True

        # Apply keyword filtering

        df_filtered = df[df["adset_name"].apply(lambda x: filter_keywords(x, excluded_keywords))]

        # Filter rows with no location match
        df_filtered = df_filtered[df_filtered["locatie"].notna()]
        df_campaign = df_filtered.groupby(["adset_name"])["campaign_name"].first().reset_index()
        campaign_dict = dict(zip(df_campaign["adset_name"], df_campaign["campaign_name"]))
        # Aggregate by ad set name to avoid duplicates
        df_agg = df_filtered.groupby(["locatie", "adset_name"])["uitgave"].sum().reset_index()
        df_merged = pd.merge(df_agg, df_campaign, on="adset_name", how="left")

        # Create a bar chart
        # Create a bar chart
        fig = px.bar(df_merged, x="locatie", y="uitgave", color="adset_name",
                     title="Ad Spending by Location",
                     hover_data={"campaign_name": True, "uitgave": True, "adset_name": False},
                     labels={"locatie": "Location", "uitgave": "Spending", "adset_name": "Ad Set"})

        # Update hover template to include ad set name, campaign name, and spending
        fig.update_traces(
            hovertemplate="Advertentie: %{customdata[1]}<br>Campagne: %{customdata[0]}<br>Uitgave: €%{y}")

        return fig

    def get_entries_per_location(self, form_name, selected_location):
        url = f'{base_url}/forms/{forms[form_name]}/entries'

        params = {
            'paging[page_size]': 2000,
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
        reversed_keys = list(monthly_counts_dict.keys())[::-1]
        reversed_values = [monthly_counts_dict[key] for key in reversed_keys]

        return px.bar(x=reversed_keys, y=reversed_values,
                      title=f"Inzendingen per maand voor {locations[selected_location]} - {form_name}")

    def get_entries(self, form_name, start_date, end_date):

        url = f'{base_url}/forms/{forms[form_name]}/entries'
        print(form_name)
        params = {
            'paging[page_size]': 2000,
        }
        response = requests.get(url, auth=self.auth, params=params)

        entries = response.json()

        locations = []

        location_sources = {}
        color_map = {
            'Facebook': '#3b5998',  # Facebook blue
            'Instagram': '#e4405f',  # Instagram pink
            'LinkedIn': '#0077b5',  # LinkedIn blue
            'Google': '#FFD700',  # Google blue
            'Via de lokale of regionale kranten of media': '#C9FFB2',  # Google red
            'Via kennissen/vrienden/familie': '#55acee',  # Twitter blue
            'Anders': 'black'
        }

        for entry in entries['entries']:

            if start_date <= entry['date_created'] <= end_date:
                id = str(form_field_id[form_name])
                location = entry[id]
                locations.append(location)

                source = entry['14']
                if form_name == "Klantaanmeldingen":
                    source = entry['16']

                # Bronnen verzamelen als anders
                if source not in color_map:
                    source = "Anders"

                if location not in location_sources:
                    location_sources[location] = {}

                location_sources[location][source] = location_sources[location].get(source, 0) + 1

        long_data = [{'Locatie': location, 'Bron': source, 'Aantal': count}
                     for location, sources in location_sources.items()
                     for source, count in sources.items()]

        fig = px.bar(long_data, x="Locatie", y="Aantal", color="Bron", barmode='stack',
                     hover_data=['Locatie', 'Aantal', 'Bron'], color_discrete_map=color_map, title="Per vestiging")

        # Compute the total count for each location
        location_totals = {}
        for item in long_data:
            location_totals[item['Locatie']] = location_totals.get(item['Locatie'], 0) + item['Aantal']

        # Add text annotations to the top of each bar
        for location, total_count in location_totals.items():
            fig.add_annotation(x=location, y=total_count * 1.14, text=str(total_count),
                               showarrow=False, font=dict(size=13))

        return fig

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
        if df.empty:
            bar = px.bar(title="Inzendingen per maand voor bijeenkomst")
            return df, df, bar

        print(df)
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

        # balk grafiek
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
        reversed_keys = list(monthly_counts_dict.keys())[::-1]
        reversed_values = [monthly_counts_dict[key] for key in reversed_keys]
        print(df)
        print(df2)
        bar = px.bar(x=reversed_keys, y=reversed_values,
                     title=f"Inzendingen per maand voor bijeenkomst")

        return df, df2, bar

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
