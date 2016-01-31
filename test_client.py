import socket
import sys
import ConfigParser


class Client:
    def __init__(self):
        self.port = None
        self.configure()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('localhost', self.port))

    def configure(self):
        config_parser = ConfigParser.ConfigParser(allow_no_value=True)
        config_parser.read('config.conf')
        self.port = config_parser.getint('general', 'port')

    def run(self, message):
        try:
            self.sock.sendall(message)
            data = self.sock.recv(4096)
            print >>sys.stderr, 'received "%s"' % data
        finally:
            print >>sys.stderr, 'closing socket'
            self.sock.close()
        return data
