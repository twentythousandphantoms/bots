from datetime import datetime, timedelta, timezone
import http
import os
import http.client
import json
import logging
import importlib

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

# 200 km around Kusadasi
a_latitude = 37.222
b_latitude = 38.518
a_longitude = 26.5988
b_longitude = 27.8612

# 1000 km around Kusadasi
a_latitude = 35.922
b_latitude = 39.818
a_longitude = 24.9988
b_longitude = 30.6612

# 5000 km around Kusadasi
a_latitude = 31.922
b_latitude = 43.818
a_longitude = 19.9988
b_longitude = 35.6612

# 10000 km around Kusadasi
a_latitude = 27.922
b_latitude = 47.818
a_longitude = 15.9988
b_longitude = 39.6612

# 30000 km around Kusadasi (for testing)
a_latitude = 22.922
b_latitude = 52.818
a_longitude = 10.9988
b_longitude = 44.6612

TELEGRAM_API_HOST = "api.telegram.org"
# USGS_URL = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"

# setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_updatedafter(minutes=10080):
    # Get current time in UTC format
    now = datetime.utcnow()
    # Subtract 5 minutes from the current time
    updatedafter = now - timedelta(minutes=minutes)
    # Use isoformat() to get the time in the format required by the URL
    updatedafter_str = updatedafter.isoformat()
    return updatedafter_str


USGS_URL = f"https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&updatedafter={get_updatedafter()}"


def utc_to_kusadasi_time(utc_timestamp):
    # Convert timestamp from milliseconds to seconds
    timestamp_seconds = utc_timestamp / 1000
    # Convert timestamp to datetime object in UTC
    date_time_utc = datetime.fromtimestamp(timestamp_seconds, timezone.utc)
    # Create a timezone object for Eastern European Time (EET)
    eet = timezone(timedelta(hours=2))
    # Convert UTC datetime to EET datetime
    date_time_eet = date_time_utc.astimezone(eet)
    # Use strftime to format the datetime object
    formatted_time = date_time_eet.strftime("%d.%m %H:%M")
    return formatted_time


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
    if 'dyfi' in data['properties']['products']:
        for content in data['properties']['products']['dyfi'][0]['contents']:
            if content == img_name:
                url = data['properties']['products']['dyfi'][0]['contents'][content]["url"]
                return url
    else:
        return data['properties']['url']
    return None


def start():
    # Create client connection with Telegram API
    conn = http.client.HTTPSConnection(TELEGRAM_API_HOST)

    # Check that token is not empty
    if TELEGRAM_TOKEN is not None and CHAT_ID is not None:

        place, url, when, mag = fetch_and_parse_usgs_summary_url()
        if not url:
            return

        if url.endswith(".jpg"):
            endpoint = f"/bot{TELEGRAM_TOKEN}/sendPhoto"
            payload = {
                'chat_id': CHAT_ID,
                'photo': url,
                'caption': f'{when}: Mag {mag} Place: {place}'
            }
            logger.info(f'endpoint: {endpoint}')
            logger.info(f'payload (image): {payload}')
            headers = {'content-type': "application/json"}
            conn.request("POST", endpoint, json.dumps(payload), headers)
        else:
            endpoint = f"/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                'chat_id': CHAT_ID,
                'text': f'{when}: Mag {mag} Place: {place}. Details: {url}'
            }
            logger.info(f'endpoint: {endpoint}')
            logger.info(f'payload: {payload}')
            headers = {'content-type': "application/json"}
            conn.request("POST", endpoint, json.dumps(payload), headers)
        # Get the request response and save it
        res = conn.getresponse()

        res = {
            'response': res.read().decode(),
            'statusCode': res.status,
            'body': json.dumps('Lambda executed.')
        }
        logger.info(res)
        return res
    else:
        raise EnvironmentError("Missing TELEGRAM_TOKEN or CHAT_ID env variable!")

start()
