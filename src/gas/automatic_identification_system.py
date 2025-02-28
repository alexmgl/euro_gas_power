import requests
import time
import gzip
import bz2
import zipfile
import io
import json

class AICCLient:
    """
    AICCLient is a Python client for accessing the AISHub webservice,
    which provides AIS data for vessels in XML, JSON, or CSV format.
    
    Key features:
      - Rate Limiting: Ensures the webservice is not accessed more than once per minute.
      - Parameter Customization: Allows you to filter by geographical boundaries, MMSI/IMO numbers,
        and set the desired output format and compression.
      - Automatic Decompression: Handles decompression (ZIP, GZIP, BZIP2) based on the chosen parameter.
      
    Note: AISHub members can use this client to retrieve data. Do not execute the webservice
    more frequently than once per minute; otherwise, it will return nothing.
    """

    def __init__(self, username):
        """
        Initializes the client with your AISHub username.
        
        Parameters:
            username (str): Your AISHub username.
        """
        self.username = username
        self.base_url = "https://data.aishub.net/ws.php"
        self.last_request_time = None

    def get_data(self, output="xml", data_format=1, compress=0, latmin=-90, latmax=90,
                 lonmin=-180, lonmax=180, mmsi=None, imo=None, interval=None):
        """
        Retrieves AIS data from AISHub with the specified parameters.
        
        Parameters:
            output (str): The output format: "xml", "json", or "csv". Default is "xml".
            data_format (int): 0 for AIS encoding, 1 for human-readable format. Default is 1.
            compress (int): Compression type: 0 (none), 1 (ZIP), 2 (GZIP), or 3 (BZIP2). Default is 0.
            latmin (float): Minimum latitude (South). Default is -90.
            latmax (float): Maximum latitude (North). Default is 90.
            lonmin (float): Minimum longitude (West). Default is -180.
            lonmax (float): Maximum longitude (East). Default is 180.
            mmsi (int or list, optional): Single MMSI or list of MMSI numbers to filter the vessels.
            imo (int or list, optional): Single IMO or list of IMO numbers to filter the vessels.
            interval (int, optional): Maximum age (in minutes) of the returned positions.
        
        Returns:
            If output is "json": A Python dictionary or list parsed from JSON.
            Otherwise: A string containing the XML or CSV data.
        
        Raises:
            Exception: If the HTTP request fails.
        
        Note:
            This method enforces a minimum interval of 60 seconds between successive calls.
        """
        # Enforce rate limiting: wait if the last call was less than 60 seconds ago.
        current_time = time.time()
        if self.last_request_time is not None:
            elapsed = current_time - self.last_request_time
            if elapsed < 60:
                wait_time = 60 - elapsed
                print(f"Rate limit in effect. Waiting for {wait_time:.2f} seconds...")
                time.sleep(wait_time)
        
        # Build the query parameters
        params = {
            "username": self.username,
            "format": data_format,
            "output": output,
            "compress": compress,
            "latmin": latmin,
            "latmax": latmax,
            "lonmin": lonmin,
            "lonmax": lonmax
        }
        if mmsi:
            if isinstance(mmsi, list):
                params["mmsi"] = ",".join(str(x) for x in mmsi)
            else:
                params["mmsi"] = str(mmsi)
        if imo:
            if isinstance(imo, list):
                params["imo"] = ",".join(str(x) for x in imo)
            else:
                params["imo"] = str(imo)
        if interval:
            params["interval"] = str(interval)

        # Make the HTTP GET request to the AISHub webservice
        response = requests.get(self.base_url, params=params)
        self.last_request_time = time.time()  # Update the last request time
        
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve data: HTTP {response.status_code}")

        content = response.content

        # Decompress data if compression is enabled
        if compress == 2:  # GZIP
            content = gzip.decompress(content)
        elif compress == 3:  # BZIP2
            content = bz2.decompress(content)
        elif compress == 1:  # ZIP
            with zipfile.ZipFile(io.BytesIO(content)) as z:
                # Assuming a single file in the ZIP archive
                file_name = z.namelist()[0]
                content = z.read(file_name)

        # Convert bytes to a UTF-8 string
        text_data = content.decode('utf-8')

        # If JSON output was requested, parse and return the JSON data
        if output.lower() == "json":
            return json.loads(text_data)
        else:
            return text_data

# Example usage:
if __name__ == "__main__":
    # Replace 'YOUR_USERNAME' with your actual AISHub username.
    client = AICCLient("YOUR_USERNAME")
    
    try:
        # Retrieve all data in JSON format with GZIP compression
        data = client.get_data(output="json", data_format=1, compress=2)
        print("Retrieved Data:")
        print(data)
    except Exception as e:
        print(f"An error occurred: {e}")
