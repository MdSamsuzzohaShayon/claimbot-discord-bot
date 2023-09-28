import discord
import re
import os
import asyncio
import logging

from utils.DisplayTable import DisplayTable

# Guesty
from utils.guesty.GuestyTaskRequests import GuestyTaskRequests
from utils.guesty.GuestyListingRequests import GuestyListingRequests
from utils.guesty.GuestyUserRequests import GuestyUserRequests
from utils.FormatString import FormatString
from utils.Enums import TaskStatus

from config.keys import DELETE_AFTER_5_MIN, TASK_TITLE

# Discord elements
from components.EmbedElements import EmbedElements
from components.UpdatePayModal import UpdatePayModal
from utils.database.DatabaseMultiOperations import DatabaseMultiOperations


class PayButtonsCallback():
    def __init__(self, client):
        self.client = client
        self.guesty_task = GuestyTaskRequests()
        self.guesty_listing = GuestyListingRequests()
        self.guesty_user = GuestyUserRequests()
        self.embed_elements = EmbedElements()
        self.dt = DisplayTable()
        self.fs = FormatString()
        self.PY_ENV = os.getenv("PY_ENV")
        self.project_directory = os.getenv("PROJECT_DIRECTORY")

    async def get_pay_summary_callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            # Get all tasks and listings
            # ===============================================================================================================
            search_task_filters = {"status":{"@nin":["canceled"]}}  # ,"title":{"@in":["Clean", "clean", "CLEAN"]}
            all_guesty_tasks, all_listings = await asyncio.gather(self.guesty_task.find_all_tasks( filters=search_task_filters), self.guesty_listing.get_all_listing())

            # Organize tasks
            # ===============================================================================================================
            find_tasks_prev = []
            find_tasks_curr = []
            # fetch_users_pending = []
            guesty_users_ids = set()
            for index, task in enumerate(all_guesty_tasks):
                if str(task['taskTitle']['children']).lower() != TASK_TITLE.lower() or task['status']['status'].upper() != TaskStatus.COMPLETED.value:
                    continue
                if 'assigneeId' in task['assignee'] and task['assignee']['assigneeId'] is not None:
                    if 'startTime' not in task["scheduledFor"] or task["scheduledFor"]["startTime"] is None:
                        continue
                    start_time = task["scheduledFor"]["startTime"]
                    within_prev_month = self.fs.is_within_specific_month(isoformat=start_time, offset_month=-1)
                    if within_prev_month:
                        find_tasks_prev.append(task)
                    within_curr_month = self.fs.is_within_specific_month(isoformat=start_time)
                    if within_curr_month:
                        find_tasks_curr.append(task)
                    if within_curr_month or within_prev_month:
                        if task['assignee']["assigneeId"] not in guesty_users_ids:
                            # fetch_users_pending.append(asyncio.ensure_future(self.guesty_user.retrieve_a_user(guesty_user_id=task['assignee']["assigneeId"])))
                            guesty_users_ids.add(task['assignee']["assigneeId"])

            # guesty_users = await asyncio.gather(*fetch_users_pending)
            guesty_users = await self.guesty_user.find_all_users()

            db = DatabaseMultiOperations()
            current_est_datetime_obj = self.fs.current_est_datetime_obj()
            prev_mon = self.fs.datetime_offset(days=-current_est_datetime_obj.day)
            prev_mon_regex = re.compile(pattern=self.fs.datetime_obj_to_readable(datetime_obj=prev_mon, format='Y-m'))
            curr_mon_regex = re.compile(pattern=self.fs.datetime_obj_to_readable(datetime_obj=current_est_datetime_obj, format='Y-m'))
            find_adjustments_prev, find_adjustments_curr = await asyncio.gather(
                db.find_adjustments(doc_filters={"updated_at": {"$regex": prev_mon_regex}}),
                db.find_adjustments(doc_filters={"updated_at": {"$regex": curr_mon_regex}}),
            )
            curr_pt, prev_pt = await asyncio.gather(
                self.dt.create_summary_table(title="Current Month", user_list=guesty_users, tasks_of_a_month=find_tasks_curr, all_listings=all_listings, adjustments_of_a_month=find_adjustments_curr),
                self.dt.create_summary_table(title="Previous Month", user_list=guesty_users, tasks_of_a_month=find_tasks_prev, all_listings=all_listings, adjustments_of_a_month=find_adjustments_prev)
            )

            target_channel = interaction.channel
            await asyncio.gather(target_channel.send(f"```{prev_pt}```", delete_after=DELETE_AFTER_5_MIN), target_channel.send(f"```{curr_pt}```", delete_after=DELETE_AFTER_5_MIN))
        except Exception as e:
            logging.error(e)
            await interaction.response.send_message(f"This interaction failed(custom)")

    async def get_listings_summary_callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()

            current_est_datetime_obj = self.fs.current_est_datetime_obj()
            prev_mon = self.fs.datetime_offset(days=-current_est_datetime_obj.day)
            prev_mon_regex = re.compile(pattern=self.fs.datetime_obj_to_readable(datetime_obj=prev_mon, format='Y-m'))
            curr_mon_regex = re.compile(pattern=self.fs.datetime_obj_to_readable(datetime_obj=current_est_datetime_obj, format='Y-m'))

            db = DatabaseMultiOperations()
            find_prev_adjusts, find_curr_adjusts = await asyncio.gather(
                db.find_adjustments(doc_filters={"updated_at": {"$regex": prev_mon_regex}}),
                db.find_adjustments(doc_filters={"updated_at": {"$regex": curr_mon_regex}})
            )

            # Get all tasks and listings
            # ===============================================================================================================
            search_task_filters = {"status":{"@nin":["canceled"]}}  # ,"title":{"@in":["Clean", "clean", "CLEAN"]}
            all_guesty_tasks, all_listings = await asyncio.gather(self.guesty_task.find_all_tasks( filters=search_task_filters), self.guesty_listing.get_all_listing())

            # Organize tasks
            # ===============================================================================================================
            find_tasks_prev = []
            find_tasks_curr = []
            for index, task in enumerate(all_guesty_tasks):
                # str(task['taskTitle']['children']).lower() != TASK_TITLE.lower() or task['status']['children'].upper() != TaskStatus.COMPLETED.value or
                if 'startTime' not in task["scheduledFor"] or task["scheduledFor"]["startTime"] is None:
                    continue
                start_time = task["scheduledFor"]["startTime"]
                within_prev_month = self.fs.is_within_specific_month(isoformat=start_time, offset_month=-1)
                if within_prev_month:
                    find_tasks_prev.append(task)
                within_curr_month = self.fs.is_within_specific_month(isoformat=start_time)
                if within_curr_month:
                    find_tasks_curr.append(task)

            target_channel = interaction.channel
            prev_pt, curr_pt = await asyncio.gather(
                self.dt.create_listing_table(title="Previous Month", tasks_of_a_month=find_tasks_prev, adjust_of_a_month=find_prev_adjusts, all_listings=all_listings),
                self.dt.create_listing_table(title="Current Month", tasks_of_a_month=find_tasks_curr, adjust_of_a_month=find_curr_adjusts, all_listings=all_listings)
            )
            await target_channel.send(f"```{prev_pt}```", delete_after=DELETE_AFTER_5_MIN)
            await target_channel.send(f"```{curr_pt}```", delete_after=DELETE_AFTER_5_MIN)
        except Exception as e:
            logging.error(e)
            await interaction.followup.send(f"This interaction failed(custom)")

    async def update_pay_callback(self, interaction: discord.Interaction):
        try:
            # await interaction.response.defer()
            update_pay_modal = UpdatePayModal()

            # me = ModalElements()
            await interaction.response.send_modal(update_pay_modal)
        except Exception as e:
            logging.error(e)
            await interaction.response.send_message(f"This interaction failed(custom)")

    async def get_my_pay_check_callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer()
            await interaction.followup.send(f"Success")
        except Exception as e:
            logging.error(e)
            await interaction.followup.send(f"This interaction failed(custom)")








