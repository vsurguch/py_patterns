import abc


class AbstractQuery(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def query(self):
        pass


class Query(AbstractQuery):
    def __init__(self, model, condition=''):
        self.model = model
        self.codintion = condition


class All(Query):
    def query(self):
        suffix = self.model.model_name
        return 'SELECT * FROM {}'.format(suffix)


class Filter(Query):
    def query(self):
        suffix = self.model.model_name
        return 'SELECT * FROM {} WHERE {}'.format(suffix, self.codintion)


class Count(Query):
    def query(self):
        suffix = self.model.model_name
        return 'SELECT COUNT({}) FROM {} WHERE {}'.format(self.model.id, suffix, self.codintion)


class Field:
    def __init__(self):
        self.default = None

    def __get__(self, obj, type=None):
        return obj._data[self._name]

    def __set__(self, obj, value):
        print(value)
        obj._data[self._name] = value


class IntField(Field):
    def __init__(self, start_from=0, autoincrement=False):
        super().__init__()
        self.current_value = start_from
        self.autoincrement = autoincrement

    def __set__(self, obj, value):
        if isinstance(value, int):
            if not self.autoincrement:
                super().__set__(obj, value)
            else:
                super().__set__(obj, self.current_value)
                self.current_value += 1
        else:
            pass

class CharField(Field):

    def __init__(self, default='', max_length=256):
        super().__init__()
        self.default = default
        self.max_length = max_length

    def __set__(self, obj, value):
        if isinstance(value, str) and (len(value) < self.max_length):
            super().__set__(obj, value)
        else:
            pass


class Meta(type):
    def __new__(cls, name, bases, dct):
        dct['_data'] = dict.fromkeys(dct.keys())

        for field_name, field in dct.items():
            if field_name[0] != '_':
                field._name = field_name
                if field.default:
                    dct['_data'][field_name] = field.default

        x = super().__new__(cls, name, bases, dct)
        x.model_name = name
        return x


class Model(metaclass=Meta):
    def __new__(cls):
        x = super().__new__(cls)
        if 'id' in cls.__dict__:
            x.id = 0
        return x


class Person(Model):
    id = IntField(autoincrement=True)
    name = CharField(default='no_name')


person = Person()
person2 = Person()
person2.name = 'name2'
person.name = "abracadabra"
print(person.name, person.id)
print(person2.name, person2.id)

query = All(Person).query()
print(query)
query = Filter(Person, 'age < 10').query()
print(query)