import requests


def fetch_ng_gas_data(dataset_url):
    """
    Fetch gas transmission data from National Grid's open data portal.

    :param dataset_url: The specific resource URL or endpoint
    :return: data in JSON or CSV (depending on endpoint)
    """
    resp = requests.get(dataset_url)
    resp.raise_for_status()
    # If it's CSV, return resp.text; otherwise convert to JSON
    return resp.text
