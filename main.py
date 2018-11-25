
from client.client_dialog import *

dialog = Dialog()
dialog.run()




# class Person(Model):
#
#     _model_name = 'Person'
#
#     id = IntField()
#     name = CharField(default='name')
#
#
# engine = Engine('test.db')
# engine.register_model(Person)
#
# person = Person(id=4, name='Vladimir')
# person.save()
#
# query = Query(Person).all()
# print(query)
