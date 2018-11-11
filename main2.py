from dialog2 import MessageFactory, MessageBuilder, ValidatorFactory, Dialog


# message factroy

msg_factory = MessageFactory()
msg_start = msg_factory.create_message('start')
msg_auth = msg_factory.create_message('auth', login='login', password='password')
msg_register = msg_factory.create_message('register', firstname = 'name')

print(msg_start)
print(msg_auth)
print(msg_register)

# MessageBuilder

def get_from_console(field):
    ans = input('введите <{}>: '.format(field))
    return ans

message_builder = MessageBuilder('make_appointment', func_answer=get_from_console)
msg = message_builder.build()
print(msg)


# validator factory

val_fact = ValidatorFactory()
age_validator = val_fact.get_validator('age')
res = age_validator.validate('77')
print('validation: ', res)


# singleton

d = Dialog()
d1 = Dialog()

print(d)
print(d1)