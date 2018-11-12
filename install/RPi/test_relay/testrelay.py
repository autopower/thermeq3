#!/usr/bin/env python
import RPi.GPIO as GPIO
import time

# if relay type is normally closed, set to True, normally open set to False
relay_type = False


def start():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(4, GPIO.OUT)


def do(action):
    global relay_type
    if relay_type:
        action = not action
    if action:
        gpio_action = GPIO.HIGH
    else:
        gpio_action = GPIO.LOW
    try:
        GPIO.output(4, gpio_action)
    finally:
        pass


def do_test():
    print "Now turning relay ON for 5sec"
    do(True)
    time.sleep(5)
    print "And now turn OFF"
    do(False)	


if __name__ == '__main__':
    print "Test relay for RPi"
    print "Please connect your relay control pin to GPIO16"
    start()
    print "Pin setup done."
    do_test()
    value = ""
    while not value == "y":
        value = raw_input("Please enter y if is this correct: ")
        if value == "y":
            pass
        else:
            relay_type = not relay_type
            do_test()
    print "You successfully setup relay. Please edit action.py, line relay_type = ", relay_type
