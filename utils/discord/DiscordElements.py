import os
import discord


class DiscordElements:
    def __init__(self, client):
        self.client = client
        self.all_discord_members = []
        self.member_limit = 150
        self.channel_catagory_list = []

    async def find_all_members(self):
        guild = await self.client.fetch_guild(os.getenv("GUILD_ID"))
        async for dm in guild.fetch_members(limit=self.member_limit):
            self.all_discord_members.append(dm)

    async def find_member_by_nickname(self, nickname):
        if nickname is None: return None
        # cleanerpay_field = next((field for field in custom_fields if field["fieldId"] == cleanerpay_field_id), None)
        find_member = next((m for m in self.all_discord_members if str(m.nick).lower() == str(nickname).lower()), None)
        return find_member

    def find_channel_category(self, category_name):
        self.channel_catagory_list = []
        target_category = None
        channel_catagory_set = set()
        for guild in self.client.guilds:
            for channel in guild.channels:
                if channel.category and not isinstance(channel, discord.CategoryChannel):
                    if str(channel.category.name).lower() == category_name.lower():
                        target_category = channel.category
                    if channel.category.id not in channel_catagory_set:
                        self.channel_catagory_list.append(channel.category)
                        channel_catagory_set.add(channel.category.id)
        return target_category
