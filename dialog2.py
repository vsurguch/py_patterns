
import re

# decorator session_id_required
# def session_id_required(func):
#     def decorated(**kwargs):
#         if not 'session_id' in kwargs:
#             raise KeyError
#         return func(**kwargs)
#
#     return decorated

FIELDS = {
    'age': {'type': 0,
            'fmt': '^[0-9]{1,2}$',
            'exmpl': '33'},
    'phone': {'type': 'str',
              'fmt': '^\+?[0-9]{10,11}$',
              'exmpl': '+79771234567 или 89771234567'},
}


class Validator:
    type = None
    fmt = ''

    def validate(self, value):
        type_ok = True
        fmt_ok = True
        if self.type:
            if not isinstance(int(value), type(self.type)):
                type_ok = False
        if self.fmt:
            if not re.fullmatch(self.fmt, value):
                fmt_ok = False
        if fmt_ok and type_ok:
            return True
        else:
            return False


class AgeValidator(Validator):
    type = FIELDS['age']['type']
    fmt = FIELDS['age']['fmt']


class PhoneValidator(Validator):
    fmt = FIELDS['phone']['fmt']


class ValidatorFactory:
    @staticmethod
    def get_validator(field_type):
        if field_type == 'age':
            return AgeValidator()


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


class EmptyMessage(Message):
    pass


class StartMessage(Message):
    type = 'start'


class AuthMessage(Message):
    type = 'auth'
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
        elif type == 'auth':
            msg = AuthMessage(**kwargs)
        elif type == 'register':
            msg = RegisterUserMessage(**kwargs)
        elif type == 'make_appointment':
            msg = MakeAppointmentMessage(**kwargs)
        else:
            msg = EmptyMessage()
        return msg


class MessageBuilder:
    def __init__(self, type, func_answer=None):

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
                field_value = self.func_answer(field)
                self.fill_field(field, field_value)

        return self.msg


class Dialog:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            return cls._instance
        else:
            return cls._instance

    def __init__(self):
        pass


