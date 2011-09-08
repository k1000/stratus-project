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

//handles another person joining chat
function userJoin(nick, timestamp) {
  //put it in the stream
  addMessage(nick, "joined", timestamp, "join");
  //if we already know about this user, ignore it
  for (var i = 0; i < nicks.length; i++)
    if (nicks[i] == nick) return;
  //otherwise, add the user to the list
  nicks.push(nick);
  //update the UI
  updateUsersLink();
}

//handles someone leaving
function userPart(nick, timestamp) {
  //put it in the stream
  addMessage(nick, "left", timestamp, "part");
  //remove the user from the list
  for (var i = 0; i < nicks.length; i++) {
    if (nicks[i] == nick) {
      nicks.splice(i,1)
      break;
    }
  }
  //update the UI
  updateUsersLink();
}

//used to keep the most recent messages visible
function scrollDown () {
  //window.scrollBy(0, 100000000000000000);
  var objDiv = document.getElementById("log");
  objDiv.scrollBottom = objDiv.scrollHeight;
  objDiv.focus();
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

  if (time == null) {
    // if the time is null or undefined, use the current time.
    time = new Date();
  } else if ((time instanceof Date) === false) {
    // if it's a timestamp, interpret it
    time = new Date(time);
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

  //the log is the stream that we view
  $("#log").append(messageElement);

  //always view the most recent message when it is added
  scrollDown();
}

//add a list of present chat members to the stream
function outputUsers () {
  var nick_string = nicks.length > 0 ? nicks.join(", ") : "(none)";
  addMessage("users:", nick_string, new Date(), "info");
  return false;
}

//get a list of the users presently in the room, and add it to the stream
function who () {
  jQuery.get(CONFIG.dir +"/who", {room:REPO}, function (data, status) {
    if (status != "success") return;
    nicks = data.nicks;
    outputUsers();
  }, "json");
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
          for (var i = msg.messages.length - 1; i >= 0; i--) {
            var ms = msg.messages[i];
            addMessage(ms.nick, ms.msg || "", ms.timestamp, ms.type);
          };
        } else {
          if ( msg ){
            addMessage(msg.nick, msg.msg, msg.timestamp, msg.type);
          }
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