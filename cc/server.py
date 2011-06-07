#! /usr/bin/env python

"""Command-and-Control server.

client <-> ccserver|handler <-> handlerproc


Config::
    [ccserver]
    logfile = ~/log/%(job_name)s.log
    pidfile = ~/pid/%(job_name)s.pid

    [routes]
    req.confdb = confdb
    req.infodb = infodb
    pub.info = infofile

    [confdb]
    plugin = cc.Proxy
    remote-xreq-cc = tcp://127.0.0.1

    [infodb]
    plugin = cc.DBQuery
    db = host=127.0.0.1 dbname=infodb

    [infofile]
    remote-xreq-cc = tcp://127.0.0.1
"""


import sys, time, json
import zmq, zmq.eventloop

import skytools

from zmq.eventloop.ioloop import PeriodicCallback

from cc.message import CCMessage
from cc.stream import CCStream
from cc.handlers import cc_handler_lookup

class CCServer(skytools.BaseScript):

    def startup(self):
        super(CCServer, self).startup()

        self.zctx = zmq.Context()
        self.ioloop = zmq.eventloop.IOLoop.instance()

        # initialize local listen socket
        s = self.zctx.socket(zmq.XREP)
        s.bind(self.cf.get('cc-socket'))
        s.setsockopt(zmq.LINGER, 500)
        self.local = CCStream(s, self.ioloop)
        self.local.on_recv(self.handle_cc_recv)

        self.handlers = {}
        self.routes = {}
        rcf = skytools.Config('routes', self.cf.filename, ignore_defs = True)
        for r, hname in rcf.cf.items('routes'):
            if hname in self.handlers:
                h = self.handlers[hname]
            else:
                self.log.info('New handler: %s/%s', r, hname)
                hcf = self.cf.clone(hname)
                htype = hcf.get('plugin')
                cls = cc_handler_lookup(htype)
                h = cls(hname, hcf, self)
                self.handlers[hname] = h
            self.add_handler(r, h)

        self.stimer = PeriodicCallback(self.send_stats, 5*1000, self.ioloop)
        self.stimer.start()

    def add_handler(self, rname, handler):
        """Add route to handler"""

        r = tuple(rname.split('.'))
        self.log.info('add_handler: %s -> %s', repr(r), handler.hname)
        rhandlers = self.routes.setdefault(r, [])
        rhandlers.append(handler)

    def handle_cc_recv(self, zmsg):
        """Got message from client, pick handler."""

        try:
            cmsg = CCMessage(zmsg)
            dst = cmsg.get_dest()
            route = tuple(dst.split('.'))

            # find and run all handlers that match
            cnt = 0
            for n in range(1, 1 + len(route)):
                p = route[ : n]
                for h in self.routes.get(p, []):
                    self.log.debug('handler=%s', h.hname)
                    h.handle_msg(cmsg)
                    cnt += 1
            if cnt == 0:
                self.log.warning('dropping msg, no route: %s', repr(zmsg))

            # update stats
            self.stat_increase('count')
            self.stat_increase('bytes', cmsg.get_size())
        except Exception, d:
            self.log.exception('handle_cc_recv crashed, dropping msg: %s', repr(zmsg))

    def work(self):
        """Default work loop simply runs ioloop."""
        self.log.info('Starting ioloop')
        self.ioloop.start()
        return 1


if __name__ == '__main__':
    s = CCServer('ccserver', sys.argv[1:])
    s.start()

