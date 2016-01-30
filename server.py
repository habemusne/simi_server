import socket
import sys
from repeated_timer import RepeatedTimer
from urllib2 import urlopen
import contextlib
from lxml.html import document_fromstring
import datetime
import ConfigParser
import threading
from time import sleep

import test_client


class Server:
    def __init__(self):
        self.port = None
        self.check_gap = 1
        self.allowed_pending_gap = 5
        self.sock = None
        self.regular_checker = None
        self.configure()
        self.stimuli_info_dict = self.init_stimuli_info_dict('http://52.24.142.90/stimuli_data/Jan29/')
        self.regular_checker = RepeatedTimer(self.check_gap, self.check_fail)

    def configure(self):
        config_parser = ConfigParser.ConfigParser(allow_no_value=True)
        config_parser.read('config.conf')
        self.port = config_parser.getint('general', 'port')

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind(('localhost', self.port))
        self.sock.listen(5)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def socket_listen_callback(self, command, option):
        if command == 'GET':
            return self.get_available_stimuli()
        if command == 'PEND':
            self.mark_stimuli_status(option, 'pending')
        if command == 'COMPLETE':
            self.mark_stimuli_status(option, 'completed')

    def get_stimuli_urls(self, stimuli_dir_url):
        """
        Scrapes stimuli sequence file names hosted on the cloud,
        and return a list containing urls of those files
        """
        with contextlib.closing(urlopen(stimuli_dir_url)) as page_source:
            html_content = page_source.read()
        doc = document_fromstring(html_content)
        stimuli_url_elements = doc.xpath('//td/a/@href')
        stimuli_urls = []
        for e in stimuli_url_elements:
            if e.endswith('.txt') or e.endswith('.csv'):
                stimuli_urls.append(stimuli_dir_url + e)
        return stimuli_urls

    def init_stimuli_info_dict(self, stimuli_dir_url):
        stimuli_urls = \
            self.get_stimuli_urls(stimuli_dir_url)
        stimuli_info_dict = dict()
        for url in stimuli_urls:
            stimuli_info_dict[url] = {
                'status': 'waiting',
                'last_update': datetime.datetime.utcnow()
            }
        return stimuli_info_dict

    def get_available_stimuli(self):
        """
        Find one stimuli_url that is marked 'waiting'
        """
        available_stimuli_url = ''
        for url in self.stimuli_info_dict.keys():
            stimuli_info = self.stimuli_info_dict[url]
            if stimuli_info['status'] == 'waiting':
                available_stimuli_url = url
                break
        return available_stimuli_url

    def mark_stimuli_status(self, stimuli_url, status):
        self.stimuli_info_dict[stimuli_url]['status'] = status
        self.stimuli_info_dict[stimuli_url]['last_update'] = datetime.datetime.utcnow()

    def check_fail(self):
        """
        For all stimuli, if the pending time is too long, mark it as 'waiting'
        so that it is availble for the other workers
        """
        time_now = datetime.datetime.utcnow()
        for stimuli_url in self.stimuli_info_dict:
            info = self.stimuli_info_dict[stimuli_url]
            if info['status'] == 'pending' and (info['last_update'] +
                    datetime.timedelta(seconds=self.allowed_pending_gap) <
                    time_now):
                info['status'] = 'waiting'
                info['last_update'] = time_now

    def validate_received_data(self, data):
        if len(data.split('=-=')) != 2:
            return False
        return True

    def run(self):

        while True:
            print 'Server starts. Listening...'
            client_socket, client_address = self.sock.accept()
            print 'Got a connection from ' + str(client_address)
            try:
                # Receive the data in small chunks and retransmit it
                data = client_socket.recv(1024)
                print >> sys.stderr, 'received "%s"' % data
                if not self.validate_received_data(data):
                    print 'Data format not correct. You need to have a command string ' + \
                          'followed by a option string, seperated by a "=-="'
                    continue
                cmd = data.split('=-=')[0]
                opt = data.split('=-=')[1]
                if data:
                    response = self.socket_listen_callback(cmd, opt)
                    print >> sys.stderr, 'sending response'
                    if not response:
                        response = 'success'
                    client_socket.sendall(response)
                else:
                    print >> sys.stderr, 'no more data from', client_address
                    break
            except KeyboardInterrupt:
                print 'KeyboardInterrupt'
            finally:
                client_socket.close()


