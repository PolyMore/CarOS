from gpiozero import Button
import time
import os
from datetime import datetime

button = Button(14)
token = open('/boot/token.txt').read()


while True:
    if button.is_pressed:
        os.system("fswebcam -r 1280x720 --no-banner /home/pi/PolyMore/"+datetime.now().strftime("%d-%m-%Y-%H-%M-%S")+".jpg")
        print("Picture saved")
        time.sleep(0.5)