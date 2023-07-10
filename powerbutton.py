#!/usr/bin/python
import os
import RPi.GPIO as gpio
from subprocess import call
import time

gpio.setmode(gpio.BCM)
gpio.setup(21, gpio.IN, pull_up_down = gpio.PUD_UP)


def shutdown(channel):
    os.system('sudo halt')


gpio.add_event_detect(21, gpio.FALLING, callback=shutdown, bouncetime=300)

while 1:
    time.sleep(360)
