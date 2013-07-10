#######################
CC -- Command & Control
#######################
============
CC use cases
============

Here we document some common / useful use cases, so that others can easily
build their own C&C setup.

`Info file transport`_
======================

Common scenario is to transfer service infofiles from one location to another,
usually from more locations to central server.  Any type of files can be dealt
with as well as any content created on the fly.

`Log file transport`_
=====================

Another common scenario is transferring log files.  In this case the files grow
fast, so it is better to watch them as they grow and send over just newly added
data.  This avoids resending of whole files, evens out cpu/io load and makes
(partial) files available at target location as soon as possible.  Also, files
can be accurately followed even after CC restarts.

`Proxy - Gateway - Bridge`_
===========================

It is often desirable to have one entry point that can forward messages as
required.  This may be seen as a gateway.  Or build a link across networks with
one side acting as a sink and the other one as a dispatcher.  This may be seen
as a bridge.  Proxy component can do these and much more.

.. _`Info file transport`: use_cases/infofile_transport.rst
.. _`Log file transport`: use_cases/logfile_transport.rst
.. _`Proxy - Gateway - Bridge`: use_cases/proxying.rst
