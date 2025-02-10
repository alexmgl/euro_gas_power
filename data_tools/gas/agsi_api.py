import requests
from mydatatools.config.settings_example import AGSI_API_TOKEN

def fetch_agsi_data(country_code, date_from, date_to, api_token=AGSI_API_TOKEN):
    """
    Fetch daily gas storage data from AGSI+ for a specified country and date range.

    :param country_code: e.g. "GB"
    :param date_from: "YYYY-MM-DD"
    :param date_to:   "YYYY-MM-DD"
    :param api_token: AGSI+ API token
    :return: dict or list of data objects
    """
    base_url = "https://agsi.gie.eu/api"
    params = {
        "country": country_code,
        "from": date_from,
        "to": date_to
    }
    headers = {
        "x-key": api_token
    }
    resp = requests.get(base_url, headers=headers, params=params)
    resp.raise_for_status()
    return resp.json()
