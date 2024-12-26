import datetime
import requests
import json
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import pycountry

def fetch_all_events(base_url):
    events = []
    page = 1
    while True:
        url_parts = list(urlparse(base_url))
        query = parse_qs(url_parts[4])
        query.update({'page': page})
        url_parts[4] = urlencode(query, doseq=True)
        url_with_page = urlunparse(url_parts)

        response = requests.get(url_with_page)
        data = response.json()
        events.extend(data['list'])
        if 'next' not in data or not data['next']:
            break
        page += 1
    return events

def save_events_to_file(events, filename):
    with open(filename, 'w') as f:
        json.dump({'timestamp': datetime.datetime.now().timestamp(), 'events': events}, f)

def load_events_from_file(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
        return data['timestamp'], data['events']

def get_events(base_url, cache_file='events_cache.json'):
    if os.path.exists(cache_file):
        timestamp, events = load_events_from_file(cache_file)
        if datetime.datetime.now().timestamp() - timestamp < 86400:  # 24 hours in seconds
            return events

    events = fetch_all_events(base_url)
    save_events_to_file(events, cache_file)
    return events

# Base URL for the API
base_url = "https://www.drupal.org/api-d7/node.json?type=event"

# Fetch all events
events = get_events(base_url)

# Get the current year
current_year = datetime.datetime.now().year

# Initialize counters
events_this_year = 0
event_type_summary = {}
total_events = 0  # Counter for total events
country_summary = {}  # Counter for events by country

# Process events
for event in events:
    total_events += 1  # Increment the counter
    created = event['created']
    if created.isdigit():  # Check if the created field is a timestamp
        created_year = datetime.datetime.fromtimestamp(int(created)).year
    else:
        created_year = datetime.datetime.strptime(created, '%Y-%m-%dT%H:%M:%S%z').year

    if created_year == current_year:
        events_this_year += 1
        event_types = event['field_event_type']
        if isinstance(event_types, list):
            for event_type in event_types:
                if event_type not in event_type_summary:
                    event_type_summary[event_type] = 0
                event_type_summary[event_type] += 1
        else:
            if event_types not in event_type_summary:
                event_type_summary[event_types] = 0
            event_type_summary[event_types] += 1

        # Group by country
        addresses = event['field_event_address']
        if isinstance(addresses, list):
            for address in addresses:
                country_code = address['country']
                country = pycountry.countries.get(alpha_2=country_code).name if pycountry.countries.get(alpha_2=country_code) else 'Unknown'
                if country not in country_summary:
                    country_summary[country] = 0
                country_summary[country] += 1
        else:
            country_code = addresses['country']
            country = pycountry.countries.get(alpha_2=country_code).name if pycountry.countries.get(alpha_2=country_code) else 'Unknown'
            if country not in country_summary:
                country_summary[country] = 0
            country_summary[country] += 1

# Output results
print(f"Total number of events processed: {total_events}")
print(f"Number of events created this year: {events_this_year}")

# Sort event type summary by count
sorted_type_summary = sorted(event_type_summary.items(), key=lambda item: item[1], reverse=True)

print("Summary of items grouped by field_event_type:")
for event_type, count in sorted_type_summary:
    print(f"{event_type}: {count}")

# Sort country summary by count
sorted_country_summary = sorted(country_summary.items(), key=lambda item: item[1], reverse=True)

print("Summary of events grouped by country (sorted by count):")
for country, count in sorted_country_summary:
    print(f"{country}: {count}")
