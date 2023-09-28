import asyncio
import logging
import os
import discord

from config.keys import CHANNELS, DELETE_AFTER_7_DAYS
from buttons.TaskButtons import TaskButtons
from utils.guesty.GuestyTaskRequests import GuestyTaskRequests
from components.ChannelManagement import ChannelManagement
from buttons.TaskButtonsView import TaskButtonsView
from bot import client
from utils.Enums import TaskStatus, MessageType
from utils.guesty.GuestyUserRequests import GuestyUserRequests
from controllers.ControllerBase import ControllerBase
from utils.FormatString import FormatString
from utils.discord.CallbackOperations import CallbackOperations
from utils.database.DatabaseMultiOperations import DatabaseMultiOperations
from controllers.MessageController import MessageController
from utils.OrganizeGuestyData import OrganizeGuestyData
from utils.discord.DiscordElements import DiscordElements


class TaskController(ControllerBase):
    def __init__(self, task=None):
        super().__init__()
        self.task = task
        self.fs = FormatString()
        self.guesty_user = GuestyUserRequests()
        self.guesty_task = GuestyTaskRequests()
        self.client = client
        self.mc = MessageController()
        self.ogd = OrganizeGuestyData()
        self.de = DiscordElements(client=client)

    async def task_add_to_available_cleaning_channel(self, task_single, listing_single, reservation_single):
        try:
            # Organize message
            # ===============================================================================================================
            guesty_task_id = self.task["_id"]
            task_embed = await self.mc.task_message_create(guesty_task_id=guesty_task_id, guesty_task=task_single, listing_single=listing_single, reservation_single=reservation_single)


            # Send message
            # ===============================================================================================================
            """
            Get a channel by ID. Returns a channel object. If the channel is a thread, a thread member object is included in the returned result. : https://discord.com/developers/docs/resources/channel#get-channel
            Get the TextChannel object for the desired channel -> https://discordpy.readthedocs.io/en/stable/api.html?highlight=embed#discord.Client.get_channel
            """
            available_cleaning_channel = self.client.get_channel(CHANNELS['available_cleaning'])

            if available_cleaning_channel is None:
                return

            cb = CallbackOperations(client=self.client)
            task_buttons = TaskButtons(client=self.client)
            task_buttons.task_add(task_id=guesty_task_id, callback_func=cb.task_add_callback)

            """
            Post a message to a guild text or DM channel - https://discord.com/developers/docs/resources/channel#create-message
            Represents a Discord direct message channel. - https://discordpy.readthedocs.io/en/stable/api.html?highlight=messageable#discord.DMChannel.send
            """
            prev_message = await self.mc.find_specific_task_message(channel=available_cleaning_channel, target_guesty_task_id=guesty_task_id, total_btns=1)
            new_message = None
            if prev_message:
                new_message = await prev_message.edit(embed=task_embed, view=task_buttons, delete_after=DELETE_AFTER_7_DAYS)
            else:
                new_message = await available_cleaning_channel.send(embed=task_embed, view=task_buttons, delete_after=DELETE_AFTER_7_DAYS)
            discord_message_id = new_message.id
            # print(f"\033[36mMessage ID -> add task to available cleaning--> \033[0m", {'msg_id': message.id, 'tid': task_id})

            # DB Operations
            # ===============================================================================================================
            db = DatabaseMultiOperations()
            find_task_local = await db.find_one_task(doc_filter={"guesty_task_id": guesty_task_id})
            local_task_id = None
            task_data = self.ogd.task_data_guesty(task=task_single, reservation=reservation_single, listing=listing_single)
            if find_task_local is None:
                task_data['guesty_task_id'] = guesty_task_id
                new_task = await db.insert_one_task(data=task_data)
                local_task_id = new_task.inserted_id
            else:
                local_task_id = find_task_local["_id"]

            find_message_local = await db.find_one_message(doc_filter={"task_id": local_task_id})
            message_data = self.ogd.msg_insert_data(user_id=None, message_type=MessageType.AVAILABLE_MESSAGE.value, discord_message_id=discord_message_id, task_id=local_task_id, guesty_task_id=guesty_task_id)

            local_message_id = None
            if find_message_local is None:
                new_message = await db.insert_one_message(data=message_data)
                local_message_id = new_message.inserted_id
            else:
                local_message_id = find_message_local["_id"]

            task_data["message_id"] = local_message_id
            if find_task_local and 'user_id' in find_task_local and find_task_local['user_id'] is not None:
                result = await db.update_one_user(find_filters={"_id": find_task_local["user_id"]}, push_dict={"task_ids": local_task_id, "message_ids": local_message_id})
            await asyncio.gather(
                db.update_one_task(find_filters={"guesty_task_id": guesty_task_id}, set_dict=task_data),
                db.update_one_message(find_filters={"_id": local_message_id}, set_dict=message_data)
            )
        except Exception as e:
            logging.error(e)

    async def task_add_to_user_channel(self, task_single, listing_single, reservation_single):
        try:
            guesty_user_id = self.task['assigneeId']
            guesty_task_id = self.task["_id"]
            start_time = self.task['startTime']

            # Send message to user channel
            # ===============================================================================================================
            find_guesty_user, user_tasks = await asyncio.gather(
                self.guesty_user.retrieve_a_user(guesty_user_id=guesty_user_id),
                self.guesty_task.all_tasks_of_an_user(guesty_user_id=guesty_user_id)
            )
            if find_guesty_user is None:
                return None
            guesty_firstname = str(find_guesty_user['firstName']).lower()
            await self.de.find_all_members()
            discord_member = await self.de.find_member_by_nickname(nickname=guesty_firstname)
            if discord_member is None:
                return None
            user_channel_name = f"{guesty_firstname}-upcoming"
            user_channel = discord.utils.get(self.client.get_all_channels(), guild__name=os.getenv("GUILD_NAME"),
                                             name=user_channel_name)
            prev_message = None
            if user_channel is None:
                cm = ChannelManagement(client=self.client)
                user_channel = await cm.create_a_channel(channel_name=user_channel_name, discord_user=discord_member)
            else:
                prev_message = await self.mc.find_specific_task_message(channel=user_channel, target_guesty_task_id=guesty_task_id, total_btns=2)

            us_today = self.fs.current_est_datetime_obj()
            discord_message_id = None
            cb = CallbackOperations(client=self.client)
            us_datetime_obj = self.fs.iso_to_time_obj(isoformat=start_time)
            if us_today.year == us_datetime_obj.year and us_datetime_obj.month == us_today.month and us_datetime_obj.day == us_today.day:
                # Organize message
                # ===============================================================================================================
                task_embed = await self.mc.task_message_create(guesty_task_id=guesty_task_id, guesty_task=task_single, listing_single=listing_single, reservation_single=reservation_single)
                task_button_view = TaskButtonsView()
                task_button_view.task_start(task_id=guesty_task_id, callback_func=cb.task_start_callback)
                task_button_view.task_release(callback_func=cb.task_release_callback_from_single, task_id=guesty_task_id)
                new_message = None
                if prev_message:
                    new_message = await prev_message.edit(embed=task_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                else:
                    new_message = await user_channel.send(embed=task_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                discord_message_id = new_message.id

            # DB Operations
            # ===============================================================================================================
            db = DatabaseMultiOperations()
            find_user_local = await db.find_one_user(doc_filter={"guesty_user_id": guesty_user_id})
            user_data = self.ogd.user_data_guesty(guesty_user=find_guesty_user, discord_member=discord_member)
            local_user_id = None
            if find_user_local is None:
                new_user = await db.insert_one_user(data=user_data)
                local_user_id = new_user.inserted_id
            else:
                del user_data['task_ids']
                del user_data['message_ids']
                local_user_id = find_user_local["_id"]
            # and update task as well
            find_task_local = await db.find_one_task(doc_filter={"guesty_task_id": guesty_task_id})
            task_data = self.ogd.task_data_guesty(task=task_single, reservation = reservation_single, listing=listing_single, local_user_id=local_user_id)
            local_task_id = None
            if find_task_local is None:
                new_task = await db.insert_one_task(data=task_data)
                local_task_id = new_task.inserted_id
            else:
                local_task_id = find_task_local["_id"]

            find_message_local = await db.find_one_message(doc_filter={"task_id": local_task_id})
            local_message_id = None
            message_data = self.ogd.msg_insert_data(user_id=local_user_id, message_type=MessageType.USER_MESSAGE.value,
                                                    discord_message_id=discord_message_id, task_id=local_task_id, guesty_task_id=guesty_task_id)
            if find_message_local is None:
                new_message = await db.insert_one_message(data=message_data)
                local_message_id = new_message.inserted_id
            else:
                local_message_id = find_message_local["_id"]

            task_data["message_id"] = local_message_id
            await asyncio.gather(
                db.update_one_task(find_filters={"guesty_task_id": guesty_task_id}, set_dict=task_data),
                db.update_one_message(find_filters={"_id": local_message_id}, set_dict=message_data),
                db.update_one_user(find_filters={"_id": local_user_id}, push_dict={"task_ids": local_task_id, 'message_ids': local_message_id})
            )

            # Display table
            task_chart_message = await cb.user_tasks_chart(channel=user_channel, task_list_of_user=user_tasks, guesty_user_id=guesty_user_id)
            user_chart_msg_id = await cb.save_user_chart_message(task_chart_message=task_chart_message, db=db, local_user_id=local_user_id, guesty_user_id=guesty_user_id)
        except Exception as e:
            logging.error(e)




