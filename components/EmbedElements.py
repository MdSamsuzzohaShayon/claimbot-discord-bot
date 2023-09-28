import discord
import json

"""
Discord Official docs: https://discord.com/developers/docs/resources/channel#embed-object
Discord py docs: https://discordpy.readthedocs.io/en/stable/api.html?highlight=messageable#embed
"""


class EmbedElements:

    def __init__(self):
        self.name = ""

    def attachment_with_thumbnail(self, title=None, description=None, thumbnail=None) -> discord.Embed:
        self.embed = discord.Embed(title=title, description=description)
        self.embed.set_thumbnail(url=thumbnail)
        return self.embed


