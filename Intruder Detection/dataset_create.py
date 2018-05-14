from __future__ import print_function
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from imutils.video import FPS
import RPi.GPIO as GPIO
import picamera
import imutils
from imutils.video.pivideostream import PiVideoStream
import numpy as np
import cv2
import argparse
import time

LCD_RS = 7
LCD_E = 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18
# Define some device constants
LCD_WIDTH = 16  # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line

# Timing constants

E_PULSE = 0.0005
E_DELAY = 0.0005
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(4, GPIO.OUT)
GPIO.setup(11, GPIO.IN)


def lcd_toggle_enable():
    # Toggle enable
    time.sleep(E_DELAY)
    GPIO.output(LCD_E, True)
    time.sleep(E_PULSE)
    GPIO.output(LCD_E, False)
    time.sleep(E_DELAY)


def lcd_byte(bits, mode):
    # Send byte to data pins
    # bits = data
    # mode = True  for character
    #        False for command

    GPIO.output(LCD_RS, mode)  # RS

    # High bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x10 == 0x10:
        GPIO.output(LCD_D4, True)
    if bits & 0x20 == 0x20:
        GPIO.output(LCD_D5, True)
    if bits & 0x40 == 0x40:
        GPIO.output(LCD_D6, True)
    if bits & 0x80 == 0x80:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()

    # Low bits
    GPIO.output(LCD_D4, False)
    GPIO.output(LCD_D5, False)
    GPIO.output(LCD_D6, False)
    GPIO.output(LCD_D7, False)
    if bits & 0x01 == 0x01:
        GPIO.output(LCD_D4, True)
    if bits & 0x02 == 0x02:
        GPIO.output(LCD_D5, True)
    if bits & 0x04 == 0x04:
        GPIO.output(LCD_D6, True)
    if bits & 0x08 == 0x08:
        GPIO.output(LCD_D7, True)

    # Toggle 'Enable' pin
    lcd_toggle_enable()


def lcd_init():
    # Initialise display
    lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
    lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
    lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
    lcd_byte(0x0C, LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
    lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
    lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
    time.sleep(E_DELAY)


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbers
GPIO.setup(LCD_E, GPIO.OUT)  # E
GPIO.setup(LCD_RS, GPIO.OUT)  # RS
GPIO.setup(LCD_D4, GPIO.OUT)  # DB4
GPIO.setup(LCD_D5, GPIO.OUT)  # DB5
GPIO.setup(LCD_D6, GPIO.OUT)  # DB6
GPIO.setup(LCD_D7, GPIO.OUT)  # DB7
lcd_init()


def lcd_string(message, line):
    # Send string to display

    message = message.ljust(LCD_WIDTH, " ")

    lcd_byte(line, LCD_CMD)

    for i in range(LCD_WIDTH):
        lcd_byte(ord(message[i]), LCD_CHR)


lcd_string(" No Intruder", LCD_LINE_1)
#################################################
recognizer = cv2.createLBPHFaceRecognizer()
recognizer.load('trainner/trainner.yml')
cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath);
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--picamera", type=int, default=1,
                help="jffj")
args = vars(ap.parse_args())
cam = PiVideoStream()
cam = cam.start()
time.sleep(.5)
font = cv2.cv.InitFont(cv2.cv.CV_FONT_HERSHEY_SIMPLEX, 1, 1, 0, 1, 1)
while (True):
    i = 0
    if i == 1:  # When output from motion sensor is HIGH
        print("Intruder Detected")
        GPIO.output(4, 1)  # Turn ON LED
        time.sleep(.5)
        GPIO.output(4, 0)
        lcd_string("Intruder Detect", LCD_LINE_1)
        lcd_string("    Room 1", LCD_LINE_2)
    img = cam.read()
    img = imutils.resize(img, width=450)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(gray, 1.2, 5)
    for (x, y, w, h) in faces:
        cv2.rectangle(img, (x, y), (x + w, y + h), (225, 0, 0), 2)
        Id, conf = recognizer.predict(gray[y:y + h, x:x + w])
        name = " "
        if (conf < 100):
            if (Id == 1):
                name = "Fabian"
            elif (Id == 2):
                name = "Fabian"
            elif (Id == 3):
                name = "Fabian"

        else:
            GPIO.output(4, 1)
            time.sleep(1)
            GPIO.output(4, 0)
            lcd_string("Intruder Detect", LCD_LINE_1)
            lcd_string("     Room 2", LCD_LINE_2)
            name = "Unknown"
            cv2.imwrite("Unknown" + ".jpg", img)
            email_user = ''
            email_password = ''
            email_send = ''
            subject = 'Intruder Detected'
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = email_send
            msg['Subject'] = subject
            body = 'There is someone in your home, please check the attached picture'
            msg.attach(MIMEText(body, 'plain'))
            filename = 'Unknown.jpg'
            attachment = open(filename, 'rb')
            part = MIMEBase('application', 'octet-stream')
            part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', "attachment; filename= " + filename)
            msg.attach(part)
            text = msg.as_string()
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_user, email_password)
            server.sendmail(email_user, email_send, text)
        server.quit()
        cv2.cv.PutText(cv2.cv.fromarray(img), str(name), (x, y + h), font, 255)
    cv2.imshow('Face', img)
    if cv2.waitKey(10) == ord('q'):
        break
lcd_byte(0x01, LCD_CMD)
lcd_string(" No Intruder", LCD_LINE_1)
time.sleep(1)
GPIO.cleanup()

cam.release()
cv2.destroyAllWindows()

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        pass
    finally:
        lcd_byte(0x01, LCD_CMD)
        lcd_string(" No Intruder", LCD_LINE_1)
        time.sleep(1)
        GPIO.cleanup()

