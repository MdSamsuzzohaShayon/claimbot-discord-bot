import logging

import discord
import os

from prettytable import PrettyTable
from utils.Enums import TaskStatus
from utils.FormatString import FormatString
from config.keys import TASK_TITLE, TASK_CHART_TITLE


class DisplayTable:

    def __init__(self):
        self.padding_width = 3
        self.fs = FormatString()
        self.listing_headers = ["Property", "Base", "Adjustment", "Total"]
        self.table_fields = ["Cleaner", "Base", "Adjustment", "Total"]

    async def user_upcoming_tasks_table(self, user_task_list):
        try:
            description = "-------------------------------------------------------------------"
            embed_table = discord.Embed(title=TASK_CHART_TITLE)
            row_list_str = []

            if len(user_task_list) == 0:
                return None
                # pt.add_row(["-", "-", "-", "-"])
            cols = 0
            for task in user_task_list:
                if str(task["status"]).upper() == TaskStatus.COMPLETED.value or str(task["status"]).upper() == TaskStatus.CANCELED.value:
                    continue
                start_time = self.fs.iso_to_time_obj(isoformat=task["start_time"])
                within_7_days = self.fs.is_within_forward_days(target_date=start_time.date(), days=7)
                if within_7_days is False:
                    continue
                formatted_time = self.fs.iso_to_est_readable_date(isoformat=task["start_time"], format="m/d/Y")
                tick = "✔" if 'ta' in task and task['ta'] is True else "✖"
                new_listing_nickname = task["listing_nickname"].split('/')[0] if "/" in task["listing_nickname"] else task["listing_nickname"]
                # property_list.append(new_listing_nickname); due_list.append(formatted_time); hash_list.append(1); ta_list.append(tick)
                row_list_str.append(f"**{new_listing_nickname}** \n ```  Due Date: {formatted_time} \n  TA: {tick}```")
                cols += 1
            if cols == 0:
                return None
            # embed_table.add_field(name="Property", value="\n".join(property_list))
            # embed_table.add_field(name="Due Date", value="\n".join(due_list))
            # embed_table.add_field(name="TA", value="\n".join(ta_list))
            items_str = "\n".join(row_list_str)
            description += f"\n {items_str}"
            embed_table.description = description
            return embed_table
        except Exception as e:
            logging.error(e)
            return None

    async def user_upcoming_tasks_table_tfl(self, task_list_of_user): # tol = task from loop
        try:
            description = "-------------------------------------------------------------------"
            embed_table = discord.Embed(title=TASK_CHART_TITLE)
            row_list_str = []

            if len(task_list_of_user) == 0:
                return None
                # pt.add_row(["-", "-", "-", "-"])
            cols = 0
            for task in task_list_of_user:
                task_status = task["status"]['status'].upper() if 'status' in task['status'] else task['status'].upper()
                task_title = task['taskTitle']['children'] if 'taskTitle' in task and 'children' in task['taskTitle'] else task['title']
                if task_title.lower() != TASK_TITLE:
                    continue
                start_time_iso = None
                if 'scheduledFor' in task and 'startTime' in task["scheduledFor"]:
                    start_time_iso = task["scheduledFor"]['startTime']
                if 'timing' in task and 'startTime' in task["timing"]:
                    start_time_iso = task["timing"]['startTime']
                if start_time_iso is None:
                    continue
                if task_status == TaskStatus.COMPLETED.value or task_status == TaskStatus.CANCELED.value:
                    continue
                start_time = self.fs.iso_to_time_obj(isoformat=start_time_iso)
                within_7_days = self.fs.is_within_forward_days(target_date=start_time.date(), days=7)
                if within_7_days is False:
                    continue
                formatted_time = self.fs.iso_to_est_readable_date(isoformat=start_time_iso, format="m/d/Y")
                tick = "✔" if 'ta' in task and task['ta'] is True else "✖"
                new_listing_nickname = None
                if 'listing' in task and 'title' in task["listing"]:
                    new_listing_nickname = task["listing"]['title'].split('/')[0] if "/" in task["listing"]['title'] else task["listing"]['title']
                # property_list.append(new_listing_nickname); due_list.append(formatted_time); hash_list.append(1); ta_list.append(tick)
                row_list_str.append(f"**{new_listing_nickname}** \n ```  Due Date: {formatted_time} \n  TA: {tick}```")
                cols += 1
            if cols == 0:
                return None
            # embed_table.add_field(name="Property", value="\n".join(property_list))
            # embed_table.add_field(name="Due Date", value="\n".join(due_list))
            # embed_table.add_field(name="TA", value="\n".join(ta_list))
            items_str = "\n".join(row_list_str)
            description += f"\n {items_str}"
            embed_table.description = description
            return embed_table
        except Exception as e:
            logging.error(e)
            return None

    async def cleaning_of_a_day(self, title, task_list, user_list):
        try:
            embed_table = discord.Embed(title=title, description="-------------------------------------------------------------------")
            cleaner_list, nickname_list, guesty_link_list = [], [], []
            cols = 0
            for task in task_list:
                find_user = next((user for user in user_list if user["_id"] == task['assignee']["assigneeId"]), None)
                if find_user:
                    listing_nickname = task["listing"]["title"] if "title" in task["listing"] else ""
                    cleaner_list.append(find_user['firstName']); nickname_list.append(listing_nickname); guesty_link_list.append(f"https://app.guesty.com/tasks/{task['id']}")
                    cols += 1

            if cols == 0:
                cleaner_list.append("-"); nickname_list.append("-"); guesty_link_list.append("-")

            embed_table.add_field(name="Cleaner", value="\n".join(cleaner_list), inline=True)
            embed_table.add_field(name="Listing", value="\n".join(nickname_list), inline=True)
            embed_table.add_field(name="Guesty", value="\n".join(guesty_link_list), inline=True)

            return embed_table
        except Exception as e:
            logging.error(e)
            return None

    async def create_listing_table(self, title, tasks_of_a_month, adjust_of_a_month, all_listings):
        try:
            pt = PrettyTable(self.listing_headers)
            pt.title = title
            pt.padding_width = 3

            total, total_base, total_adjust = 0, 0, 0

            task_listings = []
            listing_ids = set()
            cleanerpay_field_id = os.getenv("CLEANERPAY_CUSTOM_FIELD_ID")

            for tI, task in enumerate(tasks_of_a_month):
                try:
                    listing_id = task["listing"]["listingId"] if 'listingId' in task["listing"] and task["listing"]["listingId"] is not None else None
                    if listing_id is None:
                        continue
                    find_listing = next(
                        (l for l in all_listings if l is not None and "listingId" in task["listing"] and task["listing"]["listingId"] is not None and l["_id"] == task["listing"]["listingId"]),
                        None)
                    cleanerpay_field = next((field for field in find_listing["customFields"] if field["fieldId"] == cleanerpay_field_id), None) if find_listing is not None else None
                    cleanerpay = cleanerpay_field["value"] if cleanerpay_field is not None else 0
                    base_amount = cleanerpay
                    adjustment = 0
                    listing_nickname = find_listing['nickname']
                    find_adjusts = list(filter(lambda a: "guesty_listing_id" in a and a["guesty_listing_id"] == listing_id, adjust_of_a_month))
                    for a in find_adjusts:
                        adjustment += a["amount"]

                    if str(listing_id) not in listing_ids:
                        listing_ids.add(str(listing_id))
                        listing_total = base_amount + adjustment
                        task_listings.append({"listing_id": listing_id, "nickname": listing_nickname,
                                              "base_amount": base_amount, "adjustment": adjustment, "listing_total": listing_total})
                    else:
                        find_listing_index = task_listings.index(next(filter(lambda l: 'listing_id' in l and l['listing_id'] == str(listing_id), task_listings)))
                        find_listing = task_listings[find_listing_index]
                        base_amount += find_listing["base_amount"]
                        adjustment += find_listing["adjustment"]
                        listing_total = base_amount + adjustment
                        task_listings.pop(find_listing_index)
                        task_listings.append({"listing_id": listing_id, "nickname": listing_nickname,
                                              "base_amount": base_amount, "adjustment": adjustment, "listing_total": listing_total})
                except Exception as te:
                    logging.warning(te)
                    continue

            for lI, listing in enumerate(task_listings):
                total += listing['listing_total']
                total_base += listing["base_amount"]
                total_adjust += listing["adjustment"]
                pt.add_row([listing["nickname"], f"${listing['base_amount']}", f"${listing['adjustment']}", f"${listing['listing_total']}"])
            pt.add_row(["------", f"------", f"------", f"------"])
            pt.add_row(["Total", f"${total_base}", f"${total_adjust}", f"${total}"])
            return pt
        except Exception as e:
            logging.error(e)
            return None

    async def create_summary_table(self, title, user_list, tasks_of_a_month, all_listings, adjustments_of_a_month=[]):
        try:
            pt = PrettyTable(self.table_fields)
            pt.title = title
            pt.padding_width = 5
            cleanerpay_field_id = os.getenv("CLEANERPAY_CUSTOM_FIELD_ID")

            cols, au_total_base, au_total_adjust, au_total  = 0, 0, 0, 0
            for user in user_list:
                guesty_user_id = user["_id"]
                base_amount = 0
                user_has_task_in_this_month = False
                for t in tasks_of_a_month:
                    if t['assignee']['assigneeId'] == guesty_user_id:
                        find_listing = next((l for l in all_listings if l is not None and "listingId" in t["listing"] and t["listing"]["listingId"] is not None and l["_id"] == t["listing"]["listingId"]),
                                            None)
                        cleanerpay_field = next((field for field in find_listing["customFields"] if field["fieldId"] == cleanerpay_field_id), None) if find_listing is not None else None
                        cleanerpay = cleanerpay_field["value"] if cleanerpay_field is not None else 0
                        base_amount += cleanerpay
                        user_has_task_in_this_month = True
                if user_has_task_in_this_month is False:
                    continue
                adjustment = 0
                find_adjustments = list(filter(lambda a: "guesty_user_id" in a and a["guesty_user_id"] != None and a["guesty_user_id"] == guesty_user_id, adjustments_of_a_month))
                for a in find_adjustments:
                    adjustment += a["amount"]
                total_pay = base_amount + adjustment
                pt.add_row([user["fullName"], f"${base_amount}", f"${adjustment}", f"${total_pay}"])
                cols += 1
                au_total_base += base_amount
                au_total_adjust += adjustment
                au_total += total_pay

            if cols == 0:
                pt.add_row(["-", "-", "-", "-"])
            else:
                pt.add_row(["------", f"------", f"------", f"------"])
                pt.add_row(["Total", au_total_base, au_total_adjust, au_total])

            return pt
        except Exception as e:
            logging.error(e)
            return None
