
import abc
from utils.message_ import Message

class ProcessorComponent(metaclass=abc.ABCMeta):
    @abc.abstractstaticmethod
    def do(request_id, request_data, final_data):
        pass


class GetDate(ProcessorComponent):
    @staticmethod
    def do(request_id, request_data, final_data):
        resp = {}
        resp['required_data'] = ['Date']
        final_data['Date'] = ''
        resp['result'] = 'Enter desired date'
        return resp


class GetDoctor(ProcessorComponent):
    @staticmethod
    def do(request_id, request_data, final_data):
        resp = {}
        resp['required_data'] = ['Doctor']
        final_data['Doctor'] = ''
        resp['result'] = 'Enter doctor\'s name'
        return resp


class MakeAppointment(ProcessorComponent):
    @staticmethod
    def do(request_id, request_data, final_data):
        resp = {}
        resp['status_code'] = 200
        resp['result'] = 'Apointment details: {}'.\
            format(' '.join(['{}: {}'.format(key, value) for key, value in final_data.items()]))
        return resp


class GetAppointmentID(ProcessorComponent):
    pass


class Start(ProcessorComponent):

    @staticmethod
    def do(request_id, request_data, final_data):
        resp = {}
        resp['primary_key'] = '123456'
        resp['status_code'] = 200
        resp['result'] = 'Communication successfully started.'
        return resp


class Auth(ProcessorComponent):

    @staticmethod
    def do(request_id, request_data, final_data):
        resp = {}
        username = request_data.get('username')
        password = request_data.get('password')
        if (username in USERS) and (USERS[username] == password):
            resp['status_code'] = 200
            resp['result'] = 'You are autherized!'
        else:
            resp['status_code'] = 300
            resp['result'] = 'You are not autherized :('
        return resp


class ReturnActions(ProcessorComponent):

    @staticmethod
    def do(request_id, request_data, final_data):
        actions = ['make_appointment', 'change_appointment', 'delete_appointment']
        resp = {'status_code': 200, 'actions': actions}
        resp['result'] = 'Available actions: {}'.format(' '.join(actions))
        return resp


class Generic(ProcessorComponent):
    @staticmethod
    def do(request_id, request_data, final_data):
        resp = {'status_code': 200}
        return resp


class Processor:

    def __init__(self, request_id, request_data, components):
        self.components = components
        self.steps = len(components)
        self.request_data = request_data
        self.request_id = request_id
        self.component_iterator = self.get_next_component()
        self.final_data = {}
        self.processed = False

    def get_next_component(self):
        for i, component in enumerate(self.components):
            yield i, component

    def fill_data(self, data):
        for key, value in data.items():
            if key in self.final_data:
                self.final_data[key] = value

    def process_next(self):

        i, component = next(self.component_iterator)
        resp = component.do(self.request_id, self.request_data, self.final_data)

        if i == self.steps - 1:
            self.processed = True

        return resp


class ProcessorBuilder:

    _components = {
        'start': [Start],
        'login': [Auth],
        'get_actions': [ReturnActions],
        'generic': [Generic],
        'answer': [Generic],
        'make_appointment': [GetDate, GetDoctor, MakeAppointment],
        'change_appointment': [GetAppointmentID, GetDate, GetDoctor],
        'delete_appointment': [GetAppointmentID]
    }

    @staticmethod
    def build(msg):
        request_type = msg.request_type
        request_id = msg.request_id
        request_data = msg.data
        processor = Processor(request_id, request_data, components=ProcessorBuilder._components[request_type])
        return processor


USERS = {
    'admin': '123',
    'guest': '123',
}


# Mediator (singleton)

class Dispatcher:

    _instance = None
    _counter = 1
    _requests_in_progress = {}

    def __new__(cls, *args, **kwargs):

        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):

        self.processor_builder = ProcessorBuilder
        self._observers = {}


    def new_request(self, msg):

        request_id = msg.request_id
        request_type = msg.request_type
        request_data = msg.data

        # print('request', request_id, request_type)
        # print(Dispatcher._requests_in_progress)

        if not request_id: #and request_id not in self.requests_in_progress:
            processor = self.processor_builder.build(msg)
            request_id = self._counter
            Dispatcher._requests_in_progress[request_id] = processor
            resp_body = processor.process_next()
            self._counter += 1
        else:
            processor = Dispatcher._requests_in_progress[request_id]
            processor.fill_data(request_data)
            resp_body = processor.process_next()

        if processor.processed:
            if request_type in self._observers:
                self.notify(request_type, processor.final_data)
            del Dispatcher._requests_in_progress[request_id]
            request_id = 0

        resp = Message(msg.session_id, request_type, request_id, resp_body)

        return resp


    def attach(self, observer, action):
        if action in self._observers:
            self._observers[action].append(observer)
        else:
            self._observers[action] = [observer]

    def notify(self, action, data):
        print('notify')
        for observer in self._observers[action]:
            observer.notify(data)

    def process_request(self, request_id):

        pass

    def response(self, request_id):

        pass