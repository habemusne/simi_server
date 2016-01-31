Author: Mark Chen

Date: Jan 30, 2016

Description: Service for managing Human Intelligence Tasks

Usage
====

* Step 1. Prepare your data
    * Put all the image files in the EC2. Specifically, put them in /var/www/html/images/ in 52.24.142.90
    * Make stimuli sequence files. Please make one file for one worker so that you don't write code to process your sequence data in exp.html.
    * After the files are ready, put them in /var/www/html/filesPublic or /var/www/html/stimuli_data.

* Step 2. Run this server program on EC2.
    * In config.conf, customize the global variables. Here are the variable's explanations:
        * allowed_pending_gap: Change this to the maximum allowed time for a worker to finish a HIT. The time should be in second. For example, if you want your worker to finished your HIT in 45 minutes, then change this value to 45 x 60 = 2700
        * stimuli_dir_url: Change this to the url of the directory of your stimuli sequence data. For example, in Amanda's server 52.24.142.90, in the directory /var/www/html/stimuli_data/Jan29/, there are three sample stimuli sequence data files. Then the url of the directory of this stimuli sequence data is http://52.24.142.90/stimuli_data/Jan29/ (You can use your browser to open this link and you will see what I mean).
        * port: the server port that you will be using. If you run this program and you terminate it very soon, then in the next run it will pop up an error "Address already in use". If so, just change the port number in this file and you will be fine
        * check_gap: don't change this
    * You are now ready to run. In the directory, type "python start.py[ENTER]"

* Step 3. Adapt your experiment to link to this server
    * In exp.html,:
        * Add the following code:

			```html
               <script src="/statis/js/EC2_communicator.js" type="text/javascript"></script>
			```
        
        * In the huge javascript codes, Specify variable EC2_IP and EC2_PORT:
       		```javascript
               var EC2_IP = '52.24.142.90';
               var EC2_PORT = '9000';
            ```
            
           The EC2_PORT variable should be consistent with the port you specified in config.conf
        * Initialize a EC2 communicator:

			```javascript
               var EC2_communicator = new EC2Communicator();
               EC2_communicator.init(EC2_IP, EC2_PORT);
            ```
            
        * When the worker loads this page, send a string 'GET=-=' to this server. This server will then return a url which links to an available stimuli sequence file (for example, http://52.24.142.90/stimuli_data/Jan29/test_data1.txt):
        	
            ```javascript
               EC2_communicator.send_command('GET=-=');
               var stimuli_file_url = EC2_communicator.get_response();
            ```
           
           Now you have a stimuli sequence, which means that the worker can start the experiment now. So let the Javascript immediately send another string 'PEND=-=<your stimuli sequence url>' (for example, 'PEND=-=http://52.24.142.90/stimuli_data/Jan29/test_data1.txt'). At this time, the server will mark this stimuli sequence file as "pending":
           
           ```javascript
               EC2_communicator.send_command('PEND=-=' + stimuli_file_url);
           ```
           
        * When the worker finishes the experiment, let the Javascript send another string to this server: "COMPLETE=-=<your stimuli sequence url>". At this moment, the server will mark the stimuli sequence file as "completed". If you are wondering which code block you should change, I would bet the 'on_finish' method in 'start' method at the end of exp.html:
        
        	```javascript
               EC2_communicator.send_command('COMPLETE=-=' + stimuli_file_url);
            ```
           
        * If the worker accidentally drops the experiment, your don't have to do anything. This program will do the work for you. Specifically, the "allowed_pending_gap" variable you configured in step 2.1 marks the time interval for checking failed experiments. If a stimuli sequence file has been marked "pending" for too long, this program will mark it as available so that the next worker can still get it.
