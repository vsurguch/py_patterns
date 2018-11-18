import sqlite3
import abc

# Engine

class Engine:

    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def register_model(self, model):
        Query(model).register(self)

    def execute_query(self, query):
        print(query)
        return self.cursor.execute(query).fetchall()

    def commit(self, query):
        print(query)
        self.cursor.execute(query)
        self.conn.commit()

# Query

class AbstractQuery(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def query(self, q):
        pass

    @abc.abstractmethod
    def commit(self, q):
        pass


class ObjQuery(AbstractQuery):

    def __init__(self, obj):
        self.model = obj.__class__
        self.obj = obj

    def commit(self, query):
        if self.model._engine:
            self.model._engine.commit(query)

    def query(self, q):
        pass

    def save(self):
        columns_list = ','.join(self.obj._data.keys())
        values_list = ','.join(['\'{}\''.format(str(x)) for x in self.obj._data.values()])

        query = 'INSERT INTO {} ({}) VALUES ({})'.format(self.model._model_name, columns_list, values_list)
        self.commit(query)


class Query(AbstractQuery):

    def __init__(self, model):
        self.model = model

    def query(self, q):
        return self.model._engine.execute_query(q)

    def commit(self, q):
        if self.model._engine:
            self.model._engine.commit(q)

    def register(self, engine):
        self.model._engine = engine
        query = 'CREATE TABLE IF NOT EXISTS {table_name} ('.format(table_name=self.model._model_name)
        for field_name, field in self.model.__dict__.items():
            if field_name[0] != '_':
                suff = '{} {}, '.format(field_name, field.datatype)
                query += suff

        query = query[:-2]
        query += ');'
        self.commit(query)

    def all(self):
        q = 'SELECT * FROM {};'.format(self.model._model_name)
        result = self.query(q)
        return result

    def first(self):
        pass

    def filter(self):
        pass

    def count(self):
        pass


# Field

class Field:

    _name = ''
    default = None

    def __get__(self, obj, type=None):
        return obj._data[self._name]

    def __set__(self, obj, value):
        print(value)
        obj._data[self._name] = value


class IntField(Field):

    datatype = 'INT'
    default = 0

    def __init__(self, reqired=False):
        self.required = reqired

    def __set__(self, obj, value):
        if isinstance(value, int):
            super().__set__(obj, value)
        else:
            pass


class CharField(Field):

    datatype = 'VARCHAR'

    def __init__(self, default='', max_length=256, required=False):
        super().__init__()
        self.default = default
        self.max_length = max_length
        self.required = required

    def __set__(self, obj, value):
        if isinstance(value, str) and (len(value) < self.max_length):
            super().__set__(obj, value)
        else:
            pass

# Model

class Model:

    _engine = None
    _model_name = ''

    def __new__(cls, **kwargs):

        obj = super().__new__(cls)
        obj.__dict__['_data'] = {}
        for key, value in cls.__dict__.items():
            if key[0] != '_':
                value._name = key
                obj._data[key] = value.default
        return obj

    def __init__(self, **kwargs):

        for key, value in kwargs.items():
            if key in self._data:
                self._data[key] = value

    def __getattr__(self, item):

        if item in self._data:
            # пока такой доступ к полям через потомок класса Field, потому что думаю добавить на уровне доступа к полям
            # дополнительный функционал
            return self.__class__.__dict__[item].__get__(self)
        else:
            raise KeyError

    def __setattr__(self, key, value):

        if key in self._data:
            # пока такой доступ к полям через потомок класса Field, потому что думаю добавить на уровне доступа к полям
            # дополнительный функционал
            self.__class__.__dict__[key].__set__(self, value)
        else:
            raise KeyError

    def save(self):
        ObjQuery(self).save()







