# PiBlinker

A simple python library that provides easy access to to GPIO ports of 20, 21, 26
and enables user to debug behavior on a raspberry pi2 using an RGB led.

It also allows you to attach an ATTINY85 programmed as slave,
if you wish to have external ADC readouts in your project.

Hardware schematics for a simple shield are included, and it costs around 5$ to
manufacture using collaborative panel manufacturers

### Features:
 * Easy to interface logging platform for Raspberry PI boards
 * Easy to manufacture boards even for novice users.
 * Hardware reading of ADC sensor and an extra pin and exposed to the API with
 a file descriptor. No embedded experience required to use, just read/write
 to File.
 * UART/ I2C communication interface, for extra flexibility (i.e Camera Project)
 * Module does not require instantiation, is used directly calling class methods
 * Easy to subclass and create custom routines using decorators
 * Supports already pre-formatted colorized log output with time-stamp and
 optional output to file.
 * Using ANSIColors format that is compatible with Linux, OSX, Putty
 * Log commands also blink the LED to provide an alert system for systems
 running without a screen.
 * Supports different levels of logging with the verbose debugging notifying
 user of the current function and line number in code.
 * Contains simple command line interface for Testing

### Screenshots

#### Console Output
![alt text](https://www.dropbox.com/s/rlsw6487il24kot/piblinker1.png?raw=1  "Console")

#### PCB
![alt text](https://www.dropbox.com/s/l8ry0m7ak1ivl2t/piblinker-pcb.png?raw=1  "PCB Top")
![alt text](https://www.dropbox.com/s/v5ppv0xh69nji23/piblinker.pcb2.png?raw=1  "PCB Bottom")

### Installation

Requires http://wiringpi.com/ compiled and installed on the board.
In most distributions this can be done by simply issuing:

`sudo pip install wiringpi2`

Assuming a Raspbian System with python 2.7
```
  cd ~/
  git clone https://github.com/minosg/piblinker.git
  ln -s ~/piblinker /usr/lib/python2.7/dist-packages/piblinker
```
Make sure you point the symbolic link to the right location.
`locate -b '\dist-packages'` Will help you locate where Python modules are stored

### Usage

Using the module is as simple as

~~~~~
PiBlinker.setup()

PiBlinker.red("Your text here")
PiBlinker.green("Your text here")
PiBlinker.blue("Your text here")
~~~~~

Setup function also returns a reference to the class object , so you can alias
it:

~~~~~
pilogger = PiBlinker.setup()

pilogger.info("Your text here")
pilogger.warning("Your text here")
pilogger.error("Your text here")
pilogger.debug("Your text here")
~~~~~

### Further customization
If you are unhappy with the default configuration you can specify parameters in
the setup function:

~~~~~
PiBlinker.setup(log_level, log_label, log_path, log_colors)
~~~~~

#### log_label
Is just the name you want to assign to the logger. It is included in every line
of log produced. The recommended standard is to set it to the __file__ name.

#### log_level
The standard level of logging. Piblinker will ignore all logging commands that
are above the current level. Supported levels are :

* info
* warning
* error
* debug
* ver_debug

Setting level to info will only display and write to file info calls, while
setting debug will print everything. Verbose debug is a special debug level that
also inspects the function  that called it and displays the information to
screen. In every other aspect ver_debug is identical to debug.

#### log_path
The file that the logging commands will be saved to.Not setting a path will only
display commands and blink the LED.

#### log_colors
This parameter allows you to override the default colors that will be displayed
by the logger to screen.It DOES not affect the blinking led behavior. Input will
be sanitized and if you attempt to set an invalid level or invalid color, it
will be ignored

~~~~~
llevels = {"info": "CYAN",
           "warning":"UBLUE",
           "error": "HRED",
           "ver_debug": "WHITE"}
~~~~~

Note that prefixing a color adjusts the formatting:
 * U  -> underline
 * H  -> Highlight
 * UH -> Underline && Highlight

### Communicating with ATTINY85

#### i2c

The file descriptors can be accessed using

~~~~~
readf, writef = PiBlinker.i2c_open_file(0x04, 1)
... do stuff
PiBlinker.i2c_close(0x04)
~~~~~

There are interface commands some simple readouts

~~~~~
adc_val = PiBlinker.i2c_read_adc(0x04)
chip_in = PiBlinker.i2c_read_pin(0x04)
~~~~~

#### UART

~~~~~
PiBlinker.uart_open()
print "ADC:", PiBlinker.uart_read("ADC")
print "PIN:", PiBlinker.uart_read("PIN")
PiBlinker.uart_close()
~~~~~

#### Switching between UART and I2C communications

By default the ATTINY85 will boot in UART mode, poll the port for a short time
interval waiting for a special byte and fall-back to use i2c interface (default)
if nothing is received. If the byte is received, then it will set UART mode as
default.

This behavior can be tested using ```piblinker -a``` , but when using the library to
custom projects that will power cycle ensure that

~~~~~~
PiBlinker.uart_activate()
~~~~~~
 is run at power-up

### Supported Test commands

~~~~~
piblinker -t all: Test i2c communications and led
piblinker -t led: Test led
piblinker -t log: Test led and loging output
piblinker -t i2c: Test i2c comms
piblinker -t poll: Continously poll ADC Switch readouts
piblinker -t uart: Get serial readouts
piblinker -a: Activate UART mode after a reset
~~~~~
