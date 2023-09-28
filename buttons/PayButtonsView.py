from discord.ui import View, Button
from discord import ButtonStyle


class PayButtonsView(View):
    def __init__(self, client):
        super().__init__(timeout=None)
        self.client = client

    def get_pay_summary(self, callback_func) -> None:
        new_button = Button(label="Get Pay Summary", custom_id=f'get_pay_summary', style=ButtonStyle.blurple)
        new_button.callback = callback_func
        self.add_item(new_button)

    def get_listings_summary(self, callback_func) -> None:
        new_button = Button(label="Get Listing Summary", custom_id=f'get_listings_summary', style=ButtonStyle.blurple)
        new_button.callback = callback_func
        self.add_item(new_button)

    def get_update_pay(self, callback_func) -> None:
        new_button = Button(label="Update Pay", custom_id=f'get_update_pay', style=ButtonStyle.blurple)
        new_button.callback = callback_func
        self.add_item(new_button)

    def get_my_pay_check(self, callback_func) -> None:
        new_button = Button(label="Check My Pay", custom_id=f'get_my_pay_check', style=ButtonStyle.blurple)
        new_button.callback = callback_func
        self.add_item(new_button)
