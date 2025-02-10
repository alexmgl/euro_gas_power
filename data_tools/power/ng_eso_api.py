import requests


def fetch_eso_data(dataset_slug, resource_id):
    """
    Fetch electricity data from National Grid ESO's data portal.

    :param dataset_slug: e.g. "demand-data"
    :param resource_id: the specific resource identifier for the dataset
    :return: CSV data or JSON, depending on the endpoint
    """
    base_url = "https://data.nationalgrideso.com"
    api_url = f"{base_url}/{dataset_slug}/resource/{resource_id}/download"
    resp = requests.get(api_url)
    resp.raise_for_status()
    return resp.text
