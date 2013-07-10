#! /usr/bin/env python

"""
UDP server to handle UDP stream sent by SkyTools' skylog.
"""

import sys
import time

import skytools

from cc.daemon.udp_listener import UdpListener
from cc.daemon.plugins.skylog import SkyLogPlugin

# use fast implementation if available, otherwise fall back to reference one
try:
    import tnetstring as tnetstrings
    tnetstrings.parse = tnetstrings.pop
except ImportError:
    import cc.tnetstrings as tnetstrings


class SkyLog (UdpListener):
    """ UDP server to handle UDP stream sent by skytools' skylog. """

    log = skytools.getLogger ('d:SkyLog')

    def reload (self):
        super(SkyLog, self).reload()

        self.log_format = self.cf.get ('log-format')
        assert self.log_format in ['netstr']
        self.log_parsing_errors = self.cf.getbool ('log-parsing-errors', False)

    def _probe_func (self, cls):
        """ Custom plugin probing function """
        if not issubclass (cls, SkyLogPlugin):
            self.log.debug ("plugin %s is not of supported type", cls.__name__)
            return False
        if self.log_format not in cls.LOG_FORMATS:
            self.log.debug ("plugin %s does not support %r formatted messages", cls.__name__, self.log_format)
            return False
        return True

    def init_plugins (self):
        """ Load suitable plugins and initialise them """
        self.load_plugins (log_fmt = self.log_format)
        for p in self.plugins:
            p.init (self.log_format)

    def parse_json (self, data):
        """ Parse JSON datagram sent by skylog """
        raise NotImplementedError

    def parse_netstr (self, data):
        """ Parse tnetstrings datagram sent by skylog """
        try:
            msg, rest = tnetstrings.parse (data)
            if rest:
                self.log.warning ("netstr parsing leftover: %r", rest)
                self.log.debug ("failed tnetstring: [%i] %r", len(data), data)
            return msg

        except Exception, e:
            if self.log_parsing_errors:
                self.log.warning ("netstr parsing error: %s", e)
                self.log.debug ("failed tnetstring: [%i] %r", len(data), data)
            return None

    def parse_syslog (self, data):
        """ Parse syslog datagram sent by skylog """
        raise NotImplementedError

    def process (self, data):
        start = time.time()
        size = len(data)

        if self.log_format == "netstr":
            msg = self.parse_netstr (data)
        else:
            raise NotImplementedError

        if msg:
            for p in self.plugins:
                try:
                    p.process (msg)
                except Exception, e:
                    self.log.exception ("plugin %s crashed", p.__class__.__name__)
                    self.log.debug ("%s", e)

        # update stats
        taken = time.time() - start
        self.stat_inc ('skylog.count')
        self.stat_inc ('skylog.bytes', size)
        self.stat_inc ('skylog.seconds', taken)

    def work (self):
        self.log.info ("Listening on %s for %s formatted messages", self.listen_addr, self.log_format)
        self.log.info ("Starting IOLoop")
        self.ioloop.start()
        return 1


if __name__ == '__main__':
    s = SkyLog ('skylog', sys.argv[1:])
    s.start()
