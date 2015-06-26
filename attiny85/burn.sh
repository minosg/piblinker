#!/bin/sh

################################################################################
# Commmand to use AVR dude to program the hex firmware onto the ATTINY
# Remember to replace the programmer and the port for the ones you use
# 
#  buspirate: Buspirate
#  usbtiny  : USBTinyICSP
#  avrisp   : Arduino as ICSP
#  stk500   : stk500 or Buspirate with skt firmware
#
# The fuses set the chip to use the 8Mhz internal oscillator
#  Programming Setup
#  Pin 1: CS
#  Pin 7: SCK
#  Pin 6: MISO
#  Pin 5: MOSI
#
#  Normal Operation
#  Pin 2: ADC Sample 
#
###############################################################################

#Set the fuses
avrdude -c buspirate -p t85 -P /dev/ttyUSB1 -b 115200 -U lfuse:w:0xe2:m -U hfuse:w:0xdf:m -U efuse:w:0xff:m
#Program the chip
avrdude -c buspirate -p t85 -P /dev/ttyUSB1 -b 115200 -U flash:w:attiny85_adc_slave.cpp.tiny8.hex:i
