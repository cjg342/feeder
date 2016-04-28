import os, sys
 
activate_this = '/home/pi/venv/feeder/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

sys.path.append('/home/pi/venv/feeder/feeder')
 
from app import app as application

home='/home/pi/venv/feeder/feeder'
