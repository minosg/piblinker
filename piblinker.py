#!/usr/bin/env python

"""blinky.py: A small library that uses wiriping pi access to raspbery pi GPIO
   ports,aimed at providing a simple notification interface"""

__author__ = "minos197@gmail.com"
__license__ = "LGPL"
__version__ = "0.0.1"
__email__ = "Minos Galanakis"
__project__ = "smartpi"
__date__ = "01-06-2015"

import sys
import io
import time
import fcntl
import serial
import struct
from subprocess import Popen, PIPE
from colorlogger import CLogger


def blinker(color, period=0.2, times=3):
    """ Decorator that allows modular output formating for PiLogger """

    def blinker_decorator(func):
        def func_wrapper(class_obj, message):
            # Blinke the LED before printing sdout
            class_obj.blink(color, times, period)
            return func(class_obj, color, message)
        return func_wrapper
    return blinker_decorator


class PiBlinkerError(Exception):
    __module__ = 'exceptions'


class PiBlinker():

    def __init__(self):
        raise ValueError('PiBlinker is not meant to be instantiated')

    @classmethod
    def setup(self,
              log_level="ver_debug",
              log_label="PiBlinker",
              log_path=None,
              log_colors=None):

        """ Module Init."""
        # Map a color to GPIO.BCM PIN
        self.LEDS = {"RED": 17, "GREEN": 18, "BLUE": 27}
        self.last_mode = 0
        # Configure the GPIO ports in hardware
        map(self.run, [(x % n) for n in self.LEDS.values()
                       for x in ["gpio export %d out",
                                 "gpio -g mode %d out"]])
        self.i2c_devices = {}

        # Assosiate log levels with colors
        if not log_colors:
            log_colors = {"base_color": "CYAN",
                          "info": "HBLUE",
                          "warning": "RED",
                          "error": "RED",
                          "debug": "GREEN",
                          "ver_debug": "GREEN"}

        # Initalise the logging module
        CLogger.setup(log_label, log_level, log_path, log_colors)
        return self

    @staticmethod
    def run(cmd):
        """ Execute shell command in detached mdoe."""
        proc = Popen([cmd], stdout=PIPE, stderr=PIPE, shell=True)
        ret, err = proc.communicate()
        if err:
            # ignore warnings in error stream
            if "Warning" in err:
                CLogger.warning(err.strip())
                return err
            raise PiBlinkerError(err)
        else:
            return ret

    @classmethod
    def set_led(self, led, mode):
        """ Set an LED to one of the supported states."""

        if led not in self.LEDS.keys():
            return
        mlist = {"ON": 1, "OFF": 0, "Toggle": -1}
        # convert input to a numerical mode
        try:
            md = mode if mode not in mlist\
                else {k: v for k, v in mlist.iteritems()}[mode]
        except KeyError:
            raise PiBlinkerError("Mode %s is not reognised" % mode)

        # Toggle the led if required
        self.last_mode = md if md > 0 else (self.last_mode + 1) % 2
        # Toggle the GPIO
        cmd = "gpio -g write %d %d" % (self.LEDS[led], self.last_mode)
        self.run(cmd)

    @classmethod
    def blink(self, led, times, delay=1):
        """ Blink an LED n number of times."""

        # Make sure led is uppercase
        led = led.upper()
        if led not in self.LEDS.keys():
            return
        mode = 0
        count = 0
        while (count <= times * 2):
            self.set_led(led, mode)
            time.sleep(delay)
            mode = (mode + 1) % 2
            count += 1

    @classmethod
    def led_print(self, color, text):
        """ Print a debug message and notify the user with the LED."""

        eval("self.%s" % color.lower())(text)

    @classmethod
    @blinker("RED")
    def red(self, *args):
        """ Print a debug message and notify the user with the LED."""

        color, message = args
        print"|%s|> %s" % (color, message)

    @classmethod
    @blinker("GREEN")
    def green(self, *args):
        """ Print a debug message and notify the user with the LED."""

        color, message = args
        print"|%s|> %s" % (color, message)

    @classmethod
    @blinker("BLUE")
    def blue(self, *args):
        """ Print a debug message and notify the user with the LED."""

        color, message = args
        print"|%s|> %s" % (color, message)

    @classmethod
    @blinker("RED")
    def error(self, *args):
        """ Print a debug message and notify the user with the LED."""

        CLogger.error(args[-1])

    @classmethod
    @blinker("BLUE")
    def info(self, *args):
        """ Print a debug message and notify the user with the LED."""

        CLogger.info(args[-1])

    @classmethod
    @blinker("RED")
    def warning(self, *args):
        """ Print a debug message and notify the user with the LED."""

        CLogger.warning(args[-1])

    @classmethod
    @blinker("GREEN")
    def debug(self, *args):
        """ Print a debug message and notify the user with the LED."""

        CLogger.debug(args[-1])

    @classmethod
    def uart_open(self, port="/dev/ttyAMA0", baud=9600, time_out=None):
        """Open the Serial Channel"""

        try:
            self.uart = serial.Serial(port, baud, timeout=time_out)
        except serial.SerialException:
            print "** Failed to initialize serial, check your port.** "
            raise ValueError

    @classmethod
    def uart_activate(self):
        """ Spam UART port untill it receives an ACK """

        self.uart_open()
        countr = 0
        # Test with a not supported command
        t_char = "O"
        while True:
            self.uart.write(t_char)
            if self.uart.inWaiting():
                repl = self.uart.read(2)
                if repl == "OK":
                    print "UART Activated"
                else:
                    print "UART was already enabled"
                break
            elif countr == 99:
                # Test with a supported command to see if activated
                t_char = "2"
            elif countr > 100:
                break

            time.sleep(0.05)
            countr += 1

    @classmethod
    def uart_read(self, target="ADC"):
        """Read the register through uart"""

        cmd = {"ADC": "2", "PIN": "1"}

        if target in cmd.keys():
            self.uart.write(cmd[target])
            return self.uart.readline()[:-1]

    @classmethod
    def uart_close(self):
        """Close the serial channel"""
        self.uart.close()

    @classmethod
    def i2c_open_file(self, slave_id, bus=1):
        """Open the I2C channel for raw byte comms"""

        if slave_id in self.i2c_devices.keys():
            print "Device %d already open" % slave_id
            return

        # Open the file descriptors
        read_ch = io.open("/dev/i2c-"+str(bus), "rb", buffering=0)
        write_ch = io.open("/dev/i2c-"+str(bus), "wb", buffering=0)

        # Set the register
        fcntl.ioctl(read_ch, 0x0703, slave_id)
        fcntl.ioctl(write_ch, 0x0703, slave_id)

        # store it to an internal dict
        self.i2c_devices[slave_id] = (read_ch, write_ch)
        # return the file descriptors if the user wants to manually drive them
        return (read_ch, write_ch)

    @classmethod
    def i2c_write_as(self, slave_id, format, data):
        """Write the data formatted using struct pack,
        Format needs to be specified"""

        try:
            wb_file = self.i2c_devices[slave_id][1]
            wb_file.write(struct.pack(format, data))
        except KeyError:
            print "Device %d does not exist" % slave_id
        except struct.error:
            print "Pack Error make sure the data fits the format structure"
        except:
            raise IOError

    @classmethod
    def i2c_read_as(self, slave_id, format, byte_no):
        try:
            rb_file = self.i2c_devices[slave_id][0]
            return struct.unpack(format, rb_file.read(byte_no))
        except KeyError:
            print "Device %d does not exit" % slave_id
        except struct.error:
            print "Pack Error make sure the data fits the format structure"
        except:
            raise IOError

    @classmethod
    def i2c_close(self, slave_id):
        """Close the file descriptors associated to the slave channel"""
        try:
            self.i2c_devices.pop(slave_id)
        except KeyError:
            print "Device %d does not exit" % slave_id

    @classmethod
    def demux(self, data):
        """ For efficiency purposes 10Bit ADC are muxed GPIO state."""

        adc_val = data & 0x3FF
        pin_val = (data >> 15)
        return (adc_val, pin_val)

    @classmethod
    def i2c_read_adc(self, slave_id):
        """Reads data as returned from a 10Bit ADC sampling operation"""

        return self.demux(self.i2c_read_as(slave_id, '>H', 2)[0])[0]

    @classmethod
    def i2c_read_pin(self, slave_id):
        """Reads data as returned from a 10Bit ADC sampling operation"""

        return self.demux(self.i2c_read_as(slave_id, '>H', 2)[0])[1]

    @classmethod
    def test_hardware(self):
        """ Detect hardware shield's presense """

        detected = False

        try:
            self.uart_open(time_out=2)
            reading = self.uart_read("ADC")
            if len(reading):
                detected = True
        except:
            pass
        try:
            readf, writef = self.i2c_open_file(0x04, 1)
            self.i2c_read_as(04, ">H", 2)
            self.i2c_close(0x04)
            detected = True
        except:
            pass
        return detected

