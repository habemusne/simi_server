import sys
from autobahn.twisted.websocket import WebSocketServerProtocol, \
    WebSocketServerFactory
import ConfigParser
from server import Server

server = Server()

class MyServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print("Client connecting: {0}".format(request.peer))

    def onOpen(self):
        print("WebSocket connection open.")

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
        else:
            message = payload.decode('utf8')
            print("Text message received: {0}".format(message))
            if not server.validate_received_data(message):
                print 'Data format not correct. You need to have a command string ' + \
                      'followed by a option string, seperated by a "=-="'
                return
            cmd = message.split('=-=')[0]
            opt = message.split('=-=')[1]
            response = self.socket_listen_callback(cmd, opt)
            self.sendMessage(response, isBinary)

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))


if __name__ == '__main__':
    from twisted.python import log
    from twisted.internet import reactor

    config_parser = ConfigParser.ConfigParser(allow_no_value=True)
    config_parser.read('config.conf')
    port = config_parser.getint('general', 'port')
    log.startLogging(sys.stdout)

    factory = WebSocketServerFactory(u"ws://127.0.0.1:" + str(port), debug=False)
    factory.protocol = MyServerProtocol
    # factory.setProtocolOptions(maxConnections=2)

    try:
        reactor.listenTCP(port, factory)
        reactor.run()
    finally:
        pass
