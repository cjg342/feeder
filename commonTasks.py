import sqlite3
import ConfigParser
import RPi.GPIO as GPIO
import time
from Adafruit_CharLCD import Adafruit_CharLCD
import datetime
import os
import subprocess

dir = os.path.dirname(__file__)  # os.getcwd()
# configFilePath=os.path.abspath(os.path.join(dir,"..")) #up one
configFilePath = os.path.abspath(os.path.join(dir, "app.cfg"))
configParser = ConfigParser.RawConfigParser()
configParser.read(configFilePath)
DB = str(configParser.get('feederConfig', 'DB'))


def connect_db():
    try:
        """Connects to the specific database."""
        rv = sqlite3.connect(DB)
        return rv
    except Exception,e:
        return e.message

def db_insert_feedtime(dateObject,complete):
    try:
        """Connects to the specific database."""
        datetime = dateObject.strftime('%Y-%m-%d %H:%M:%S')
        con = connect_db()
        cur = con.execute('''insert into feedtimes (feeddate,completed) values (?,?)''',[str(datetime), int(complete)])
        con.commit()
        cur.close()
        con.close()

        return 'ok'
    except Exception,e:
        return e.message
# def db_get_last_feedtime():
#     try:
#         """Connects to the specific database."""
#         con = connect_db()
#         cur = con.execute('''select feeddate from feedtimes where completed=1 order by feeddate desc limit 1''')
#         lastFeedDate=cur.fetchone()
#         lastFeedDate = lastFeedDate[0]
#         cur.close()
#         con.close()
#         return lastFeedDate

def db_get_last_feedtimes(numberToGet):
        con = connect_db()
        cur = con.execute(''' select feeddate,description
                            from feedtimes ft
                            join feedtypes fty on ft.completed=fty.feedtype
                            where completed<>0
                            order by feeddate desc
                            limit ?''', [str(numberToGet), ])
        LastFeedingTimes = cur.fetchall()
        cur.close()
        con.close()
        return LastFeedingTimes


def db_get_scheduled_feedtimes(numberToGet):
    con = connect_db()
    cur = con.execute(''' select feeddate,description
                            from feedtimes ft
                            join feedtypes fty on ft.completed=fty.feedtype
                            where completed=0
                            order by feeddate desc
                        limit ?''', [str(numberToGet), ])
    LastFeedingTimes = cur.fetchall()
    cur.close()
    con.close()
    return LastFeedingTimes


def get_last_feedtime_string():
    try:

        # Get last date from database
        lastFeedDateCursor=db_get_last_feedtimes(1)
        lastFeedDateString = lastFeedDateCursor[0][0]
        lastFeedDateObject = datetime.datetime.strptime(lastFeedDateString, "%Y-%m-%d %H:%M:%S")
        ## Test old dates
        # lastFeedDateObject=datetime.datetime.now() - datetime.timedelta(days=20)

        yesterdayDateObject = datetime.datetime.now() - datetime.timedelta(days=1)
        nowDateObject = datetime.datetime.now()
        verbiageString=''
        finalMessage=''
        if lastFeedDateObject.year == nowDateObject.year and lastFeedDateObject.month == nowDateObject.month and lastFeedDateObject.day == nowDateObject.day:
            verbiageString='Today'+' '+lastFeedDateObject.strftime("%I:%M %p")#+str('%02d' % lastFeedDateObject.hour)+':'+str('%02d' % lastFeedDateObject.minute)
        elif lastFeedDateObject.year == yesterdayDateObject.year and lastFeedDateObject.month == yesterdayDateObject.month and lastFeedDateObject.day == yesterdayDateObject.day:
            verbiageString='Yesterday'+' '+lastFeedDateObject.strftime("%I:%M %p").replace(' ','')#str('%02d' % lastFeedDateObject.hour)+':'+str('%02d' % lastFeedDateObject.minute)
        else:
            verbiageString=str(abs((nowDateObject - lastFeedDateObject).days))+' days ago!'#str('%02d' % lastFeedDateObject.month)+'-'+str('%02d' % lastFeedDateObject.day)+'-'+str(lastFeedDateObject.year)[2:]+' '+str('%02d' % lastFeedDateObject.hour)+':'+str('%02d' % lastFeedDateObject.minute)

        finalMessage='Last feed time:\n'+verbiageString
        return finalMessage
    except Exception, e:
        print e


def spin_hopper(pin,duration):
    try:
        pin=int(pin)
        duration=float(duration)
        GPIO.setwarnings(False)
        GPIO.cleanup(pin)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, GPIO.HIGH)
        GPIO.output(pin, GPIO.LOW)
        time.sleep(duration)
        GPIO.output(pin, GPIO.HIGH)
        GPIO.cleanup(pin)

        return 'ok'
    except Exception,e:
        return e


def print_to_LCDScreen (message):
    try:
        lcd = Adafruit_CharLCD()
        lcd.begin(16,2)
        for x in range(0, 16):
            for y in range(0, 2):
                lcd.setCursor(x, y)
                lcd.message('>')
                time.sleep(.025)
        lcd.noDisplay()
        lcd.clear()
        lcd.message(str(message))
        for x in range(0, 16):
            lcd.DisplayLeft()
        lcd.display()
        for x in range(0, 16):
            lcd.scrollDisplayRight()
            time.sleep(.05)
        # lcd.noDisplay()
        # lcd.display()
        # lcd.blink()
        # lcd.noCursor()
        # lcd.clear()
        # lcd.noBlink()
        # lcd.begin(16, 2)
        # lcd.setCursor(7, 0)
        # lcd.message('123')
        # lcd.message('x')
        # lcd.clear()
        return 'ok'
    except Exception,e:
        return e

