import os
import aiofiles
import discord

from components.EmbedElements import EmbedElements

from utils.discord.NotificationBase import NotificationBase
from config.keys import DELETE_AFTER_5_MIN, CHANNELS


class NotificationManagement(NotificationBase):
    def __init__(self, client):
        super().__init__(client=client)
        self.client = client
        self.project_directory = os.getenv("PROJECT_DIRECTORY")

    async def notify_admin(self, message: str, task_id: str, title: str = None) -> None:
        # Send notification to admin if something happen
        # ===============================================================================================================
        embed_elements = EmbedElements()
        new_message = message + f"\n[Task in Guesty](https://app.guesty.com/tasks/{task_id})"
        embed = embed_elements.attachment_with_thumbnail(title=title, description=new_message)
        message_to_management = await self.notifications_channel.send(embed=embed)

    async def notify_specific_user(self, user_discord_id, message: str, task_id=None, ) -> None:
        # Send notification to a single user
        # ===============================================================================================================
        user = await self.client.fetch_user(user_discord_id)
        new_msg = message
        if task_id is not None:
            new_msg = message + f"\nhttps://app.guesty.com/tasks/{task_id}"

        await user.send(new_msg)

    async def notify_todays_cleaning(self, embed_table):
        not_channel = await self.client.fetch_channel(CHANNELS["notifications"])
        await not_channel.send(embed=embed_table)