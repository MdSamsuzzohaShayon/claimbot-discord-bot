import logging
import discord
import os
import asyncio

from utils.database.DatabaseMultiOperations import DatabaseMultiOperations
from utils.discord.NotificationManagement import NotificationManagement
from utils.guesty.GuestyUserRequests import GuestyUserRequests
from utils.guesty.GuestyListingRequests import GuestyListingRequests
from utils.guesty.GuestyReservationRequests import GuestyReservationRequests
from utils.guesty.GuestyTaskRequests import GuestyTaskRequests
from utils.FormatString import FormatString
from config.keys import CHANNELS, DELETE_AFTER_7_DAYS, CLEANING_TITLES
from buttons.TaskButtonsView import TaskButtonsView
from utils.discord.CallbackOperations import CallbackOperations
from controllers.MessageController import MessageController
from utils.Enums import MessageType, TaskStatus
from components.ChannelManagement import ChannelManagement
from utils.OrganizeGuestyData import OrganizeGuestyData
from utils.discord.DiscordElements import DiscordElements


class TaskUpdateController:

    def __init__(self, guesty_task_id, client, task, task_before, task_today, is_within_7_days):

        # Initial setter variables
        self.guesty_task_id = guesty_task_id
        self.task_today = task_today
        self.is_within_7_days = is_within_7_days
        self.client = client
        self.task = task
        self.task_before = task_before

        # Classes Declarations
        self.fs = FormatString()
        self.mc = MessageController()
        self.cm = ChannelManagement(client=client)
        self.guesty_user = GuestyUserRequests()
        self.guesty_listing = GuestyListingRequests()
        self.guesty_reservation = GuestyReservationRequests()
        self.guesty_task = GuestyTaskRequests()
        self.db = DatabaseMultiOperations()
        self.de = DiscordElements(client=client)
        self.nm = NotificationManagement(client=client)
        self.ogd = OrganizeGuestyData()

        # Db variables
        self.find_local_task = None
        self.find_local_curr_user = None
        self.find_local_prev_user = None
        self.find_local_message = None

        # Guesty variables
        self.find_guesty_listing = None
        self.find_guesty_reservation = None
        self.find_guesty_curr_user = None
        self.find_guesty_prev_user = None

        # Update variables
        self.curr_user_update_dict = {}
        self.prev_user_update_dict = {}
        self.task_update_dict = {}
        self.message_update_dict = {}

        # Variables for updating API
        self.operation_at_the_end = []

        # Discord
        self.available_cleaning_channel = None
        self.curr_user_channel = None
        self.prev_user_channel = None
        self.discord_curr_user = None
        self.discord_prev_user = None

        # Variables of the class
        self.user_task_message = None
        self.available_task_message = None
        self.remove_message_id = None
        self.add_message_to_user = None

    async def task_cancel(self):
        """
        TODO:
            find task by guesty id and find message
            If the task is assigned to someone send notification to user (DM) and remove that message
            Update user tasks table -> remove deleted task from the table
            if the task is in available cleaning channel remove that message too
        """
        try:
            # if self.find_local_task is None:
            #     await self.fetch_and_insert()

            guesty_task_id = self.task["_id"]
            # Delete the message if message is exist
            # ===============================================================================================================
            if "assigneeId" not in self.task or self.task["assigneeId"] is None:
                await self.remove_task_from_available_cleaning()
            else:
                guesty_user_id = self.task["assigneeId"]
                if self.find_local_curr_user is None:
                    create_user = await self.create_curr_user_in_db()
                    if create_user is False:
                        return False
                discord_message_id = await self.remove_task_from_curr_user(curr_username=self.find_local_curr_user['username'])
                if discord_message_id:
                    # Db operations
                    message_to_user = f"A task is been canceled!"
                    await self.nm.notify_specific_user(user_discord_id=self.discord_curr_user.id, message=message_to_user, task_id=guesty_task_id)
            print("Task cancelled successfully")
            return True
        except Exception as e:
            logging.error(e)
            return False

    async def task_revive(self):
        """
        TODO:
            Do mostly opposite of task cancel
            Take action according to not change status from discord interaction
            make a few more if statement or if else statement to Check
            what type of status is made and take action according the that status
        """
        try:
            await self.find_listing_reservation_from_guesty()
            if self.find_local_task is None:
                create_new_task = await self.create_task_in_db()
                if create_new_task is False:
                    return False

            if "assigneeId" not in self.task or self.task["assigneeId"] is None:
                self.available_cleaning_channel = await self.client.fetch_channel(CHANNELS['available_cleaning'])
                new_message = await self.add_task_message_to_available_cleaning()
            else:
                username = None
                guesty_user_id = self.task["assigneeId"]
                if self.find_local_curr_user is None:
                    create_user = await self.create_curr_user_in_db()
                    if create_user is False:
                        return False
                    username = self.find_guesty_curr_user['firstName']
                    # Update-user from here
                else:
                    username = self.find_local_curr_user['username']

                if self.task_today:
                    new_message = await self.add_task_message_to_user(username=username)
                    if new_message is None:
                        return False

            print("Task Revived successfully")
            return True
        except Exception as e:
            logging.error(e)
            return False

    async def task_assignee_change(self):
        try:
            # Get user, message, task
            guesty_task_id = self.task["_id"]
            prev_assignee_id = self.task_before["assigneeId"] if 'assigneeId' in self.task_before else None
            curr_assignee_id = self.task["assigneeId"] if 'assigneeId' in self.task else None

            # Prevent add task and release task callback calling again
            await asyncio.sleep(60)  # Delay 1 minute - at that time a message will be created from another event trigger

            if self.task['status'].upper() == TaskStatus.CANCELED.value:
                return False

            message_already_exist, curr_username, prev_username = None, None, None
            if self.find_local_prev_user is None:
                create_user = await self.create_prev_user_in_db()

            curr_username = self.find_local_curr_user['username'] if self.find_local_curr_user is not None else None
            prev_username = self.find_local_prev_user['username'] if self.find_local_prev_user is not None else None

            # Check current user or available cleaning has a message or not
            # ===============================================================================================================
            if "assigneeId" not in self.task or self.task["assigneeId"] is None:
                self.available_cleaning_channel = await self.client.fetch_channel(CHANNELS['available_cleaning'])
                message_already_exist = await self.mc.find_specific_task_message(channel=self.available_cleaning_channel, target_guesty_task_id=guesty_task_id, total_btns=1)
            else:
                if self.find_local_curr_user is None:
                    create_user = await self.create_curr_user_in_db()
                    if create_user is False:
                        return False
                curr_username = self.find_local_curr_user['username'] if self.find_local_task is not None else None
                if curr_username is not None:
                    channel_name = f"{curr_username.lower()}-upcoming"
                    self.curr_user_channel = discord.utils.get(self.client.get_all_channels(), guild__name=os.getenv("GUILD_NAME"),
                                                               name=channel_name)
                if self.curr_user_channel:
                    message_already_exist = await self.mc.find_specific_task_message(channel=self.curr_user_channel, target_guesty_task_id=guesty_task_id, total_btns=2)

            if message_already_exist:
                logging.warning("Can not add task again! message already exist")
                return False

            await self.find_listing_reservation_from_guesty()

            if self.find_local_task is None:
                create_new_task = await self.create_task_in_db()
                if create_new_task is False:
                    return False

            # Remove message from previous user and available cleaning
            if prev_assignee_id:
                remove_user_message_id = await self.remove_task_from_prev_user(prev_username=prev_username)
            if curr_assignee_id is not None:
                remove_available_message_id = await self.remove_task_from_available_cleaning()
            if curr_assignee_id is None:
                # Remove message from current user
                remove_message_id = await self.remove_task_from_curr_user(curr_username=curr_username)

            # Send message if task is today
            # ===============================================================================================================
            new_message = None
            if curr_assignee_id:
                new_message = await self.add_task_message_to_user(username=curr_username)
            else:
                new_message = await self.add_task_message_to_available_cleaning()

            if new_message is None:
                return False

            # Send notifications to both users and show the table
            # ===============================================================================================================
            message_to_user = f"Assignee has been changed for a task"
            send_notifications_list = []
            if curr_assignee_id:
                send_notifications_list.append(asyncio.ensure_future(self.nm.notify_specific_user(user_discord_id=self.discord_curr_user.id, message=message_to_user, task_id=guesty_task_id)))
            if prev_assignee_id:
                if self.discord_prev_user is None:
                    await self.de.find_all_members()
                    self.discord_curr_user = await self.de.find_member_by_nickname(nickname=prev_username)
                send_notifications_list.append(asyncio.ensure_future(self.nm.notify_specific_user(user_discord_id=self.discord_prev_user.id, message=message_to_user, task_id=guesty_task_id)))
            await asyncio.gather(*send_notifications_list)

            return True
        except Exception as e:
            logging.error(e)
            return False

    async def task_reschedule(self):
        """
        TODO:
            if starting time change let the user know in notification
            Update user's message if a user is assigned
            Update message on available cleaning channel if the user not assigned
        """
        try:
            guesty_task_id = self.task["_id"]

            await self.find_listing_reservation_from_guesty()
            if self.find_local_task is None:
                create_new_task = await self.create_task_in_db()
                if create_new_task is False:
                    return False

            add_task = True
            task_status = self.task['status'].upper()
            if self.task_today and (task_status != TaskStatus.COMPLETED.value or task_status != TaskStatus.CANCELED.value):
                add_task = True
            else:
                add_task = False

            if "assigneeId" not in self.task or self.task["assigneeId"] is None or self.task is None:
                self.available_cleaning_channel = await self.client.fetch_channel(CHANNELS['available_cleaning'])

                if add_task:
                    new_message = await self.add_task_message_to_available_cleaning()
                else:
                    deleted_message_id = await self.remove_task_from_available_cleaning()

            else:
                # check if there is already a task message or not
                username = None
                guesty_user_id = None
                if self.find_local_curr_user is None:
                    create_user = await self.create_curr_user_in_db()
                    if create_user is False:
                        return False
                    username = self.find_guesty_curr_user['firstName']
                    guesty_user_id = self.find_guesty_curr_user["_id"]
                else:
                    username = self.find_local_curr_user['username']
                    guesty_user_id = self.find_local_curr_user["guesty_user_id"]

                if add_task:
                    new_message = await self.add_task_message_to_user(username=username)
                else:
                    deleted_message_id = await self.remove_task_from_curr_user(curr_username=username)

                # Send notification to the user
                message_to_user = f"Date has been changed for a cleaning"
                await self.nm.notify_specific_user(user_discord_id=self.discord_curr_user.id, message=message_to_user, task_id=guesty_task_id)
            return True
        except Exception as e:
            logging.error(e)
            return False

    # Common functions
    # ===============================================================================================================
    async def remove_task_from_curr_user(self, curr_username):
        try:
            if curr_username is None:
                return None
            channel_name = f"{curr_username.lower()}-upcoming"
            self.curr_user_channel = discord.utils.get(self.client.get_all_channels(), guild__name=os.getenv("GUILD_NAME"),
                                                       name=channel_name)
            if self.curr_user_channel is None:
                return None
            await self.de.find_all_members()
            self.discord_curr_user = await self.de.find_member_by_nickname(nickname=curr_username)
            if self.discord_curr_user is None:
                return None

            self.remove_message_id = await self.remove_the_message(user_channel=self.curr_user_channel)
            return self.remove_message_id

        except Exception as e:
            logging.error(e)

    async def remove_task_from_prev_user(self, prev_username):
        try:
            if prev_username is None:
                return None
            channel_name = f"{prev_username.lower()}-upcoming"
            self.prev_user_channel = discord.utils.get(self.client.get_all_channels(), guild__name=os.getenv("GUILD_NAME"),
                                                       name=channel_name)
            if self.prev_user_channel is None:
                return None
            await self.de.find_all_members()
            self.discord_prev_user = await self.de.find_member_by_nickname(nickname=prev_username)
            if self.discord_prev_user is None:
                return None

            self.remove_message_id = await self.remove_the_message(user_channel=self.prev_user_channel)
            return self.remove_message_id
        except Exception as e:
            logging.error(e)

    async def remove_the_message(self, user_channel):
        prev_message = await self.mc.find_specific_task_message(channel=user_channel, target_guesty_task_id=self.task["_id"], total_btns=2)
        delete_message_id = None
        if prev_message is not None:
            delete_message_id = prev_message.id
            await prev_message.delete()
        self.remove_message_id = delete_message_id
        return delete_message_id

    async def remove_task_from_available_cleaning(self):
        try:
            if self.available_cleaning_channel is None:
                self.available_cleaning_channel = await self.client.fetch_channel(CHANNELS['available_cleaning'])
            prev_message = await self.mc.find_specific_task_message(channel=self.available_cleaning_channel, target_guesty_task_id=self.task["_id"], total_btns=1)
            delete_message_id = None
            if prev_message is not None:
                delete_message_id = prev_message.id
                await prev_message.delete()
            self.remove_message_id = delete_message_id
            return delete_message_id
        except Exception as e:
            logging.error(e)

    async def add_task_message_to_user(self, username):
        try:
            if username is None:
                return None
            guesty_task_id = self.task["_id"]
            user_channel_name = f"{username.lower()}-upcoming"

            await self.de.find_all_members()
            self.discord_curr_user = await self.de.find_member_by_nickname(nickname=username)
            if self.discord_curr_user is None:
                return None

            # check current user channel is already exist or not
            if not (self.curr_user_channel and self.curr_user_channel.name == user_channel_name):
                self.curr_user_channel = discord.utils.get(self.client.get_all_channels(), guild__name=os.getenv("GUILD_NAME"),
                                                           name=user_channel_name)
            prev_message = None
            if self.curr_user_channel is None:
                self.curr_user_channel = await self.cm.create_a_channel(channel_name=user_channel_name, discord_user=self.discord_curr_user)
            else:
                prev_message = await self.mc.find_specific_task_message(channel=self.curr_user_channel, target_guesty_task_id=guesty_task_id, total_btns=2)

            task_status = self.task['status'].upper()
            if self.task_today and (task_status != TaskStatus.COMPLETED.value or task_status != TaskStatus.CANCELED.value):
                new_embed = await self.mc.task_message_create(guesty_task_id=guesty_task_id, title=CLEANING_TITLES["cleaning_added"], guesty_task=self.task, listing_single=self.find_guesty_listing,
                                                              reservation_single=self.find_guesty_reservation)
                cb = CallbackOperations(client=self.client)
                task_button_view = TaskButtonsView()
                task_button_view.task_start(task_id=guesty_task_id, callback_func=cb.task_start_callback)
                task_button_view.task_release(task_id=guesty_task_id, callback_func=cb.task_release_callback)
                new_message = None
                if prev_message:
                    new_message = await prev_message.edit(embed=new_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                else:
                    new_message = await self.curr_user_channel.send(embed=new_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                self.user_task_message = new_message
                self.add_message_to_user = True
            elif prev_message:
                await prev_message.delete()

            return self.user_task_message
        except Exception as e:
            logging.error(e)
            return None

    async def add_task_message_to_available_cleaning(self):
        try:
            guesty_task_id = self.task["_id"]
            task_status = self.task['status'].upper()
            prev_message = await self.mc.find_specific_task_message(channel=self.available_cleaning_channel, target_guesty_task_id=guesty_task_id, total_btns=1)
            if self.is_within_7_days and (task_status != TaskStatus.COMPLETED.value or task_status != TaskStatus.CANCELED.value):
                new_embed = await self.mc.task_message_create(guesty_task_id=guesty_task_id, title=CLEANING_TITLES["cleaning_available"], guesty_task=self.task, listing_single=self.find_guesty_listing,
                                                              reservation_single=self.find_guesty_reservation)
                cb = CallbackOperations(client=self.client)
                task_button_view = TaskButtonsView()
                add_button = task_button_view.task_add(task_id=guesty_task_id, callback_func=cb.task_add_callback)
                task_button_view.add_item(add_button)
                new_message = None
                if prev_message:
                    new_message = await prev_message.edit(embed=new_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                else:
                    new_message = await self.available_cleaning_channel.send(embed=new_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                self.available_task_message = new_message
                self.add_message_to_user = False
            elif prev_message:
                await prev_message.delete()

            return self.available_task_message
        except Exception as e:
            logging.error(e)

    async def find_listing_reservation_from_guesty(self):
        try:
            # fetch listing and reservation
            # ===============================================================================================================
            listing_id = self.task["listingId"] if "listingId" in self.task and self.task["listingId"] is not None else None
            reservation_id = self.task["reservationId"] if "reservationId" in self.task and self.task["reservationId"] is not None else None
            self.find_guesty_listing, self.find_guesty_reservation = await asyncio.gather(
                self.guesty_listing.retrive_a_listing(listing_id=listing_id),
                self.guesty_reservation.retrive_a_reservation(reservation_id=reservation_id)
            )
        except Exception as e:
            logging.error(e)

    async def create_curr_user_in_db(self):
        try:
            self.find_guesty_curr_user = await self.guesty_user.retrieve_a_user(guesty_user_id=self.task["assigneeId"])
            if self.find_guesty_curr_user is None:
                return False
            user_data = self.ogd.user_data_guesty(guesty_user=self.find_guesty_curr_user, discord_member=self.discord_curr_user)
            new_user = await self.db.insert_one_user(data=user_data)
            self.find_local_curr_user = await self.db.find_one_user(doc_filter={'_id': new_user.inserted_id})
            return True
        except Exception as e:
            logging.error(e)
            return False

    async def create_prev_user_in_db(self):
        try:
            self.find_guesty_prev_user = await self.guesty_user.retrieve_a_user(guesty_user_id=self.task_before["assigneeId"])
            if self.find_guesty_prev_user is None:
                return False
            user_data = self.ogd.user_data_guesty(guesty_user=self.find_guesty_prev_user, discord_member=self.discord_prev_user)
            new_user = await self.db.insert_one_user(data=user_data)
            self.find_local_prev_user = await self.db.find_one_user(doc_filter={'_id': new_user.inserted_id})
            return True
        except Exception as e:
            logging.error(e)
            return False

    async def create_task_in_db(self):
        try:
            new_task_data = self.ogd.task_data_guesty(task=self.task, reservation=self.find_guesty_reservation, listing=self.find_guesty_listing)
            new_task = await self.db.insert_one_task(data=new_task_data)
            self.find_local_task = await self.db.find_one_task(doc_filter={"_id": new_task.inserted_id})
            return self.find_local_task
        except Exception as e:
            logging.error(e)

    async def return_fake_document(self):
        return None

    async def find_from_db(self, guesty_curr_u_id, guesty_prev_u_id, guesty_task_id):
        try:
            if guesty_curr_u_id == guesty_prev_u_id:
                guesty_prev_u_id = None
            find_doc_from_db_list = []
            if guesty_curr_u_id:
                find_doc_from_db_list.append(asyncio.ensure_future(self.db.find_one_user(doc_filter={"guesty_user_id": guesty_curr_u_id})))
            else:
                find_doc_from_db_list.append(asyncio.ensure_future(self.return_fake_document()))

            if guesty_prev_u_id:
                find_doc_from_db_list.append(asyncio.ensure_future(self.db.find_one_user(doc_filter={"guesty_user_id": guesty_prev_u_id})))
            else:
                find_doc_from_db_list.append(asyncio.ensure_future(self.return_fake_document()))

            find_doc_from_db_list.append(asyncio.ensure_future(self.db.find_one_task(doc_filter={"guesty_task_id": guesty_task_id})))
            find_doc_from_db_list.append(asyncio.ensure_future(self.db.find_one_message(doc_filter={"guesty_task_id": guesty_task_id})))

            self.find_local_curr_user, self.find_local_prev_user, self.find_local_task, self.find_local_message = await asyncio.gather(*find_doc_from_db_list)
        except Exception as e:
            logging.error(e)

    async def update_user_channel(self, guesty_user_id):
        try:
            if self.find_local_curr_user is None and self.find_local_prev_user is None:
                return None
            cb = CallbackOperations(client=self.client)
            prev_message, user_channel, target_guesty_user_id, local_user_id = None, None, None, None
            fetch_message = True if len(self.mc.message_list) > 0 else False

            if self.find_local_curr_user is not None and self.find_local_curr_user['guesty_user_id'] == guesty_user_id:
                local_user_id = self.find_local_curr_user["_id"]
                target_guesty_user_id = self.find_local_curr_user['guesty_user_id']
                prev_message = await self.mc.find_upcoming_tasks_message(user_channel=self.curr_user_channel, fetch_messages=fetch_message)
                user_channel = self.curr_user_channel
            elif self.find_local_prev_user is not None and self.find_local_prev_user['guesty_user_id'] == guesty_user_id:
                local_user_id = self.find_local_prev_user["_id"]
                target_guesty_user_id = self.find_local_prev_user['guesty_user_id']
                prev_message = await self.mc.find_upcoming_tasks_message(user_channel=self.prev_user_channel)
                user_channel = self.prev_user_channel

            if target_guesty_user_id is None:
                return None

            user_task_list = await self.db.find_tasks(doc_filters={"user_id": local_user_id})
            task_chart_message = await cb.tasks_of_a_user(guesty_user_id=target_guesty_user_id, channel=user_channel, user_task_list=user_task_list, prev_message=prev_message)
            user_chart_msg_id = await cb.save_user_chart_message(task_chart_message=task_chart_message, db=self.db, local_user_id=local_user_id, guesty_user_id=target_guesty_user_id)
        except Exception as e:
            logging.error(e)

    async def update_from_db(self, task_must, curr_user_must, message_must, prev_user_must=False, delete_task=False):
        try:
            guesty_curr_user_id = self.find_guesty_curr_user['_id'] if self.find_guesty_curr_user else None
            guesty_prev_user_id = self.find_guesty_prev_user['_id'] if self.find_guesty_prev_user else None

            local_task_id = self.find_local_task["_id"] if self.find_local_task is not None else None
            local_message_id = self.find_local_message["_id"] if self.find_local_message is not None else None
            local_curr_u_id = self.find_local_curr_user['_id'] if self.find_local_curr_user is not None else None
            local_prev_u_id = self.find_local_prev_user['_id'] if self.find_local_prev_user is not None else None

            all_updates = []

            # Update message
            # ===============================================================================================================
            message_type = MessageType.USER_MESSAGE.value if self.add_message_to_user else MessageType.AVAILABLE_MESSAGE.value
            discord_message_id = None
            if self.add_message_to_user is True and self.user_task_message:
                discord_message_id = self.user_task_message.id
            elif self.add_message_to_user is False and self.available_task_message:
                discord_message_id = self.available_task_message.id

            if self.find_local_message and message_must and task_must:
                message_update_data = {"type": message_type, 'task_id': local_task_id, 'guesty_task_id': self.guesty_task_id, "discord_message_id": discord_message_id}
                all_updates.append(asyncio.ensure_future(self.db.update_one_message(find_filters={"guesty_task_id": self.guesty_task_id}, set_dict=message_update_data)))
                local_message_id = self.find_local_message['_id']
            elif self.find_local_message is None and message_must and task_must is True:
                new_message_data = self.ogd.msg_insert_data(message_type=message_type, discord_message_id=discord_message_id, task_id=local_task_id, guesty_task_id=self.guesty_task_id,
                                                            guesty_user_id=guesty_curr_user_id)
                local_task = await self.db.insert_one_message(data=new_message_data)
                local_message_id = local_task.inserted_id
            elif self.find_local_message and task_must is False:
                await self.db.delete_one_message(filters={"_id": local_message_id})

            # Update task
            # ===============================================================================================================
            if self.find_local_task and delete_task is False:
                task_update_data = {"status": self.task['status'].upper(), 'start_time': self.task['startTime'], 'user_id': local_curr_u_id, 'message_id': local_message_id}
                all_updates.append(asyncio.ensure_future(self.db.update_one_task(find_filters={"guesty_task_id": self.guesty_task_id}, set_dict=task_update_data)))
                local_task_id = self.find_local_task['_id']
            elif self.find_local_task and delete_task is True:
                await self.db.delete_one_task(filters={'_id': local_task_id})
            # elif self.find_local_task and task_must is False:
            #     await self.db.delete_one_task(filters={'_id': local_task_id})

            # Update current user, previous user
            # ===============================================================================================================
            if self.find_local_curr_user and self.add_message_to_user:
                curr_guesty_u_id = self.find_local_curr_user['guesty_user_id']
                all_updates.append(
                    asyncio.ensure_future(self.db.update_one_user(find_filters={'guesty_user_id': curr_guesty_u_id}, push_dict={'task_ids': local_task_id, 'message_ids': local_message_id})))
            if self.find_local_prev_user and prev_user_must:
                prev_guesty_u_id = self.find_local_prev_user['guesty_user_id']
                all_updates.append(
                    asyncio.ensure_future(self.db.update_one_user(find_filters={'guesty_user_id': prev_guesty_u_id}, pull_dict={'task_ids': local_task_id, 'message_ids': local_message_id})))
            if curr_user_must and self.find_local_curr_user and task_must is False:
                curr_guesty_u_id = self.find_local_curr_user['guesty_user_id']
                all_updates.append(
                    asyncio.ensure_future(self.db.update_one_user(find_filters={'guesty_user_id': curr_guesty_u_id}, pull_dict={'task_ids': local_task_id, 'message_ids': local_message_id})))

            await asyncio.gather(*all_updates)
        except Exception as e:
            logging.error(e)

    async def update_discord_user_chart(self):
        try:
            prev_assignee_id = self.task_before["assigneeId"] if self.task_before is not None and 'assigneeId' in self.task_before else None
            curr_assignee_id = self.task["assigneeId"] if 'assigneeId' in self.task else None
            update_user_chart_list = []
            if self.curr_user_channel:
                update_user_chart_list.append(asyncio.ensure_future(self.update_user_channel(guesty_user_id=curr_assignee_id)))
            if self.prev_user_channel:
                update_user_chart_list.append(asyncio.ensure_future(self.update_user_channel(guesty_user_id=prev_assignee_id)))
            await asyncio.gather(*update_user_chart_list)
        except Exception as e:
            logging.error(e)
