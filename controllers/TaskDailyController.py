import asyncio
import logging

from controllers.ControllerBase import ControllerBase
from utils.discord.NotificationManagement import NotificationManagement
from utils.FormatString import FormatString
from utils.guesty.GuestyTaskRequests import GuestyTaskRequests
from utils.guesty.GuestyListingRequests import GuestyListingRequests
from utils.guesty.GuestyReservationRequests import GuestyReservationRequests
from utils.guesty.GuestyUserRequests import GuestyUserRequests
from config.keys import TASK_TITLE
from utils.Enums import TaskStatus
from utils.discord.DiscordElements import DiscordElements
from utils.OrganizeGuestyData import OrganizeGuestyData


class TaskDailyController(ControllerBase):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.fs = FormatString()
        self.guesty_task = GuestyTaskRequests()
        self.guesty_listing = GuestyListingRequests()
        self.guesty_reservation = GuestyReservationRequests()
        self.guesty_user = GuestyUserRequests()
        self.de = DiscordElements(client=client)
        self.ogd = OrganizeGuestyData()
        self.nm = NotificationManagement(client=client)

        self.all_guesty_tasks = []
        self.all_guesty_users = []
        self.all_tasks_today = []
        self.all_tasks_tomorrow = []

    async def fetch_and_organize(self):
        try:
            search_task_filters = {}
            self.all_guesty_tasks = await self.guesty_task.find_all_tasks(filters=search_task_filters)

            est_time_now = self.fs.current_est_datetime_obj()
            user_guesty_ids = set()
            for tI, t in enumerate(self.all_guesty_tasks):
                try:
                    if str(t["taskTitle"]['children']).lower() != TASK_TITLE:
                        continue
                    if t['status']['status'].upper() == TaskStatus.COMPLETED.value or t['status']['status'].upper() == TaskStatus.CANCELED.value:
                        continue
                    task_start = self.fs.iso_to_est_time(iso_time=t['scheduledFor']["startTime"])
                    if t['assignee']['assigneeId'] is None:
                        continue
                    if t['assignee']['assigneeId'] not in user_guesty_ids:
                        # fetch_users_pending.append(asyncio.ensure_future(self.guesty_user.retrieve_a_user(guesty_user_id=t['assignee']["assigneeId"])))
                        user_guesty_ids.add(t['assignee']['assigneeId'])
                    if task_start.year == est_time_now.year and task_start.month == est_time_now.month and task_start.day == est_time_now.day:
                        self.all_tasks_today.append(t)
                    tomorrow_date = self.fs.datetime_offset(days=1)
                    if task_start.year == tomorrow_date.year and task_start.month == tomorrow_date.month and task_start.day == tomorrow_date.day:
                        self.all_tasks_tomorrow.append(t)
                except Exception as tE:
                    continue

            # self.all_guesty_users = await asyncio.gather(*fetch_users_pending)
            self.all_guesty_users = await self.guesty_user.find_all_users()
        except Exception as e:
            logging.error(e)

    async def remind_cleaning_notifications(self):
        try:
            await asyncio.gather(
                self.fetch_and_organize(),
                self.de.find_all_members()
            )

            for user in self.all_guesty_users:
                try:
                    guesty_user_id = user['_id']
                    find_member = await self.de.find_member_by_nickname(nickname=user['firstName'])
                    if find_member is None:
                        continue
                    discord_user_id = find_member.id

                    tasks_today = [t for t in self.all_tasks_today if 'assigneeId' in t['assignee'] and t['assignee']['assigneeId'] == guesty_user_id]
                    tasks_tomorrow = [t for t in self.all_tasks_tomorrow if t['assignee']['assigneeId'] == guesty_user_id]

                    if tasks_today:
                        msg_str = '\n'.join([f"https://app.guesty.com/tasks/{t['id']}" for t in tasks_today])
                        await self.nm.notify_specific_user(user_discord_id=discord_user_id, message=f"You have cleaning today! {msg_str}")

                    if tasks_tomorrow:
                        msg_str = '\n'.join([f"https://app.guesty.com/tasks/{t['id']}" for t in tasks_tomorrow])
                        await self.nm.notify_specific_user(user_discord_id=discord_user_id, message=f"You have cleaning tomorrow! {msg_str}")

                except Exception as uE:
                    continue

        except Exception as e:
            logging.error(e)
