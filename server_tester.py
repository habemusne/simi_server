from server import Server
import test_client
import threading
from time import sleep


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

    # Worker1 waits for 1 second, then clicks on 'Accept HIT'. She finishes
    #   the HIT in 4 seconds, after which she click on "submit HIT" and get done.
    def test_integration_worker1(self):
        worker1_get_client = test_client.Client()
        worker1_accept_client = test_client.Client()
        worker1_complete_client = test_client.Client()

        sleep(1)
        worker1_get_client


server_tester = ServerTester()
# server_tester.test_get_stimuli_urls()
# server_tester.test_GET()
# server_tester.test_PEND()
# server_tester.test_COMPLETE()
server_tester.test_checkfail()
