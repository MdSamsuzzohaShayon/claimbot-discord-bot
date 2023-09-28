import logging

import httpx
import urllib.parse
import json

from utils.guesty.GuestyRequestBase import GuestyRequestBase


class GuestyReservationRequests(GuestyRequestBase):
    def __init__(self):
        super().__init__()

    async def retrive_a_reservation(self, reservation_id):
        if reservation_id is None:
            return None
        token = await self.read_token()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'Authorization': f"Bearer {token}"}
                response = await client.get(url=f"{self.open_api_url}/reservations/{reservation_id}", headers=headers)
                response_details = self.get_details(response=response)
                if response.status_code == 200:
                    return response.json()
                logging.error(response_details)
                return None
        except httpx.TimeoutException as te:
            logging.error(te)
            return None
        except Exception as e:
            logging.error(e)
            return None

    async def search_reservations(self, skip=0, limit=100, filters={}):
        token = await self.read_token()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    'Content-Type': 'application/json',
                    'accept': 'application/json',
                    'Authorization': f"Bearer {token}"
                }
                query_params = {
                    "limit": limit,
                    'skip': skip,
                    "fields": "guest.fullName guestsCount",
                    'filters': json.dumps(filters)
                }
                encoded_params = urllib.parse.urlencode(query_params)
                response = await client.get(url=f"{self.open_api_url}/reservations?{encoded_params}", headers=headers)
                response_details = self.get_details(response=response)
                if response.status_code == 200:
                    result =  response.json()
                    return result['results']
                logging.error(response_details)
                return []
        except httpx.TimeoutException as te:
            logging.error(te)
            return []
        except Exception as e:
            logging.error(e)
            return []

    async def find_all_reservations(self, filters={}):
        try:
            all_guesty_reservations = []
            skip, limit = 0, 100
            while True:
                find_reservations = await self.search_reservations(skip=skip, limit=limit, filters=filters)
                all_guesty_reservations.extend(find_reservations)
                if len(find_reservations) < limit:
                    break
                skip += limit
            return all_guesty_reservations
        except Exception as e:
            logging.error(e)
            return []