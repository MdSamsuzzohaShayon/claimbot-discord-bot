# PayCalcController
import asyncio
import logging

from utils.database.DatabaseMultiOperations import DatabaseMultiOperations
from utils.FormatString import FormatString
from components.ChannelManagement import ChannelManagement
from utils.discord.DiscordElements import DiscordElements
from controllers.MessageController import MessageController
from utils.OrganizeGuestyData import OrganizeGuestyData
from utils.Enums import MessageType
from config.keys import CHANNELS
from components.EmbedElements import EmbedElements
from buttons.PayButtonsView import PayButtonsView
from buttons.PayButtonsCallback import PayButtonsCallback


class PayCalcController:
    def __init__(self, client):

        self.client = client

        self.fs = FormatString()
        self.ogd = OrganizeGuestyData()
        self.db = DatabaseMultiOperations()
        self.de = DiscordElements(client=client)
        self.cm = ChannelManagement(client=client)
        self.mc = MessageController()
        self.success_messages = {}

        # Enbed elements
        self.pay_update_embed = None
        self.pay_update_button = None
        self.pay_listing_embed = None
        self.pay_listing_button = None
        self.pay_embed = None
        self.pay_button = None

        # Previous Messages
        self.update_pay_message = None
        self.listing_pay_message = None
        self.pay_calc_message = None

        self.calc_channel = None

    async def delete_message_if_there_is_any(self, exist_local, message_type, discord_message_id):
        try:
            if exist_local:
                await self.db.update_one_message(find_filters={"type": message_type, "task_id": None, "user_id": None}, set_dict={"discord_message_id": discord_message_id})
            else:
                message_data = self.ogd.msg_insert_data(message_type=message_type, discord_message_id=discord_message_id)
                await self.db.insert_one_message(data=message_data)
        except Exception as e:
            logging.error(e)

    def create_embed_elements(self):
        embed_element = EmbedElements()
        pay_buttons_callback = PayButtonsCallback(client=self.client)

        self.pay_button = PayButtonsView(client=self.client)
        self.pay_embed = embed_element.attachment_with_thumbnail(description="Click the button below to see a summary of payments for the current and previous month")
        self.pay_button.get_pay_summary(callback_func=pay_buttons_callback.get_pay_summary_callback)

        self.pay_listing_button = PayButtonsView(client=self.client)
        self.pay_listing_button.get_listings_summary(callback_func=pay_buttons_callback.get_listings_summary_callback)
        self.pay_listing_embed = embed_element.attachment_with_thumbnail(description="Click the button below to see a summary of listing expenses for the current and previous month")

        self.pay_update_button = PayButtonsView(client=self.client)
        self.pay_update_button.get_update_pay(callback_func=pay_buttons_callback.update_pay_callback)
        self.pay_update_embed = embed_element.attachment_with_thumbnail(description="Click the button below to update a cleaner's pay for this month")

    async def edit_or_add_btns(self):
        # Fetch messages
        await self.mc.fetch_prev_pay_msgs(calc_channel=self.calc_channel)

        self.pay_calc_message, self.listing_pay_message, self.update_pay_message = await asyncio.gather(
            self.mc.find_prev_pay_spec_msg(custom_id='get_pay_summary'),
            self.mc.find_prev_pay_spec_msg(custom_id='get_listings_summary'),
            self.mc.find_prev_pay_spec_msg(custom_id='get_update_pay')
        )

        # If message exists update that in contrast send a new message
        create_or_edit_calc_btns = []
        if self.pay_calc_message:
            create_or_edit_calc_btns.append(asyncio.ensure_future(self.pay_calc_message.edit(embed=self.pay_embed, view=self.pay_button)))
        else:
            create_or_edit_calc_btns.append(asyncio.ensure_future(self.calc_channel.send(embed=self.pay_embed, view=self.pay_button)))

        if self.listing_pay_message:
            create_or_edit_calc_btns.append(asyncio.ensure_future(self.listing_pay_message.edit(embed=self.pay_listing_embed, view=self.pay_listing_button)))
        else:
            create_or_edit_calc_btns.append(asyncio.ensure_future(self.calc_channel.send(embed=self.pay_listing_embed, view=self.pay_listing_button)))

        if self.update_pay_message:
            create_or_edit_calc_btns.append(asyncio.ensure_future(self.update_pay_message.edit(embed=self.pay_update_embed, view=self.pay_update_button)))
        else:
            create_or_edit_calc_btns.append(asyncio.ensure_future(self.calc_channel.send(embed=self.pay_update_embed, view=self.pay_update_button)))

        await asyncio.gather(*create_or_edit_calc_btns)

        # If a message sent (not edit) early,
        self.pay_calc_message, self.listing_pay_message, self.update_pay_message = await asyncio.gather(
            self.mc.find_prev_pay_spec_msg(custom_id='get_pay_summary'),
            self.mc.find_prev_pay_spec_msg(custom_id='get_listings_summary'),
            self.mc.find_prev_pay_spec_msg(custom_id='get_update_pay')
        )

    async def send_new_btns(self):
        self.pay_calc_message, self.listing_pay_message, self.update_pay_message = await asyncio.gather(
            self.calc_channel.send(embed=self.pay_embed, view=self.pay_button),
            self.calc_channel.send(embed=self.pay_listing_embed, view=self.pay_listing_button),
            self.calc_channel.send(embed=self.pay_update_embed, view=self.pay_update_button)
        )

    async def create_or_edit_in_db(self):
        # Database operations - Deleting previous messages
        # ===============================================================================================================
        pay_calc_exist_local, listing_pay_exist_local, update_pay_exist_local = await asyncio.gather(
            self.db.update_one_message(find_filters={"type": MessageType.PAY_CALC.value, "task_id": None, "user_id": None}),
            self.db.update_one_message(find_filters={"type": MessageType.LISTING_PAY.value, "task_id": None, "user_id": None}),
            self.db.update_one_message(find_filters={"type": MessageType.UPDATE_PAY.value, "task_id": None, "user_id": None}),
        )

        await asyncio.gather(
            self.delete_message_if_there_is_any(exist_local=pay_calc_exist_local, message_type=MessageType.PAY_CALC.value, discord_message_id=self.pay_calc_message.id),
            self.delete_message_if_there_is_any(exist_local=listing_pay_exist_local, message_type=MessageType.LISTING_PAY.value, discord_message_id=self.listing_pay_message.id),
            self.delete_message_if_there_is_any(exist_local=update_pay_exist_local, message_type=MessageType.UPDATE_PAY.value, discord_message_id=self.update_pay_message.id)
        )

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
            self.calc_channel = await self.client.fetch_channel(CHANNELS["pay_calc"])
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
