import os
from copy import copy

PY_ENV = os.getenv("PY_ENV")
from config.keys_dev import CHANNELS as CHANNELS_DEV, TASK_TITLE_DEV
from config.keys_prod import CHANNELS as CHANNELS_PROD, TASK_TITLE_PROD


TASK_TITLE = TASK_TITLE_DEV
CHANNELS = copy(CHANNELS_DEV)
if PY_ENV == "production":
    CHANNELS = copy(CHANNELS_PROD)
    TASK_TITLE = TASK_TITLE_PROD

CLEANING_TITLES = {
    'cleaning_available': "New Cleaning Availabled",
    'cleaning_added': "New Cleaning Added",
    'cleaning_started': "Cleaning Started",
}

TASK_CHART_TITLE = "Upcoming Tasks"


DELETE_AFTER_5_MIN = 60 * 5
DELETE_AFTER_1_DAY = 60 * 60 * 24
DELETE_AFTER_7_DAYS = 60 * 60 * 24 * 7
