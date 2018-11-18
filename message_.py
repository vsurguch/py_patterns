import json


def get_from_console(prompt='', avilable_options=None):
    ans = input('{}>: '.format(prompt))
    if ans == '/':
        for option in avilable_options:
            print(option)
        ans = input('{}>: '.format(prompt))
    return ans



class Message(dict):
    type = 'empty_message'
    session_id = 0
    ref_data = set()

    def __init__(self, **kwargs):
        super().__init__()
        self['request'] = self.type
        self['data'] = {}
        self.validate(**kwargs)
        return

    def validate(self, **kwargs):
        for key in self.ref_data:
            self['data'][key] = kwargs.get(key)

    def json(self):
        return json.dumps(self)


class EmptyMessage(Message):
    pass


class StartMessage(Message):
    type = 'start'


class AuthMessage(Message):
    type = 'login'
    ref_data = {'login', 'password'}


class RegisterUserMessage(Message):
    type = 'register'
    ref_data = {'firstname', 'lastname', 'login', 'password', 'password2', 'age'}


class MakeAppointmentMessage(Message):
    type = 'make_appointment'
    ref_data = {'date', 'time', 'doctor'}


class MessageFactory:

    @staticmethod
    def create_message(type, **kwargs):
        if type == 'start':
            msg = StartMessage(**kwargs)
        elif type == 'login':
            msg = AuthMessage(**kwargs)
        elif type == 'register':
            msg = RegisterUserMessage(**kwargs)
        elif type == 'make_appointment':
            msg = MakeAppointmentMessage(**kwargs)
        else:
            msg = EmptyMessage()
        return msg


class MessageBuilder:
    def __init__(self, type, func_answer=get_from_console):

        msg_factory = MessageFactory()
        self.msg = msg_factory.create_message(type)
        self.iter = self.field_iterator()
        self.ready = False
        self.func_answer = func_answer

    def field_iterator(self):

        for key, value in self.msg['data'].items():
            if not value:
                yield key

    def get_field(self):

        while True:
            try:
                field = next(self.iter)
                return field
            except StopIteration:
                self.ready = True
                break

    def fill_field(self, field, value):
        self.msg['data'][field] = value

    def build(self):

        while not self.ready:
            field = self.get_field()
            if field:
                prompt = 'enter {}'.format(field)
                field_value = self.func_answer(prompt)
                self.fill_field(field, field_value)

        return self.msg