if __name__ == "__main__":
    mode = 0
    pb = PiBlinker.setup()

    if len(sys.argv) == 3:

        # Set up test conditions
        if sys.argv[1] == "-t":

            if sys.argv[2] == "all":
                pb.red("This is important")
                pb.green("This worked")
                pb.blue("This you should know")

                readf, writef = pb.i2c_open_file(0x04, 1)
                # read two bytes using the direct file descriptor
                print repr(readf.read(2))

                # read a 2byte uint8_t variable
                print pb.i2c_read_as(04, ">H", 2)
                pb.i2c_close(0x04)

            elif sys.argv[2] == "i2c":
                readf, writef = pb.i2c_open_file(0x04, 1)

                # read two bytes using the direct file descriptor
                print "2", repr(readf.read(2))

                # read a 2byte uint8_t variable
                print pb.i2c_read_as(04, ">H", 2)
                pb.i2c_close(0x04)

            elif sys.argv[2] == "poll":

                readf, writef = pb.i2c_open_file(0x04, 1)
                while True:

                    # Read using read ADC
                    print "| ADC:", pb.i2c_read_adc(0x04), "| PIN: ",\
                        pb.i2c_read_pin(0x04), "|"
                    time.sleep(0.2)
                pb.i2c_close(0x04)

            elif sys.argv[2] == "uart":
                pb.uart_open()
                print "ADC:", pb.uart_read("ADC")
                print "PIN:", pb.uart_read("PIN")
                pb.uart_close()

            elif sys.argv[2] == "led":
                pb.led_print("RED", "This is important")
                pb.led_print("GREEN", "This is important2")
                pb.led_print("BLUE", "This is important3")

            elif sys.argv[2] == "log":
                pb.info("This is an info")
                pb.warning("This is a warning")
                pb.error("This is an error")
                pb.debug("This is debug")

    elif len(sys.argv) == 2 and sys.argv[1] == "-h":
        print "\n ******** Basic testing commands ************"
        print "piblinker -t all: Test i2c communications and led"
        print "piblinker -t led: Test led"
        print "piblinker -t log: Test led and loging output"
        print "piblinker -t i2c: Test i2c comms"
        print "piblinker -t poll: Continously poll ADC Switch readouts"
        print "piblinker -t uart: Get serial readouts"

        print "piblinker -a: Activate UART mode after a reset"

    elif len(sys.argv) == 2 and sys.argv[1] == "-a":
        pb.uart_activate()
    else:
        print "use -h to see test command syntax"
