import asyncio
import logging
import os
import discord
import json

from utils.guesty.GuestyTaskRequests import GuestyTaskRequests
from utils.guesty.GuestyUserRequests import GuestyUserRequests
from utils.guesty.GuestyListingRequests import GuestyListingRequests
from utils.guesty.GuestyReservationRequests import GuestyReservationRequests
from utils.database.DatabaseMultiOperations import DatabaseMultiOperations
from utils.FormatString import FormatString
from utils.Enums import TaskStatus, MessageType
from utils.discord.CallbackOperations import CallbackOperations
from config.keys import CHANNELS, TASK_TITLE, DELETE_AFTER_7_DAYS
from buttons.TaskButtonsView import TaskButtonsView
from components.ChannelManagement import ChannelManagement
from utils.discord.DiscordElements import DiscordElements
from utils.OrganizeGuestyData import OrganizeGuestyData
from controllers.MessageController import MessageController


class Initializer:
    def __init__(self, client):

        self.client = client
        self.guesty_task = GuestyTaskRequests()
        self.guesty_listing = GuestyListingRequests()
        self.guesty_user = GuestyUserRequests()
        self.guesty_reservation = GuestyReservationRequests()

        self.fs = FormatString()
        self.db = DatabaseMultiOperations()
        self.de = DiscordElements(client=client)
        self.cm = ChannelManagement(client=client)
        self.ogd = OrganizeGuestyData()
        self.mc = MessageController()

        self.all_guesty_tasks = []
        self.all_guesty_listings = []
        self.all_guesty_reservations = []
        self.all_guesty_users = []

        self.invalid_task_ids = set()
        self.tasks_within_seven_days = []
        self.available_cleaning_tasks = []

        self.us_today = self.fs.current_est_datetime_obj()

        self.update_many_users, self.update_many_tasks, self.update_many_messages = [], [], []
        self.success_messages = {}

    async def run(self, daily):
        """
        TODO:
            fetch all tasks, listings, users, discord members
            available cleaning: Remove all previous messages, Loop through tasks, search for message, insert or update task and message into database
            user's cleaning: Loop through users, check discord and guesty membership, send task message, and task upcoming chart
        """
        try:
            await self.fetch_and_organize(daily=daily)
            await self.user_tasks_update(daily=daily)
            await self.available_tasks_update(daily=daily)
            await asyncio.gather(*self.update_many_users, *self.update_many_tasks, *self.update_many_messages)
            logging.warning(json.dumps(self.success_messages))
        except Exception as e:
            logging.error(e)

    async def fetch_and_organize(self, daily):
        try:
            search_task_filters = {}  # "status":{"@nin":["canceled", "completed"]} ,"title":{"@in":["Clean", "clean", "CLEAN"]}
            self.all_guesty_tasks, self.all_guesty_listings = await asyncio.gather(
                self.guesty_task.find_all_tasks(filters=search_task_filters),
                self.guesty_listing.get_all_listing()
            )

            reservation_ids = []
            user_guesty_ids = set()
            for tI, t in enumerate(self.all_guesty_tasks):
                try:
                    is_invalid_task = False
                    if 'assigneeId' in t['assignee'] and t['assignee']['assigneeId'] is not None and t['assignee']['assigneeId'] not in user_guesty_ids:
                        user_guesty_ids.add(t['assignee']['assigneeId'])
                    if str(t["taskTitle"]['children']).lower() != TASK_TITLE:
                        is_invalid_task = True
                    if str(t['status']['status']).upper() == TaskStatus.COMPLETED.value.upper() or str(t['status']['status']).upper() == TaskStatus.CANCELED.value.upper():
                        is_invalid_task = True

                    if t['scheduledFor']["startTime"] is None:
                        continue

                    task_start_date = self.fs.iso_to_est_time(iso_time=t['scheduledFor']["startTime"]).date()
                    is_within_7_days = self.fs.is_within_forward_days(target_date=task_start_date, days=7)
                    if is_within_7_days is False:
                        is_invalid_task = True

                    if is_invalid_task:
                        # Find message and delete message from here ->
                        # if guesty_task_id does match add the delete request to queue and later make all requests at once from outside of this function
                        self.invalid_task_ids.add(t['id'])
                        continue

                    if 'reservationId' in t['reservation'] and t['reservation']['reservationId'] is not None:
                        reservation_ids.append(t['reservation']['reservationId'])
                    if t['assignee']['assigneeId'] is None:
                        self.available_cleaning_tasks.append(t)
                    self.tasks_within_seven_days.append(t)
                except Exception as tE:
                    continue

            reservation_search_filters = [{"field": "_id", "operator": "$in", "value": reservation_ids}]
            self.all_guesty_reservations = await self.guesty_reservation.find_all_reservations(filters=reservation_search_filters)
            self.all_guesty_users = await self.guesty_user.find_all_users()
            await self.de.find_all_members()
            self.success_messages["1"] = f"tasks -> {len(self.all_guesty_tasks)}, listings-> {len(self.all_guesty_listings)}, users-> {len(user_guesty_ids)}"
        except Exception as e:
            logging.error(e)

    async def user_tasks_update(self, daily):
        try:

            for guI, gu in enumerate(self.all_guesty_users):
                is_invalid_user = False
                if gu is None:
                    is_invalid_user = True
                discord_member = await self.de.find_member_by_nickname(nickname=gu['firstName'])
                user_channel_name = f"{gu['firstName'].lower()}-upcoming"
                if gu['firstName'].lower() == 'amanda':
                    print(gu['firstName'].lower())
                user_channel = discord.utils.get(self.client.get_all_channels(), guild__name=os.getenv("GUILD_NAME"),
                                                 name=user_channel_name)
                if discord_member is None and os.getenv('PY_ENV') == 'production':
                    is_invalid_user = True

                cb = CallbackOperations(client=self.client)
                guesty_user_id = gu["_id"]
                all_tasks_of_user = list(filter(lambda t: t['assignee']["assigneeId"] == guesty_user_id, self.tasks_within_seven_days))
                if len(all_tasks_of_user) == 0:
                    # Create an empty message
                    if user_channel:
                        prev_upcoming_chart = await self.mc.find_upcoming_tasks_message(user_channel=user_channel)
                        await cb.user_blank_tasks_chart(channel=user_channel, guesty_user_id=guesty_user_id, prev_message=prev_upcoming_chart)
                    is_invalid_user = True

                if is_invalid_user:
                    continue

                user_data = self.ogd.user_data_guesty(guesty_user=gu, discord_member=discord_member)

                # Database operations
                find_user_local = await self.db.find_one_user(doc_filter={"username": gu['firstName'].lower()})
                local_user_id = None
                if find_user_local:
                    local_user_id = find_user_local["_id"]
                else:
                    new_user = await self.db.insert_one_user(data=user_data)
                    local_user_id = new_user.inserted_id


                prev_upcoming_chart = None
                if user_channel is None:
                    user_channel = await self.cm.create_a_channel(channel_name=user_channel_name, discord_user=discord_member)
                else:
                    if daily is False:
                        await user_channel.purge()
                    else:
                        await self.mc.delete_redundant_messages(channel=user_channel, redundant_task_ids=list(self.invalid_task_ids), total_btns=2)
                        prev_upcoming_chart = await self.mc.find_upcoming_tasks_message(user_channel=user_channel, fetch_messages=True)

                if prev_upcoming_chart is None:
                    prev_upcoming_chart = await cb.user_blank_tasks_chart(channel=user_channel, guesty_user_id=guesty_user_id)

                # Loop through tasks of the user in 7 days
                # ===============================================================================================================
                tasks_of_user = []
                task_ids, message_ids = set(), set()

                for tou in all_tasks_of_user:
                    try:
                        guesty_task_id = tou["id"]
                        tasks_of_user.append(tou)

                        find_listing = next((l for l in self.all_guesty_listings if l["_id"] == tou['listing']['listingId']), None)
                        if find_listing is None:
                            continue
                        find_reservation = next(
                            (r for r in self.all_guesty_reservations if r is not None and 'reservationId' in tou['reservation'] and r["_id"] == tou['reservation']['reservationId']), None)
                        current_task_data = self.ogd.task_data_guesty_tfl(task=tou, reservation=find_reservation, listing=find_listing, local_user_id=local_user_id)

                        # Database Operations - find or create data
                        find_task_local = await self.db.find_one_task(doc_filter={"guesty_task_id": guesty_task_id})
                        local_task_id, local_message_id = None, None
                        if find_task_local:
                            local_task_id = find_task_local["_id"]
                        else:
                            new_task = await self.db.insert_one_task(data=current_task_data)
                            local_task_id = new_task.inserted_id

                        task_ids.add(local_task_id)

                        # check if there is already a task message or not and send task one by one
                        # ===============================================================================================================
                        start_datetime_obj = self.fs.iso_to_est_time(iso_time=tou['scheduledFor']['startTime'])
                        target_date = start_datetime_obj.date()
                        today_date = self.us_today.date()
                        if tou['status']['status'].lower() == TaskStatus.IN_PROGRESS.value.lower() or target_date == today_date:
                            task_button_view = TaskButtonsView()
                            prev_task_message = await self.mc.find_specific_task_message(channel=user_channel, target_guesty_task_id=guesty_task_id, total_btns=2, task_fetch=True)
                            new_embed = await self.mc.task_message_create_tfl(task=tou, all_listing=self.all_guesty_listings, all_reservations=self.all_guesty_reservations)
                            if tou['status']['status'].lower() == TaskStatus.IN_PROGRESS.value.lower():
                                task_button_view.task_complete(task_id=guesty_task_id, callback_func=cb.task_complete_callback)
                            else:
                                task_button_view.task_start(task_id=guesty_task_id, callback_func=cb.task_start_callback)
                            task_button_view.task_release(callback_func=cb.task_release_callback_from_single, task_id=guesty_task_id)

                            user_message = None
                            if prev_task_message:
                                user_message = await prev_task_message.edit(embed=new_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                            else:
                                user_message = await user_channel.send(embed=new_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                            discord_message_id = user_message.id

                            # Database operations
                            find_message_local = await self.db.find_one_message(doc_filter={"discord_message_id": discord_message_id})
                            message_data = self.ogd.msg_insert_data(user_id=local_user_id, message_type=MessageType.USER_MESSAGE.value, discord_message_id=discord_message_id, task_id=local_task_id,
                                                                    guesty_task_id=guesty_task_id)
                            if find_message_local:
                                local_message_id = find_message_local["_id"]
                                self.update_many_messages.append(asyncio.ensure_future(self.db.update_one_message(find_filters={"_id": local_message_id}, set_dict=message_data)))
                            else:
                                new_message = await self.db.insert_one_message(data=message_data)
                                local_message_id = new_message.inserted_id
                            message_ids.add(local_message_id)

                        if find_task_local:
                            current_task_data['message_id'] = local_message_id
                            self.update_many_tasks.append(asyncio.ensure_future(self.db.update_one_task(find_filters={"guesty_task_id": guesty_task_id}, set_dict=current_task_data)))
                    except Exception as utE:
                        continue

                # Show table or chart of user
                # ===============================================================================================================
                user_data["task_ids"] = list(task_ids)
                user_data["message_ids"] = list(message_ids)
                self.update_many_users.append(asyncio.ensure_future(self.db.update_one_user(find_filters={"_id": local_user_id}, set_dict=user_data)))
                user_task_chart_message = await cb.user_tasks_chart(channel=user_channel, task_list_of_user=tasks_of_user, guesty_user_id=guesty_user_id,
                                                                    prev_message=prev_upcoming_chart)  # use unorganized task instead
                local_message_id = None
                if user_task_chart_message:
                    discord_message_id = user_task_chart_message.id
                    find_message_local = await self.db.find_one_message(doc_filter={"discord_message_id": discord_message_id})
                    message_data = self.ogd.msg_insert_data(user_id=local_user_id, message_type=MessageType.USER_TASKS.value, discord_message_id=discord_message_id, guesty_user_id=guesty_user_id)
                    if find_message_local:
                        local_message_id = find_message_local["_id"]
                        self.update_many_messages.append(asyncio.ensure_future(self.db.update_one_message(find_filters={"_id": local_message_id}, set_dict=message_data)))
                    else:
                        new_message = await self.db.insert_one_message(data=message_data)
                        local_message_id = new_message.inserted_id

            self.success_messages["2"] = f"Daily-> {daily}"
        except Exception as e:
            logging.error(e)

    async def available_tasks_update(self, daily):
        try:
            available_cleaning_channel = self.client.get_channel(CHANNELS['available_cleaning'])

            if daily is False:
                await available_cleaning_channel.purge()

            if len(self.available_cleaning_tasks) == 0:
                self.success_messages["3"] = "available_tasks_update successfully made [no available cleaning]"
                return

            cb = CallbackOperations(client=self.client)

            await self.mc.fetch_prev_messages(target_channel=available_cleaning_channel)
            await self.mc.delete_redundant_messages(channel=available_cleaning_channel, redundant_task_ids=list(self.invalid_task_ids), total_btns=1, message_fetch=True)

            for actI, act in enumerate(self.available_cleaning_tasks):
                try:
                    guesty_task_id = act["id"]
                    task_button_view = TaskButtonsView()
                    # Add available cleaning that is under 7 days
                    # ===============================================================================================================
                    new_embed = await self.mc.task_message_create_tfl(task=act, all_listing=self.all_guesty_listings, all_reservations=self.all_guesty_reservations)
                    prev_task_message = await self.mc.find_specific_task_message(channel=available_cleaning_channel, target_guesty_task_id=guesty_task_id, total_btns=1, task_fetch=True)
                    task_add_button = task_button_view.task_add(task_id=guesty_task_id, callback_func=cb.task_add_callback)
                    task_button_view.add_item(task_add_button)
                    find_listing = next((l for l in self.all_guesty_listings if l["_id"] == act['listing']['listingId']), None)
                    if find_listing is None:
                        continue
                    find_reservation = next((r for r in self.all_guesty_reservations if r is not None and 'reservationId' in act['reservation'] and r["_id"] == act['reservation']['reservationId']),
                                            None)
                    current_task_data = self.ogd.task_data_guesty_tfl(task=act, reservation=find_reservation, listing=find_listing)
                    discord_message_id = None
                    if prev_task_message:
                        new_message = await prev_task_message.edit(embed=new_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                        discord_message_id = new_message.id
                    else:
                        new_message = await available_cleaning_channel.send(embed=new_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                        discord_message_id = new_message.id

                    # Database operations
                    find_task_local = await self.db.find_one_task(doc_filter={"guesty_task_id": guesty_task_id})
                    local_task_id = None
                    if find_task_local:
                        local_task_id = find_task_local["_id"]
                        self.update_many_tasks.append(asyncio.ensure_future(self.db.update_one_task(find_filters={"guesty_task_id": guesty_task_id}, set_dict=current_task_data)))
                    else:
                        new_task = await self.db.insert_one_task(data=current_task_data)
                        local_task_id = new_task.inserted_id
                    find_message_local = await self.db.find_one_message(doc_filter={"discord_message_id": discord_message_id})
                    message_data = self.ogd.msg_insert_data(user_id=None, message_type=MessageType.AVAILABLE_MESSAGE.value, discord_message_id=discord_message_id, task_id=local_task_id,
                                                            guesty_task_id=guesty_task_id)
                    local_message_id = None
                    if find_message_local:
                        local_message_id = find_message_local["_id"]
                        self.update_many_messages.append(asyncio.ensure_future(self.db.update_one_message(find_filters={"_id": local_message_id}, set_dict=message_data)))
                    else:
                        new_message = await self.db.insert_one_message(data=message_data)
                        local_message_id = new_message.inserted_id

                except Exception as actE:
                    continue
            self.success_messages["3"] = "available_tasks_update successfully made"
        except Exception as e:
            logging.error(e)
