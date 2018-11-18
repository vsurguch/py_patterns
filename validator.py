from re import fullmatch

FIELDS = {
    'age': {'type': 0,
            'fmt': '^[0-9]{1,2}$',
            'exmpl': '33'},
    'phone': {'type': 'str',
              'fmt':  '^\+?[0-9]{10,11}$',
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
            if not fullmatch(self.fmt, value):
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