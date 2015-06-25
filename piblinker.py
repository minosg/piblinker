#!/usr/bin/env python

"""blinky.py: A small library that uses wiriping pi access to raspbery pi GPIO 
   ports,aimed at providing a simple notification interface"""

__author__  = "minos197@gmail.com"
__license__ = "LGPL"
__version__ = "0.0.1"
__email__   = "Minos Galanakis"
__project__ = "smartpi"
__date__    = "01-06-2015"

import sys
import io
import os
import time
import fcntl
import struct
import subprocess


class PiBlinker():

    def __init__(self):
        """ Module Init."""
        self.LEDS = {"RED": 21, "GREEN": 26, "BLUE": 20}
        self.last_mode = 0
        self.setup()
        self.i2c_devices = {}

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

    def i2c_open_file(self, slave_id, bus = 1):
        """Open the I2C channel for raw byte comms"""

        if slave_id in self.i2c_devices.keys():
            print "Device %d already open"%slave_id
            return

        #Open the file descriptors
        read_ch  = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
        write_ch = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)

        #Set the register
        fcntl.ioctl(read_ch, 0x0703, slave_id)
        fcntl.ioctl(write_ch, 0x0703, slave_id)

        #store it to an internal dict
        self.i2c_devices[slave_id] = (read_ch,write_ch)
        #return the file descriptors if the user wants to manually drive them
        return (read_ch,write_ch) 

    def i2c_write_as(self, slave_id, format, data):
        """Format data before i2c transmit using struct pack,"""

        try:
            wb_file = self.i2c_devices[slave_id][1]
            wb_file.write(struct.pack(format,data))
        except KeyError:
            print "Device %d does not exit"%slave_id
        except struct.error:
            print "Pack Error make sure the data fits the format structure"
        except:
            print "Unspecified Error"

    def i2c_read_as(self, slave_id, format, byte_no):
        """Format data afte i2c rx using struct pack,"""
        try:
            rb_file = self.i2c_devices[slave_id][0]
            return struct.unpack(format,rb_file.read(byte_no))
        except KeyError:
            print "Device %d does not exit"%slave_id
        except struct.error:
            print "Pack Error make sure the data fits the format structure"
        except:
            print "Unspecified Error"

    def i2c_close(self,slave_id):
        """Close the file descriptors associated to the slave channel"""

        try:
            self.i2c_devices.pop(slave_id)
        except KeyError:
            print "Device %d does not exit"%slave_id
        
if __name__ == "__main__":
    #Use case example/test
    pb = PiBlinker()
    pb.led_print("RED", "This is important")
    pb.led_print("GREEN", "This worked")
    pb.led_print("BLUE", "This you should know")

    #Test the i2c
    readf,writef = pb.i2c_open_file(0x04,1)
    #read two bytes using the direct file descriptor
    print repr(readf.read(2))

    #read a 2byte uint8_t variable
    print pb.i2c_read_as(04,">H",2)
