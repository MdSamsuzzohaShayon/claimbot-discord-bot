import asyncio
import logging
from fastapi.responses import JSONResponse
from fastapi import status

from copy import copy

from fastapi import APIRouter, Request, Body,  HTTPException
from utils.FormatString import FormatString
from utils.OrganizeGuestyData import OrganizeGuestyData

from config.keys import TASK_TITLE
from utils.Enums import TaskStatus

from utils.guesty.GuestyListingRequests import GuestyListingRequests
from utils.guesty.GuestyReservationRequests import GuestyReservationRequests
from utils.guesty.GuestyTaskRequests import GuestyTaskRequests

from utils.database.DatabaseManagement import DatabaseManagement

from controllers.ReservationController import ReservationController
from controllers.TaskController import TaskController
from controllers.TaskUpdateController import TaskUpdateController
from bot import client

router = APIRouter()


@router.post('/reservation/new')
async def reservation_new(request: Request, body: dict = Body(...)):
    """
    TODO:
        Change ta/trun around from here. check in data and if that date is match with any task's start date it is ta
    """
    try:
        if body is None or 'reservation' not in body:
            return None

        reservation = body["reservation"]
        # SEND BUTTON FROM HERE
        reservation_controller = ReservationController(reservation)
        await reservation_controller.reservation_new()
        logging.warning("New reservation controlled successfully")
        return JSONResponse(status_code=status.HTTP_200_OK, content="Reservation created successfully")
    except HTTPException as e:
        logging.error(e)


@router.post("/reservation/update")
async def reservation_update(body: dict = Body(...)):
    """
    TODO:
        If number of guest change update the value in database as well as in discord message
    """
    try:
        if body is None or 'reservation' not in body or 'reservationBefore' not in body:
            return None

        reservation = body["reservation"]
        reservation_before = body["reservationBefore"]
        reservation_controller = ReservationController(reservation=reservation, reservation_before=reservation_before)
        await reservation_controller.reservation_update()
        # logging.warning("Reservation updated successfully")
        return JSONResponse(status_code=status.HTTP_200_OK, content="Reservation updated successfully")
    except HTTPException as e:
        logging.error(e)


@router.post('/task/new')
async def task_new(request: Request, body: dict = Body(...)):
    """
    TODO:
        When a new task is created in guesty called "clean", Then that task is added to available cleanings Once a
        cleaner accepts this task, you need to assign the task to the correct cleaner in guesty and then in discord remove it
        from available and add the info to the users list
    """
    try:
        task = body['task']
        reservation_id = task["reservationId"] if "reservationId" in task and task["reservationId"] is not None else None
        listing_id = task["listingId"]
        guesty_task_id = task["_id"]
        if task["title"].lower() != TASK_TITLE:
            return None

        fs = FormatString()
        # Get reservation and listing concurrently
        guesty_listing = GuestyListingRequests()
        guesty_reservation = GuestyReservationRequests()
        guesty_task = GuestyTaskRequests()
        db = DatabaseManagement()
        task_single, listing_single, reservation_single, find_task_local = await asyncio.gather(
            guesty_task.retrive_a_task(task_id=guesty_task_id),
            guesty_listing.retrive_a_listing(listing_id=listing_id),
            guesty_reservation.retrive_a_reservation(reservation_id=reservation_id),
            db.find_one_task(doc_filter={"guesty_task_id": guesty_task_id})
        )

        if listing_single is None or task_single is None:
            return None



        # if find_task_local and find_task_local['user_id'] is not None:
        #     find_local_user = await db.find_one_user(doc_filter={"_id": find_task_local['user_id']})
        #     find_local_user
        # print({
        #     "guesty_task_id": guesty_task_id,
        #     "task_new":{
        #         "status": task['status'],
        #         "assignee_id": task['assigneeId'],
        #         "start_time": start_time,
        #     },
        #     "fetched_task": {
        #         "status": task_single['status'],
        #         "assignee_id": task_single['assigneeId'],
        #         "start_time": task_single['timing']['startTime'],
        #     },
        # })
        ogd = OrganizeGuestyData()
        new_task = ogd.reorganize_task_data(prev_task=task, fetched_task=task_single)

        start_time = new_task["startTime"]
        start_time_obj = fs.iso_to_est_time(iso_time=start_time).date()
        is_within_seven_days = fs.is_within_forward_days(target_date=start_time_obj, days=7)
        if is_within_seven_days is False:
            return None

        # Add task to available cleaning channel
        task_controller = TaskController(task=new_task)
        if 'assigneeId' in new_task and new_task['assigneeId'] is not None:
            await task_controller.task_add_to_user_channel(task_single=new_task, listing_single=listing_single, reservation_single=reservation_single)
        else:
            await task_controller.task_add_to_available_cleaning_channel(task_single=new_task, listing_single=listing_single, reservation_single=reservation_single)

        return JSONResponse(status_code=status.HTTP_200_OK, content="New task created successfully")
    except Exception as e:
        logging.error(e)


