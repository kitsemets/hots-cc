#######################
CC -- Command & Control
#######################

CC components
=============

Server_
-------
Command-and-Control server.

Handlers_
---------
Handlers are called in CC main loop, from single thread.  They should process
CC messages as quickly as possible.

Daemons_
--------
These are scripts that can be run alone or better launched & controlled by CC
Job Manager.

Tasks_
------
Tasks are programs, somewhat similar to daemons, that are executed once per
request.  They are managed by TaskRunner daemon.

.. _Server: components/server.rst
.. _Handlers: components/handlers.rst
.. _Daemons: components/daemons.rst
.. _Tasks: components/tasks.rst
