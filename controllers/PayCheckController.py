import logging
import asyncio
from config.keys import CHANNELS
from components.EmbedElements import EmbedElements
from buttons.PayButtonsCallback import PayButtonsCallback
from buttons.PayButtonsView import PayButtonsView
from controllers.MessageController import MessageController

class PayCheckController:
    def __init__(self, client):
        self.pay_embed = None
        self.pay_button = None
        self.client = client
        self.mc = MessageController()


    def create_embed_elements(self):
        embed_element = EmbedElements()
        pay_buttons_callback = PayButtonsCallback(client=self.client)

        self.pay_button = PayButtonsView(client=self.client)
        self.pay_embed = embed_element.attachment_with_thumbnail(description="Click the button below to see your pay for current month")
        self.pay_button.get_my_pay_check(callback_func=pay_buttons_callback.get_my_pay_check_callback)


    async def run(self, daily: bool):
        """
        TODO:
            Find previous message from database
            if the message was found delete the previous one and create a new message on the database
            if there are no message create one and save it to the database
            send 3 buttons
                1. Get pay summery - Click the button below to see a summary of payments for the current and previous month
                2. Get listings summery - Click the button below to see a summary of listing expenses for the current and previous month
                3. Pay Update - Click the button below to update a cleaner's pay for this month
        """
        try:
            self.calc_channel = await self.client.fetch_channel(CHANNELS["pay_check"])
            self.create_embed_elements()
            if daily:
                await self.edit_or_add_btns()
            else:
                await self.calc_channel.purge()  # delete all previous messages
                await self.send_new_btns()

            await self.create_or_edit_in_db()
            logging.warning("Calculation functions completed")
        except Exception as e:
            logging.error(e)