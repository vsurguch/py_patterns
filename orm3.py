

import sqlite3
import threading

connection = sqlite3.connect('database.sqlite')
# curs = connection.cursor()

def execute_statement(cursor, statement):
    cursor.execute(statement)
    result = cursor.fetchall()
    return result

# Engine

class Engine:

    def __init__(self, db_name):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()

# ------------------------------------------

# add singleton
class MapperRegistry:

    models = {}
    engine = None

    @staticmethod
    def register_model(model):
        __class__.models[model._model_name] = model
        cursor = __class__.engine.cursor
        model.engine = __class__.engine
        fields_list = []
        for key, value in model.fields.items():
            fields_list.append('{} {} {}'.format(key, value.datatype, value.params))

        fields_definition = ', '.join(fields_list)
        statement = 'CREATE TABLE IF NOT EXISTS {} ({})'.format(model._model_name, fields_definition)
        print(statement)
        execute_statement(cursor, statement)

    @staticmethod
    def get_model(obj):
        return __class__.models[obj._model_name]

    @staticmethod
    def get_model_by_name(name):
        return __class__.models[name]

    @classmethod
    def set_engine(cls, engine):
        cls.engine = engine


class UnitOfWork:

    current = threading.local()

    def __init__(self):
        self.new = []
        self.changed = []
        self.deleted = []

    def register_new(self, obj):
        self.new.append(obj)

    def register_changed(self, obj):
        self.changed.append(obj)

    def register_deleted(self, obj):
        self.deleted.append(obj)

    def commit(self):
        self.insert()
        self.update()
        self.delete()
        self.new = []
        self.changed = []
        self.deleted = []

    def insert(self):
        for obj in self.new:
            MapperRegistry.get_model(obj).insert(obj)

    def update(self):
        for obj in self.changed:
            MapperRegistry.get_model(obj).update(obj)

    def delete(self):
        for obj in self.deleted:
            MapperRegistry.get_model(obj).delete(obj)

    @staticmethod
    def new_current():
        __class__.set_current(UnitOfWork())

    @classmethod
    def set_current(cls, unit_of_work):
        cls.current.unit_of_work = unit_of_work

    @classmethod
    def get_current(cls):
        return cls.current.unit_of_work


class Field:

    _name = ''
    datatype = ''
    params = ''
    default = None
    autoincrement = False

    def __get__(self, obj, type=None):
        return obj._data[self._name]

    def __set__(self, obj, value):
        obj._data[self._name] = value


class IntField(Field):
    datatype = 'INTEGER'
    default = 0

    def __init__(self, reqired=False, autoincrement=False, not_null=False, primary_key=False):
        self.required = reqired
        self.autoincrement = autoincrement
        self.not_null = not_null
        self.params = ''
        if not_null:
            self.params += 'NOT NULL '
        if primary_key:
            self.params += 'PRIMARY KEY '
        if autoincrement:
            self.params += 'AUTOINCREMENT '

    def __set__(self, obj, value):
        # if self.autoincrement:
        #     pass
        # else:
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


class ForeignKeyField(Field):

    def __init__(self, model, field):
        self._refernece_model = model
        self._reference_field = field
        self.params = 'REFERENCES {}({})'.format(self._refernece_model, self._reference_field)


class DomainObject:

    def mark_new(self):
        UnitOfWork.get_current().register_new(self)

    def mark_changed(self):
        UnitOfWork.get_current().register_changed(self)

    def mark_deleted(self):
        UnitOfWork.get_current().register_deleted(self)



