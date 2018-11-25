# import types

# raw_msg = types.SimpleNamespace(addr=None, length=0, inb=b'', recieved_length=0, full=False, outb=b'')

class raw_msg(object):
    __slots__ = ['addr', 'length', 'recieved_length', 'full', 'inb', 'outb']
    def __init__(self, addr=None, length=0, recieved_length=0, full=False, inb=b'', outb=b''):
        self.addr = addr
        self.length = length
        self.recieved_length = recieved_length
        self.full = full
        self.inb = inb
        self.outb = outb

def process_raw_msg(recv_data, raw_msg):
    if raw_msg.length == 0:
        msg_size = get_msg_size(recv_data[:4])
        raw_msg.length = msg_size
        raw_msg.inb += recv_data[4:]
        raw_msg.recieved_length += len(recv_data)
    else:
        raw_msg.inb += recv_data
        raw_msg.recieved_length += len(recv_data)
    if raw_msg.recieved_length == raw_msg.length:
        raw_msg.full = True

def get_msg_size(msg_header):
    return int.from_bytes(msg_header, byteorder='big')

def set_msg_size(msg_length):
    return int.to_bytes(msg_length+4, byteorder='big', length=4)

def make_message(message):
    bmessage = message.encode('utf-8')
    return set_msg_size(len(bmessage)) + bmessage

def read_message(message):
    return message.decode('utf-8')

