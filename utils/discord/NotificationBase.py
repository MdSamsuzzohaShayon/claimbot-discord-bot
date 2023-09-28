from config.keys import CHANNELS


class NotificationBase:
    def __init__(self, client):
        self.notifications_channel = client.get_channel(CHANNELS['notifications'])