class Model(DomainObject):

    _model_name = ''
    fields = {}
    engine = None

    def __new__(cls, *args, **kwargs):
        obj = super().__new__(cls)
        obj.__dict__['_data'] = {}
        for key, value in obj.fields.items():
            value._name = key
            obj._data[key] = value.default
        return obj

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            self.__setattr__(key, value)

    def __getattr__(self, item):
        if item in self._data:
            return self.__class__.fields[item].__get__(self)

    def __setattr__(self, key, value):
        if key in self._data:
            self.__class__.fields[key].__set__(self, value)

    @classmethod
    def obj_from_result(cls, result):
        print(result)
        fields = cls.get_fields(with_autoincrement=True)
        fields_dict = dict(zip(fields, result))
        obj = cls(**fields_dict)
        return obj

    @classmethod
    def filter(cls, field_name, value):
        table_name = cls._model_name
        condition = "{}=\'{}\'".format(field_name, value)
        statement = 'SELECT * FROM {} WHERE {}'.format(table_name, condition)
        cls.engine.cursor.execute(statement)
        results = cls.engine.cursor.fetchall()
        return results

    @classmethod
    def filter_by(cls, field_name, value):
        results = cls.filter(field_name, value)
        return [cls.obj_from_result(result) for result in results]

    @classmethod
    def first(cls, field_name, value):
        results = cls.filter(field_name, value)
        if len(results) > 0:
            return cls.obj_from_result(results[0])

    @classmethod
    def all(cls):
        table_name = cls._model_name
        statement = 'SELECT * FROM {}'.format(table_name)
        cls.engine.cursor.execute(statement)
        results = cls.engine.cursor.fetchall()
        # if results:
        fields = cls.get_fields(with_autoincrement=True)
        objects_list = []
        for result in results:
            fields_dict = dict(zip(fields, result))
            objects_list.append(cls(**fields_dict))
        return objects_list
        # else:
        #     return None

    @classmethod
    def filter_by_id(cls, id):
        table_name = cls._model_name
        condition = "{}=\'{}\'".format('id', id)
        statement = 'SELECT * FROM {} WHERE {}'.format(table_name, condition)
        cls.engine.cursor.execute(statement)
        result = cls.engine.cursor.fetchall()
        if result:
            fields = cls.get_fields(with_autoincrement=True)
            fields_dict = dict(zip(fields, result[0]))
            obj = cls(**fields_dict)
            return obj
        else:
            return None

    @classmethod
    def get_fields(cls, with_autoincrement=False):
        if with_autoincrement:
            result = [key for key in cls.fields.keys()]
        else:
            result = [key for key in cls.fields.keys() if not cls.fields[key].autoincrement]
        return result

    def get_values_for_fields(self, fields):
        result = ['\'{}\''.format(self._data[field]) for field in fields]
        return result

    @classmethod
    def insert(cls, obj):
        table_name = cls._model_name
        fields = obj.get_fields()
        values = obj.get_values_for_fields(fields)
        fields_str = ', '.join(fields)
        values_str = ', '.join(values)
        statement = 'INSERT INTO {} ({}) VALUES ({})'.format(table_name, fields_str, values_str)
        print(statement)
        cls.engine.cursor.execute(statement)
        try:
            cls.engine.connection.commit()
        except:
            pass

    @classmethod
    def update(cls, obj):
        table_name = cls._model_name
        fields = obj.get_fields()
        values = obj.get_values_for_fields(fields)
        field_value = zip(fields, values)
        fields_values = ', '.join(['{}={}'.format(item[0], item[1]) for item in field_value])
        condition = 'id={}'.format(obj.id)
        statement = 'UPDATE {} SET {} WHERE {}'.format(table_name, fields_values, condition)
        print(statement)
        cls.engine.cursor.execute(statement)
        try:
            cls.engine.connection.commit()
        except:
            pass

    @classmethod
    def delete(cls, obj):
        table_name = cls._model_name
        condition = 'id={}'.format(obj.id)
        statement = 'DELETE FROM {} WHERE {}'.format(table_name, condition)
        print(statement)
        cls.engine.cursor.execute(statement)
        try:
            cls.engine.connection.commit()
        except:
            pass

    def __str__(self):
        return ', '.join(['{}: {}'.format(key, value) for key, value in self._data.items()])


class Profession(Model):
    _model_name = 'Profession'
    fields = {
        'id': IntField(not_null=True, primary_key=True, autoincrement=True),
        'name': CharField()
    }


class Person(Model):
    _model_name = 'Person'
    fields = {
        'id': IntField(not_null=True, primary_key=True, autoincrement=True),
        'name': CharField(),
        'age': IntField(),
        'profession': ForeignKeyField('Profession', 'id')
    }


def main():
    engine = Engine('database.sqlite')

    MapperRegistry.set_engine(engine)

    MapperRegistry.register_model(Profession)
    MapperRegistry.register_model(Person)

    res = Person.all()
    for item  in res:
        print(item)

    UnitOfWork().new_current()

    profession1 = Profession(name='Manager')
    profession1.mark_new()
    profession2 = Profession(name='Developer')
    profession2.mark_new()


    UnitOfWork().get_current().commit()
    manager = Profession.first('name', 'Manager')
    developer = Profession.first('name', 'Developer')

    person = Person(name='Aleksei', age=20, profession=manager.id)
    person.mark_new()
    person2 = Person(name='Boris', age=30, profession=developer.id)
    person2.mark_new()

    UnitOfWork().get_current().commit()

    res = Profession.all()
    gen = (print(prof) for prof in res)
    for _ in gen:
        pass

    res = Person.all()
    gen = (print(person) for person in res)
    for _ in gen:
        pass

    UnitOfWork().set_current(None)

if __name__ == '__main__':
    main()

# person = Person(name='Aleksei', age=10)
# person.mark_new()
# person2 = Person(name='Boris', age=11)
# person2.mark_new()
# person3 = Person(name='Cynthia', age=12)
# person3.mark_new()
# person4 = Person(name='David', age=13)
# person4.mark_new()
# person5 = Person(name='Eva', age=13)
# person5.mark_new()

# person6.name = 'Dmitrii'
# person4.mark_changed()
#
# person5.mark_deleted()
#




# person = Person.filter_by_id(1)
# person.name = 'Martin'
# Person.update(person)
#
# person = Person.filter_by_id(2)
# Person.delete(person)


# res = execute_statement(MapperRegistry.engine.cursor, 'SELECT * FROM Person')
# res = execute_statement(curs, 'SELECT name FROM sqlite_master WHERE type=\'table\'')
