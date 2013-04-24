#######################
CC -- Command & Control
#######################
=============
CC components
=============

Tasks
#####

Task handler is implementation of one specific type of task.  They are executed
by TaskRunner upon request.  Parameters and feedback are task specific.

SampleTask (``t:sample``)
=========================

Example task.  Does some "work" and sends feedback after each chunk.
Can optionally crash during launch or run.

Parameters:
-----------

* ``cmd`` -- selects desired behaviour; if empty then 'run' assumed

  - run, crash-launch, crash-run

Feedback:
---------

* ``i`` -- simple counter

SampleTask (``t:sample_async``)
===============================

Example task with asynchronous feedback.  Similar to SampleTask above but since
it executes long running step, it needs to send its feedback from another thread
(otherwise requestor would not know about progress and TaskRouter might expire
reply route if no msg seen for long time).

Parameters:
-----------
None

Feedback:
---------

* ``elapsed_delta`` -- time elapsed since last feedback sent
* ``elapsed_total`` -- time elapsed since task was started; in seconds
