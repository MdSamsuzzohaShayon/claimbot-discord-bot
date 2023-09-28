import os
import aiofiles
from datetime import datetime
from dotenv import load_dotenv
from utils.FormatString import FormatString

load_dotenv()


class ErrorHandler:
    def __init__(self):
        self.count = 1
        self.project_directory = os.getenv("PROJECT_DIRECTORY")
        self.fs = FormatString()
        self.filename = os.getenv("LOG_FILE")
        self.file_path = os.path.join(self.project_directory,  self.filename)

    async def error(self, desc = None, reference_file: str = None) -> None:
        self.current_time = self.fs.current_est_datetime_obj()
        async with aiofiles.open(self.file_path, 'a') as file:
            await file.write(f"\n=================================================================\n{self.count} | {reference_file} | {self.current_time} \n")
            await file.write(f"Error : {str(desc)}")
            self.count += 1

    async def info(self, desc = None, reference_file: str = None) -> None:
        self.current_time = self.fs.current_est_datetime_obj()
        async with aiofiles.open(self.file_path, 'a') as file:
            await file.write(f"\n=================================================================\n{self.count} | {reference_file} | {self.current_time} \n")
            await file.write(f"Info : {str(desc)}")
            self.count += 1

    async def warning(self, desc = None, reference_file: str = None) -> None:
        self.current_time = self.fs.current_est_datetime_obj()
        async with aiofiles.open(self.file_path, 'a') as file:
            await file.write(f"\n=================================================================\n{self.count} | {reference_file} | {self.current_time} \n")
            await file.write(f"Warning : {str(desc)}")
            self.count += 1

    async def debug(self, desc = None, reference_file: str = None) -> None:
        self.current_time = self.fs.current_est_datetime_obj()
        async with aiofiles.open(self.file_path, 'a') as file:
            await file.write(f"\n=================================================================\n{self.count} | {reference_file} | {self.current_time} \n")
            await file.write(f"Debug : {str(desc)}")
            self.count += 1