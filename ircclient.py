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
        self.handlers = {
                'PING': self.handle_ping,
                '001': self.handle_001,
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
                if irc_message.command in self.handlers:
                    self.handlers[irc_message.command](irc_message)
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

    def handle_001(self, message):
        for channel in settings.channels.split(','):
            self.buffer += 'JOIN %s\r\n' % channel
