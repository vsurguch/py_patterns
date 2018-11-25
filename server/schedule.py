

class Schedule():
    _instance = None

    _appointments = []

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def notify(self, data):
        print('notification')

