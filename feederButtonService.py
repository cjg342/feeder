#!/home/pi/venv/feeder/bin/python
import sys
sys.path.extend(['/home/pi/venv/feeder/feeder'])
import logging.handlers
import argparse
import time  # this is only being used as part of the example
import signal
import commonTasks
import RPi.GPIO as GPIO
import datetime
import ConfigParser
import os

dir = os.path.dirname(__file__)  # os.getcwd()
configFilePath = os.path.abspath(os.path.join(dir, "app.cfg"))
configParser = ConfigParser.RawConfigParser()
configParser.read(configFilePath)

feedButtonGPIO =configParser.get('feederConfig', 'feedButtonGPIO')
hopperGPIO =configParser.get('feederConfig', 'hopperGPIO')
hopperTime =configParser.get('feederConfig', 'hopperTime')
LOG_ButtonService_FILENAME=configParser.get('feederConfig', 'LOG_ButtonService_FILENAME')
delayBetweenButtonPushes=configParser.get('feederConfig', 'delayBetweenButtonPushes')

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="My simple Python service")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_ButtonService_FILENAME + "')")

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
        LOG_FILENAME = args.log


# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(logging.INFO) # Could be e.g. "DEBUG" or "WARNING"
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_ButtonService_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
        def __init__(self, logger, level):
                """Needs a logger and a logger level."""
                self.logger = logger
                self.level = level

        def write(self, message):
                # Only log if there is a message (not just a new line)
                if message.rstrip() != "":
                        self.logger.log(self.level, message.rstrip())

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)


class GracefulKiller:
  kill_now = False
  def __init__(self):
    signal.signal(signal.SIGINT, self.exit_gracefully)
    signal.signal(signal.SIGTERM, self.exit_gracefully)

  def exit_gracefully(self,signum, frame):
    self.kill_now = True

print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
print("Starting up")

print("Print welcome and Last feed time")
welcomeMessage = commonTasks.print_to_LCDScreen("Welcome!")
time.sleep(1)
lastFeedTime = commonTasks.print_to_LCDScreen(commonTasks.get_last_feedtime_string())

print("Create Gracekiller class")
killer = GracefulKiller()

print("Set up button for While Loop")
feedButton=int(feedButtonGPIO)
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.cleanup(feedButton)
GPIO.setup(feedButton,GPIO.IN,pull_up_down=GPIO.PUD_UP)

print("End Start up. Starting while loop")
print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
while True:
    ##Other way to log to log
    #logger.info("The counter is now " + str(i))
    if GPIO.input(feedButton) == 0:
            print "-------------------------------------------------------------------------"
            time.sleep(.1)
            buttonPressDatetime=datetime.datetime.now()
            print "Button was pressed at "+str(buttonPressDatetime)

            lastFeedDateCursor = commonTasks.db_get_last_feedtimes(1)
            lastFeedDateString = lastFeedDateCursor[0][0]
            lastFeedDateObject = datetime.datetime.strptime(lastFeedDateString, "%Y-%m-%d %H:%M:%S")
            print "Last feed time in DB was at " + str(lastFeedDateObject)

            tdelta = buttonPressDatetime - lastFeedDateObject
            print "Difference in seconds between two: " + str(tdelta.seconds)

            if tdelta.seconds < int(delayBetweenButtonPushes):
                print "Feed times closure than "+str(delayBetweenButtonPushes)+ " seconds. Hold off for now."
            else:
                # !!!!!!!!!!!!!!!!!!!!!!!!!put in code to check if return true=completed successfully!!!!!!!!!!!!!!!!!!!!!!!!!
                spin=commonTasks.spin_hopper(hopperGPIO,hopperTime)
                print "End Hopper return status: "+spin
                dblog=commonTasks.db_insert_feedtime(buttonPressDatetime,1)
                print "End DB Insert return status: "+dblog
                updatescreen=commonTasks.print_to_LCDScreen(commonTasks.get_last_feedtime_string())
                print "End Message Display return status: " + updatescreen
            print "-------------------------------------------------------------------------"
    if killer.kill_now:break
print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
print "End of the program. I was killed gracefully :)"
print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