class ServerTester:
    def __init__(self):
        self.server = Server()

    def test_get_stimuli_urls(self):
        url = 'http://52.24.142.90/stimuli_data/Jan29/'
        result = self.server.get_stimuli_urls(url)
        assert result[0] == 'http://52.24.142.90/stimuli_data/Jan29/test_data1.txt'
        assert result[1] == 'http://52.24.142.90/stimuli_data/Jan29/test_data2.txt'
        assert result[2] == 'http://52.24.142.90/stimuli_data/Jan29/test_data3.txt'

    def test_GET(self):
        client_thread = threading.Thread(target=self.test_GET_client_func)
        client_thread.start()
        self.server.run()

    def test_PEND(self):
        client_thread = threading.Thread(target=self.test_PEND_client_func)
        client_thread.start()
        self.server.run()

    def test_COMPLETE(self):
        client_thread = threading.Thread(target=self.test_COMPLETE_client_func)
        client_thread.start()
        self.server.run()

    def test_checkfail(self):
        stimuli_urls = [key for key in self.server.stimuli_info_dict.keys()]
        self.server.mark_stimuli_status(stimuli_urls[0], 'pending')
        for i in range(0, self.server.allowed_pending_gap + 5):
            sleep(1)
            if i < self.server.allowed_pending_gap:
                assert self.server.stimuli_info_dict[stimuli_urls[0]]['status'] == 'pending'
            else:
                assert self.server.stimuli_info_dict[stimuli_urls[0]]['status'] == 'waiting'

    def test_GET_client_func(self):
        sleep(2)

        client = test_client.Client()
        stimuli_url = client.run('GET=-=')
        assert stimuli_url in self.server.stimuli_info_dict
        assert self.server.stimuli_info_dict[stimuli_url]['status'] == 'waiting'

        print 'Client side is done'

    def test_PEND_client_func(self):
        sleep(2)

        client = test_client.Client()
        stimuli_url = client.run('GET=-=')

        client = test_client.Client()
        client.run('PEND=-=' + stimuli_url)
        assert self.server.stimuli_info_dict[stimuli_url]['status'] == 'pending'

        print 'Client side is done'

    def test_COMPLETE_client_func(self):
        sleep(2)

        client = test_client.Client()
        stimuli_url = client.run('GET=-=')

        client = test_client.Client()
        client.run('PEND=-=' + stimuli_url)
        assert self.server.stimuli_info_dict[stimuli_url]['status'] == 'pending'

        client = test_client.Client()
        client.run('COMPLETE=-=' + stimuli_url)
        assert self.server.stimuli_info_dict[stimuli_url]['status'] == 'completed'

        print 'Client side is done'

    def test_checkfail_client_func(self):
        sleep(2)

        client = test_client.Client()
        stimuli_url = client.run('GET=-=')

        client = test_client.Client()
        client.run('PEND=-=' + stimuli_url)

        for i in range(0, self.server.allowed_pending_gap + 5):
            sleep(1)
            print 'Sleeped ' + str(i) + 'th second.'
            print 'status: ' + self.server.stimuli_info_dict[stimuli_url]['status']
            # if i < self.server.allowed_pending_gap:
            #     assert self.server.stimuli_info_dict[stimuli_url]['status'] == 'pending'
            # else:
            #     assert self.server.stimuli_info_dict[stimuli_url]['status'] == 'waiting'

        print 'Client side is done'

    def test_integration(self):

        worker1_get_client

        worker2_get_client = test_client.Client()
        worker2_accept_client = test_client.Client()
        worker2_complete_client = test_client.Client()

        worker3_get_client = test_client.Client()
        worker3_accept_client = test_client.Client()
        worker3_complete_client = test_client.Client()

        worker4_get_client = test_client.Client()
        worker4_accept_client = test_client.Client()
        worker4_complete_client = test_client.Client()

    # Worker1 waits for 1 second, then clicks on 'Accept HIT'.
    def test_integration_worker1(self):
        worker1_get_client = test_client.Client()
        worker1_accept_client = test_client.Client()
        worker1_complete_client = test_client.Client()

        sleep(1)


server_tester = ServerTester()
# server_tester.test_get_stimuli_urls()
# server_tester.test_GET()
# server_tester.test_PEND()
# server_tester.test_COMPLETE()
server_tester.test_checkfail()

# server = Server()
# server.run()
