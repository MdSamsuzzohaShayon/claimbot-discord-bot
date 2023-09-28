from enum import Enum

"""
Base class for creating enumerated constants. -> https://docs.python.org/3/library/enum.html
"""


class TaskStatus(Enum):
    CREATED = 'CREATED'
    IN_PROGRESS = 'IN PROGRESS'
    ACCEPTED = 'ACCEPTED'
    PENDING = 'PENDING'
    COMPLETED = 'COMPLETED'
    CONFIRMED = 'CONFIRMED'
    CANCELED = 'CANCELED'


class MessageType(Enum):
    USER_MESSAGE = "USER_MESSAGE"
    AVAILABLE_MESSAGE = "AVAILABLE_MESSAGE"
    USER_TASKS = "USER_TASKS"

    PAY_CALC = "PAY_CALC"
    LISTING_PAY = "LISTING_PAY"
    UPDATE_PAY = "UPDATE_PAY"
