

from server.dispatcher import Dispatcher
from server.schedule import Schedule

from utils.message_ import Message


class Clinic:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.dispatcher = Dispatcher()
        self.schedule = Schedule()
        self.dispatcher.attach(self.schedule, 'make_appointment')

    def request_processor(self, request_json):
        msg = Message().from_json(request_json)
        resp = self.dispatcher.new_request(msg)
        return resp