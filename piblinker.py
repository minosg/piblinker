#!/usr/bin/env python

"""PiBlinker.py: A small library that uses wiriping pi access to raspbery pi GPIO 
   ports,aimed at providing a simple notification interface"""

__author__  = "minos197@gmail.com"
__license__ = "LGPL"
__version__ = "0.0.1"
__email__   = "Minos Galanakis"
__project__ = "codename"
__date__    = "01-06-2015"

import sys
import os
import time
import subprocess


class PiBlinker():

    def __init__(self):
        """ Module Init."""
        self.LEDS = {"RED": 21, "GREEN": 26, "BLUE": 20}
        self.last_mode = 0
        self.setup()

    def run(self, cmd):
        """ Execute shell command in detached mdoe."""

        proc = subprocess.Popen([cmd], stdout=subprocess.PIPE, shell=True)
        proc.communicate()

    def setup(self):
        """ Set the enviroment for the module."""
        commands = [
            "gpio export 20 out",
            "gpio export 21 out",
            "gpio export 26 out",
            "gpio -g mode 21 out",
            "gpio -g mode 20 out",
            "gpio -g mode 26 out"]
        for c in commands:
            self.run(c)

    def set_led(self, led, mode):
        """ Set an LED to one of the supported states."""

        if led not in ["RED", "GREEN", "BLUE"]:
            return
        if mode == "ON":
            md = 1
        elif mode == "OFF":
            md = 0
        elif mode == "Toggle":
            md = (self.last_mode + 1) % 2
        elif mode == 0:
            md = 0
        elif mode == 1:
            md = 1
        else:
            print "Invalid Mode"
            return
        self.last_mode = md
        led_gpio = self.LEDS[led]
        cmd = "gpio -g write %d %d" % (led_gpio, mode)
        self.run(cmd)

    def blink(self, led, times, delay=1):
        """ Blink an LED n number of times."""

        if led not in ["RED", "GREEN", "BLUE"]:
            return
        mode = 0
        count = 0
        while (count <= times * 2):
            self.set_led(led, mode)
            time.sleep(delay)
            mode = (mode + 1) % 2
            count += 1

    def led_print(self, led, text, blink_no=3):
        """ Print a debug message and notify the user with the LED."""

        if led not in ["RED", "GREEN", "BLUE"]:
            print "invalid led", led
            return
        print"|%s|> %s" % (led, text)
        self.blink(led, blink_no, 0.5)

if __name__ == "__main__":
    #Use case example/test
    pb = PiBlinker()
    pb.led_print("RED", "This is important")
    pb.led_print("GREEN", "This worked")
    pb.led_print("BLUE", "This you should know")
