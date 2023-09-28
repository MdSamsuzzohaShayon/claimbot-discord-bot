import os
import re
import logging
import aiofiles

from utils.guesty.GuestyRequestBase import GuestyRequestBase
from utils.FormatString import FormatString

"""
Create an object which operates like a regular writer but maps dictionaries onto output rows -> https://docs.python.org/3/library/csv.html#csv.DictWriter
Open file and return a corresponding file object. -> https://docs.python.org/3/library/functions.html#open
datetime.now(tz=None) -> Return the current local date and time. -> https://docs.python.org/3/library/datetime.html#datetime.datetime.now
"""


class TokenManager:

    def __init__(self):
        self.filename = os.getenv('TOKEN_FILE_NAME')
        self.project_directory = os.getenv("PROJECT_DIRECTORY")
        self.fs = FormatString()

    async def create_token(self):
        try:
            file_path = os.path.join(self.project_directory, 'config', self.filename)
            token_request = GuestyRequestBase()
            guesty_token = await token_request.get_guesty_token()
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
