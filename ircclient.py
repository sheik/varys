import asyncore, socket, settings

class IRCMessage:
    def __init__(self, message):
        self.message = message = message.replace('\r\n','')
        self.prefix = ''
        self.parameters = []

        pfx_end = -1

        # build prefix
        if message.startswith(':'):
            pfx_end = message.find(' ')
            self.prefix = message[1:pfx_end]

        # get trailing portion
        trail_start = message.find(' :')
        if trail_start >= 0:
            trailing = message[trail_start+2:]
        else:
            trail_start = len(message)

        # build command and parameters
        cmd_par = message[pfx_end+1:trail_start].split(' ')
        self.command = cmd_par[0]

        # populate parameters if they exist
        if len(cmd_par) > 1:
           self.parameters = cmd_par[1:]

        # If trailing exists, append to parameters
        if 'trailing' in locals():
            self.parameters.append(trailing)

class IRCClient(asyncore.dispatcher):
    def __init__(self, host, port):
        # build function table
        self.irc_handlers = {
                'PING': self.handle_ping,
                'PRIVMSG': self.handle_privmsg,
                '001': self.handle_001,
                }

        self.bot_handlers = {
                'credits': self.bot_credits,
                'md5': self.bot_md5,
                }

        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host,port))
        self.buffer = ''

    def handle_connect(self):
        print 'Connected!'
        self.buffer = 'USER %s %s %s :%s\r\n' % (settings.nick, settings.nick, settings.nick, settings.nick)
        self.buffer += 'NICK %s\r\n' % settings.nick

    def handle_close(self):
        self.close()

    def handle_read(self):
        for line in self.recv(1024).split("\r\n"):
            if line != '':
                irc_message = IRCMessage(line)
                print line
                if irc_message.command in self.irc_handlers:
                    self.irc_handlers[irc_message.command](irc_message)
                else:
                    self.handle_unknown(irc_message)

    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    # IRC command handlers
    def handle_unknown(self, message):
        print "unknown command %s" % message.command

    def handle_ping(self, message):
        print 'PONG %s' % ' '.join(message.parameters)
        self.buffer += 'PONG %s\r\n' % ' '.join(message.parameters)

    def handle_privmsg(self, message):
        channel = message.parameters[0]
        privmsg = message.parameters[1]
        print "<%s> %s" % (message.prefix, message.parameters[1])

        # URL catching
        if privmsg.find('http://') >= 0:
            self.bot_handle_url(message)

        # bot command processing
        if privmsg.startswith(settings.command_char):
            parts = privmsg.split(' ')
            command = parts[0][1:]
            args = parts[1:] if len(parts) > 1 else []
            if command in self.bot_handlers:
                self.bot_handlers[command](message, args)

    def handle_001(self, message):
        for channel in settings.channels.split(','):
            self.buffer += 'JOIN %s\r\n' % channel

    def bot_credits(self, message, args):
        channel = message.parameters[0]
        self.buffer += 'PRIVMSG %s :I\'m a real spider! I don\'t have credits!\r\n' % channel

    def bot_md5(self, message, args):
        from hashlib import md5
        channel = message.parameters[0]
        self.buffer += 'PRIVMSG %s :%s\r\n' % (channel, md5(' '.join(args)).hexdigest())

    def bot_handle_url(self, message):
        from re import findall 
        channel = message.parameters[0]
        privmsg = message.parameters[1]
        urls = findall("http://[^ ]+", privmsg)
        for url in urls:
            new_url = self.bitly(url)
            if new_url != None:
                self.buffer += 'PRIVMSG %s :%s\r\n' % (channel, new_url)

    def bitly(self, long_url):
        from urllib import urlencode
        from httplib import HTTPConnection
        from json import loads

        params = urlencode({
            'login': settings.bitly_api_login,
            'apiKey': settings.bitly_api_key,
            'longUrl': long_url
            })

        conn = HTTPConnection(settings.bitly_api_host)
        conn.request("GET", settings.bitly_api_path + params)
        data = loads(conn.getresponse().read())

        if data['status_code'] == 200:
            return data['data']['url']
        else:
            return None 

