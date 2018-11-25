import json


def get_from_console(prompt='', avilable_options=None):
    ans = input('{}> '.format(prompt))
    if ans == '/':
        for i, option in enumerate(avilable_options, start=1):
            print('{}. {}'.format(i, option))
        ans = input('{}>: '.format(prompt))
        try:
            i = int(ans)
            if i > 0 and i < len(avilable_options)+1:
                ans = avilable_options[i - 1]
        except:
            pass

    return ans


#
class Message():
    _msg = {'session_id': '',
            'body': {'request': '',
                     'request_id': 0,
                     'data': None}
            }

    def __init__(self, session_id = '', request_type='', request_id=0,  data=None):
        self._msg['session_id'] = session_id
        self._msg['body']['request'] = request_type
        self._msg['body']['request_id'] = request_id
        self._msg['body']['data'] = data

    @property
    def request_id(self):
        return self._msg['body']['request_id']

    @request_id.setter
    def request_id(self, id):
        self._msg['body']['request_id'] = id

    @property
    def session_id(self):
        return self._msg['session_id']

    @session_id.setter
    def session_id(self, id):
        self._msg['session_id'] = id

    @property
    def request_type(self):
        return self._msg['body']['request']

    @request_type.setter
    def request_type(self, request_type):
        self._msg['body']['request'] = request_type

    @property
    def data(self):
        return self._msg['body']['data']

    @data.setter
    def data(self, data):
        self._msg['body']['data'] = data

    def json(self):
        return json.dumps(self._msg)

    def from_json(self, json_data):
        self._msg = json.loads(json_data)
        return self
#
#
# class EmptyMessage(Message):
#     pass
#
#
# class StartMessage(Message):
#     type = 'start'
#
#
# class AuthMessage(Message):
#     type = 'login'
#     ref_data = {'login', 'password'}
#
#
# class RegisterUserMessage(Message):
#     type = 'register'
#     ref_data = {'firstname', 'lastname', 'login', 'password', 'password2', 'age'}
#
#
# class MakeAppointmentMessage(Message):
#     type = 'make_appointment'
#     ref_data = {'date', 'time', 'doctor'}
#
#
# class MessageFactory:
#
#     @staticmethod
#     def create_message(type, **kwargs):
#         if type == 'start':
#             msg = StartMessage(**kwargs)
#         elif type == 'login':
#             msg = AuthMessage(**kwargs)
#         elif type == 'register':
#             msg = RegisterUserMessage(**kwargs)
#         elif type == 'make_appointment':
#             msg = MakeAppointmentMessage(**kwargs)
#         else:
#             msg = EmptyMessage()
#         return msg


class MessageBuilder2:
    def __init__(self, msg_body_data, func_answer=get_from_console):
        self.msg = {}
        self.msg_body_data = msg_body_data
        self.ready = False
        self.func_answer = func_answer

    def build(self):
        for field in self.msg_body_data:
            prompt = '{}'.format(field)
            value = self.func_answer(prompt)
            self.msg[field] = value

        return self.msg



# class MessageBuilder:
#     def __init__(self, type, func_answer=get_from_console):
#
#         msg_factory = MessageFactory()
#         self.msg = msg_factory.create_message(type)
#         self.iter = self.field_iterator()
#         self.ready = False
#         self.func_answer = func_answer
#
#     def field_iterator(self):
#
#         for key, value in self.msg['data'].items():
#             if not value:
#                 yield key
#
#     def get_field(self):
#
#         while True:
#             try:
#                 field = next(self.iter)
#                 return field
#             except StopIteration:
#                 self.ready = True
#                 break
#
#     def fill_field(self, field, value):
#         self.msg['data'][field] = value
#
#     def build(self):
#
#         while not self.ready:
#             field = self.get_field()
#             if field:
#                 prompt = 'enter {}'.format(field)
#                 field_value = self.func_answer(prompt)
#                 self.fill_field(field, field_value)
#
#         return self.msg
