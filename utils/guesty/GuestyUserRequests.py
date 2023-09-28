import logging
import urllib.parse

import httpx
from utils.guesty.GuestyRequestBase import GuestyRequestBase


class GuestyUserRequests(GuestyRequestBase):
    def __init__(self):
        super().__init__()

    async def search_users(self, limit=200, skip=0, q=''):
        token = await self.read_token()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'Authorization': f"Bearer {token}"}
                query_params = {
                    'limit': limit,
                    'skip': skip,
                    'q': q
                }
                encoded_params = urllib.parse.urlencode(query_params)
                url = f"{self.open_api_url}/users?{encoded_params}"
                response = await client.get(url=url, headers=headers)
                response_details = self.get_details(response=response)
                if response.status_code == 200:
                    guesty_user = response.json()
                    return guesty_user['results']
                logging.error(response_details)
                return []
        except Exception as e:
            logging.error(e)
            return []

    async def search_a_user(self, username):
        try:
            find_user = await self.search_users(q=username)
            if len(find_user) == 0:
                return None
            for user in find_user:
                if user['firstName'].lower() == username.lower():
                    return user
            return None
        except Exception as e:
            logging.error(e)
            return None

    async def find_all_users(self):
        try:
            all_guesty_users = []
            skip, limit = 0, 200
            while True:
                find_users = await self.search_users(skip=skip, limit=limit)
                all_guesty_users.extend(find_users)
                if len(find_users) < limit:
                    break
                skip += limit
            return all_guesty_users
        except Exception as e:
            logging.error(e)
            return []

    async def retrieve_a_user(self, guesty_user_id):
        if guesty_user_id is None:
            return None
        token = await self.read_token()
        try:
            async with httpx.AsyncClient() as client:
                headers = {'Authorization': f"Bearer {token}"}
                response = await client.get(url=f"{self.open_api_url}/users/{guesty_user_id}", headers=headers, timeout=self.timeout)
                response_details = self.get_details(response=response)
                if response.status_code == 200:
                    return response.json()
                logging.error(response_details)
                return None
        except Exception as e:
            logging.error(e)
            return None
