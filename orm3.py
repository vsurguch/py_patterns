

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

    def __init__(self, db_name, verbose=True):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.verbose = verbose

    def execute(self, statement):
        if self.verbose:
            print(statement)
        self.cursor.execute(statement)

    def execute_statement(self, statement):
        self.execute(statement)
        result = self.cursor.fetchall()
        return result

    def get_description(self):
        desc = [field[0] for field in self.cursor.description ]
        return desc

# ------------------------------------------

# add singleton
class MapperRegistry:

    models = {}
    engine = None

    @staticmethod
    def register_model(model):
        __class__.models[model._model_name] = model
        model.engine = __class__.engine
        fields_list = []
        for key, value in model.fields.items():
            fields_list.append('{} {} {}'.format(key, value.datatype, value.params))

        fields_definition = ', '.join(fields_list)
        statement = 'CREATE TABLE IF NOT EXISTS {} ({})'.format(model._model_name, fields_definition)
        __class__.engine.execute_statement(statement)

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
    foreign = False

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
    foreign = True

    def __init__(self, model, field):
        self._reference_model = model
        self._reference_field = field
        self.params = 'REFERENCES {}({})'.format(self._reference_model._model_name, self._reference_field)

    def __set__(self, obj, value):
        if isinstance(value, Model):
            super().__set__(obj, value)


class Query:
    def __init__(self, model):
        self._model = model
        self.fields = self._model.get_fields(with_autoincrement=True)
        self.foreign = self._model.get_foreign_keys(self.fields)

    def make_statement(self):
        statement = 'SELECT * FROM {} '.format(self._model._model_name)
        if len(self.foreign) > 0:
            for foreign in self.foreign:
                ref_model_name = foreign['model']._model_name
                statement += ' LEFT OUTER JOIN {} ON {}.{} = {}.{}'.\
                    format(ref_model_name, self._model._model_name, foreign['field'],
                           ref_model_name, foreign['ref_field'])
        statement += '$condition$'
        return statement

    def query(self, statement):
        results = self._model.engine.execute_statement(statement)
        desc = self._model.engine.get_description()
        return results, desc

    def all(self):
        result = []
        statement = self.make_statement()
        statement = statement.replace('$condition$', '')
        query_results, fields = self.query(statement)
        for res in query_results:
            obj = self._model.obj_from_result(self.fields, fields, res)
            result.append(obj)
        return result

    def _filter(self, field_name, value):
        condition = " WHERE {}.{}=\'{}\' ".format(self._model._model_name, field_name, value)
        statement = self.make_statement()
        statement = statement.replace('$condition$', condition)
        results, fields = self.query(statement)
        return results, fields

    def filter(self, field_name, value):
        query_results, fields = self._filter(field_name, value)
        result = self._model.list_from_result(self.fields, fields, query_results)
        return result

    def first(self, field_name, value):
        results, fields = self._filter(field_name, value)
        if results and len(results) > 0:
            result = self._model.obj_from_result(self.fields, fields, results[0])
            return result
        else:
            return None

    def find_by_id(self, id):
        result = self.first('id', id)
        return result


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
            if self.__class__.fields[key].foreign and (not isinstance(value, Model)):
                model = self.__class__.fields[key]._reference_model
                field = self.__class__.fields[key]._reference_field
                obj = Query(model).first(field, value)
                value = obj
            self.__class__.fields[key].__set__(self, value)

    @classmethod
    def get_fields(cls, with_autoincrement=False):
        if with_autoincrement:
            fields = [key for key in cls.fields.keys()]
        else:
            fields = [key for key in cls.fields.keys() if not cls.fields[key].autoincrement]
        return fields

    @classmethod
    def get_foreign_keys(self, fields):
        foreign_keys = []
        for field in fields:
            if isinstance(self.fields[field], ForeignKeyField):
                foreign = {
                    'model': self.fields[field]._reference_model,
                    'field': field,
                    'ref_field': self.fields[field]._reference_field,
                }
                foreign_keys.append(foreign)
        return foreign_keys

    def get_field_values(self, fields):
        result = {}
        for field in fields:
            if isinstance(self.fields[field], ForeignKeyField):
                obj = self._data[field]
                if obj:
                    value = obj._data[self.fields[field]._reference_field]
                    value = '\'{}\''.format(value)
                else:
                    value = 'NULL'
                result[field] = value
            else:
                result[field] = '\'{}\''.format(self._data[field])
        return result

    # другая реализация предыдущеего метода ()
    def get_values_for_fields(self, fields):
        result = []
        for field in fields:
            if isinstance(self.fields[field], ForeignKeyField):
                obj = self._data[field]
                if obj:
                    value = obj._data[self.fields[field]._reference_field]
                    value = '\'{}\''.format(value)
                else:
                    value = 'NULL'
                result.append(value)
            else:
                result.append('\'{}\''.format(self._data[field]))
        # result = ['\'{}\''.format(self._data[field]) for field in fields]
        return result

    # добавление записи в БД напрямую
    def add(self):
        lastrow = self.__class__.insert(self)
        if lastrow:
            return Query(self.__class__).find_by_id(lastrow)
        else:
            return None

    # составление словаря(поле-значение) из результата полученного с помощью sql-запроса
    @classmethod
    def make_fields_dict(cls, fields, result_fields, values):
        field_l = len(cls.fields)
        start = field_l
        result = dict()
        # print(fields, result_fields, values)
        for n, field in enumerate(fields):
            if isinstance(cls.fields[field], ForeignKeyField):
                foreign_length = len(cls.fields[field]._reference_model.fields)
                to = start + foreign_length
                obj_dict = dict(zip(result_fields[start:to], values[start:to]))
                obj = cls.fields[field]._reference_model(**obj_dict)
                result[field] = obj
                start = to
            else:
                result[field] = values[n]
        return result

    # составление объекта из резульата полученного из БД
    @classmethod
    def obj_from_result(cls, fields, result_fields, result):
        fields_dict = cls.make_fields_dict(fields, result_fields, result)
        # fields_dict = dict(zip(fields, result))
        obj = cls(**fields_dict)
        return obj

    # составление списка объектов
    @classmethod
    def list_from_result(cls, fields, result_fields, query_result):
        result = []
        for res in query_result:
            obj = cls.obj_from_result(fields, result_fields, res)
            result.append(obj)
        return result

    # добавление записи в БД
    @classmethod
    def insert(cls, obj):
        table_name = cls._model_name
        fields = obj.get_fields()
        fields_values = obj.get_field_values(fields)
        fields_str = ', '.join(fields_values.keys())
        values_str = ', '.join(fields_values.values())
        statement = 'INSERT INTO {} ({}) VALUES ({})'.format(table_name, fields_str, values_str)
        cls.engine.execute(statement)
        lastrowid = cls.engine.cursor.lastrowid
        try:
            cls.engine.connection.commit()
            return lastrowid
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
        cls.engine.execute(statement)
        try:
            cls.engine.connection.commit()
        except:
            pass

    @classmethod
    def delete(cls, obj):
        table_name = cls._model_name
        condition = 'id={}'.format(obj.id)
        statement = 'DELETE FROM {} WHERE {}'.format(table_name, condition)
        cls.engine.execute(statement)
        try:
            cls.engine.connection.commit()
        except:
            pass

    def __str__(self):
        return ', '.join(['{}: {}'.format(key, value) for key, value in self._data.items()])


