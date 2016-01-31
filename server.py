"""
Author: Mark Chen
Date: Jan 30, 2016
Description: Service for managing Human Intelligence Tasks

Usage:

Step 1. Prepare your data
    1.1. Put all the image files in the EC2. Specifically, put them in /var/www/html/images/ in
        52.24.142.90
    1.2. Make stimuli sequence files. Please make one file for one worker so that you don't
        write code to process your sequence data in exp.html.
    1.3. After the files are ready, put them in /var/www/html/filesPublic or /var/www/html/stimuli_data.

Step 2. Run this server program on EC2.
    2.1. In config.conf, customize the global variables. Here are the variable's explanations:
        allowed_pending_gap: Change this to the maximum allowed time for a worker to finish a
                HIT. The time should be in second. For example, if you want your worker to
                finished your HIT in 45 minutes, then change this value to 45 x 60 = 2700
        stimuli_dir_url: Change this to the url of the directory of your stimuli sequence data.
                For example, in Amanda's server 52.24.142.90, in the directory
                /var/www/html/stimuli_data/Jan29/, there are three sample stimuli sequence data
                files. Then the url of the directory of this stimuli sequence data is
                http://52.24.142.90/stimuli_data/Jan29/ (You can use your browser to open this
                link and you will see what I mean).
        port: the server port that you will be using. If you run this program and you terminate it
                very soon, then in the next run it will pop up an error "Address already in use".
                If so, just change the port number in this file and you will be fine
        check_gap: don't change this
    2.2. You are now ready to run. In the directory, type "python server.py[ENTER]"

Step 3. Adapt your experiment to link to this server
    3.1. In exp.html, change your code so that:
        1. When the worker loads this page, send a string 'GET=-=' to this server. This server
            will then return a url which links to an available stimuli sequence file (for example,
            http://52.24.142.90/stimuli_data/Jan29/test_data1.txt). Then you have a stimuli sequence,
            which means that the worker can start the experiment now. So let the Javascript immediately
            send another string 'PEND=-=<your stimuli sequence url>' (for example,
            'PEND=-=http://52.24.142.90/stimuli_data/Jan29/test_data1.txt'). At this time, the server
            will mark this stimuli sequence file as "pending".
        2. When the worker finishes the experiment, let the Javascript send another string to this server:
            "COMPLETE=-=<your stimuli sequence url>". At this moment, the server will mark the stimuli
            sequence file as "completed". If you are wondering which code block you should change, I
            would bet the 'on_finish' method in 'start' method at the end of exp.html
        3. If the worker accidentally ddrops the experiment, your don't have to do anything. This
            program will do the work for you. Specifically, the "allowed_pending_gap" variable
            you configured in step 2.1 marks the time interval for checking failed experiments.
            If a stimuli sequence file has been marked "pending" for too long, this program will
            mark it as available so that the next worker can still get it.
"""
import sys
from repeated_timer import RepeatedTimer
from urllib2 import urlopen
import contextlib
from lxml.html import document_fromstring
import datetime
import ConfigParser


class Server:
    def __init__(self):
        self.port = None
        self.check_gap = 1
        self.allowed_pending_gap = 5
        self.sock = None
        self.regular_checker = None
        self.stimuli_dir_url = None
        self.configure()
        self.stimuli_info_dict = self.init_stimuli_info_dict(self.stimuli_dir_url)
        self.regular_checker = RepeatedTimer(self.check_gap, self.check_fail)

    def configure(self):
        config_parser = ConfigParser.ConfigParser(allow_no_value=True)
        config_parser.read('config.conf')
        self.port = config_parser.getint('general', 'port')
        self.stimuli_dir_url = config_parser.get('general', 'stimuli_dir_url')

        # self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.bind(('localhost', self.port))
        # self.sock.listen(5)
        # self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

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
                data = client_socket.recv(4096)
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
