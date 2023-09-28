from copy import copy
import os

class OrganizeGuestyData:
    def __init__(self):
        pass

    # For database validation
    def user_insert_data(self, username, fullname, guesty_user_id, discord_user_id, task_ids, message_ids, receivable):
        user_data = {
            "username": username,
            "fullname": fullname,
            "guesty_user_id": guesty_user_id,
            "discord_user_id": discord_user_id,
            "task_ids": task_ids,
            "message_ids": message_ids,
            "receivable": receivable
        }
        return user_data
    def user_data_guesty(self, guesty_user, discord_member, message_ids=[], task_ids=[], receivable=0):
        discord_user_id = discord_member.id if discord_member is not None else None
        user_data = self.user_insert_data( username=guesty_user['firstName'].lower(), fullname=guesty_user['fullName'],
                                           guesty_user_id=guesty_user["_id"], discord_user_id=discord_user_id,
                                           task_ids=task_ids, message_ids=message_ids, receivable=receivable)
        return user_data

    def task_insert_data(self, listing_id, reservation_id, status, guest_count, listing_nickname, listing_address, guest_fullname, local_user_id, start_time, guesty_task_id, local_message_id, cleanerpay):
        task_data = {
            "listing_id": listing_id,
            "reservation_id": reservation_id,
            "status": str(status).upper(),
            "guest_count": guest_count,
            "listing_nickname": listing_nickname,
            'listing_address': listing_address,
            'guest_fullname': guest_fullname,
            "user_id": local_user_id,
            "start_time": start_time,
            "ta": False,
            "guesty_task_id": guesty_task_id,
            "message_id": local_message_id,
            "cleanerpay": cleanerpay
        }
        return task_data

    def task_data_guesty(self, task, reservation = None, listing=None, local_user_id=None, local_message_id=None, cleanerpay=0):
        guesty_task_id = task["_id"]
        status = task["status"]
        start_time = task["startTime"] if 'timing' not in task else task['timing']['startTime']
        listing_id = task["listingId"] if "apply" not in task else task['apply']['listingId']
        reservation_id = None
        if 'apply' in task:
            reservation_id = task['apply']['reservationId'] if 'reservationId' in task['apply'] and task['apply']['reservationId'] is not None else None
        elif "reservationId" in task:
            reservation_id = task["reservationId"] if "reservationId" in task and task["reservationId"] is not None else None
        listing_address = listing["address"]['full'] if listing is not None else ''
        listing_nickname = listing["nickname"] if listing is not None else ''

        new_cleanerpay = 0
        if cleanerpay == 0:
            cleanerpay_field_id = os.getenv("CLEANERPAY_CUSTOM_FIELD_ID")
            cleanerpay_field = next((field for field in listing["customFields"] if field["fieldId"] == cleanerpay_field_id), None) if listing is not None else None
            cleanerpay = cleanerpay_field["value"] if cleanerpay_field is not None else 0
            new_cleanerpay = cleanerpay

        guest_fullname = reservation["guest"]["fullName"] if reservation is not None and "fullName" in reservation["guest"] and reservation["guest"]["fullName"] is not None else ''
        guest_count = reservation["guest"]["count"] if reservation is not None and "count" in reservation["guest"] and reservation["guest"]["count"] is not None else 0

        task_organized_data = self.task_insert_data(listing_id=listing_id, reservation_id=reservation_id, status=status,
                                                    guest_count=guest_count, listing_nickname=listing_nickname,
                                                    listing_address=listing_address, guest_fullname=guest_fullname,
                                                    local_user_id=local_user_id, start_time=start_time, guesty_task_id=guesty_task_id,
                                                    local_message_id=local_message_id, cleanerpay=cleanerpay)
        return task_organized_data

    def task_data_guesty_tfl(self, task, reservation = None, listing=None, local_user_id=None, local_message_id=None, cleanerpay=0): # tfl = task from loop
        try:
            guesty_task_id = task["id"]
            status = task["status"]['status']
            start_time = task['scheduledFor']["startTime"]
            listing_id = task['listing']["listingId"] if 'listingId' in task['listing'] and task['listing']["listingId"] is not None else None
            reservation_id = task['reservation']["reservationId"] if 'reservationId' in task['reservation'] and task['reservation']["reservationId"] is not None else None
            listing_address = listing["address"]['full'] if listing is not None else ''
            listing_nickname = listing["nickname"] if listing is not None else ''

            new_cleanerpay = 0
            if cleanerpay == 0:
                cleanerpay_field_id = os.getenv("CLEANERPAY_CUSTOM_FIELD_ID")
                cleanerpay_field = next((field for field in listing["customFields"] if field["fieldId"] == cleanerpay_field_id), None) if listing is not None else None
                cleanerpay = cleanerpay_field["value"] if cleanerpay_field is not None else 0
                new_cleanerpay = cleanerpay

            guest_fullname = reservation["guest"]["fullName"] if reservation is not None and "fullName" in reservation["guest"] and reservation["guest"]["fullName"] is not None else ''
            guest_count = reservation["guestsCount"] if reservation is not None and "guestsCount" in reservation and reservation["guestsCount"] is not None else 0

            task_organized_data = self.task_insert_data(listing_id=listing_id, reservation_id=reservation_id, status=status,
                                                        guest_count=guest_count, listing_nickname=listing_nickname,
                                                        listing_address=listing_address, guest_fullname=guest_fullname,
                                                        local_user_id=local_user_id, start_time=start_time, guesty_task_id=guesty_task_id,
                                                        local_message_id=local_message_id, cleanerpay=cleanerpay)
            return task_organized_data
        except Exception as tflE:
            return None


    def msg_insert_data(self, message_type, discord_message_id, user_id=None, task_id=None, guesty_task_id=None, guesty_user_id=None):
        new_message_data = {
            "user_id": user_id,
            "message_type": message_type,
            "discord_message_id": discord_message_id,
            "task_id": task_id,
            "guesty_task_id": guesty_task_id,
            "guesty_user_id": guesty_user_id
        }
        return new_message_data

    def adjust_insert_data(self, amount, guesty_user_id=None, guesty_listing_id=None):
        adjust_data = {
            "amount": amount,
            "guesty_user_id": guesty_user_id,
            "guesty_listing_id": guesty_listing_id,
        }
        return adjust_data

    def reorganize_task_data(self, prev_task, fetched_task):
        new_task = copy(prev_task)
        new_task['assigneeId'] = fetched_task['assigneeId']
        if 'timing' in fetched_task:
            new_task['startTime'] = fetched_task['timing']['startTime']
        new_task['status'] = fetched_task['status']
        return new_task