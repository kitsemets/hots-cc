
import os, subprocess, select, fcntl

from zmq.eventloop.ioloop import PeriodicCallback
from cc.handler import CCHandler

import skytools

__all__ = ['JobMgr']

CC_HANDLER = 'JobMgr'

def set_nonblocking(fd, onoff):
    """Toggle the O_NONBLOCK flag.
    If onoff==None then return current setting.
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    if onoff is None:
        return (flags & os.O_NONBLOCK) > 0
    if onoff:
        flags |= os.O_NONBLOCK
    else:
        flags &= ~os.O_NONBLOCK
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)

def set_cloexec(fd, onoff):
    """Toggle the FD_CLOEXEC flag.
    If onoff==None then return current setting.
    """
    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    if onoff is None:
        return (flags & fcntl.FD_CLOEXEC) > 0
    if onoff:
        flags |= fcntl.FD_CLOEXEC
    else:
        flags &= ~fcntl.FD_CLOEXEC
    fcntl.fcntl(fd, fcntl.F_SETFL, flags)

#
# JobMgr
#

class JobState:
    def __init__(self, jname, jcf, log, cc_url, ioloop):
        self.jname = jname
        self.jcf = jcf
        self.proc = None
        self.log = log
        self.cc_url = cc_url
        self.timer = None
        self.ioloop = ioloop
        pidfiledir = self.jcf.getfile('pidfiledir', '~/pid')
        self.pidfile = "%s/%s.pid" % (pidfiledir, self.jname)
        self.cfdict = {
                'job_name': self.jname,
                'pidfile': self.pidfile,
        }
        for o in self.jcf.options():
            self.cfdict[o] = self.jcf.get(o)

    def handle_timer(self):
        if self.proc:
            self.log.info('JobState.handle_timer')
            data = self.proc.stdout.read()
            if data:
                self.log.info('handle_timer: stdout=%s', repr(data.strip()))
            if self.proc.poll() is not None:
                x = self.proc.wait()
                self.log.info('handle_timer: proc exited with %s', repr(x))
                self.proc = None
        else:
            # daemonization successful?
            live = skytools.signal_pidfile(self.pidfile, 0)
            if live:
                self.log.info('handle_timer: %s is alive', self.jname)
            else:
                self.log.info('handle_timer: %s is dead', self.jname)


    def start(self):
        # unsure about the best way to specify target
        mod = self.jcf.get('module', '')
        script = self.jcf.get('module', '')
        cls = self.jcf.get('class', '')
        args = ['-d', '--cc', self.cc_url, '--ccdaemon', self.jname]
        if mod:
            cmd = ['python', '-m', mod] + args
        elif script:
            cmd = [script] + args
        else:
            raise skytools.UsageError('dunno how to launch class')

        self.log.info('Launching %s: %s', self.jname, cmd)
        self.proc = subprocess.Popen(cmd, close_fds=True,
                                stdin = open(os.devnull, 'rb'),
                                stdout = subprocess.PIPE,
                                stderr = subprocess.STDOUT)

        set_nonblocking(self.proc.stdout, True)

        self.timer = PeriodicCallback(self.handle_timer, 2*1000, self.ioloop)
        self.timer.start()

class JobMgr(CCHandler):
    """Provide config to local daemons / tasks."""

    def __init__(self, hname, hcf, ccscript):
        super(JobMgr, self).__init__(hname, hcf, ccscript)

        self.local_url = ccscript.local_url

        self.jobs = {}
        for dname in self.cf.getlist('daemons'):
            self.add_job(dname)

    def add_job(self, jname):
        jcf = skytools.Config(jname, self.cf.filename, ignore_defs = True)
        jstate = JobState(jname, jcf, self.log, self.local_url, self.ioloop)
        self.jobs[jname] = jstate
        jstate.start()
        
    def handle_msg(self, cmsg):
        """Got message from client, send to remote CC"""

        self.log.info('JobMgr req: %s', cmsg)
        data = cmsg.get_payload()

        res = {'req': data['req']}
        if data['req'] == 'job.config':
            # send config
            job = self.jobs[data['job_name']]
            res['config'] = job.cfdict
        else:
            res['msg'] = 'Unsupported req'
        ans = cmsg.make_reply(res)
        self.cclocal.send_cmsg(ans)
        self.log.info('JobMgr answer: %s', ans)
