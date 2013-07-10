#######################
CC -- Command & Control
#######################

About
=====

CC (Command & Control) is a scalable service management framework.

We need to provide a scalable and portable alternative to already existing
frameworks kuberner and sbell.  These legacy tools currently take care of many
server / service management tasks on SiteOps server platform, but they are
unmaintained and/or hard to maintain.  Moreover, we need scalable and secure
approach for log / application data transport and more real-time control over
maintenance jobs and processes.

CC lives in Git in `common/hots`__ repository.

__ https://internal-git.host/?p=common/hots.git;a=summary

Goals
=====

* Gathering monitoring data from servers
* Realtime task submission and feedback
* Log file / info file transport
* Secure, efficient, robust

Documentation
=============

* Introduction:

  - `CC overview`_

* Configuration and daily usage:

  - `CC use cases`_ -- common / useful use cases
  - `CC components`_ -- detailed info and config examples
  - `CC changelog`_ -- news important for CC users

* Legacy notes and documents:

* Miscellaneous:

User stories
============

* infofiles transport -- works; in production
* infoscript plugin -- works; in production
* log shipping -- works; in production (databases, monitoring)
* pg_logforward -- works; in production
* relman task execution -- in progress
* kuberner harvester replacement -- needs design review

Resources
=========


.. _`CC overview`: overview.rst
.. _`CC use cases`: use_cases.rst
.. _`CC components`: components.rst
.. _`CC changelog`: changelog.rst
