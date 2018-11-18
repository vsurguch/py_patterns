
import abc
from message_ import *
from request import Request

import json

# monkey_patch_client_server - заглушка имитирующая передачу по сети и получение ответа
def monkey_patch_clint_server(request):
    request_dict = json.loads(request)
    resp = Request(request_dict).process()
    return resp

# decorator session_id_required
# def session_id_required(func):
#     def decorated(**kwargs):
#         if not 'session_id' in kwargs:
#             raise KeyError
#         return func(**kwargs)
#
#     return decorated

ROLES = {
    'basic': ['start', 'login', 'register'],
    'patient': ['make_appointment', 'get_my_appointments'],
    'doctor': ['select_patients', ]
}


class User:

    def __init__(self):
        self._role = 'basic'
        self.autherized = False
        self.session_id = ''
        self.primary_key = ''
        self.actions = []

    @property
    def role(self):
        return self._role

    @role.setter
    def role(self, role):
        if role in ROLES:
            self._role = role
            self.actions = ROLES[role]


class Action(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def act(self):
        pass

class BasicAction(Action):
    def __init__(self, gateway, user):
        self.gateway = gateway
        self.user = user

    def act(self):
        pass

class StartAction(BasicAction):
    def act(self):
        msg = MessageBuilder('start').build()
        resp = self.gateway(msg.json())
        print(resp)


class LoginAction(BasicAction):
    def act(self):
        msg = MessageBuilder('login').build()
        resp = self.gateway(msg.json())
        print(resp)


class RegisterAction(BasicAction):
    def act(self):
        msg = MessageBuilder('register').build()
        resp = self.gateway(msg.json())
        print(resp)

class MakeAppointmentAction(BasicAction):
    def act(self):
        pass


ACTIONS = {
        'start': {'info': 'start',
                  'action': StartAction,
                  },
        'login': {'info': 'autherization',
                 'action': LoginAction,
                 },
        'register': {'info': 'registration',
                     'message': RegisterAction
                    },
        'make_appointment': {'info': 'make appointment',
                             'action': MakeAppointmentAction
                             },
    }


class Dialog:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            return cls._instance
        else:
            return cls._instance

    def __init__(self, gateway=monkey_patch_clint_server, choice_func=get_from_console):

        # gateway - это клиент - сокет, который будет отправлять сообщение и возвращать ответ от сервера
        # monkey_patch_client_server - заглушка имитирующая передачу по сети и получение ответа

        self.gateway = gateway
        self.user = User()
        self.user.actions = ROLES[self.user.role]
        self.choice_func = choice_func

    @staticmethod
    def get_action(action_name):
        return ACTIONS[action_name]['action']

    def start_dialog(self):
        action = self.get_action('start')
        action(self.gateway, self.user).act()

        action = self.get_action('login')
        action(self.gateway, self.user).act()
        self.user.role = 'patient'

    def run(self):
        while True:
            choice = self.choice_func(avilable_options=self.user.actions)
            if choice == 'quit' or choice == 'q' or choice == 'exit':
                break
            else:
                if choice in self.user.actions:
                    action = self.get_action(choice)
                    action(self.gateway, self.user).act()
                else:
                    print('wrong command')





