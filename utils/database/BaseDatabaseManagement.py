from copy import copy
from bson import ObjectId
from utils.FormatString import FormatString
from config.database import task_collection, user_collection, message_collection, adjust_collection


class BaseDatabaseManagement:
    def __init__(self):
        self.task_collection = task_collection
        self.user_collection = user_collection
        self.message_collection = message_collection
        self.adjust_collection = adjust_collection
        self.fs = FormatString()

    async def update_precise(self, find_filters, set_dict=None, pull_dict=None, push_dict=None):
        # This function will be used in subclass of this class in order to not use operators manually inside dict
        # ===============================================================================================================
        new_update_dict = {}

        new_find_filters = copy(find_filters)
        if "_id" in new_find_filters:
            new_find_filters["_id"] = ObjectId(new_find_filters["_id"])

        if set_dict is not None:
            new_set_dict = copy(set_dict)
            new_set_dict["updated_at"] = self.fs.current_est_isotime()
            new_update_dict["$set"] = new_set_dict
        else:
            new_set_dict = {"updated_at": self.fs.current_est_isotime()}
            new_update_dict["$set"] = new_set_dict

        if pull_dict is not None:
            new_update_dict["$pull"] = pull_dict

        if push_dict is not None:
            for k, v in push_dict.items():
                new_find_filters[k] = {"$nin": [v]}
            new_update_dict["$push"] = push_dict

        return new_find_filters, new_update_dict

    async def find_all(self, collection, find_filters):
        try:
            # cursor does not give a list therefore, it is looping to return a list
            # ===============================================================================================================
            new_find_filters = copy(find_filters)
            if "user_id" in new_find_filters:
                new_find_filters['user_id'] = ObjectId(find_filters["user_id"])
            if "task_id" in new_find_filters:
                new_find_filters['task_id'] = ObjectId(find_filters["task_id"])
            if "message_id" in new_find_filters:
                new_find_filters['message_id'] = ObjectId(find_filters["message_id"])
            cursor = collection.find(new_find_filters)
            documents = []
            if cursor is None:
                return []
            async for doc in cursor:
                documents.append(doc)
            return documents
        except Exception:
            return []

    async def find_one(self, collection, doc_filter):
        try:
            new_filters = copy(doc_filter)
            if "_id" in new_filters:
                new_filters["_id"] = ObjectId(new_filters["_id"])
            if "user_id" in new_filters:
                new_filters["user_id"] = ObjectId(new_filters["user_id"])
            find_task = await collection.find_one(new_filters)
            if find_task is None:
                return None
            return find_task
        except Exception as e:
            return None

    async def insert_one(self, collection, data):
        new_date = copy(data)
        new_date["created_at"] = self.fs.current_est_isotime()
        new_date["updated_at"] = self.fs.current_est_isotime()
        new_record = await collection.insert_one(new_date)
        return new_record

    async def insert_many(self, collection, data):
        try:
            if len(data) <= 0:
                return None
            precised_data = []
            for d in data:
                nd = copy(d)
                nd["created_at"] = self.fs.current_est_isotime()
                nd["updated_at"] = self.fs.current_est_isotime()
                precised_data.append(nd)
            docs = await collection.insert_many(precised_data)
            return docs
        except Exception as e:
            return None

    async def delete_one(self, collection, filters):
        try:
            new_filters = copy(filters)
            if "_id" in new_filters:
                new_filters["_id"] = ObjectId(new_filters["_id"])
            if "task_id" in new_filters:
                new_filters["task_id"] = ObjectId(new_filters["task_id"])
            result = await collection.find_one_and_delete(new_filters)
            document_id = result["_id"] if "_id" in result else None
            return document_id
        except Exception as e:
            return None

    async def delete_many(self, collection, filters = {}):
        try:
            new_filters = copy(filters)
            if "_id" in new_filters:
                new_filters["_id"] = ObjectId(new_filters["_id"])
            if "task_id" in new_filters:
                new_filters["task_id"] = ObjectId(new_filters["task_id"])
            result = await collection.delete_many(new_filters)
            return result
        except Exception:
            return None