# --------------------------------
# реализация

class Categroy(Model):
    _model_name = 'Category'
    fields = {
        'id': IntField(not_null=True, primary_key=True, autoincrement=True),
        'name': CharField()
    }

class Profession(Model):
    _model_name = 'Profession'
    fields = {
        'id': IntField(not_null=True, primary_key=True, autoincrement=True),
        'name': CharField(),
        'category': ForeignKeyField(Categroy, 'id')
    }

class City(Model):
    _model_name = 'City'
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
        'city': ForeignKeyField(City, 'id'),
        'profession': ForeignKeyField(Profession, 'id')
    }


def main():
    engine = Engine('database.sqlite')

    MapperRegistry.set_engine(engine)
    MapperRegistry.register_model(Categroy)
    MapperRegistry.register_model(Profession)
    MapperRegistry.register_model(City)
    MapperRegistry.register_model(Person)

    UnitOfWork().new_current()

    cat1 = Categroy(name='Top').add()

    prof1 = Profession(name='CEO', category=cat1).add()
    print(prof1)
    city_la= City(name='LA').add()
    city_moscow = City(name='Moscow').add()
    print(city_la)

    person = Person(name='Aleksei', age=30, city=city_la, profession=prof1)
    person.mark_new()

    UnitOfWork().get_current().commit()

    persons = Query(Person).all()
    print(persons)
    print(persons[0])
    print(persons[0].profession)
    print(persons[0].profession.category)
    persons[0].city = city_moscow
    persons[0].mark_changed()

    UnitOfWork().get_current().commit()

    aleksei = Query(Person).filter('name', 'Aleksei')
    if len(aleksei) > 0:
        aleksei = aleksei[0]
        print(aleksei)


    #

    # gen = (print(prof) for prof in res)
    # for _ in gen:
    #     pass
    #
    # res = Person.all()
    # gen = (print(person) for person in res)
    # for _ in gen:
    #     pass
    #

    UnitOfWork().set_current(None)

if __name__ == '__main__':
    main()



# res = execute_statement(MapperRegistry.engine.cursor, 'SELECT * FROM Person')
# res = execute_statement(curs, 'SELECT name FROM sqlite_master WHERE type=\'table\'')
