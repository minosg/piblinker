#!/usr/bin/env python

"""daemon.py: A background running daemon that maps RPI GPIO events to
methods or runnable scripts/programs"""

__author__ = "minos197@gmail.com"
__license__ = "LGPL"
__version__ = "0.0.1"
__email__ = "Minos Galanakis"
__project__ = "smartpi"
__date__ = "20-06-2015"

import os
import time
import daemon
from signal import SIGTERM
from daemon.pidfile import PIDLockFile
from collections import namedtuple
from subprocess import Popen, PIPE
import RPi.GPIO as GPIO

def normal_start(f1=None,
                 f2=None,
                 user=None,
                 sudopass=None,
                 pid_file="/tmp/piblinker_daemon.pid"):
    """ Wrapper utility function to call Daemon Class"""

    pid_file_path = pid_file
    if os.path.isfile(pid_file_path):
        print "PiDaemon Already Running, Restarting"
    PiDaemon(f1, f2, user, sudopass)

def start_daemon(f1=None,
                 f2=None,
                 user=None,
                 sudopass=None,
                 pid_file="/tmp/piblinker_daemon.pid"):
    """ Wrapper utility function to call Daemon Class"""

    pid_file_path = pid_file
    if os.path.isfile(pid_file_path):
        print "PiDaemon Already Running, Restarting"

    with daemon.DaemonContext(pidfile=PIDLockFile(pid_file_path)):
        PiDaemon(f1, f2, user, sudopass)


def kill_daemon(pid_file="/tmp/piblinker_daemon.pid"):
    """ Kill a running daemon"""

    pid_file_path = pid_file
    try:
        with open(pid_file_path) as F:
            pid = F.read().strip()
        print "Killing PiBlinker Daemon Running with pid %s" % pid
        os.kill(int(pid), SIGTERM)
    except Exception as e:
        pass


class PiDaemon(object):

    def __init__(self, method1=None, method2=None, user=None, sudopass=None):
        """ Initialize the a bakcground running daemon class that maps python
        methods or native binaries to callbacks. When a non callable method
        is detected it will wrap it around the script calling function """

        # Configure the GPIO
        self.button_map = {5: "button1", 6: "button2"}
        map(self._setup_button, self.button_map)
        self.colors = namedtuple('Colors', 'red green blue')(17, 18, 27)
        self._setup_led()

        # Class assumes that you have associated the user with a NOPASSWD
        # directive.You can run srcipt as another user if you has sudo rights.
        self.base_cmd = "%ssudo%s%s" % ('echo %s | ' % sudopass if
                                        sudopass else "", " -S" if sudopass
                                        else "", " -u %s" % user if user
                                        else "")

        # Detect if a the input argument has a callable property
        method_det = map(lambda x: not hasattr(x,  '__call__')
                         if x else False,  [method1, method2])

        # If an non callable object exists
        if filter(lambda x: x, method_det):
            # Map possible scripts with their callable property
            scripts = map(lambda x: x[1], zip(method_det, [method1, method2]))

            # Check that the arugemtn is poitning to a file and wrap it around
            # the run_scipt method
            method1, method2 = map(lambda x: (lambda: self.run_script(x))
                                   if (x and os.path.isfile(x)) else None,
                                   scripts)

        # Map interrupts to actions
        if (method1 and method2):
            self.actions = namedtuple('Actions',
                                      'button1 button2')(method1, method2)
        elif method1:
            self.actions = namedtuple('Actions',
                                      'button1 button2')(method1,
                                                         self.shutdown)
        elif method2:
            self.actions = namedtuple('Actions',
                                      'button1 button2')(self.reboot, method2)
        else:
            self.actions = namedtuple('Actions',
                                      'button1 button2')(self.reboot,
                                                         self.shutdown)

        self._run()

    def _setup_button(self, button_no):
        """ Handle the GPIO configuration """
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(button_no, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(button_no,
                              GPIO.RISING,
                              callback=self._button_cb,
                              bouncetime=300)

    def _setup_led(self):
        # TODO move GPIO LED setup to external lib or make it skip
        # setup if pins are already in USE
        GPIO.setwarnings(False)
        GPIO.setup(self.colors.red, GPIO.OUT)
        GPIO.setup(self.colors.green, GPIO.OUT)
        GPIO.setup(self.colors.blue, GPIO.OUT)
        GPIO.setwarnings(True)

    def run_script(self, script_path):
        """ Run an executable script """

        self._blink(self.colors.blue)
        self._shell_run(script_path)

    def reboot(self):
        """ Reboot the System """

        self._blink(self.colors.green)
        self._shell_run("/sbin/reboot")

    def shutdown(self):
        """Shutdown the system"""

        self._blink(self.colors.red)
        self._shell_run("/sbin/shutdown -h 0")

    def _button_cb(self, pin):
        """ Universal button callback. When triggered it will run the mapped
        method for event"""
        # Debounce
        if GPIO.input(pin):
            button = self.button_map[pin]
            action = eval("self.actions.%s" % button)
            action()

    def _run(self):
        """ keep the daemon running"""

        try:
            while(True):
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            GPIO.cleanup()

    def _blink(self, pin):
        """Blink an LED using PRI.GPIO"""

        for _ in range(3):
            GPIO.output(pin, GPIO.HIGH)
            time.sleep(0.4)
            GPIO.output(pin, GPIO.LOW)
            time.sleep(0.4)

    def _shell_run(self, cmd):
        """ Execute shell command in detached mdoe."""

        # There is no need to monitor output
        cmd = "%s %s" % (self.base_cmd, cmd)
        ret, err = Popen([cmd],
                         stdout=PIPE,
                         stderr=PIPE,
                         shell=True).communicate()

if __name__ == "__main__":
    pass
