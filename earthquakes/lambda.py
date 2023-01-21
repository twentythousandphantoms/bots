import importlib
from datetime import datetime, timedelta, timezone
import http
import os
import http.client
import json
import time
import logging

module_name = 'config'

try:
    # Try to import the module
    config = importlib.import_module(module_name)
    TELEGRAM_TOKEN = config.TELEGRAM_TOKEN
    CHAT_ID = config.CHAT_ID
    print(f"Variables imported from module {module_name}.")

except ImportError:
    # Handle the ImportError exception if the module is not found
    print(f"Module {module_name} not found. Importing variables from environment.")
    try:
        TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
        CHAT_ID = os.getenv('CHAT_ID')
    except KeyError:
        print(f"Environment variables TELEGRAM_TOKEN and CHAT_ID not found.")

except AttributeError:
    # Handle the AttributeError exception if the specific variables are not found in the module
    print(f"Variables TELEGRAM_TOKEN and CHAT_ID not found in module {module_name}. Importing variables from "
          f"environment.")
    try:
        TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
        CHAT_ID = os.getenv('CHAT_ID')
    except KeyError:
        print(f"Environment variables TELEGRAM_TOKEN and CHAT_ID not found.")


# 50 km around Kusadasi
a_latitude = 37.422
b_latitude = 38.318
a_longitude = 26.8988
b_longitude = 27.6612

TELEGRAM_API_HOST = "api.telegram.org"
# USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"

# setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_updatedafter():
    # Get current time in UTC format
    now = datetime.utcnow()
    # Subtract 5 minutes from the current time
    updatedafter = now - timedelta(minutes=5)
    # Use isoformat() to get the time in the format required by the URL
    updatedafter_str = updatedafter.isoformat()
    return updatedafter_str


def utc_to_kusadasi_time(utc_timestamp):
    # Convert timestamp to datetime object in UTC
    date_time_utc = datetime.fromtimestamp(utc_timestamp, timezone.utc)
    # Create a timezone object for Eastern European Time (EET)
    eet = timezone(timedelta(hours=2))
    # Convert UTC datetime to EET datetime
    date_time_eet = date_time_utc.astimezone(eet)
    # Use strftime to format the datetime object
    formatted_time = date_time_eet.strftime("%d.%m %H:%M")
    return formatted_time


USGS_URL = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&updatedafter={get_updatedafter()}"


def fetch_and_parse_usgs_summary_url():
    # Fetch earthquake data from USGS API
    conn = http.client.HTTPSConnection("earthquake.usgs.gov")
    conn.request("GET", USGS_URL)
    res = conn.getresponse()
    data = json.loads(res.read())
    logger.info(f'URL: {USGS_URL}')
    logger.info(f'Len: {len(data)}')
    # Iterate over the earthquakes
    for feature in data['features']:
        # Get the earthquake coordinates
        latitude = feature['geometry']['coordinates'][1]
        longitude = feature['geometry']['coordinates'][0]
        # Check if the coordinates match the given condition
        if a_latitude < latitude < b_latitude and a_longitude < longitude < b_longitude:
            logger.info(f'Found earthquake in {feature["properties"]["place"]}')
            place = feature['properties']['place']
            mag = feature['properties']['mag']
            jpg_url = fetch_and_parse_usgs_detail_url(detail_url=feature['properties']['detail'])
            timestamp = feature['properties']['time']
            formatted_time = utc_to_kusadasi_time(timestamp)
            return place, jpg_url, formatted_time, mag
    return None, None, None, None


def fetch_and_parse_usgs_detail_url(detail_url):
    # Fetch earthquake data from USGS API
    conn = http.client.HTTPSConnection("earthquake.usgs.gov")
    conn.request("GET", detail_url)
    res = conn.getresponse()
    data = json.loads(res.read())
    logger.info(f'detail_url: {detail_url}')
    logger.info(f'detail_len: {len(data)}')
    ids = data['properties']['ids'].replace(",", "")
    img_name = f'{ids}_ciim.jpg'
    for content in data['properties']['products']['dyfi'][0]['contents']:
        if content == img_name:
            url = data['properties']['products']['dyfi'][0]['contents'][content]["url"]
            return url
    return None


def lambda_handler(_event, _context):
    # Create client connection with Telegram API
    conn = http.client.HTTPSConnection(TELEGRAM_API_HOST)

    # Check that token is not empty
    if TELEGRAM_TOKEN is not None and CHAT_ID is not None:

        endpoint = f"/bot{TELEGRAM_TOKEN}/sendPhoto"

        place, jpg_url, when, mag = fetch_and_parse_usgs_summary_url()
        logger.info(f'when: {when}, mag: {mag}, place: {place}, jpg_url: {jpg_url}')
        if not jpg_url:
            return {
                'statusCode': 400,
                'body': json.dumps('No jpg_url for this earthquake')
            }

        payload = {
            'chat_id': CHAT_ID,
            'photo': jpg_url,
            'caption': f'{when}: Earthquake in Kusadasi ({place}), Mag: {mag}'
        }

        headers = {'content-type': "application/json"}

        # Make a POST request
        conn.request("POST", endpoint, json.dumps(payload), headers)

        # Get the request response and save it
        res = conn.getresponse()

        return {
            'statusCode': res.status,
            'body': json.dumps('Lambda executed.')
        }
    else:
        raise EnvironmentError("Missing TELEGRAM_TOKEN or CHAT_ID env variable!")
