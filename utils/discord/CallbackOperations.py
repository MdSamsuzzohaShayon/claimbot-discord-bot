# In-built
import json
import logging
import discord
import re
import asyncio
import os

from utils.FormatString import FormatString
from components.ChannelManagement import ChannelManagement

# Config
from config.keys import CHANNELS, DELETE_AFTER_1_DAY, DELETE_AFTER_7_DAYS, CLEANING_TITLES, TASK_CHART_TITLE

# Utils
from utils.database.DatabaseMultiOperations import DatabaseMultiOperations
from utils.DisplayTable import DisplayTable
from utils.Enums import TaskStatus, MessageType
from selects.TaskSelectsView import TaskSelectsView
from utils.discord.NotificationManagement import NotificationManagement
from utils.discord.CallbackBase import CallbackBase
from controllers.MessageController import MessageController
from utils.OrganizeGuestyData import OrganizeGuestyData
from utils.discord.DiscordElements import DiscordElements

# Guesty
from utils.guesty.GuestyUserRequests import GuestyUserRequests
from utils.guesty.GuestyTaskRequests import GuestyTaskRequests
from utils.guesty.GuestyListingRequests import GuestyListingRequests
from utils.guesty.GuestyReservationRequests import GuestyReservationRequests

from components.UpdatePayModal import UpdatePayModal
from components.EmbedElements import EmbedElements

# Discord elements
from buttons.TaskButtonsView import TaskButtonsView

"""
Create channel - https://discordpy.readthedocs.io/en/stable/api.html?highlight=create%20channel#discord.Guild.create_text_channel
Edit channel permission - https://discord.com/developers/docs/resources/channel#edit-channel-permissions
Set permission - https://discordpy.readthedocs.io/en/stable/api.html#discord.TextChannel.set_permissions
"""


