var CONFIG = { debug: false
             , port: 8777
             , nick: "#"   // set in onConnect
             , id: 234    // set in onConnect
             , last_message_time: 1
             , focus: true //event listeners bound in onConnect
             , unread: 0 //updated in the message-processing loop
             , dir: "/chat" // set in onConnect
             };

var nicks = [];
// -------------------------------------------------------------

//updates the users link to reflect the number of active users
function updateUsersLink ( ) {
  var t = nicks.length.toString() + " user";
  if (nicks.length != 1) t += "s";
  $("#usersLink").text(t);
}

//used to keep the most recent messages visible
function scrollDown () {
  var objDiv = document.getElementById("log");
  objDiv.scrollTop = objDiv.scrollHeight;
}

// utility functions

util = {
  urlRE: /https?:\/\/([-\w\.]+)+(:\d+)?(\/([^\s]*(\?\S+)?)?)?/g, 

  //  html sanitizer 
  toStaticHTML: function(inputHtml) {
    inputHtml = inputHtml.toString();
    return inputHtml.replace(/&/g, "&amp;")
                    .replace(/</g, "&lt;")
                    .replace(/>/g, "&gt;");
  }, 

  //pads n with zeros on the left,
  //digits is minimum length of output
  //zeroPad(3, 5); returns "005"
  //zeroPad(2, 500); returns "500"
  zeroPad: function (digits, n) {
    n = n.toString();
    while (n.length < digits) 
      n = '0' + n;
    return n;
  },

  //it is almost 8 o'clock PM here
  //timeString(new Date); returns "19:49"
  timeString: function (date) {
    var minutes = date.getMinutes().toString();
    var hours = date.getHours().toString();
    return this.zeroPad(2, hours) + ":" + this.zeroPad(2, minutes);
  },

  //does the argument only contain whitespace?
  isBlank: function(text) {
    var blank = /^\s*$/;
    return (text.match(blank) !== null);
  }
};

//inserts an event into the stream for display
//the event may be a msg, join or part type
//from is the user, text is the body and time is the timestamp, defaulting to now
//_class is a css class to apply to the message, usefull for system events
function addMessage (from, text, time, _class) {
  if (text === null)
    return;
  
  console.log(time)
  if (time == null) {
    // if the time is null or undefined, use the current time.
    time = new Date();
  } else if ((time instanceof Date) === false) {
    // if it's a timestamp, interpret it
    time = new Date(time * 1000);
  }

  //every message you see is actually a table with 3 cols:
  //  the time,
  //  the person who caused the event,
  //  and the content
  var messageElement = $(document.createElement("div"));

  messageElement.addClass("message");

  // If the current user said this, add a special css class
  var nick_re = new RegExp(USER_NAME);
  if (nick_re.exec(text)) 
      messageElement.addClass("personal");
  if (USER_NAME == from ) 
      messageElement.addClass("self");
  if (_class) 
      messageElement.addClass(_class);

  // sanitize
  text = util.toStaticHTML(text);

  // replace URLs with links
  text = text.replace(util.urlRE, '<a target="_blank" href="$&">$&</a>');

  var content = '<div class="meta">'
              + '  <em class="nick">' + util.toStaticHTML(from) + '</em>'
              + '  <date>' + util.timeString(time) + '</date>'
              + '</div>'
              + '<p class="msg-text">' + text  + '</p>'
              ;
  messageElement.html(content);

  $(messageElement).appendTo( $("#log") )
      .animate({ backgroundColor: "#FCFCD8" },1).delay(1000).animate({ backgroundColor: "#EFEAEA" }, 1500);

  //always view the most recent message when it is added
  scrollDown();
}




$(document).ready(function() {
    
    $("#entry").keypress(function (e) {
      if (e.keyCode != 13 /* Return */) return;
      var entry = $("#entry");
      var text = entry.val();
      if (!util.isBlank(text)) send({"msg":text, "room":REPO, "nick":USER_NAME} );
      entry.val(""); // clear the entry field.
    });

    onopen = function() {
      send( {"nick":USER_NAME, "room":REPO, "type":"join" });
      //userJoin(message.nick, message.timestamp);
    };
    onmessage = function (msg) {
        
        if ( msg.messages){
          messages = msg.messages.reverse();
          for (var i = messages.length - 1; i >= 0; i--) {
            var ms = messages[i];
            addMessage(ms.nick, ms.text || "", ms.timestamp, ms.type);
          };
        } else {
            if ( msg.type == "who"){
              nicks = msg.who;
              updateUsersLink()
              msg.msg = "connected users: " + msg.who.join(" ");
            }
            addMessage(msg.nick, msg.msg, msg.timestamp, msg.type);
        }
    };
    onclose = function(message) {
        //userPart(message.nick, message.timestamp);
    };
    ws = new io.Socket(window.location.hostname, {
            port:CONFIG.port,
            resource:"socket.io/",
            transports:['websocket', 'flashsocket','xhr-multipart', 'xhr-polling']
        }
    );
    ws.on('message', onmessage);
    ws.on('connect', onopen);
    ws.on('disconnect', onclose);
    ws.connect();

    //submit a new message to the server
    function send(msg) {
      ws.send( msg );
    }
    // remove fixtures
    $("#log table").remove();
    
})