import json

import httpx
import urllib.parse
import logging

from utils.guesty.GuestyRequestBase import GuestyRequestBase


class GuestyListingRequests(GuestyRequestBase):
    def __init__(self):
        super().__init__()

    async def retrive_a_listing(self, listing_id):
        if listing_id is None:
            return None
        token = await self.read_token()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'Authorization': f"Bearer {token}"}
                response = await client.get(url=f"{self.open_api_url}/listings/{listing_id}", headers=headers)
                response_details = self.get_details(response=response)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    await self.get_guesty_token()
                    # self.token
                logging.error(json.dumps(response_details))
                return None
        except Exception as e:
            logging.error(e)
            return None

    async def get_listings(self, filters=None):
        if filters is None:
            filters = {"limit": 100}
        token = await self.read_token()
        # {'status': {'@nin': ['completed']}, 'scheduledFor': {'@today': true}}
        try:
            encoded_params = urllib.parse.urlencode(filters)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'Authorization': f"Bearer {token}"}
                response = await client.get(url=f"{self.open_api_url}/listings?{encoded_params}", headers=headers)
                response_details = self.get_details(response=response)
                if response.status_code == 200:
                    return response.json()["results"]
                elif response.status_code == 401:
                    await self.create_token()
                logging.error(json.dumps(response_details))
                return []
        except Exception as e:
            logging.error(e)
            return []

    async def get_all_listing(self):
        all_listings = []
        skip, limit = 0, 100
        while True:
            find_listings = await self.get_listings()
            all_listings.extend(find_listings)
            if len(find_listings) < limit:
                break
            skip += limit
        return all_listings
