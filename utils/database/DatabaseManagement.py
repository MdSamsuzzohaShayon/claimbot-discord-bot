from copy import copy
from bson import ObjectId

from utils.database.BaseDatabaseManagement import BaseDatabaseManagement
from utils.Enums import MessageType, TaskStatus


class DatabaseManagement(BaseDatabaseManagement):
    def __init__(self):
        super().__init__()

    # Insert documents
    # ===============================================================================================================
    async def insert_one_task(self, data):
        new_task = await self.insert_one(collection=self.task_collection, data=data)
        return new_task

    async def insert_one_message(self, data):
        new_message = await self.insert_one(collection=self.message_collection, data=data)
        return new_message

    async def insert_one_user(self, data):
        new_user = await self.insert_one(collection=self.user_collection, data=data)
        return new_user

    async def insert_one_adjust(self, data):
        new_adjust = await self.insert_one(collection=self.adjust_collection, data=data)
        return new_adjust

    async def insert_many_users(self, data):
        new_users = await self.insert_many(collection=self.user_collection, data=data)
        return new_users

    async def insert_many_tasks(self, data):
        new_tasks = await self.insert_many(collection=self.task_collection, data=data)
        return new_tasks

    # Find documents
    # ===============================================================================================================
    async def find_all_tasks(self):
        task_list = await self.find_all(collection=self.task_collection, find_filters={})
        return task_list

    async def find_all_messages(self):
        message_list = await self.find_all(collection=self.message_collection, find_filters={})
        return message_list

    async def find_all_users(self):
        user_list = await self.find_all(collection=self.user_collection, find_filters={})
        return user_list

    async def find_users_populate_tasks(self, doc_filter):
        try:
            # Find all users and populate their tasks -> here we can use find all function from super class of this class
            # ===============================================================================================================
            cursor = self.task_collection.find(doc_filter)  # "2023-04-29T13:45:00.000Z"

            task_list = []
            user_id_set = set()
            user_list = []

            async for doc in cursor:
                if "user_id" in doc:
                    task_list.append(doc)
                    user_id_set.add(doc["user_id"])

            user_cursor = self.user_collection.find({"_id": {"$in": list(user_id_set)}})
            async for doc in user_cursor:
                user_list.append(doc)

            return task_list, user_list

        except Exception as e:
            return None, None

    async def find_user_by_id(self, user_id):
        try:
            # A simple function to find user by user_id
            # ===============================================================================================================
            find_user = await self.find_one(collection=self.user_collection, doc_filter={'_id': user_id})
            if find_user is None:
                return None
            return find_user
        except Exception as e:
            return None

    async def find_user_by_id_populate_tasks(self, user_id):
        try:
            # Find one user and get all the tasks he has -> again, here to get all the tasks we can use find_all
            # ===============================================================================================================
            find_user = await self.find_one_user(doc_filter={"_id": user_id})
            if find_user is None:
                return None
            # tasks = await self.find_tasks_of_user(tasks_ids=find_user["task_ids"])
            tasks = await self.find_tasks(doc_filters={"user_id": user_id})
            find_user["tasks"] = tasks
            return find_user
        except Exception as e:
            await self.error_handler.exception_error(desc=e, reference_file="utils/database/DatabaseManagement.py:98")
            return None

    async def find_one_user_and_filter_tasks(self, doc_filter):
        try:
            # find_user = await self.user_collection.find_one(doc_filter)
            find_user = await self.find_one_user(doc_filter=doc_filter)
            if find_user is None:
                return None
            new_user = copy(find_user)

            task_id_set = set()
            for task_id in new_user["task_ids"]:
                task_id_set.add(task_id)

            tasks = []
            if len(task_id_set) > 0:
                doc_filters = {
                    "_id": {"$in": list(task_id_set)},
                    "status": TaskStatus.IN_PROGRESS.value
                }
                tasks = await self.find_tasks(doc_filters=doc_filters)

            new_user["tasks"] = tasks
            return new_user
        except Exception as e:
            await self.error_handler.exception_error(desc=e, reference_file="utils/database/DatabaseManagement.py:140")
            return None

    async def find_one_adjustment(self, doc_filter):
        try:
            # Find from adjustment collections -> again I should create a function for this in super class
            # ===============================================================================================================
            find_user = await self.user_collection.find_one(doc_filter)
            if find_user is None:
                return None
            return find_user
        except Exception as e:
            return None

    async def find_task_by_guesty_id(self, guesty_task_id):
        try:
            # Find from task collections
            # ===============================================================================================================
            find_task = await self.task_collection.find_one({'guesty_task_id': guesty_task_id})
            return find_task
        except Exception as e:
            return None

    async def find_one_task(self, doc_filter):
        find_task = await self.find_one(collection=self.task_collection, doc_filter=doc_filter)
        return find_task

    async def find_one_user(self, doc_filter):
        find_user = await self.find_one(collection=self.user_collection, doc_filter=doc_filter)
        return  find_user

    async def find_one_message(self, doc_filter):
        find_task = await self.find_one(collection=self.message_collection, doc_filter=doc_filter)
        return find_task

    async def find_task_by_id(self, task_id):
        try:
            find_task = await self.message_collection.find_one({'task_id': task_id})
            if find_task is None:
                return None
            new_task = copy(find_task)
            return new_task
        except Exception as e:
            return None

    async def find_message_by_id(self, message_id):
        try:
            find_task = await self.message_collection.find_one({'_id': ObjectId(message_id)})
            if find_task is None:
                return None
            new_task = copy(find_task)
            return new_task
        except Exception as e:
            return None

    async def find_tasks(self, doc_filters):
        # This function should be declared in a subclass of this class, and instead of find again call find_all function
        # ===============================================================================================================
        task_list = await self.find_all(find_filters=doc_filters, collection=self.task_collection)
        return task_list

    async def find_users(self, doc_filters):
        # This function should be declared in a subclass of this class, and instead of find again call find_all function
        # ===============================================================================================================
        user_list = await self.find_all(find_filters=doc_filters, collection=self.user_collection)
        return user_list

    async def find_adjustments(self, doc_filters):
        # This function should be declared in a subclass of this class, and instead of find again call find_all function
        # ===============================================================================================================
        adjust_list = await self.find_all(find_filters=doc_filters, collection=self.adjust_collection)
        return adjust_list


    # find and update from collections
    # ===============================================================================================================
    async def find_one_and_update(self, collection_to_update, find_filters, set_dict=None, push_dict=None, pull_dict=None):
        try:
            new_find_filters, new_update_dict = await self.update_precise(find_filters=find_filters, set_dict=set_dict, pull_dict=pull_dict, push_dict=push_dict)

            updated = await collection_to_update.update_one(
                new_find_filters,
                new_update_dict
            )
            if updated is not None:
                return True
            return False
        except Exception as e:
            return False

    async def find_and_update_many(self, collection_to_update, find_filters, set_dict=None, push_dict=None, pull_dict=None):
        try:
            new_find_filters, new_update_dict = await self.update_precise(find_filters=find_filters, set_dict=set_dict, pull_dict=pull_dict, push_dict=push_dict)
            # await collection_to_update.update_many({'i': {'$gt': 100}},
            #                                        {'$set': {'key': 'value'}})
            updated = await collection_to_update.update_many(
                new_find_filters,
                new_update_dict
            )
            if updated is not None:
                return True
            return False
        except Exception as e:
            return False

    async def update_one_task(self, find_filters, set_dict=None, push_dict=None, pull_dict=None):
        updated = await self.find_one_and_update(collection_to_update=self.task_collection, find_filters=find_filters, set_dict=set_dict, push_dict=push_dict, pull_dict=pull_dict)
        return updated

    async def update_one_message(self, find_filters, set_dict=None, push_dict=None, pull_dict=None):
        try:
            await self.find_one_and_update(collection_to_update=self.message_collection, find_filters=find_filters, set_dict=set_dict, push_dict=push_dict, pull_dict=pull_dict)
        except Exception as e:
            return False

    async def update_one_user(self, find_filters, set_dict=None, push_dict=None, pull_dict=None):
        try:
            await self.find_one_and_update(collection_to_update=self.user_collection, find_filters=find_filters, set_dict=set_dict, push_dict=push_dict, pull_dict=pull_dict)
        except Exception as e:
            return False

    async def update_many_task(self, find_filters, set_dict=None, push_dict=None, pull_dict=None):
        try:
            await self.find_and_update_many(collection_to_update=self.task_collection, find_filters=find_filters, set_dict=set_dict, push_dict=push_dict, pull_dict=pull_dict)
        except Exception as e:
            return False


    async def delete_one_message(self, filters):
        try:
            delete_one = await self.delete_one(collection=self.message_collection, filters=filters)
            return delete_one
        except Exception as e:
            return False

    async def delete_one_task(self, filters):
        try:
            delete_one = await self.delete_one(collection=self.task_collection, filters=filters)
            return delete_one
        except Exception as e:
            return False

    async def delete_many_messages(self, filters={}):
        try:
            result = await self.delete_many(collection=self.message_collection, filters=filters)
            return result
        except Exception as e:
            return None
