import json
import os
import urllib.parse
import logging
import httpx

from datetime import datetime

from utils.guesty.GuestyRequestBase import GuestyRequestBase
from utils.Enums import TaskStatus

class GuestyTaskRequests(GuestyRequestBase):
    def __init__(self):
        super().__init__()
        self.task_retrive_columns = "status taskTitle listing reservation scheduledFor endTime canStartAfter mustFinishBefore assignee id"

    async def retrive_a_task(self, task_id: str):
        token = await self.read_token()
        try:
            async with httpx.AsyncClient() as client:
                headers = {'Authorization': f"Bearer {token}", "Content-Type": "application/json", "accept": "application/json"}
                response = await client.get(url=f"https://open-api.guesty.com/v1/tasks-open-api/{task_id}", headers=headers)
                details = self.get_details(response=response)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logging.error(details)
                else:
                    logging.warning(details)
                return None
        except Exception as e:
            logging.error(e)
            return None

    async def assign_task_to_a_user(self, task_id, user_id):
        try:
            data = {"assigneeId": user_id, "status": TaskStatus.CONFIRMED.value.lower()}
            response = await self.update_task(task_id=task_id, update_data=data)
            return response
        except Exception as e:
            logging.error(e)
            return None

    async def update_task(self, task_id: str, update_data: dict):
        token = await self.read_token()
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {'Authorization': f"Bearer {token}"}
                if os.getenv('PY_ENV') == 'development':
                    update_data["description"] = f"This task is been updated at {datetime.now()}"
                print(task_id, update_data)
                response = await client.put(url=f"{self.open_api_url}/tasks-open-api/{task_id}", json=update_data, headers=headers)
                details = self.get_details(response=response)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logging.error(details)
                else:
                    logging.warning(details)
                return None
        except Exception as e:
            logging.error(e)
            return None

    async def find_tasks(self, skip=0, limit=200, filters={}):
        try:
            # Value of task title https://open-api.guesty.com/v1/tasks-open-api/tasks?filters={'title':{'@eq':'TestTask'}}&columns=status
            # For one value of startTime : https://open-api.guesty.com/v1/tasks-open-api/tasks?filters={'startTime':{'@eq':'2022-12-25T20:00:00.000Z'}}&columns=status
            # For value of startTime arrary: https://open-api.guesty.com/v1/tasks-open-api/tasks?filters={'startTime':{'@in':['2022-12-25T20:00:00.000Z','2022-12-29T20:00:00.000Z']}}&columns=status
            token = await self.read_token()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    'Content-Type': 'application/json',
                    'accept': 'application/json',
                    'Authorization': f"Bearer {token}"
                }
                query_params = {
                    "columns": self.task_retrive_columns,
                    'filters': json.dumps(filters),
                    'skip': skip,
                    "limit": limit
                }
                encoded_params = urllib.parse.urlencode(query_params)
                url = f"{self.open_api_url}/tasks-open-api/tasks?{encoded_params}"
                response = await client.get(url=url, headers=headers)
                details = self.get_details(response=response)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    logging.error(details)
                else:
                    logging.warning(details)

                return []
        except Exception as e:
            logging.error(e)
            return []

    async def find_all_tasks(self, filters={}):
        try:
            all_guesty_tasks = []
            skip, limit = 0, 200
            while True:
                find_tasks = await self.find_tasks(skip=skip, limit=limit, filters=filters)
                all_guesty_tasks.extend(find_tasks)
                if len(find_tasks) < limit:
                    break
                skip += limit
            return all_guesty_tasks
        except Exception as e:
            logging.error(e)
            return []

    async def all_tasks_of_an_user(self, guesty_user_id):
        if guesty_user_id is None:
            return []
        try:
            task_list = []
            search_task_filters = {'assigneeId': {"@eq": guesty_user_id}}
            skip = 0
            limit = 200
            while True:
                find_tasks = await self.find_tasks(skip=skip, limit=limit, filters=search_task_filters)
                task_list.extend(find_tasks)
                if len(find_tasks) < limit:
                    break
                skip += limit
            return task_list
        except Exception as e:
            logging.error(e)
            return []
