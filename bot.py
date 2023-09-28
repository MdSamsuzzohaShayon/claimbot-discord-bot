import logging

import discord
import os
import asyncio

from dotenv import load_dotenv
from discord import app_commands
from discord.ext import tasks

from controllers.TaskDailyController import TaskDailyController
from controllers.StartupController import StartupController
from utils.FormatString import FormatString
from config.TokenManager import TokenManager
from seeds.Initializer import Initializer

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
TEST_GUILD = discord.Object(GUILD_ID)

"""
Discord Client -> https://discordpy.readthedocs.io/en/stable/api.html#client
Discord extension -> https://discordpy.readthedocs.io/en/stable/ext/tasks/index.html 
"""


class MyClient(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        startup_controller = StartupController(client=self)
        await startup_controller.initialize()

    @tasks.loop(seconds=60)  # Checks every 60 seconds if it is time to send the message
    async def daily_activities(self):

        fs = FormatString()
        est_time_now = fs.current_est_datetime_obj()

        # Initialize every day at 5.55 am EST
        if est_time_now.hour == 7 and est_time_now.minute == 55:
            initilizer = Initializer(client=self)
            await initilizer.run(daily=True)

        # Send cleaning notification every day at 8 am EST
        if est_time_now.hour == 8 and est_time_now.minute == 0:
            task_controller = TaskDailyController(client=self)
            try:
                await task_controller.remind_cleaning_notifications()
                logging.warning("Sent daily notifications successfully at eastern time")
            except Exception as e:
                logging.error(e)

        # Refresh Token
        if est_time_now.hour == 1 and est_time_now.minute == 0:
            token_manager = TokenManager()
            asyncio.create_task(token_manager.create_token())

    async def setup_hook(self) -> None:
        self.daily_activities.start()
        await self.tree.sync(guild=TEST_GUILD)


client = MyClient()
