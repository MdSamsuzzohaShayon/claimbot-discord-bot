from discord.ui import View, Select
from utils.Enums import TaskStatus
from utils.FormatString import FormatString

"""
Represents a UI select menu with a list of custom options. This is represented to the user as a dropdown menu. -> https://discordpy.readthedocs.io/en/stable/interactions/api.html#select-menus
The library provides classes to help create the different types of select menus. -> https://discordpy.readthedocs.io/en/stable/interactions/api.html#select-menus
"""


class TaskSelectsView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.fs = FormatString()

    def task_list_display(self, user_id: str, task_list: list, callback_func):
        new_select_menu = Select(custom_id=f'tasklist_{user_id}')
        new_select_menu.callback = callback_func
        for t in task_list:
            listing_title = t['listing']['title']
            listing_nickname = listing_title.split("/")[0] if "/" in listing_title else listing_title
            guesty_task_id = t['id']
            start_time = t['scheduledFor']['startTime'] if 'scheduledFor' in t and "startTime" in t['scheduledFor'] else None
            if start_time is None:
                continue
            start_time_obj = self.fs.iso_to_est_time(iso_time=start_time)
            new_select_menu.add_option(label=f"{listing_nickname}[{start_time_obj.day}]", value="taskoption_" + guesty_task_id)
        self.add_item(new_select_menu)
