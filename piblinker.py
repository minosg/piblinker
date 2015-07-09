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
        self.LEDS = {"RED": 17, "GREEN": 18, "BLUE": 27}
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
            "gpio export %d out"%self.LEDS["RED"],
            "gpio export %d out"%self.LEDS["GREEN"],
            "gpio export %d out"%self.LEDS["BLUE"],
            "gpio -g mode %d out"%self.LEDS["RED"],
            "gpio -g mode %d out"%self.LEDS["GREEN"],
            "gpio -g mode %d out"%self.LEDS["BLUE"]]
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

    def uart_open(self, port = "/dev/ttyAMA0", baud = 9600):
        """Open the Serial Channel"""

        try:
            self.uart = serial.Serial(port, baud)
        except serial.SerialException:
            print "** Failed to initialize serial, check your port.** "
            raise ValueError

    def uart_activate(self):
        """ Spam UART port untill it receives an ACK """

        self.uart_open()
        countr = 0
        #Test with a not supported command
        t_char = "O"
        while True:
            self.uart.write(t_char)
            if self.uart.inWaiting():
                repl = self.uart.read(2)
                if repl == "OK": print "UART Activated"
                else: print "UART was already enabled"
                break
            elif countr == 99:
                #Test with a supported command to see if activated
                t_char = "2"
            elif countr > 100:
                break

            time.sleep(0.05)
            countr += 1

    def uart_read(self, target = "ADC"):
        """Read the register through uart"""

        cmd = { "ADC":"2", "PIN":"1" }

        if target in cmd.keys():
            self.uart.write(cmd[target])
            return self.uart.readline()[:-1]

    def uart_close(self):
        """Close the serial channel"""
        self.uart.close()

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
        """Write the data formatted using struct pack,Format needs to be specified"""

        try:
            wb_file = self.i2c_devices[slave_id][1]
            wb_file.write(struct.pack(format,data))
        except KeyError:
            print "Device %d does not exist"%slave_id
        except struct.error:
            print "Pack Error make sure the data fits the format structure"
        except:
            print "Unspecified Error"

    def i2c_read_as(self, slave_id, format, byte_no):
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

    def demux(self,data):
        """ For efficiency purposes 10Bit ADC are muxed GPIO state."""

        adc_val = data & 0x3FF
        pin_val = (data >> 15)
        return (adc_val,pin_val)

    def i2c_read_adc(self,slave_id):
        """Reads data as returned from a 10Bit ADC sampling operation"""

        return self.demux(self.i2c_read_as(slave_id, '>H', 2)[0])[0]

    def i2c_read_pin(self,slave_id):
        """Reads data as returned from a 10Bit ADC sampling operation"""

        return self.demux(self.i2c_read_as(slave_id, '>H', 2)[0])[1]


if __name__ == "__main__":
    mode = 0
    import serial
    pb = PiBlinker()

    if len(sys.argv) == 3:
        
        # Set up test conditions
        if sys.argv[1] == "-t":

            if sys.argv[2] == "all":
                pb.led_print("RED", "This is important")
                pb.led_print("GREEN", "This worked")
                pb.led_print("BLUE", "This you should know")

                readf,writef = pb.i2c_open_file(0x04,1)
                #read two bytes using the direct file descriptor
                print repr(readf.read(2))

                #read a 2byte uint8_t variable
                print pb.i2c_read_as(04,">H",2)
                pb.i2c_close(0x04)

            elif sys.argv[2] == "i2c":
                readf,writef = pb.i2c_open_file(0x04,1)
                #read two bytes using the direct file descriptor

                print "2",repr(readf.read(2))

                #read a 2byte uint8_t variable
                print pb.i2c_read_as(04,">H",2)
                pb.i2c_close(0x04)

            elif sys.argv[2] == "poll":

                readf,writef = pb.i2c_open_file(0x04,1)
                while True:

                    #Read using read ADC
                    print "| ADC:",pb.i2c_read_adc(0x04),"| PIN: ",\
                        pb.i2c_read_pin(0x04),"|"
                    time.sleep(0.2)
                pb.i2c_close(0x04)

            elif sys.argv[2] == "uart":
                pb.uart_open()
                print "ADC:", pb.uart_read("ADC")
                print "PIN:", pb.uart_read("PIN")
                pb.uart_close()

            elif sys.argv[2] == "led":
                pb.led_print("RED", "This is important")
                pb.led_print("GREEN", "This worked")
                pb.led_print("BLUE", "This you should know")

    elif  len(sys.argv) == 2 and sys.argv[1] == "-h":
        print "\n ******** Basic testing commands ************"
        print "piblinker -t all: Test i2c communications and led"
        print "piblinker -t led: Test led"
        print "piblinker -t i2c: Test i2c comms"
        print "piblinker -t poll: Continously poll ADC Switch readouts"
        print "piblinker -t uart: Get serial readouts"

        print "piblinker -a: Activate UART mode after a reset"

    elif  len(sys.argv) == 2 and sys.argv[1] == "-a":
        pb.uart_activate()
    else:
        print "use -h to see test command syntax"

