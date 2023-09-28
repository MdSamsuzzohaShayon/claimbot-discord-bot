import logging
import re

from utils.guesty.GuestyListingRequests import GuestyListingRequests
from utils.database.DatabaseMultiOperations import DatabaseMultiOperations


class ReservationController:
    def __init__(self, reservation, reservation_before=None):
        self.reservation = reservation
        self.reservation_before = reservation_before
        self.guesty_listing = GuestyListingRequests()
        self.db = DatabaseMultiOperations()

    async def reservation_new(self):
        try:
            if "checkIn" not in self.reservation or "listingId" not in self.reservation:
                return None
            listingId = self.reservation["listingId"]

            find_listing = await self.guesty_listing.retrive_a_listing(listing_id=listingId)
            if find_listing is None:
                return None
            listing_nickname = find_listing["nickname"]
            # find_all task -> Check task time from db match with reservationTime and listing_nickname does match with the nickname got from guesty listing
            # if any task found update the value of ta of that task
            # ===============================================================================================================
            regex = re.compile(r"\d{4}-\d{2}-\d{2}")
            reservation_time = regex.findall(self.reservation["checkIn"])[0] if 'checkIn' in self.reservation else None
            await self.db.update_many_task(find_filters={"start_time": {"$regex": reservation_time}, "listing_nickname": listing_nickname}, set_dict={"ta": True})
        except Exception as e:
            logging.error(e)


    async def reservation_update(self):
        try:
            if self.reservation_before is None or "guestsCount" not in self.reservation or "guestsCount" not in self.reservation_before:
                return None
            listingId = self.reservation["listingId"]

            # Get a task using listingId from task collection
            # Change guest count in task collection
            # Change guest count in message from available cleaning or user cleaning channel
        except Exception as e:
            logging.error(e)

