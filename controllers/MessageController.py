import asyncio
import logging

from utils.guesty.GuestyTaskRequests import GuestyTaskRequests
from utils.guesty.GuestyReservationRequests import GuestyReservationRequests
from utils.guesty.GuestyListingRequests import GuestyListingRequests
from utils.FormatString import FormatString
from config.keys import TASK_CHART_TITLE, CLEANING_TITLES
from components.EmbedElements import EmbedElements


class MessageController:
    def __init__(self):
        self.guesty_task = GuestyTaskRequests()
        self.guesty_listing = GuestyListingRequests()
        self.guesty_reservation = GuestyReservationRequests()
        self.fs = FormatString()
        self.default_title = "New Cleaning Available"
        self.message_list = []

        self.pay_msg_list = [] # messages of pay-calc channel

    async def task_message_create(self, guesty_task_id, title=CLEANING_TITLES['cleaning_added'], guesty_task=None, listing_single=None, reservation_single=None):
        try:
            guesty_task_new, listing_single_new, reservation_single_new = guesty_task, listing_single, reservation_single
            start_time, listing_id, reservation_id = None, None, None
            if guesty_task is None:
                guesty_task_new = await self.guesty_task.retrive_a_task(task_id=guesty_task_id)
            start_time = None
            if 'timing' in guesty_task_new:
                start_time = guesty_task_new['timing']['startTime']
            elif 'startTime' in guesty_task_new:
                start_time = guesty_task_new['startTime']

            listing_id, reservation_id = None, None

            if 'apply' in guesty_task_new:
                listing_id = guesty_task_new['apply']['listingId']
            elif 'listingId' in guesty_task_new:
                listing_id = guesty_task_new['listingId']

            if 'apply' in guesty_task_new:
                reservation_id = guesty_task_new['apply']['reservationId']
            elif 'reservationId' in guesty_task_new:
                reservation_id = guesty_task_new['reservationId']

            fetch_from_guesty = []
            if listing_single is None:
                fetch_from_guesty.append(asyncio.ensure_future(self.guesty_listing.retrive_a_listing(listing_id=listing_id)))
            if reservation_single is None:
                fetch_from_guesty.append(asyncio.ensure_future(self.guesty_reservation.retrive_a_reservation(reservation_id=reservation_id)))
            result = await asyncio.gather(*fetch_from_guesty)
            if listing_single is None:
                listing_single_new = result[0]
            if reservation_single is None:
                reservation_single_new = result[1] if len(result) == 2 else result[0]

            us_datetime_obj = self.fs.iso_to_est_time(iso_time=start_time)
            us_formatted_date = self.fs.datetime_obj_to_readable(datetime_obj=us_datetime_obj, format='m/d/y')
            listing_nickname = listing_single_new['nickname'] if listing_single_new is not None else ''
            listing_address = listing_single_new['address']['full'] if listing_single_new is not None else ''
            thumbnail = listing_single_new['picture'][
                'thumbnail'] if listing_single_new is not None else 'https://as2.ftcdn.net/v2/jpg/04/70/29/97/1000_F_470299797_UD0eoVMMSUbHCcNJCdv2t8B2g1GVqYgs.jpg'
            guest_fullname = reservation_single_new['guest']['fullName'] if reservation_single_new is not None else ''
            guest_count = reservation_single_new['guestsCount'] if reservation_single_new is not None else ''
            guesty_task_id = guesty_task['_id']
            description = self.create_task_message(formatted_date=us_formatted_date, listing_nickname=listing_nickname, listing_address=listing_address, guest_fullname=guest_fullname,
                                                   guest_count=guest_count, task_id=guesty_task_id)
            embed_element = EmbedElements()
            new_message_embed = embed_element.attachment_with_thumbnail(title=title, description=description,
                                                                        thumbnail=thumbnail)
            return new_message_embed
        except Exception as e:
            logging.error(e)
            return None

    async def task_message_create_tfl(self, task, all_reservations=[], all_listing=[], title="New Cleaning Available"):  # tfl = task from loop
        try:
            guesty_task_id = task["id"]
            listing_id = task["listing"]["listingId"] if "listingId" in task["listing"] else None
            reservation_id = task["reservation"]["reservationId"] if "reservationId" in task["reservation"] else None
            find_reservation = next((r for r in all_reservations if r is not None and r["_id"] == reservation_id), None)
            guest_fullname = find_reservation['guest']['fullName'] if find_reservation is not None else ''

            find_listing = next((r for r in all_listing if r["_id"] == listing_id), None)
            listing_nickname = find_listing['nickname'] if find_listing is not None else ''
            listing_address = find_listing['address']['full'] if find_listing is not None else ''
            thumbnail = find_listing['picture']['thumbnail'] if find_listing is not None else 'https://as2.ftcdn.net/v2/jpg/04/70/29/97/1000_F_470299797_UD0eoVMMSUbHCcNJCdv2t8B2g1GVqYgs.jpg'

            start_time = task['scheduledFor']['startTime']
            us_datetime_obj = self.fs.iso_to_est_time(iso_time=start_time)
            us_formatted_date = self.fs.datetime_obj_to_readable(datetime_obj=us_datetime_obj, format='m/d/y')
            guest_count = task["reservation"]["guestsCount"] if "reservation" in task and "guestsCount" in task["reservation"] and task["reservation"]["guestsCount"] is not None else 0
            description = self.create_task_message(formatted_date=us_formatted_date, listing_nickname=listing_nickname, listing_address=listing_address, guest_fullname=guest_fullname,
                                                   guest_count=guest_count, task_id=guesty_task_id)
            embed_element = EmbedElements()
            new_message_embed = embed_element.attachment_with_thumbnail(title=title, description=description,
                                                                        thumbnail=thumbnail)
            return new_message_embed
        except Exception as e:
            logging.error(e)
            return None

    async def fetch_prev_messages(self, target_channel):
        message_list = [message async for message in target_channel.history(limit=None)]
        self.message_list = message_list
        return message_list

    async def find_upcoming_tasks_message(self, user_channel, fetch_messages=False):
        if fetch_messages is False:
            self.message_list = [message async for message in user_channel.history(limit=None)]
        find_msg = None
        for msg in self.message_list:
            try:
                if len(msg.embeds) != 1:
                    continue
                # Check is this a chart message or not
                if msg.embeds[0].title.lower() == TASK_CHART_TITLE.lower():
                    return msg
            except Exception as mE:
                continue
        return None

    async def find_specific_task_message(self, channel, target_guesty_task_id, total_btns, task_fetch=False):
        try:
            if task_fetch is False:
                self.message_list = [message async for message in channel.history(limit=None)]
            for msg in self.message_list:
                try:
                    guesty_task_id = msg.components[0].children[0].custom_id.split('_')[1]
                    if len(msg.components[0].children) == total_btns and guesty_task_id == target_guesty_task_id:
                        return msg
                except Exception as e:
                    continue
            return None
        except Exception as tmE:
            return None

    async def delete_redundant_messages(self, channel, redundant_task_ids, total_btns, message_fetch=False):
        try:
            if message_fetch is False:
                self.message_list = [message async for message in channel.history(limit=None)]
            for msg in self.message_list:
                try:
                    guesty_task_id = msg.components[0].children[0].custom_id.split('_')[1]
                    if len(msg.components[0].children) == total_btns and guesty_task_id in redundant_task_ids:
                        self.message_list = list(filter(lambda m:m.id != msg.id, self.message_list))
                        await msg.delete()
                except Exception as e:
                    continue
            return None
        except Exception as tmE:
            return None

    def create_task_message(self, formatted_date, listing_nickname, listing_address, guest_fullname, guest_count, task_id):
        new_guest_fullname = "Unknown" if guest_fullname is None or guest_fullname == '' else guest_fullname
        new_guest_count = "Unknown" if guest_count is None or guest_count == 0 else guest_count
        description: str = "Due {start_time}\n" \
                           "{listing_nickname}\n" \
                           "{listing_address}\n" \
                           "Guest Name: {guest_fullname}\n " \
                           "{guest_count} guests\n" \
                           "Not turn around\n " \
                           "[Task in guesty](https://app.guesty.com/tasks/{task_id})".format(start_time=formatted_date,
                                                                                             listing_nickname=listing_nickname,
                                                                                             listing_address=listing_address,
                                                                                             guest_fullname=new_guest_fullname,
                                                                                             guest_count=new_guest_count,
                                                                                             task_id=task_id)
        return description

    async def fetch_prev_pay_msgs(self, calc_channel):
        msg_list = [msg async for msg in calc_channel.history(limit=None)]
        self.pay_msg_list = msg_list
        return msg_list

    async def find_prev_pay_spec_msg(self, custom_id: str):
        find_msg = None
        for msg in self.pay_msg_list:
            try:
                if len(msg.embeds) == 1 and len(msg.components) == 1:
                    btn_custom_id = msg.components[0].children[0].custom_id
                    if btn_custom_id == custom_id:
                        return msg
            except Exception as mE:
                continue
        return None

