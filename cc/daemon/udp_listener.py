#! /usr/bin/env python

"""
UDP server to handle generic UDP messages.
"""

import errno
import functools
import socket
import sys
import time

import skytools
from zmq.eventloop.ioloop import IOLoop, PeriodicCallback

from cc.daemon import CCDaemon

RECV_BUFSIZE = 8192 # MAX_MESSAGE_SIZE


class UdpListener (CCDaemon):
    """ UDP server to handle UDP stream. """

    log = skytools.getLogger ('d:UdpListener')

    def reload (self):
        super(UdpListener, self).reload()

        self.listen_host = self.cf.get ('listen-host')
        self.listen_port = self.cf.getint ('listen-port')
        self.stats_period = self.cf.getint ('stats-period', 30)

    def startup (self):
        super(UdpListener, self).startup()

        # plugins should be ready before we start receiving udp stream
        self.init_plugins()

        self.listen_addr = (self.listen_host, self.listen_port)
        self.sock = socket.socket (socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking (0)
        try:
            self.sock.bind (self.listen_addr)
        except Exception, e:
            self.log.exception ("failed to bind to %s - %s", self.listen_addr, e)
            raise

        self.ioloop = IOLoop.instance()
        callback = functools.partial (self.handle_udp, self.sock)
        self.ioloop.add_handler (self.sock.fileno(), callback, self.ioloop.READ)

        self.timer_stats = PeriodicCallback (self.send_stats, self.stats_period * 1000, self.ioloop)
        self.timer_stats.start()

    def find_plugins (self, mod_name, probe_func = None):
        """ Overridden to use our custom probing function """
        return super(UdpListener, self).find_plugins (mod_name, self._probe_func)

    def _probe_func (self, cls):
        """ Custom plugin probing function """
        raise NotImplementedError

    def init_plugins (self):
        """ Load suitable plugins and initialise them """
        self.load_plugins()
        for p in self.plugins:
            p.init()

    def handle_udp (self, sock, fd, events):
        try:
            while True:
                data = sock.recv (RECV_BUFSIZE)
                self.process (data)
        except socket.error, e:
            if e.errno != errno.EAGAIN:
                self.log.error ("failed receiving data: %s", e)
        except Exception, e:
            self.log.exception ("handler crashed: %s", e)

    def process (self, data):
        start = time.time()
        size = len(data)

        if data:
            for p in self.plugins:
                try:
                    p.process (data)
                except Exception, e:
                    self.log.exception ("plugin %s crashed", p.__class__.__name__)
                    self.log.debug ("%s", e)

        # update stats
        taken = time.time() - start
        self.stat_inc ('udp_listener.count')
        self.stat_inc ('udp_listener.bytes', size)
        self.stat_inc ('udp_listener.seconds', taken)

    def work (self):
        self.log.info ("Listening on %s", self.listen_addr)
        self.log.info ("Starting IOLoop")
        self.ioloop.start()
        return 1

    def stop (self):
        """ Called from signal handler """
        super(UdpListener, self).stop()
        self.log.info ("stopping")
        self.ioloop.stop()
        for p in self.plugins:
            self.log.debug ("stopping %s", p.__class__.__name__)
            p.stop()


if __name__ == '__main__':
    s = UdpListener ('udp_listener', sys.argv[1:])
    s.start()
