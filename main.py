#!/usr/bin/env python
from ircclient import IRCClient
import settings, asyncore

if __name__ == '__main__':
    client = IRCClient(settings.hostname, settings.port)
    asyncore.loop()

