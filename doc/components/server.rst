#######################
CC -- Command & Control
#######################
=============
CC components
=============

Server
######

Command-and-Control server.

CCServer
========

CC is ZMQ proxy for specific type of ZMQ messages (CC messages).

It listens on single ZMQ socket and processes messages by matching message type
to handler (one message can be dispatched to multiple handlers):

    client <-> ccserver|handler <-> handlerproc

It also has optional support for launching daemon processes, providing them
with configuration and keep watching them.  It is provided only for easier
administration, as any daemon can be written to be standalone.

Config options:
---------------

* ``cc-socket`` -- URI at which this CC instance will listen

* ``cc-role`` -- mode in which this CC instance will run

  - 'local', 'remote'
  - default: insecure

* ``cc-stats`` -- statistics level (raise for more counters to be tracked & logged)

  - 0..2 where 0 means no statistics
  - default: 1

* ``stats-period`` -- how often to send / write stats; in seconds

  - default: 30 seconds

* ``infofile-level`` -- infofile output level (raise for more stats to be tracked & logged)

  - 0..3 where 0 means no infofile
  - default: 2
  - note that level 3 may be rather cpu heavy

* ``heartbeat`` -- how often to log heartbeat; in seconds

  - 0 means no heartbeat
  - default: 60 seconds

* ``zmq_hwm`` -- ZMQ_HWM socket option (high water mark)

  - default: 50 -- *Careful changing!*

* ``zmq_linger`` -- ZMQ_LINGER socket option (linger period for socket shutdown)

  - default: 500 -- *Careful changing!*

* ``zmq_nthreads`` -- zmq_init.io_threads argument (size of thread pool to handle I/O operations)

  - default: 1 -- *Careful changing!*

* ``zmq_tcp_keepalive`` -- ZMQ_TCP_KEEPALIVE socket option (feature on/off switch)

  - default: on -- *Careful changing!*

* ``zmq_tcp_keepalive_intvl`` -- ZMQ_TCP_KEEPALIVE_INTVL socket option (keep-alive period in idle condition; in seconds)

  - default: 15 -- *Careful changing!*

* ``zmq_tcp_keepalive_idle`` -- ZMQ_TCP_KEEPALIVE_IDLE socket option (connection in idle before sending out keep-alive probes; in seconds)

  - default: 240 -- *Careful changing!*

* ``zmq_tcp_keepalive_cnt`` -- ZMQ_TCP_KEEPALIVE_CNT socket option (number of probes to send before declaring remote end not available)

  - default: 4 -- *Careful changing!*

Config example:
---------------
::

    [ccserver]
    pidfile = ~/pid/%(job_name)s.pid
    logfile = ~/log/%(job_name)s.log
    infofile = ~/log/%(job_name)s.info

    cc-socket = tcp://127.0.0.1:10000
    cc-role = local
    cc-stats = 2

    cms-keystore = ./keys
    #cms-verify-ca = ca
    #cms-decrypt = server
    #cms-encrypt = confdb

    # msgtype -> handler mapping
    [routes]
    # local routes
    echo = h:echo
    log = h:locallog
    job = h:jobmgr

    # remote routes
    pub = h:proxycc
    task = h:proxycc
    confdb = h:proxycc
