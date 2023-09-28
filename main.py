import uvicorn
import logging

from server import app
from bot import client, BOT_TOKEN
import asyncio

# Set the logging level for the root logger to WARNING
logging.basicConfig(format="%(levelname)s-> (%(asctime)s) %(message)s [%(pathname)s:%(lineno)d]")
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)

# Create a file handler
file_handler = logging.FileHandler("config/claimbotpy.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)

# Set the desired format for the file handler
file_formatter = logging.Formatter("%(levelname)s-> (%(asctime)s) %(message)s [%(pathname)s:%(lineno)d]")
file_handler.setFormatter(file_formatter)

# Add the file handler to the root logger
root_logger.addHandler(file_handler)

# Disable logs from the 'discord' logger
discord_logger = logging.getLogger("discord")
discord_logger.setLevel(logging.WARNING)


# Filter out logs from specific virtual environment modules
# class ExcludeVirtualEnvFilter(logging.Filter):
#     def filter(self, record):
#         return "module_name_to_exclude" not in record.getMessage()
#
# root_logger.addFilter(ExcludeVirtualEnvFilter())

# Filter out logs from the watchfiles library
class ExcludeWatchfilesFilter(logging.Filter):
    def filter(self, record):
        return "watchfiles" not in record.name


root_logger.addFilter(ExcludeWatchfilesFilter())


@app.on_event("startup")
async def startup_event():
    # Discord bot connection
    asyncio.create_task(client.start(BOT_TOKEN))


if __name__ == "__main__":
    uvicorn.run("server:app", host='0.0.0.0', port=8000, reload=True)
