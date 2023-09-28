import discord
import random
from discord.ui import View, Button
from discord import ButtonStyle

"""
Official docs - https://discord.com/developers/docs/interactions/message-components#action-rows
Discord py docs - https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.ui.View
The callback associated with this UI item. -> https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=interaction#discord.ui.Button.callback
A helper that returns the first element in the iterable that meets all the traits passed in attrs.  -> https://discordpy.readthedocs.io/en/stable/api.html#discord.utils.get
"""


class TaskButtonsView(View):
    def __init__(self):
        super().__init__(timeout=None)

    def task_add(self, task_id: str, callback_func) -> None:
        new_button = Button(label="Accept Task", custom_id=f'addtask_{task_id}', style=ButtonStyle.blurple)
        new_button.callback = callback_func
        return new_button

    def task_start(self, task_id, callback_func) -> None:
        new_button = Button(label="Start Task", custom_id=f'starttask_{task_id}', style=ButtonStyle.blurple)
        new_button.callback = callback_func
        self.add_item(new_button)

    def task_release(self, callback_func, task_id: str = None) -> None:
        new_task_id = "releasetask_all" if task_id == None else f'releasetask_{task_id}'
        new_button = Button(label="Release Task", custom_id=new_task_id, style=ButtonStyle.gray)
        new_button.callback = callback_func
        self.add_item(new_button)

    def task_release_of_a_user(self, user_id, callback_func):
        new_button = Button(label="Release Task", custom_id=f"charttask_{user_id}", style=ButtonStyle.gray)
        new_button.callback = callback_func
        self.add_item(new_button)

    def task_complete(self, task_id: str, callback_func) -> None:
        new_button = Button(label="Complete Task", custom_id=f'completetask_{task_id}', style=ButtonStyle.blurple)
        new_button.callback = callback_func
        self.add_item(new_button)
