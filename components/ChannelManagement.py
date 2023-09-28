import discord
import os
from utils.discord.DiscordElements import DiscordElements


class ChannelManagement:
    def __init__(self, client):
        self.guild_id = os.getenv("GUILD_ID")
        self.client = client
        self.de = DiscordElements(client=client)

    async def create_a_channel(self, channel_name, discord_user = None, category_name = "Information"):
        guild = await self.client.fetch_guild(self.guild_id)

        target_category = self.de.find_channel_category(category_name=category_name)
        if target_category is None:
            target_category = await guild.create_category(category_name)
        new_channel = await guild.create_text_channel(name=channel_name, category=target_category)
        if discord_user:
            await new_channel.set_permissions(discord_user, read_messages=True, send_messages=True, read_message_history=True)
        else:
            await new_channel.set_permissions(guild.default_role, read_messages=True, send_messages=True, read_message_history=True)
        return new_channel
