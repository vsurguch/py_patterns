
class RequestProcessor:
    def __init__(self, data):
        self.data = data

    def make_query(self, data):
        pass

    def add_status_code(self, status_code):
        return {'status_code': status_code, 'data': self.data}

    def action(self, data):
        pass


class StartRequestProcessor(RequestProcessor):
    def action(self, data=None):
        self.data = {'primary_key': 123456}
        response = self.add_status_code(200)
        return response


class LoginRequestProcessor(RequestProcessor):
    def action(self, data):
        login = data['login']
        password = data['password']

#         authenticate
#         store session_key

        self.data = {'role': 'patient'}
        response = self.add_status_code(200)
        return response


class Request:
    _processors = {
        'start': StartRequestProcessor,
        'login': LoginRequestProcessor,
    }

    def __init__(self, request_dict):
        self.request = request_dict['request']
        self.data = request_dict['data']
        request_processor_cls = __class__._processors[self.request]
        self.request_processor = request_processor_cls(self.data)

    def process(self):
        result = self.request_processor.action(self.data)
        return result

