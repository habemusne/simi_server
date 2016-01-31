
var EC2Communicator = function(){
   var socket = null;
   var isopen = false;
   var server_response = null;
   this.init = function(ec2_ip, ec2_port) {
      socket = new WebSocket("ws://" + ec2_ip + ":" + ec2_port);
      socket.binaryType = "arraybuffer";
      socket.onopen = function() {
         console.log("Connected!");
         isopen = true;
      };
      socket.onmessage = function(e) {
         if (typeof e.data == "string") {
            console.log("Text message received: " + e.data);
            server_response = e.data;
         } else {
            var arr = new Uint8Array(e.data);
            var hex = '';
            for (var i = 0; i < arr.length; i++) {
               hex += ('00' + arr[i].toString(16)).substr(-2);
            }
            console.log("Binary message received: " + hex);
         }
      };
      socket.onclose = function(e) {
         console.log("Connection closed.");
         socket = null;
         isopen = false;
      };
   };
   this.send_command = function(command) {
      if (isopen) {
         socket.send(command);
         console.log("Text message sent.");               
      } else {
         console.log("Connection not opened.")
      }
   };
   this.get_response = function(){
      return server_response;
   }
};