@router.post("/task/update")
async def task_update(body: dict = Body(...)):
    """
    TODO:
        When task status change update message on available cleaning channel or user's channel
        Send notification if reservation date change
        remove task if the reservation canceled and notify user
        If we change task status pending to confirm it will automatically add assigneeId (By default our user ID)
    """
    try:
        val_not_found = "A Essential parameter not found in the body of the request"
        task_before = body.get("taskBefore", val_not_found)
        task = body.get("task", val_not_found)
        if task is val_not_found or task_before is val_not_found:
            return None

        if task["title"].strip().lower() != TASK_TITLE and task_before['title'].strip().lower() != TASK_TITLE:
            return None

        guesty_task_id = task['_id']
        new_task = copy(task)

        # Fetch guesty task from here and change some properties
        guesty_task = GuestyTaskRequests()
        task_single = await guesty_task.retrive_a_task(task_id=guesty_task_id)
        if task_single:
            ogd = OrganizeGuestyData()
            new_task = ogd.reorganize_task_data(prev_task=task, fetched_task=task_single)

        guesty_curr_u_id = new_task["assigneeId"] if 'assigneeId' in new_task else None
        guesty_prev_u_id = task_before["assigneeId"] if 'assigneeId' in task_before else None
        task_status = new_task['status']

        task_updated, cancel_task, revive_task, change_assignee, change_schedule, remove_assignee = False, False, False, False, False, False
        start_time = new_task["startTime"]
        fs = FormatString()
        us_datetime_obj = fs.iso_to_est_time(iso_time=start_time)
        is_within_7_days = fs.is_within_forward_days(target_date=us_datetime_obj.date(), days=7)
        task_today = False
        us_today = fs.current_est_datetime_obj()
        if us_today.year == us_datetime_obj.year and us_datetime_obj.month == us_today.month and us_datetime_obj.day == us_today.day:
            task_today = True

        update_controller = TaskUpdateController(guesty_task_id=guesty_task_id, client=client, task=new_task, task_before=task_before, task_today=task_today, is_within_7_days=is_within_7_days)

        # Cancel the task
        if new_task["title"].strip().lower() != TASK_TITLE and task_before["title"].strip().lower() == TASK_TITLE:
            cancel_task = True
            task_updated = True

        # Reassign the task
        if new_task["title"].strip().lower() == TASK_TITLE and task_before["title"].strip().lower() != TASK_TITLE:
            revive_task = True
            task_updated = True

        # Cancel the task
        if new_task["status"] == TaskStatus.CANCELED.value.lower() and task_before['status'] != TaskStatus.CANCELED.value.lower():
            # let user know that the task is canceled if task is assigned
            cancel_task = True
            task_updated = True

        # Time change
        if new_task["startTime"] != task_before['startTime'] and new_task["status"] != TaskStatus.CANCELED.value.lower():
            change_schedule = True
            task_updated = True

        # Reassign the task
        if new_task['status'] != TaskStatus.CANCELED.value.lower() and task_before["status"] == TaskStatus.CANCELED.value.lower():
            revive_task = True
            task_updated = True

        # Check if the assignee remove - this is also affecting main function such add task from available cleaning channel
        # Check if the message is already there or not, if it is already there return
        if new_task["assigneeId"] is not None and new_task["assigneeId"] != task_before["assigneeId"] and new_task["status"] != TaskStatus.CANCELED.value.lower():
            # Assignee change
            change_assignee = True
            task_updated = True
        elif task["assigneeId"] is None and task_before["assigneeId"] is not None:
            # Add task to available cleaning and remove task from previous user
            change_assignee = True
            task_updated = True

        # Update database
        if task_updated:
            await update_controller.find_from_db(guesty_curr_u_id=guesty_curr_u_id, guesty_prev_u_id=guesty_prev_u_id, guesty_task_id=guesty_task_id)
            is_successful = False
            # Operations
            if cancel_task:
                is_successful = await update_controller.task_cancel()
            if revive_task:
                is_successful = await update_controller.task_revive()
            if change_schedule:
                is_successful = await update_controller.task_reschedule()
            if change_assignee:
                is_successful = await update_controller.task_assignee_change()

            if is_successful:
                # Update, add, or delete (task, user, and message)
                await update_controller.update_from_db(task_must=not cancel_task, curr_user_must=True, prev_user_must=change_assignee, message_must=task_today)
                await update_controller.update_discord_user_chart()
                print("Task updated successfully")

        return JSONResponse(status_code=status.HTTP_200_OK, content="Task updated successfully")
    except Exception as e:
        logging.error(e)


@router.post("/task/delete")
async def task_delete(body: dict = Body(...)):
    """
    TODO:
        When task delete do the same action we did for canceling a task
    """
    try:
        val_not_found = "A Essential parameter not found in the body of the request"
        task = body.get("task", val_not_found)
        guesty_task_id = task["_id"]
        if task is val_not_found:
            return None

        # return if task title id not clean
        if task["title"].lower() != TASK_TITLE:
            return None

        new_task = copy(task)

        fs = FormatString()
        start_time = new_task["startTime"]
        us_datetime_obj = fs.iso_to_est_time(iso_time=start_time)
        is_within_7_days = fs.is_within_forward_days(target_date=us_datetime_obj.date(), days=7)
        task_today = False
        us_today = fs.current_est_datetime_obj()
        if us_today.year == us_datetime_obj.year and us_datetime_obj.month == us_today.month and us_datetime_obj.day == us_today.day:
            task_today = True
        update_controller = TaskUpdateController(guesty_task_id=guesty_task_id, client=client, task=new_task, task_before=None, task_today=task_today, is_within_7_days=is_within_7_days)
        # let user know that the task is canceled if task is assigned
        guesty_user_id = new_task['assigneeId'] if new_task['assigneeId'] is not None else None
        await update_controller.find_from_db(guesty_curr_u_id=guesty_user_id, guesty_prev_u_id=None, guesty_task_id=guesty_task_id)
        await update_controller.task_cancel()
        await update_controller.update_from_db(task_must=False, curr_user_must=True, prev_user_must=False, message_must=False, delete_task=True)
        await update_controller.update_discord_user_chart()

        return JSONResponse(status_code=status.HTTP_200_OK, content="Task deleted successfully")
    except Exception as e:
        logging.error(e)
