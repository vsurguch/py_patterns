
import abc
from utils.message_ import *
from server.clinic import Clinic

monkey_clinic = Clinic()

# monkey_patch_client_server - заглушка имитирующая передачу по сети и получение ответа
def monkey_patch_clint_server(request):
    resp = monkey_clinic.request_processor(request).json()
    return resp


# msg_template = {
#     'session_key': None,
#     'body': {
#         'request': 'empty',
#         'request_id': None,
#         'data': {}
#     }
# }


class User:
    def __init__(self):
        self.autherized = False
        self.session_id = ''
        self.primary_key = ''
        self.actions = ['start', 'login', 'get_actions']


class Action(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def act(self):
        pass


class BasicAction(Action):
    _msg_type = ''
    _msg_body_data = []

    def __init__(self, gateway, user, request_id=0, required_data=None):
        self.gateway = gateway
        self.user = user
        self.request_id = request_id
        if required_data != None:
            self._msg_body_data = required_data
        self.get_msg_body_data()

    def set_request_type(self, value):
        pass

    def get_msg_body_data(self):
        self.msg_body = MessageBuilder2(self._msg_body_data).build()

    def act(self):
        msg = Message(self.user.session_id,
                      self._msg_type,
                      self.request_id,
                      self.msg_body)
        raw_resp = self.gateway(msg.json())
        resp = Message().from_json(raw_resp)
        if 'result' in resp.data:
            print(resp.data['result'])
        return resp



class StartAction(BasicAction):
    _msg_type = 'start'


class LoginAction(BasicAction):
    _msg_type = 'login'
    _msg_body_data = ['username', 'password']

    def act(self):
        resp = super().act()
        status_code = resp.data.get('status_code')
        if status_code == 200:
            self.user.autherized = True
        return resp


class RegisterAction(BasicAction):
    _msg_type = 'register'
    _msg_body_data = ['username', 'password', 'password2']


class GetActinsListAction(BasicAction):
    _msg_type = 'get_actions'

    def act(self):
        resp = super().act()
        status_code = resp.data.get('status_code')
        if status_code == 200:
            self.user.actions = resp.data['actions']
        return resp


# class AnswerAction(BasicAction):
#     _msg_type = 'answer'


class GenericAction(BasicAction):
    _msg_type = 'generic'

    def set_request_type(self, request_type):
        self._msg_type = request_type

    def act(self):
        resp = super().act()
        if resp.request_id:
            required_data = resp.data['required_data']
            action = GenericAction(self.gateway,
                                   self.user,
                                   request_id=resp.request_id,
                                   required_data=required_data)
            action.set_request_type(self._msg_type)
            resp =  action.act()
        return resp


ACTIONS = {
        'start': {'info': 'start',
                  'action': StartAction,
                  },
        'login': {'info': 'autherization',
                 'action': LoginAction,
                 },
        'register': {'info': 'registration',
                     'action': RegisterAction
                    },
        'get_actions': {'info': '',
                        'action': GetActinsListAction
                        },
        'generic': {'info': 'generic',
                             'action': GenericAction
                             },
        # 'answer': {'info': 'answer',
        #            'action': AnswerAction
        #            }
    }


class Dialog:

    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, gateway=monkey_patch_clint_server,
                 choice_func=get_from_console):

        # gateway - это клиент - сокет, который будет отправлять сообщение и возвращать ответ от сервера
        # monkey_patch_client_server - заглушка имитирующая передачу по сети и получение ответа

        self.gateway = gateway
        self.user = User()
        self.choice_func = choice_func

    @staticmethod
    def get_action(action_name):
        if action_name in ACTIONS:
            return ACTIONS[action_name]['action']
        else:
            return ACTIONS['generic']['action']

    def start_dialog(self):
        Action = self.get_action('start')
        resp = Action(self.gateway, self.user).act()

        Action = self.get_action('login')
        resp = Action(self.gateway, self.user).act()

        if self.user.autherized:
            Action = self.get_action('get_actions')
            resp = Action(self.gateway, self.user).act()

    def run(self):
        while True:

            choice = self.choice_func(avilable_options=self.user.actions)

            if choice == 'quit' or choice == 'q' or choice == 'exit':
                break
            elif choice in self.user.actions:
                Action = self.get_action(choice)
                action = Action(self.gateway, self.user)
                action.set_request_type(choice)
                resp = action.act()
            else:
                Action = self.get_action('generic')
                action = Action(self.gateway, self.user)
                action.set_request_type('generic')
                resp = action.act()





