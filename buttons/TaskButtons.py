import discord
from discord.ui import View
# from buttons.TaskButtonsCallback import TaskButtonsCallback
from buttons.TaskButtonsView import TaskButtonsView

"""
Official docs - https://discord.com/developers/docs/interactions/message-components#action-rows
Discord py docs - https://discordpy.readthedocs.io/en/stable/interactions/api.html#discord.ui.View
The callback associated with this UI item. -> https://discordpy.readthedocs.io/en/stable/interactions/api.html?highlight=interaction#discord.ui.Button.callback
A helper that returns the first element in the iterable that meets all the traits passed in attrs.  -> https://discordpy.readthedocs.io/en/stable/api.html#discord.utils.get
"""


class TaskButtons(View):
    def __init__(self, client: discord.Client):
        super().__init__(timeout=None)
        self.client = client
        self.task_button_view = TaskButtonsView()

    def task_add(self, task_id: str, callback_func) -> None:
        new_button = self.task_button_view.task_add(task_id=task_id, callback_func=callback_func)
        self.add_item(new_button)