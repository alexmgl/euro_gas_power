import requests

# todo - split this for OCGT / CCGT UK demand 

class ElexonClient:

    ELEXON_URL = 'https://api.bmreports.com/BMRS'

    def __init__():

        pass

def fetch_bmrs_data(service, service_type='json', api_key=BMRS_API_KEY):
    """
    Retrieve data from Elexon BMRS for a given service code.

    :param service: e.g. "B1620" (Generation by Fuel Type)
    :param service_type: 'xml' or 'json'
    :param api_key: Elexon BMRS API key
    :return: JSON or XML response
    """
    base_url = "https://api.bmreports.com/BMRS"
    url = f"{base_url}/{service}"
    params = {
        "APIKey": api_key,
        "ServiceType": service_type
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    if service_type == 'json':
        return resp.json()
    return resp.text


if __name__ == "__main__":
    pass
