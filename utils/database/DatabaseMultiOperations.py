import asyncio
import re

from bson import ObjectId
from datetime import datetime

from utils.database.DatabaseManagement import DatabaseManagement
from utils.Enums import TaskStatus, MessageType


# This class is for doing multiple database operations within one function
# ===============================================================================================================
class DatabaseMultiOperations(DatabaseManagement):

    def __init__(self):
        super().__init__()

    async def find_task_user_message(self, guesty_task_id, username):
        try:
            task_exist_local, user_exist_local = await asyncio.gather(
                self.find_task_by_guesty_id(guesty_task_id=guesty_task_id),
                self.find_one_user(doc_filter={"username": username})
            )
            message_exist_local =  await self.message_collection.find_one({'user_id': user_exist_local["_id"]})
            return task_exist_local, user_exist_local, message_exist_local
        except Exception as e:
            return None, None, None

    async def update_task_user_message_for_task_release(self, db_task_id, db_user_id, db_message_id, discord_message_id):
        try:
            await asyncio.gather(
                self.find_one_and_update(collection_to_update=self.task_collection, find_filters={"_id": ObjectId(db_task_id)}, set_dict={'status': TaskStatus.PENDING.value, "user_id": None}),
                self.find_one_and_update(collection_to_update=self.user_collection, find_filters={"_id": ObjectId(db_user_id)}, pull_dict={"task_ids": db_task_id, "message_ids": db_message_id}),
                self.find_one_and_update(collection_to_update=self.message_collection, find_filters={"_id": ObjectId(db_message_id)}, set_dict={"discord_message_id": discord_message_id, "user_id": None, "type": MessageType.AVAILABLE_MESSAGE.value})
            )
            return True
        except Exception as e:
            return False

    # find or update update collections
    # ===============================================================================================================
    async def create_adjust_with_user_relation(self, adjust_amount, user_id):
        try:
            # find a document, if the document is found update that otherwise create new document
            adjust_data = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "amount": adjust_amount,
                "user_id": user_id
            }
            new_adjustment = await self.adjust_collection.insert_one(adjust_data)
            await self.find_one_and_update(collection_to_update=self.user_collection, find_filters={"_id": ObjectId(user_id)}, push_dict={"adjust_ids": new_adjustment.inserted_id})
            return True
        except Exception as e:
            return False

    # For user and tasks
    async def create_adjustment_with_relation(self, adjust_amount, task_id=None, user_id=None, guesty_user_id=None, guesty_listing_id=None):
        try:
            # find a document, if the document is found update that otherwise create new document
            # ===============================================================================================================
            if task_id is None and user_id is None:
                return False
            adjust_data = {
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "amount": adjust_amount
            }

            collection  = None
            if task_id is not None:
                collection = self.task_collection
                adjust_data["task_id"] = task_id
            if user_id is not None:
                collection = self.user_collection
                adjust_data["user_id"] = user_id

            new_adjustment = await self.adjust_collection.insert_one(adjust_data)
            await self.find_one_and_update(collection_to_update=collection, find_filters={"_id": ObjectId(task_id)}, push_dict={"adjust_ids": new_adjustment.inserted_id})
            return True
        except Exception as e:
            return False

    async def find_users_tasks_adjusts(self, regex):
        try:
            find_tasks, find_adjustments = await asyncio.gather(
                self.find_all(collection=self.task_collection, find_filters={"status": TaskStatus.COMPLETED.value, "start_time": {"$regex": regex}}),
                self.find_all(collection=self.adjust_collection, find_filters={"updated_at": {"$regex": regex}})
            )

            user_ids = set()
            for doc in find_tasks:
                user_ids.add(doc["user_id"])

            for doc in find_adjustments:
                if "user_id" in doc and doc["user_id"] is not None:
                    user_ids.add(doc["user_id"])

            find_users = await self.find_all(collection=self.user_collection, find_filters={"_id": {"$in": list(user_ids)}})
            return find_users, find_tasks, find_adjustments
        except Exception:
            return None, None, None