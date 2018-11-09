import RPi.GPIO as GPIO

# if relay type is normally closed, set to True, normally open set to False
relay_type = False


def start():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(16, GPIO.OUT)


def do(action):
    global relay_type
    if relay_type:
        action = not action
    if action:
        gpio_action = GPIO.HIGH
    else:
        gpio_action = GPIO.LOW
    try:
        GPIO.output(16, gpio_action)
    finally:
        pass