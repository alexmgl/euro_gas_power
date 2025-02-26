import requests
import time
import pandas as pd
from src.credentials import gie_api_key


class GIE:
    """
    A client for interacting with Gas Infrastructure Europe (GIE) APIs, namely:
    - Aggregated Gas Storage Inventory (AGSI)
    - Aggregated LNG Storage Inventory (ALSI)

    GIE also serves as an Inside Information Platform (IIP) for Urgent Market Messaging (UMM).
    """

    # Separate endpoints for AGSI and ALSI based on documentation
    agsi_url = "https://agsi.gie.eu/api"
    alsi_url = "https://alsi.gie.eu/api"

    # Endpoint for urgent market messages
    umm_url = "https://iip.gie.eu/api/umm"

    # EIC urls
    eic_listing_url = "https://agsi.gie.eu/api/about?show=listing"
    eic_table_url = "https://agsi.gie.eu/api/about?show=table"

    def __init__(self, api_key=None):
        """
        Initialise the GIE client.

        :param api_key: Optional GIE API key. If not provided, it will default to 'gie_api_key' from src.credentials.
        """
        self.api_key = api_key or gie_api_key
        self._instantiate_session()
        self._load_eic_listing()

    def _instantiate_session(self):
        self.session = requests.Session()
        self.session.headers.update({"x-key": self.api_key})

    def _get_with_rate_limiting(self, url, params=None):
        """
        Helper method to handle rate limiting (HTTP 429) by retrying after a delay.
        """
        while True:
            response = self.session.get(url, params=params)
            if response.status_code == 429:
                time.sleep(60)
                continue
            response.raise_for_status()
            return response

    def _load_eic_listing(self):
        response = self._get_with_rate_limiting(self.eic_listing_url)
        self.eic_listing = response.json()
        return self.eic_listing

    def fetch_agsi_data(self, country_code, date_from, date_to, page=1, size=300, all_pages=False):
        """
        Fetch daily gas storage data from AGSI for a specified country and date range.

        :param country_code: e.g. "GB"
        :param date_from: "YYYY-MM-DD"
        :param date_to:   "YYYY-MM-DD"
        :param page: Starting page number (default: 1)
        :param size: Number of records per page (default: 300, max: 300)
        :param all_pages: If True, fetch all pages and combine results.
        :return: JSON response parsed into a Python dict.
        """
        params = {
            "country": country_code,
            "from": date_from,
            "to": date_to,
            "page": page,
            "size": size
        }
        response = self._get_with_rate_limiting(self.agsi_url, params=params)
        data = response.json()

        if all_pages:
            all_data = data.get("data", [])
            last_page = data.get("last_page", page)
            current_page = page
            while current_page < last_page:
                current_page += 1
                params["page"] = current_page
                resp = self._get_with_rate_limiting(self.agsi_url, params=params)
                page_data = resp.json()
                all_data.extend(page_data.get("data", []))
            data["data"] = all_data
        return data

    def fetch_alsi_data(self, country_code, date_from, date_to, page=1, size=300, all_pages=False):
        """
        Fetch daily LNG storage data from ALSI for a specified country and date range.

        :param country_code: e.g. "FR"
        :param date_from: "YYYY-MM-DD"
        :param date_to:   "YYYY-MM-DD"
        :param page: Starting page number (default: 1)
        :param size: Number of records per page (default: 300, max: 300)
        :param all_pages: If True, fetch all pages and combine results.
        :return: JSON response parsed into a Python dict.
        """
        params = {
            "country": country_code,
            "from": date_from,
            "to": date_to,
            "page": page,
            "size": size
        }
        response = self._get_with_rate_limiting(self.alsi_url, params=params)
        data = response.json()

        if all_pages:
            all_data = data.get("data", [])
            last_page = data.get("last_page", page)
            current_page = page
            while current_page < last_page:
                current_page += 1
                params["page"] = current_page
                resp = self._get_with_rate_limiting(self.alsi_url, params=params)
                page_data = resp.json()
                all_data.extend(page_data.get("data", []))
            data["data"] = all_data
        return data

    def fetch_urgent_market_messages(self, page=1, size=300, all_pages=False):
        """
        Fetch urgent market messages from the GIE IIP endpoint with optional pagination.

        :param page: Starting page number (default: 1)
        :param size: Number of records per page (default: 300)
        :param all_pages: If True, fetch all pages and combine results.
        :return: JSON response parsed into a Python dict.
        """
        params = {
            "page": page,
            "size": size
        }
        response = self._get_with_rate_limiting(self.umm_url, params=params)
        data = response.json()

        if all_pages:
            all_data = data.get("data", [])
            last_page = data.get("last_page", page)
            current_page = page
            while current_page < last_page:
                current_page += 1
                params["page"] = current_page
                resp = self._get_with_rate_limiting(self.umm_url, params=params)
                page_data = resp.json()
                all_data.extend(page_data.get("data", []))
            data["data"] = all_data

        return data

    def group_eic_listing_by_country(self):
        """
        Group the EIC listing facilities by country.

        :return: A dictionary {country_code: [list_of_facility_dicts]}.
        """
        grouped = {}
        for fac in self.eic_listing:
            country_code = fac.get("country")
            if country_code not in grouped:
                grouped[country_code] = []
            grouped[country_code].append(fac)
        return grouped

    def group_eic_listing_by_type(self, facility_type):
        """
        Filter the EIC listing by the specified facility type (e.g. "DSR", "SSO", "ASF", etc.).

        :param facility_type: Facility type string.
        :return: A filtered list of facility dicts.
        """
        return [fac for fac in self.eic_listing if fac.get("type") == facility_type]

    def group_eic_listing_by_eic_code(self, eic_code):
        """
        Filter the EIC listing by the specified EIC code.

        :param eic_code: EIC code string.
        :return: A filtered list of facility dicts matching the EIC code.
        """
        return [fac for fac in self.eic_listing if fac.get("eic") == eic_code]

    def get_unique_countries(self):
        """
        Get a set of unique country codes from the EIC listing.
        """
        return {fac.get("country") for fac in self.eic_listing if fac.get("country")}

    def get_unique_types(self):
        """
        Get a set of unique facility types from the EIC listing.
        """
        return {fac.get("type") for fac in self.eic_listing if fac.get("type")}

    def convert_eic_to_dataframe(self):
        """
        Convert the EIC listing into a pandas DataFrame.
        """
        return pd.json_normalize(self.eic_listing)


if __name__ == '__main__':

    # EXAMPLE USAGE
    gie_client = GIE("decd58bbd95344e7639f1634c6b93141")

    types = gie_client.get_unique_types()
    print("Unique Types:", types)

    countries = gie_client.get_unique_countries()
    print("Unique Countries:", countries)

    # Fetch AGSI data (with pagination support)
    agsi_data = gie_client.fetch_agsi_data(
        country_code='DE',
        date_from='2025-01-01',
        date_to='2025-01-02',
        all_pages=True
    )
    df_agsi = pd.json_normalize(agsi_data.get('data', []))

    # Optionally, fetch ALSI data similarly
    alsi_data = gie_client.fetch_alsi_data(
        country_code='FR',
        date_from='2024-01-01',
        date_to='2024-01-02',
        all_pages=True
    )
    df_alsi = pd.json_normalize(alsi_data.get('data', []))
    print("ALSI Data (first few rows):")
    print(df_alsi.head())

    market_messages = gie_client.fetch_urgent_market_messages(size=10)
    df = pd.json_normalize(market_messages['data'])
    print(df.head())