class CallbackOperations(CallbackBase):

    def __init__(self, client):

        self.logger = logging.getLogger('claimbotpy')
        self.logger.setLevel(logging.DEBUG)

        self.embed_elements = EmbedElements()
        self.client = client
        self.guesty_user = GuestyUserRequests()
        self.guesty_listing = GuestyListingRequests()
        self.guesty_reservation = GuestyReservationRequests()
        self.fs = FormatString()
        self.ogd = OrganizeGuestyData()
        self.de = DiscordElements(client=client)
        self.mc = MessageController()
        self.guesty_task = GuestyTaskRequests()

    async def task_add_callback_backup(self, interaction: discord.Interaction):
        try:
            # make sure only assignee can start the task
            # ===============================================================================================================
            await interaction.response.defer()
            guesty_task_id = interaction.data['custom_id'].split('_')[1]
            find_a_task = await self.guesty_task.retrive_a_task(task_id=guesty_task_id)
            channel_id = 1126935585286799483
            test_channel = await self.client.fetch_channel(channel_id)
            test_message_id = 1126936008865353808
            find_doscord_message = await test_channel.fetch_message(test_message_id)
            time_now = self.fs.current_est_isotime()

            json_data = json.dumps({
                "discord_message_id": find_doscord_message.id,
                "guesty_task_id": find_a_task['_id'],
                "iso_est_time": time_now
            })
            update_guesty_task = await self.guesty_task.update_task(task_id=guesty_task_id, update_data={"description": f"This was updated. {json_data}"})
            new_message = await interaction.followup.send(json_data, ephemeral=True)
            print({
                "find_doscord_message": find_doscord_message,
                "find_a_task": find_a_task,
                "new_message": new_message,
                "update_task": guesty_task_id,
            })
        except Exception as e:
            logging.error(e)
            await interaction.followup.send(f"This interaction failed(custom)", ephemeral=True)

    async def task_add_callback(self, interaction: discord.Interaction):
        try:
            # Obtain user info
            # ===============================================================================================================
            await interaction.response.defer()
            guesty_task_req = GuestyTaskRequests()
            guesty_task_id = interaction.data['custom_id'].split('_')[1]
            if interaction.user.nick is None:
                logging.error("Can not found user nickname -> ",interaction.user)
                await interaction.followup.send(f"No guesty user found. "
                                                f"Ensure you have a guesty account and your Discord nickname "
                                                f"is your first name only. (No nickname found)", ephemeral=True)
                return
            discord_username = str(interaction.user.nick).lower()
            user_from_guesty = await self.guesty_user.search_a_user(username=discord_username)

            if user_from_guesty is None:
                await interaction.followup.send(f"No guesty user found matching {discord_username}. "
                                                f"Ensure you have a guesty account and your Discord nickname "
                                                f"is your first name only. (Unable to fetch user, try again later!)", ephemeral=True)
                return

            guesty_user_id = user_from_guesty["_id"]
            if user_from_guesty["firstName"] == '' or user_from_guesty["firstName"] is None or user_from_guesty["firstName"].lower() != discord_username:
                await interaction.followup.send(f"No guesty user found matching {discord_username}. "
                                                f"Ensure you have a guesty account and your Discord nickname "
                                                f"is your first name only. (Nickname no match)", ephemeral=True)
                return

            channel_name = f"{discord_username}-upcoming"
            user_channel = discord.utils.get(self.client.get_all_channels(), guild__name=os.getenv("GUILD_NAME"),
                                             name=channel_name)

            if user_channel is None:
                # Create a new channel
                cm = ChannelManagement(client=self.client)
                user_channel = await cm.create_a_channel(channel_name=channel_name, discord_user=interaction.user)

            # Db operations
            # ===============================================================================================================
            db = DatabaseMultiOperations()
            task_exist_local, user_exist_local = await asyncio.gather(
                db.find_one_task(doc_filter={'guesty_task_id': guesty_task_id}),
                db.find_one_user(doc_filter={'username': discord_username})
            )

            if task_exist_local is None:
                await interaction.followup.send(f"No task found, try again later! ID#{guesty_task_id}", ephemeral=True)
                return

            local_user_id = None
            user_data = self.ogd.user_data_guesty(guesty_user=user_from_guesty, discord_member=interaction.user)
            if user_exist_local is None:
                new_user = await db.insert_one_user(data=user_data)
                local_user_id = new_user.inserted_id
            else:
                del user_data['message_ids']
                del user_data['task_ids']
                local_user_id = user_exist_local["_id"]

            start_time = task_exist_local['start_time']
            formatted_date = self.fs.iso_to_est_readable_date(isoformat=start_time, format='Y-m-d')
            regex = re.compile(formatted_date)
            find_task_on_same_date = await db.find_one_task(doc_filter={"user_id": local_user_id, "start_time": {"$regex": regex}})
            local_task_id = task_exist_local['_id'] if task_exist_local is not None else None
            if find_task_on_same_date and find_task_on_same_date['_id'] != local_task_id and find_task_on_same_date['status'] != TaskStatus.CANCELED.value:
                # Send personal message
                await interaction.followup.send(f"You already have a task on {formatted_date}, therefore, you can not accept another one on the same day.", ephemeral=True)
                return

            # Assign user to the task
            # ===============================================================================================================
            assign_task_to_the_user = await guesty_task_req.assign_task_to_a_user(task_id=guesty_task_id,
                                                                                  user_id=guesty_user_id)
            if assign_task_to_the_user is None:
                await interaction.followup.send(f"Task can not assign user due to some issue, please try again later!", ephemeral=True)
                return

            # Find previous chart
            prev_upcoming_chart = await self.mc.find_upcoming_tasks_message(user_channel=user_channel)
            if prev_upcoming_chart is None:
                prev_upcoming_chart = await self.user_blank_tasks_chart(channel=user_channel, guesty_user_id=guesty_user_id)

            # Move message to user channel - Let's check there is no tasks on the same day as this one from database
            # ===============================================================================================================
            new_embed = interaction.message.embeds[0]
            new_embed.title = CLEANING_TITLES['cleaning_added']

            task_button_view = TaskButtonsView()
            task_button_view.task_start(task_id=guesty_task_id, callback_func=self.task_start_callback)
            task_button_view.task_release(callback_func=self.task_release_callback_from_single, task_id=guesty_task_id)

            await interaction.message.delete()
            # Check if the task is today post it otherwise add to the list of tasks of user
            us_today = self.fs.current_est_datetime_obj()
            start_date_obj = self.fs.iso_to_est_time(iso_time=start_time)
            discord_message_id = None
            if us_today.year == start_date_obj.year and start_date_obj.month == us_today.month and start_date_obj.day == us_today.day:
                user_message = await user_channel.send(embed=new_embed, view=task_button_view, delete_after=DELETE_AFTER_7_DAYS)
                discord_message_id = user_message.id

            # Db operations
            # ===============================================================================================================
            local_task_id = task_exist_local["_id"]
            message_exist_local = await db.find_one_message(doc_filter={'task_id': local_task_id})
            message_data = self.ogd.msg_insert_data(user_id=local_user_id, message_type=MessageType.USER_MESSAGE.value, discord_message_id=discord_message_id, task_id=local_task_id,
                                                    guesty_task_id=guesty_task_id)
            if message_exist_local:
                local_message_id = message_exist_local["_id"]
                await db.update_one_message(find_filters={"task_id": local_task_id}, set_dict=message_data)
            else:
                new_message = await db.insert_one_message(data=message_data)
                local_message_id = new_message.inserted_id
            await asyncio.gather(
                db.update_one_task(find_filters={'guesty_task_id': guesty_task_id}, set_dict={'user_id': local_user_id, 'message_id': local_message_id}),
                db.update_one_user(find_filters={"_id": local_user_id}, push_dict={"task_ids": local_task_id, 'message_ids': local_message_id}),
            )

            # Display user tasks table
            # ===============================================================================================================
            user_task_list = await db.find_tasks(doc_filters={"user_id": local_user_id})
            task_chart_message = await self.tasks_of_a_user(guesty_user_id=guesty_user_id, channel=user_channel, user_task_list=user_task_list, prev_message=prev_upcoming_chart)
            user_chart_msg_id = await self.save_user_chart_message(task_chart_message=task_chart_message, db=db, local_user_id=local_user_id, guesty_user_id=guesty_user_id)

            print("Task added successfully")
        except Exception as e:
            logging.error(e)
            await interaction.followup.send(f"This interaction failed(custom)", ephemeral=True)

    async def task_start_callback(self, interaction: discord.Interaction):
        try:
            # make sure only assignee can start the task
            # ===============================================================================================================
            await interaction.response.defer()
            guesty_task_req = GuestyTaskRequests()
            guesty_task_id = interaction.data['custom_id'].split('_')[1]

            # Fetch and validate task and user
            # ===============================================================================================================
            discord_username = str(interaction.user.nick).lower()
            user_from_guesty = await self.guesty_user.search_a_user(username=discord_username)
            if user_from_guesty is None:
                await interaction.followup.send(f"User not found!", ephemeral=True)
                await interaction.channel.delete()
                return
            guesty_user_id = user_from_guesty["_id"]

            # Db Operations
            db = DatabaseMultiOperations()
            find_task_local, find_user_local, find_message_local = await asyncio.gather(
                db.find_one_task(doc_filter={"guesty_task_id": guesty_task_id}),
                db.find_one_user(doc_filter={"guesty_user_id": guesty_user_id}),
                db.find_one_message(doc_filter={"guesty_task_id": guesty_task_id})
            )
            local_user_id = find_user_local["_id"] if find_user_local is not None else None
            local_task_id = find_task_local["_id"] if find_task_local is not None else None

            if find_task_local is None:
                await interaction.message.delete()
                await interaction.followup.send(f"Task not found!!", ephemeral=True)
                return

            if str(user_from_guesty["firstName"]).lower() != str(interaction.user.nick).lower():
                await interaction.followup.send("Only task assignee can start the task", ephemeral=True)
                return

            start_time = find_task_local['start_time']
            today_time = self.fs.current_est_datetime_obj()
            start_time_obj = self.fs.iso_to_time_obj(isoformat=start_time)
            if today_time.year != start_time_obj.year or today_time.month != start_time_obj.month or today_time.day != start_time_obj.day:
                formatted_date = self.fs.iso_to_readable_date(isoformat=start_time, format="m/d/Y")
                await interaction.followup.send(f"This task can only be started on {formatted_date}!", ephemeral=True)
                return

            # Change status of the task on guesty
            # ===============================================================================================================
            update_guesty_task = await guesty_task_req.update_task(task_id=guesty_task_id,
                                                                   update_data={"status": TaskStatus.IN_PROGRESS.value.lower()})
            if update_guesty_task is None:
                await interaction.followup.send("Not been able to start the task, please try again later!", ephemeral=True)
                return

            # Send a embed message with two buttons. Complete task and release task
            # ===============================================================================================================
            embed = interaction.message.embeds[0]
            embed.title = CLEANING_TITLES['cleaning_started']
            task_button_view = TaskButtonsView()
            task_button_view.task_complete(task_id=guesty_task_id, callback_func=self.task_complete_callback)
            task_button_view.task_release(callback_func=self.task_release_callback_from_single, task_id=guesty_task_id)
            message_edit = await interaction.message.edit(embed=embed, view=task_button_view)

            # Send notification about starting the task
            # ===============================================================================================================
            notification_management = NotificationManagement(client=self.client)
            pattern = r'(?<=\n)\d+\s\w+'
            find_target = re.findall(pattern, interaction.message.embeds[0].description)
            listing_nickname = find_target[0] if len(find_target) > 0 else ''
            message = f"{interaction.user.nick.capitalize()} just started cleaning {listing_nickname}"
            await asyncio.gather(
                notification_management.notify_specific_user(user_discord_id=interaction.user.id, message=f"You have started cleaning {listing_nickname}", task_id=guesty_task_id),
                notification_management.notify_admin(message=message, task_id=guesty_task_id, title="A task started")
            )

            message_data = self.ogd.msg_insert_data(user_id=local_user_id, message_type=MessageType.USER_MESSAGE.value, discord_message_id=message_edit.id, task_id=local_task_id,
                                                    guesty_task_id=guesty_task_id)
            local_message_id = None
            if find_message_local is not None:
                local_message_id = find_message_local["_id"]
                await db.update_one_message(find_filters={"_id": local_message_id}, set_dict=message_data)
            else:
                new_msg = await db.insert_one_message(data=message_data)
                local_message_id = new_msg.inserted_id

            # await db.update_one_task(find_filters={"guesty_task_id": guesty_task_id}, set_dict={'status': TaskStatus.IN_PROGRESS.value, 'message_id': local_message_id})
            await asyncio.gather(
                db.update_one_task(find_filters={'guesty_task_id': guesty_task_id}, set_dict={'user_id': local_user_id, 'message_id': local_message_id, 'status': TaskStatus.IN_PROGRESS.value, }),
                db.update_one_user(find_filters={"guesty_user_id": guesty_user_id}, push_dict={"task_ids": local_task_id, 'message_ids': local_message_id}),
            )
            print("Start task successfully")
        except Exception as e:
            logging.error(e)
            await interaction.followup.send(f"This interaction failed(custom)", ephemeral=True)

    async def task_complete_callback(self, interaction: discord.Interaction):
        try:
            # make sure only assignee can start the task
            # ===============================================================================================================
            await interaction.response.defer()
            guesty_task_req = GuestyTaskRequests()
            guesty_task_id = interaction.data['custom_id'].split('_')[1]

            # Fetch and validate task and user
            # ===============================================================================================================
            discord_username = str(interaction.user.nick).lower()
            user_from_guesty = await self.guesty_user.search_a_user(username=discord_username)
            if user_from_guesty is None:
                await interaction.followup.send(f"User not found, please try again later!", ephemeral=True)
                await interaction.channel.delete()
                return
            guesty_user_id = user_from_guesty['_id']

            # Database operations
            # ===============================================================================================================
            db = DatabaseMultiOperations()
            find_user_local, find_task_local = await asyncio.gather(
                db.find_one_user(doc_filter={"guesty_user_id": guesty_user_id}),
                db.find_one_task(doc_filter={"guesty_task_id": guesty_task_id})
            )
            local_user_id = find_user_local["_id"] if find_user_local is not None else None
            local_task_id = find_task_local["_id"] if find_task_local is not None else None

            if find_task_local is None:
                if interaction.message:
                    try:
                        await interaction.message.delete()
                    except discord.NotFound:
                        pass
                await interaction.followup.send(f"Task not found, please try again later!", ephemeral=True)
                return

            if str(user_from_guesty["firstName"]).lower() != str(interaction.user.nick).lower():
                await interaction.followup.send("Only task assignee can start the task", ephemeral=True)
                return

            # After completing update the task status as complete and delete the message
            # ===============================================================================================================
            update_guesty_task = await guesty_task_req.update_task(task_id=guesty_task_id, update_data={"status": TaskStatus.COMPLETED.value.lower()})
            if update_guesty_task is None:
                await interaction.followup.send("Not been able to complete the task, please try again later!", ephemeral=True)
                return
            if interaction.message:
                try:
                    await interaction.message.delete()
                except discord.NotFound:
                    pass

            delete_message_id = await db.delete_one_message(filters={"guesty_task_id": guesty_task_id})
            # Find previous chart
            user_channel = interaction.channel
            prev_upcoming_chart = await self.mc.find_upcoming_tasks_message(user_channel=user_channel)
            if prev_upcoming_chart is None:
                prev_upcoming_chart = await self.user_blank_tasks_chart(channel=user_channel, guesty_user_id=guesty_user_id)

            listing_id = find_task_local['listing_id']
            guesty_listing = await self.guesty_listing.retrive_a_listing(listing_id=listing_id)

            # Retrieve task and listing in order or get customFields to know about amount of payment or cleaner pay
            # ===============================================================================================================
            custom_fields = guesty_listing['customFields'] if guesty_listing is not None else None
            cleanerpay_field_id = os.getenv("CLEANERPAY_CUSTOM_FIELD_ID")
            cleanerpay_field = next((field for field in custom_fields if field["fieldId"] == cleanerpay_field_id), None)

            # Send notification
            # ===============================================================================================================
            pattern = r'(?<=\n)\d+\s\w+'
            listing_nickname = re.findall(pattern, interaction.message.embeds[0].description)[0]
            message = f"{interaction.user.nick} just finished cleaning ${listing_nickname}"
            notification_management = NotificationManagement(client=self.client)
            await asyncio.gather(
                notification_management.notify_specific_user(user_discord_id=interaction.user.id, message=f"You have completed a task {listing_nickname}", task_id=guesty_task_id),
                notification_management.notify_admin(message=message, task_id=guesty_task_id, title="A task finished")
            )
            payable_amount = cleanerpay_field["value"] if cleanerpay_field is not None else 0
            if 'receivable' in find_user_local:
                payable_amount += find_user_local['receivable']
            await asyncio.gather(
                db.update_one_task(find_filters={"guesty_task_id": guesty_task_id}, set_dict={"status": TaskStatus.COMPLETED.value, "cleanerpay": payable_amount, "message_id": None}),
                db.update_one_user(find_filters={"guesty_user_id": guesty_user_id}, set_dict={"receivable": payable_amount}, pull_dict={"message_ids": delete_message_id})
            )
            # Display user tasks table
            # ===============================================================================================================
            user_task_list = await db.find_tasks(doc_filters={"user_id": local_user_id})
            task_chart_message = await self.tasks_of_a_user(guesty_user_id=guesty_user_id, channel=user_channel, user_task_list=user_task_list, prev_message=prev_upcoming_chart)
            user_chart_msg_id = await self.save_user_chart_message(task_chart_message=task_chart_message, db=db, local_user_id=local_user_id, guesty_user_id=guesty_user_id)
            print("Start completed successfully")
        except Exception as e:
            logging.error(e)
            await interaction.followup.send(f"This interaction failed(custom)", ephemeral=True)

    async def task_release_callback_from_single(self, interaction: discord.Interaction):
        try:
            # From here call the actual function in order to release the task
            # ===============================================================================================================
            await interaction.response.defer()
            task_id = interaction.data['custom_id'].split('_')[1]
            await self.task_release_callback(interaction=interaction, guesty_task_id=task_id)
        except Exception as e:
            logging.error(e)
            await interaction.followup.send(f"This interaction failed(custom)", ephemeral=True)

    async def task_releaseoption_callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            # Get id of the task which is been selected from select menu and release that task
            # ===============================================================================================================
            guesty_task_id = interaction.data['values'][0].split("_")[1]
            await self.task_release_callback(interaction=interaction, guesty_task_id=guesty_task_id, select_menu_message=True)
        except Exception as e:
            logging.error(e)
            await interaction.followup.send(f"This interaction failed(custom)", ephemeral=True)

    async def task_release_callback(self, interaction: discord.Interaction, guesty_task_id, select_menu_message=False):
        try:
            # Fetch and validate task and user
            # ===============================================================================================================
            guesty_task_req = GuestyTaskRequests()
            discord_username = str(interaction.user.nick).lower()
            user_from_guesty = await self.guesty_user.search_a_user(username=discord_username)
            if user_from_guesty is None:
                await interaction.followup.send(f"User not found, please try again later!", ephemeral=True)
                await interaction.channel.delete()
                return

            if str(user_from_guesty["firstName"]).lower() != str(interaction.user.nick).lower():
                await interaction.followup.send("Only task assignee can start the task", ephemeral=True)
                return

            guesty_user_id = user_from_guesty["_id"]

            db = DatabaseMultiOperations()
            # Only assignee can release the task
            find_task_local, find_user_local, find_message_local = await asyncio.gather(
                db.find_one_task(doc_filter={"guesty_task_id": guesty_task_id}),
                db.find_one_user(doc_filter={"guesty_user_id": guesty_user_id}),
                db.find_one_message(doc_filter={"guesty_task_id": guesty_task_id})
            )
            if find_task_local is None:
                await interaction.message.delete()
                await interaction.followup.send(f"Task not found, please try again later!", ephemeral=True)
                return

            listing_id = find_task_local['listing_id']
            reservation_id = find_task_local['reservation_id']

            # Update task on guesty
            # ===============================================================================================================
            update_task_data = {
                'assigneeGroup': ["Cleaner"],
                'assigneeId': None,
                'status': TaskStatus.PENDING.value.lower()
            }
            update_guesty_task = await guesty_task_req.update_task(task_id=guesty_task_id,
                                                                   update_data=update_task_data)
            if update_guesty_task is None:
                await interaction.message.delete()
                await interaction.followup.send("Not been able to release the task, please try again later", ephemeral=True)
                return

            user_channel = interaction.channel
            prev_upcoming_chart = await self.mc.find_upcoming_tasks_message(user_channel=user_channel)
            if prev_upcoming_chart is None:
                prev_upcoming_chart = await self.user_blank_tasks_chart(channel=user_channel, guesty_user_id=guesty_user_id)

            find_listing, find_reservation, user_task_list = await asyncio.gather(
                self.guesty_listing.retrive_a_listing(listing_id=listing_id),
                self.guesty_reservation.retrive_a_reservation(reservation_id=reservation_id),
                guesty_task_req.all_tasks_of_an_user(guesty_user_id=guesty_user_id)
            )

            # Find message from discord and create new message and delete previous message
            # ===============================================================================================================
            prev_message = await self.mc.find_specific_task_message(channel=user_channel, target_guesty_task_id=guesty_task_id, total_btns=2)
            new_embed = None
            if prev_message is not None:
                new_embed = prev_message.embeds[0]
                await prev_message.delete()
            else:
                custom_create_task = {
                    "_id": guesty_task_id,
                    'apply': {
                        'listingId': listing_id,
                        'reservationId': reservation_id,
                    },
                    'timing': {
                        'startTime': find_task_local['start_time']
                    }
                }
                new_embed = await self.mc.task_message_create(guesty_task_id=guesty_task_id, guesty_task=custom_create_task, listing_single=find_listing, reservation_single=find_reservation)
            if select_menu_message:
                await interaction.message.delete()

            available_channel = await self.client.fetch_channel(CHANNELS['available_cleaning'])
            task_buttons_view = TaskButtonsView()
            add_task_button = task_buttons_view.task_add(task_id=guesty_task_id, callback_func=self.task_add_callback)
            task_buttons_view.add_item(add_task_button)
            new_message = await available_channel.send(embed=new_embed, view=task_buttons_view)
            listing_nickname = find_listing['nickname'] if find_listing is not None else ''

            # Send notification
            # ===============================================================================================================
            notification_management = NotificationManagement(client=self.client)
            message = f"{interaction.user.nick.capitalize()} just released a cleaning {listing_nickname}"
            await asyncio.gather(
                notification_management.notify_specific_user(user_discord_id=interaction.user.id, message=f"You have released a task {listing_nickname}", task_id=guesty_task_id),
                notification_management.notify_admin(message=message, task_id=guesty_task_id, title="A task released")
            )

            # Db Operations
            local_user_id = find_user_local["_id"] if find_user_local is not None else None
            local_task_id = find_task_local["_id"] if find_task_local is not None else None
            message_data = self.ogd.msg_insert_data(message_type=MessageType.AVAILABLE_MESSAGE.value, discord_message_id=new_message.id, task_id=local_task_id,
                                                    guesty_task_id=guesty_task_id)

            local_message_id = None
            if find_message_local is not None:
                local_message_id = find_message_local["_id"]
                await db.update_one_message(find_filters={"_id": local_message_id}, set_dict=message_data)
            else:
                new_msg = await db.insert_one_message(data=message_data)
                local_message_id = new_msg.inserted_id

            await asyncio.gather(
                db.update_one_task(find_filters={'guesty_task_id': guesty_task_id}, set_dict={'user_id': None, 'message_id': None, 'status': TaskStatus.PENDING.value, }),
                db.update_one_user(find_filters={"guesty_user_id": guesty_user_id}, pull_dict={"task_ids": local_task_id, 'message_ids': local_message_id}),
            )
            # Update task table
            # ===============================================================================================================
            user_task_list = await db.find_tasks(doc_filters={"user_id": local_user_id})
            task_chart_message = await self.tasks_of_a_user(guesty_user_id=guesty_user_id, channel=user_channel, user_task_list=user_task_list, prev_message=prev_upcoming_chart)
            user_chart_msg_id = await self.save_user_chart_message(task_chart_message=task_chart_message, db=db, local_user_id=local_user_id, guesty_user_id=guesty_user_id)
            print(f"Task released successfully ")
        except Exception as e:
            logging.error(e)
            await interaction.followup.send(f"This interaction failed(custom)", ephemeral=True)

    async def release_task_select_menu_callback(self, interaction: discord.Interaction):
        try:
            guesty_task_req = GuestyTaskRequests()
            await interaction.response.defer()
            guesty_user_id = interaction.data['custom_id'].split('_')[1]
            # find all tasks of a user from database and display them in a select menu along with a button to release
            # ===============================================================================================================
            user_task_list = await guesty_task_req.all_tasks_of_an_user(guesty_user_id=guesty_user_id)
            view = TaskSelectsView()

            task_list = []
            for t in user_task_list:
                if t['scheduledFor']['startTime'] is None:
                    continue
                start_date = self.fs.iso_to_time_obj(isoformat=t['scheduledFor']['startTime']).date()
                is_within7_days = self.fs.is_within_forward_days(target_date=start_date, days=7)
                task_status = t['status']['status'].upper()
                if (task_status == TaskStatus.IN_PROGRESS.value or task_status == TaskStatus.PENDING.value or task_status == TaskStatus.CONFIRMED.value) and is_within7_days is True:
                    task_list.append(t)

            if len(task_list) == 0:
                await interaction.followup.send(f"No task to release or an internal issue, please try again later!", ephemeral=True)
            elif len(task_list) >= 25:
                new_task_list = task_list[:25]
                view.task_list_display(user_id=guesty_user_id, task_list=new_task_list, callback_func=self.task_releaseoption_callback)
                await interaction.followup.send(f"More than 25 tasks found", view=view, ephemeral=True)
            else:
                view.task_list_display(user_id=guesty_user_id, task_list=task_list, callback_func=self.task_releaseoption_callback)
                await interaction.followup.send(f"Select a task to release", view=view)
            print("release_task_select_menu_callback successfully")
        except Exception as e:
            logging.error(e)

    async def update_pay_callback(self, interaction: discord.Interaction):
        try:
            # a simple modal to update an adjustment for cleaner or listing
            # ===============================================================================================================
            update_pay_modal = UpdatePayModal()
            await interaction.response.send_modal(update_pay_modal, delete_after=DELETE_AFTER_1_DAY)
        except Exception as e:
            logging.error(e)

    async def tasks_of_a_user(self, guesty_user_id, channel, user_task_list, prev_message=None):
        """
        TODO:
            Display table of tasks, Update database
            Display release task button with it
        """
        try:
            # Obtain data and create table and button element and send them
            # ===============================================================================================================
            display_table = DisplayTable()
            embed_table = await display_table.user_upcoming_tasks_table(user_task_list=user_task_list)

            user_tasks_message = await self.user_task_chart_message(user_channel=channel, guesty_user_id=guesty_user_id, embed_table=embed_table, prev_message=prev_message)
            return user_tasks_message
        except Exception as e:
            logging.error(e)
            return None

    async def user_blank_tasks_chart(self, channel, guesty_user_id, prev_message=None):
        """
        TODO:
            Create a simple upcoming task chart with no data for the first entry/message so that we can edit later. In this way it will always be at the top
        """
        try:
            description = f"-------------------------------------------------------------------\n**You have no task!!**"
            embed_table = discord.Embed(title=TASK_CHART_TITLE, description=description)
            embed_table.colour = discord.Colour.red()
            # embed_table.set_thumbnail(url="https://t4.ftcdn.net/jpg/04/73/25/49/360_F_473254957_bxG9yf4ly7OBO5I0O5KABlN930GwaMQz.jpg")
            task_button_view = TaskButtonsView()
            task_button_view.task_release_of_a_user(user_id=guesty_user_id, callback_func=self.release_task_select_menu_callback)
            user_tasks_message = None
            if prev_message:
                user_tasks_message = await prev_message.edit(embed=embed_table, view=task_button_view)
            else:
                user_tasks_message = await channel.send(embed=embed_table, view=task_button_view)
            return user_tasks_message
        except Exception as e:
            logging.error(e)
            return None

    async def user_tasks_chart(self, channel, task_list_of_user, guesty_user_id, prev_message=None):
        """
        TODO:
            Display table of tasks, Update database
            Display release task button with it
        """
        try:
            # Obtain data and create table and button element and send them
            # ===============================================================================================================
            display_table = DisplayTable()
            embed_table = await display_table.user_upcoming_tasks_table_tfl(task_list_of_user=task_list_of_user)

            user_tasks_message = await self.user_task_chart_message(user_channel=channel, guesty_user_id=guesty_user_id, embed_table=embed_table, prev_message=prev_message)
            return user_tasks_message
        except Exception as e:
            logging.error(e)
            return None

    async def user_task_chart_message(self, user_channel, guesty_user_id, embed_table, prev_message):
        try:
            if embed_table is None:
                user_tasks_message = await self.user_blank_tasks_chart(channel=user_channel, guesty_user_id=guesty_user_id, prev_message=prev_message)
                return user_tasks_message

            embed_table.colour = discord.Colour.green()

            task_button_view = TaskButtonsView()
            task_button_view.task_release_of_a_user(user_id=guesty_user_id, callback_func=self.release_task_select_menu_callback)

            user_tasks_message = None
            if prev_message:
                user_tasks_message = await prev_message.edit(embed=embed_table, view=task_button_view)
            else:
                find_prev_upcoming_chart = await self.mc.find_upcoming_tasks_message(user_channel=user_channel)
                if find_prev_upcoming_chart:
                    user_tasks_message = await find_prev_upcoming_chart.edit(embed=embed_table, view=task_button_view)
                else:
                    user_tasks_message = await user_channel.send(embed=embed_table, view=task_button_view)
            return user_tasks_message
        except Exception as e:
            logging.error(e)
            return None

    async def save_user_chart_message(self, task_chart_message, db, local_user_id, guesty_user_id):
        if task_chart_message:
            discord_message_id = task_chart_message.id
            find_message_local = await db.find_one_message(doc_filter={"guesty_user_id": guesty_user_id})
            message_data = self.ogd.msg_insert_data(user_id=local_user_id, message_type=MessageType.USER_TASKS.value, discord_message_id=discord_message_id, guesty_user_id=guesty_user_id)
            if find_message_local:
                local_message_id = find_message_local["_id"]
                await db.update_one_message(find_filters={"_id": local_message_id}, set_dict=message_data)
            else:
                new_message = await db.insert_one_message(data=message_data)
                local_message_id = new_message.inserted_id
            return local_message_id
        return None