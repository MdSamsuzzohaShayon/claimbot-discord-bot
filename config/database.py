import motor.motor_asyncio
import os
from dotenv import load_dotenv


load_dotenv()


"""
You typically create a single instance of AsyncIOMotorClient at the time your application starts up. -> https://motor.readthedocs.io/en/stable/tutorial-asyncio.html
"""

# Connection
# ======================================================================================================================
client = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGODB_URI'))

# Database
# ======================================================================================================================
database = client.claimbot

# Collections
# ======================================================================================================================
# (Unused)
reservation_collection = database.reservation
# Create one-to-many relationship with user
# ===============================================================================================================
task_collection = database.task
user_collection = database.user
# Create one-to-many relationship with user and one-to-one relationship with task
# ===============================================================================================================
message_collection = database.message
not_collection = database.notification
# Create one-to-many relationship with user
# ===============================================================================================================
adjust_collection = database.adjustment
