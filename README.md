PiBlinker

A simple python library that provides easy access to to GPIO ports of 20,21,26
and enables user to debug behaviour on a raspberry pi2 using an RGB led.

It also allows you to attach an ATTINY85 programmed as slave, 
if you wish to have external ADC readouts in your project.

Harware schematics for a simple shield are included, and it costs around 5$ to
manufacture using collaborative panel manufacturers 

Requires http://wiringpi.com/ compiled and installed on the board. 
In most distributions this can be done by simply issuing:
    `sudo pip install wiringpi2`

Installation:
Assuming a Rasbian System with python 2.7
```
  cd ~/
  git clone https://github.com/minosg/piblinker.git
  ln -s ~/piblinker /usr/lib/python2.7/dist-packages/piblinker
```
Make sure you point the symbolic link to the right location.
`locate -b '\dist-packages'` Will help you locate where Python modules are stored
