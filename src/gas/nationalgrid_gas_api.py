import logging
from typing import Any, Dict, Optional
from datetime import date, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import os

# Configure logging for the module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# todo - go through the NG website and review endpoints https://data.nationalgas.com/find-gas-data

class NationalGasClient:
    """
    Client to interact with National Gas APIs.
    """

    # Base URLs for various endpoints.
    DATA_BASE_URL: str = "https://data.nationalgas.com/api"
    MIPIWS_URL: str = "https://marketinformation.nationalgas.com/MIPIws-public/public/publicwebservice.asmx"
    ENERGYWATCH_URL: str = "https://energywatch.nationalgas.com/EDP-PublicUI/PublicPI/InstantaneousFlowWebService.asmx"

    def __init__(self, timeout: float = 10.0) -> None:
        """
        Initialise the NationalGasClient with a session configured with retries.

        Args:
            timeout (float): The timeout for API requests in seconds.
        """
        self.session = requests.Session()
        self.timeout = timeout
        self._setup_retries()

        self.D = date.today().strftime("%Y-%m-%d")
        self.D_minus_1 = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    def _setup_retries(self, total_retries: int = 3, backoff_factor: float = 0.3) -> None:
        """
        Set up the session to automatically retry failed requests.

        Args:
            total_retries (int): The maximum number of retries.
            backoff_factor (float): A backoff factor to apply between attempts.
        """
        retry_strategy = Retry(
            total=total_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=backoff_factor,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Internal helper to perform GET requests.

        Args:
            endpoint (str): The API endpoint path (appended to the base URL).
            params (Optional[Dict[str, Any]]): Query parameters for the request.

        Returns:
            Dict[str, Any]: Parsed JSON response.

        Raises:
            requests.RequestException: If the request fails.
        """
        url = f"{self.DATA_BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error("GET request failed for endpoint '%s': %s", endpoint, e)
            raise

    def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Internal helper to perform POST requests.

        Args:
            endpoint (str): The API endpoint path (appended to the base URL).
            payload (Dict[str, Any]): The JSON payload to send.

        Returns:
            Dict[str, Any]: Parsed JSON response.

        Raises:
            requests.RequestException: If the request fails.
        """
        url = f"{self.DATA_BASE_URL}/{endpoint}"
        try:
            response = self.session.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error("POST request failed for endpoint '%s': %s", endpoint, e)
            raise

    def search_everywhere(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Search across all available National Gas data endpoints.

        Args:
            **kwargs: Additional query parameters to include in the GET request.

        Returns:
            Dict[str, Any]: JSON response from the search endpoint.
        """
        endpoint = "search-everywhere"
        return self._get(endpoint, params=kwargs)

    def latest_gas_flows(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Get latest gas flows.

        Args:
            **kwargs: Additional query parameters to include in the GET request.

        Returns:
            Dict[str, Any]: JSON response from the search endpoint.
        """
        endpoint = "latest-gas-flows"
        return self._get(endpoint, params=kwargs)

    def latest_gas_flows_by_terminal(
            self,
            isLastUpdate: bool = True,
            isLastHour: bool = False,
            isLast24Hours: bool = False,
            **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Get the latest gas flows by terminal.

        Args:
            isLastUpdate (bool): Whether to return only the latest update (default: True).
            isLastHour (bool): Whether to return data from only the last hour (default: False).
            isLast24Hours (bool): Whether to return data from only the last 24 hours (default: False).
            **kwargs: Additional query parameters to include in the POST payload.

        Returns:
            Dict[str, Any]: JSON response from the gas flows endpoint.
        """
        endpoint = "gas-flows-by-terminal"
        payload = {
            "isLastUpdate": isLastUpdate,
            "isLastHour": isLastHour,
            "isLast24Hours": isLast24Hours,
        }
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def flow_rates_map(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve flow rates map data.

        Args:
            **kwargs: Additional parameters to include in the POST payload.

        Returns:
            Dict[str, Any]: JSON response containing flow rates map data.
        """
        endpoint = "gas-system-status-data"
        payload = {"request": "flowRatesMap"}
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def gas_balancing_notification(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve gas balancing notification data.

        Args:
            **kwargs: Additional parameters to include in the POST payload.

        Returns:
            Dict[str, Any]: JSON response containing gas balancing notifications.
        """
        endpoint = "daily-summary-report-data"
        payload = {"request": "gasBalancingNotification"}
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def demand_forecast_margin_notices(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve demand forecast margin notices.

        Args:
            **kwargs: Additional parameters to include in the POST payload.

        Returns:
            Dict[str, Any]: JSON response containing demand forecast margin notices.
        """
        endpoint = "gas-system-status-data"
        payload = {"request": "demandForecastMarginNotices"}
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def forecast_data(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve forecast data.

        Args:
            **kwargs: Additional parameters to include in the POST payload.

        Returns:
            Dict[str, Any]: JSON response containing forecast data.
        """
        endpoint = "gas-system-status-data"
        payload = {"request": "forecastData"}
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def linepack(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve linepack data.

        Args:
            **kwargs: Additional parameters to include in the POST payload.

        Returns:
            Dict[str, Any]: JSON response containing linepack data.
        """
        endpoint = "gas-system-status-data"
        payload = {"request": "linepack"}
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def summary_table_and_mrs_lng(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve summary table and MRS LNG data.

        Args:
            **kwargs: Additional parameters to include in the POST payload.

        Returns:
            Dict[str, Any]: JSON response containing summary table and MRS LNG data.
        """
        endpoint = "gas-system-status-data"
        payload = {"request": "summaryTableAndMrsLng"}
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def flow_rates_table(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve flow rates table data.

        Args:
            **kwargs: Additional parameters to include in the POST payload.

        Returns:
            Dict[str, Any]: JSON response containing flow rates table data.
        """
        endpoint = "gas-system-status-data"
        payload = {"request": "flowRatesTable"}
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def nts_apf(self, gas_day: str = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the Aggregate Physical NTS System Entry Flows (NTSAPF) report.

        This report aggregates physical NTS system entry flows for the given gas day.

        Args:
            gas_day (str, optional): The gas day for which to retrieve the report.
                                     Defaults to today's date if None.
            **kwargs: Additional parameters to include in the request payload.

        Returns:
            Dict[str, Any]: Parsed JSON response from the API containing the NTSAPF report data.
        """
        if gas_day is None:
            gas_day = self.D

        endpoint = "reports"
        payload = {
            "reportName": "Aggregate Physical NTS System Entry Flows (NTSAPF)",
            "gasDay": gas_day,
        }
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def nts_de(self, gas_day: str = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the D-2 to D-5 NTS Demand Forecast Report (NTSDE).

        Args:
            gas_day (str, optional): The gas day for which to retrieve the report.
                                     Defaults to today's date if None.
            **kwargs: Additional parameters to include in the request payload.

        Returns:
            Dict[str, Any]: Parsed JSON response from the API containing the NTSDE report data.
        """
        if gas_day is None:
            gas_day = self.D

        endpoint = "reports"
        payload = {
            "reportName": "D-2 to D-5 NTS Demand Forecast Report (NTSDE)",
            "gasDay": gas_day,
        }
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def day_ahead_gas_flow_nominations(self, gas_day: str = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the Day Ahead Gas Flow Nominations report.

        Args:
            gas_day (str, optional): The gas day for which to retrieve the report.
                                     Defaults to today's date if None.
            **kwargs: Additional parameters to include in the request payload.

        Returns:
            Dict[str, Any]: Parsed JSON response from the API containing the Day Ahead Gas Flow Nominations report data.
        """
        if gas_day is None:
            gas_day = self.D

        endpoint = "reports"
        payload = {
            "reportName": "Day Ahead Gas Flow Nominations",
            "gasDay": gas_day,
        }
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def nts_aff(self, gas_day: str = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the End Of Day Aggregate Forecast NTS System Entry Flows (NTSAFF) report.

        Args:
            gas_day (str, optional): The gas day for which to retrieve the report.
                                     Defaults to today's date if None.
            **kwargs: Additional parameters to include in the request payload.

        Returns:
            Dict[str, Any]: Parsed JSON response from the API containing the NTSAFF report data.
        """
        if gas_day is None:
            gas_day = self.D

        endpoint = "reports"
        payload = {
            "reportName": "End Of Day Aggregate Forecast NTS System Entry Flows (NTSAFF)",
            "gasDay": gas_day,
        }
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def SISR01(self, gas_day: str = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the Forecast Composite Weather Variables (SISR01) report.

        Args:
            gas_day (str, optional): The gas day for which to retrieve the report.
                                     Defaults to today's date if None.
            **kwargs: Additional parameters to include in the request payload.

        Returns:
            Dict[str, Any]: Parsed JSON response from the API containing the SISR01 report data.
        """
        if gas_day is None:
            gas_day = self.D

        endpoint = "reports"
        payload = {
            "reportName": "Forecast Composite Weather Variables (SISR01)",
            "gasDay": gas_day,
        }
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def SISR03(self, gas_day: str = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the Forecast Demands (SISR03) report.

        Args:
            gas_day (str, optional): The gas day for which to retrieve the report.
                                     Defaults to today's date if None.
            **kwargs: Additional parameters to include in the request payload.

        Returns:
            Dict[str, Any]: Parsed JSON response from the API containing the SISR03 report data.
        """
        if gas_day is None:
            gas_day = self.D

        endpoint = "reports"
        payload = {
            "reportName": "Forecast Demands (SISR03)",
            "gasDay": gas_day,
        }
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def nomination_report(self, gas_day: str = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the Nomination Report.

        Note: Re-nominations for D are shown at 4 intervals within the gas day. The re-nomination value shown is
        the Prevailing End of Day (EOD) approved nomination at that point in time. If there is no nomination(s)
        made then the report value will be blank and Zero Nomination(s) will be displayed as a zero in the report.
        Nominations/Re-nominations for D-1, D and D+1 (all figures are in kWh).

        Args:
            gas_day (str, optional): The gas day for which to retrieve the report.
                                     Defaults to today's date if None.
            **kwargs: Additional parameters to include in the request payload.

        Returns:
            Dict[str, Any]: Parsed JSON response from the API containing the Nomination Report data.
        """
        if gas_day is None:
            gas_day = self.D

        endpoint = "reports"
        payload = {
            "reportName": "Nomination Report",
            "gasDay": gas_day,
        }
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def NB05(self, gas_day: str = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the System Nomination Balance (NB05) report.

        Args:
            gas_day (str, optional): The gas day for which to retrieve the report.
                                     Defaults to today's date if None.
            **kwargs: Additional parameters to include in the request payload.

        Returns:
            Dict[str, Any]: Parsed JSON response from the API containing the System Nomination Balance (NB05) report data.
        """
        if gas_day is None:
            gas_day = self.D

        endpoint = "reports"
        payload = {
            "reportName": "System Nomination Balance (NB05)",
            "gasDay": gas_day,
        }
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def NB92(self, gas_day: str = None, **kwargs: Any) -> Dict[str, Any]:
        """
        Retrieve the System Status Information (NB92) report.

        Args:
            gas_day (str, optional): The gas day for which to retrieve the report.
                                     Defaults to today's date if None.
            **kwargs: Additional parameters to include in the request payload.

        Returns:
            Dict[str, Any]: Parsed JSON response from the API containing the System Status Information (NB92) report data.
        """
        if gas_day is None:
            gas_day = self.D

        endpoint = "reports"
        payload = {
            "reportName": "System Status Information (NB92)",
            "gasDay": gas_day,
        }
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def find_gas_data(self, ids: list,
                      dateType: str = "GASDAY",
                      dateFrom: str = "2025-02-21",
                      dateTo: str = "2025-03-01",
                      **kwargs):

        allowed_date_types = {"GASDAY", "NORMALDAY"}
        if dateType not in allowed_date_types:
            raise ValueError(f"dateType must be one of {allowed_date_types}")

        payload = {
            "latestFlag": "Y",
            "applicableFor": "Y",
            "dateFrom": dateFrom,
            "dateTo": dateTo,
            "dateType": dateType,
            "ids": ",".join(ids)
        }
        endpoint = "find-gas-data"
        payload.update(kwargs)
        return self._post(endpoint, payload)

    def get_pub_mapping(self, min_range: int = 0, max_range: int = 2_500, prefixes=None):
        """
        Fetches the mapping of PUB IDs from the National Gas API and saves the result as a JSON file.

        Args:
            min_range (int): The lower limit for the range of IDs to search. Default is 0.
            max_range (int): The upper limit for the range of IDs to search. Default is 2500.
            prefixes (set): A set of prefix strings to prepend to the IDs. Default is {"PUBOBJ", "PUBOBS"}.
        """
        if prefixes is None:
            prefixes = {"PUBOBJ", "PUBOB"}

        ng_map = {}

        # Process each prefix and iterate over the given range.
        for prefix in prefixes:
            for i in range(min_range, max_range + 1):
                ID = f"{prefix}{i}"
                try:
                    response = self.find_gas_data([ID])
                    if "data" in response and response["data"]:
                        item_name = response["data"][0].get("itemName", "Unknown")
                        print(f"{ID}: {item_name}")
                        ng_map[ID] = item_name  # Store the mapping in the dictionary.
                    else:
                        print(f"No data found for {ID}")
                except Exception as e:
                    print(f"Error fetching data for {ID}: {e}")

        filename = "ng_map.json"
        # Merge with existing mapping if the file exists.
        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as json_file:
                existing_map = json.load(json_file)

            # Compare and update (new values override existing ones)
            for key, new_value in ng_map.items():
                if key in existing_map and existing_map[key] != new_value:
                    print(
                        f"Conflict for {key}: Existing value '{existing_map[key]}' will be overridden by new value '{new_value}'.")
            existing_map.update(ng_map)
            merged_map = existing_map
        else:
            merged_map = ng_map

        # Save the merged mapping to the JSON file.
        with open(filename, "w", encoding="utf-8") as json_file:
            json.dump(merged_map, json_file, indent=4)

        print(f"Mapping saved to {filename}")


if __name__ == "__main__":

    client = NationalGasClient()
    try:
        client.get_pub_mapping(min_range=0, max_range=10_000)
    except Exception as ex:
        logger.exception("An error occurred while retrieving the report: %s", ex)
