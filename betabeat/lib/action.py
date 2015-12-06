import RPi.GPIO as GPIO

def start(platform):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(18, GPIO.OUT)
    # GPIO pin 18 is for DEV, prod is 17

def do(action):
    if action:
        gpio_action = GPIO.HIGH
    else:
        gpio_action = GPIO.LOW
    try:
        GPIO.output(18, gpio_action)
        # PIN 18 if for DEV, 17 for PROD
    finally:
        pass
