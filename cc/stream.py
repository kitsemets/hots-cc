"""Wrapper around ZMQStream
"""

import logging
import time

import zmq
from zmq.eventloop import IOLoop
from zmq.eventloop.zmqstream import ZMQStream

from cc.message import CCMessage

__all__ = ['CCStream', 'CCReqStream']

#
# simple wrapper around ZMQStream
#

class CCStream(ZMQStream):
    """Add CCMessage methods to ZMQStream"""

    def send_cmsg(self, cmsg):
        """Send CCMessage to socket"""
        self.send_multipart(cmsg.zmsg)

    def on_recv_cmsg(self, cbfunc):
        """Set callback that receives CCMessage."""
        def convert_cmsg(zmsg):
            cmsg = CCMessage(zmsg)
            cbfunc(cmsg)
        self.on_recv(convert_cmsg)


#
# request multiplexer on single stream
#

class QueryInfo:
    """Store callback details for query."""
    log = logging.getLogger('QueryInfo')

    def __init__(self, qid, cmsg, cbfunc, rqs):
        self.qid = qid
        self.orig_cmsg = cmsg
        self.cbfunc = cbfunc
        self.timeout_ref = None
        self.ioloop = rqs.ioloop
        self.remove_query = rqs.remove_query

    def on_timeout(self):
        """Called by ioloop on timeout, needs to handle exceptions"""
        try:
            self.timeout_ref = None
            self.launch_cb(None)
        except:
            self.log.exception('timeout callback crashed')

    def launch_cb(self, arg):
        """Run callback, re-wire timeout and query if needed."""
        keep, timeout = self.cbfunc(arg)
        self.log.debug('keep=%r', keep)
        if keep:
            self.set_timeout(timeout)
        else:
            self.remove_query(self.qid)

    def set_timeout(self, timeout):
        """Set new timeout for task, None means drop it"""
        if self.timeout_ref:
            self.ioloop.remove_timeout(self.timeout_ref)
            self.timeout_ref = None
        if timeout:
            deadline = time.time() + timeout
            self.timeout_ref = self.ioloop.add_timeout(deadline, self.on_timeout)

    def send_to(self, cc):
        self.orig_cmsg.send_to(cc)

class CCReqStream:
    """Request-based API for CC socket.

    Add request-id into route, later map replies to original request
    based on that.
    """

    log = logging.getLogger('CCReqStream')

    def __init__(self, cc_url, xtx, ioloop=None, zctx=None):
        """Initialize stream."""

        zctx = zctx or zmq.Context.instance()
        ioloop = ioloop or IOLoop.instance()

        s = zctx.socket(zmq.XREQ)
        s.connect(cc_url)
        s.setsockopt(zmq.LINGER, 500)

        self.ccs = CCStream(s, ioloop)
        self.ioloop = ioloop
        self.xtx = xtx

        self.query_id_seq = 1
        self.query_cache = {}

        self.ccs.on_recv(self.handle_recv)

    def remove_query(self, qid):
        """Drop query state.  Further replies are ignored."""
        qi = self.query_cache.get(qid)
        if qi:
            del self.query_cache[qid]
            qi.set_timeout(None)

    def ccquery_sync(self, msg, timeout=0):
        """Synchronous query.

        Returns first reply.
        """
        res = [None]
        def sync_cb(_rep):
            res[0] = _rep
            self.ioloop.stop()
            return (False, 0)
        self.ccquery_async(msg, sync_cb, timeout)
        self.ioloop.start()
        return res[0]

    def ccquery_async(self, msg, cbfunc, timeout=0):
        """Asynchronous query.

        Maps replies to callback function based on request id.
        """
        # create query id prefix
        qid = "Q%06d" % self.query_id_seq
        self.query_id_seq += 1

        # create message, add query id
        cmsg = self.xtx.create_cmsg(msg)
        cmsg.set_route([qid])

        qi = QueryInfo(qid, cmsg, cbfunc, self)
        self.query_cache[qid] = qi

        qi.set_timeout(timeout)

        qi.send_to(self.ccs)

        return qid

    def ccpublish(self, msg):
        """Broadcast API."""
        cmsg = self.xtx.create_cmsg(msg)
        cmsg.send_to(self.ccs)

    def handle_recv(self, zmsg):
        """Internal callback on ZMQStream.

        It must not throw exceptions.
        """
        try:
            self.handle_recv_real(zmsg)
        except Exception:
            self.log.exception('handle_recv_real crashed, dropping msg: %r', zmsg)

    def handle_recv_real(self, zmsg):
        """Actual callback that can throw exceptions."""

        cmsg = CCMessage(zmsg)

        route = cmsg.get_route()
        if len(route) != 1:
            self.log.error('Invalid reply route: %r', route)
            return

        qid = route[0]
        if qid not in self.query_cache:
            self.log.error('reply for unknown query: %r', qid)
            return

        msg = cmsg.get_payload(self.xtx)

        qi = self.query_cache[qid]
        qi.launch_cb(msg)

    def resend(self, qid, timeout=0):
        if qid in self.query_cache:
            qi = self.query_cache[qid]
            qi.send_to(self.ccs)
            qi.set_timeout(timeout)
        else:
            pass # ?
