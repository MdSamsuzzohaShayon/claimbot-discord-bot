import os
import re
import aiofiles
import httpx
import logging
import json

from dotenv import load_dotenv
from utils.FormatString import FormatString

load_dotenv()


class GuestyRequestBase:
    def __init__(self):
        self.open_api_url_base = os.getenv('OPEN_API_URL_BASE')
        self.open_api_url = os.getenv('OPEN_API_URL')
        self.client_id = os.getenv('CLIENT_ID')
        self.client_secret = os.getenv('CLIENT_SECRET')
        self.project_directory = os.getenv("PROJECT_DIRECTORY")
        self.filename = os.getenv('TOKEN_FILE_NAME')
        self.token_file_path = os.path.abspath(f"config/{self.filename}")
        self.client = httpx.AsyncClient()
        self.timeout = httpx.Timeout(10.0)
        self.fs = FormatString()
        # self.connection_timeout = httpx.Timeout(connect_timeout=5.0, read_timeout=10.0)

    async def read_token(self):
        try:
            file_path = os.path.join(self.project_directory, 'config', self.filename)
            file = await aiofiles.open(file_path, mode='r')
            content = await file.read()
            await file.close()
            if len(str(content)) <= 0:
                return None
            pattern = r"\S+\.\S+\.\S+(?=,)"
            regex = re.compile(pattern)
            access_token = regex.findall(str(content))
            return access_token[0] if len(access_token) > 0 else None
        except StopAsyncIteration as e:
            logging.error(e)
            return None

    async def get_guesty_token(self):
        try:
            async with httpx.AsyncClient() as client:
                data = {"grant_type": "client_credentials", "scope": "open-api",
                        "client_secret": self.client_secret,
                        "client_id": self.client_id}
                headers = {"Content-Type": "application/x-www-form-urlencoded"}
                response = await client.post(url=f"{self.open_api_url_base}/oauth2/token", data=data, headers=headers)
                response_details = self.get_details(response=response)
                if response.status_code == 200:
                    return response.json()
                logging.error(response_details)
                return None
        except Exception as e:
            logging.error(e)
            return None

    async def create_token(self):
        try:
            file_path = os.path.join(self.project_directory, 'config', self.filename)
            guesty_token = await self.get_guesty_token()
            if guesty_token is None:
                logging.error("No token found")
                return
            async with aiofiles.open(file_path, 'w+', newline='') as csvfile:
                fieldnames = ['current_token', 'created_at']
                access_token = guesty_token['access_token']
                await csvfile.write(', '.join(fieldnames))
                western_time_now = self.fs.current_est_datetime_obj()
                await csvfile.write(f"\n{access_token}, {western_time_now.isoformat()}")
                if access_token is None:
                    logging.error("No token found")
                    return
                print("\033[91mThe token had been created successfully, this will expire tomorrow\033[0m")
        except Exception as fE:
            logging.error(fE)

    async def close(self):
        await self.client.aclose()


    def get_details(self, response):
        request_details = json.dumps({
            "URL": str(response.url),
            "Status": response.status_code,
            "Headers": str(response.headers),
            "Text": str(response.text),
        })
        return  request_details