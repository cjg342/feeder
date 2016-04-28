#!/home/pi/venv/feeder/bin/python
from __future__ import with_statement
import sys
sys.path.extend(['/home/pi/venv/feeder/feeder'])
import sqlite3
import os
# import gpxpy
from flask import Flask, flash, Markup, redirect, render_template, request,Response, session, url_for
# from PIL import Image
# from pytz import timezone
# import pytz
import random
import string
import subprocess
import datetime
from subprocess import call
from subprocess import check_output
# from werkzeug import check_password_hash, generate_password_hash
import commonTasks
import os
# emulated camera
#from camera import Camera
# Raspberry Pi camera module (requires picamera package)
#from camera_pi import Camera
import ConfigParser
import datetime

app = Flask(__name__)
#app.config.from_pyfile('../app.cfg')

# create table feedtimes (feedid integer primary key autoincrement,feeddate string,completed integer);

dir = os.path.dirname(__file__)  # os.getcwd()
# configFilePath=os.path.abspath(os.path.join(dir,"..")) #up one
configFilePath = os.path.abspath(os.path.join(dir, "app.cfg"))
configParser = ConfigParser.RawConfigParser()
configParser.read(configFilePath)
SECRETKEY = str(configParser.get('feederConfig', 'SECRETKEY'))
hopperGPIO =str(configParser.get('feederConfig', 'hopperGPIO'))
hopperTime =str(configParser.get('feederConfig', 'hopperTime'))



@app.route('/', methods=['GET', 'POST'])
def home_page():
    try:
        # return render_template('home1.html')

        latestXNumberFeedTimes=commonTasks.db_get_last_feedtimes(5)
        upcomingXNumberFeedTimes=commonTasks.db_get_scheduled_feedtimes(5)

        finalFeedTimeList = []
        for x in latestXNumberFeedTimes:
            x = list(x)
            dateobject = datetime.datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S')
            x[0] = dateobject.strftime("%m-%d-%y %I:%M:%S %p")
            x = tuple(x)
            finalFeedTimeList.append(x)

        finalUpcomingFeedTimeList = []
        for x in upcomingXNumberFeedTimes:
            x = list(x)
            dateobject = datetime.datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S')
            x[0] = dateobject.strftime("%m-%d-%y %I:%M:%S %p")
            x = tuple(x)
            finalUpcomingFeedTimeList.append(x)

        ipAddress = request.remote_addr
        cameraSiteAddress=''
        if str(ipAddress).startswith('192.'):
            cameraSiteAddress='http://192.168.0.113:8080/html/'
        else:
            cameraSiteAddress = 'http://cjg342.duckdns.org:8080/html/'

        return render_template('home.html',latestXNumberFeedTimes=finalFeedTimeList
                               ,upcomingXNumberFeedTimes=finalUpcomingFeedTimeList
                               ,cameraSiteAddress=cameraSiteAddress
                               )

    except Exception,e:
        return render_template('error.html',resultsSET=e)



@app.route('/admin', methods=['GET', 'POST'])
def admin_page():
    try:
        # active (running) since Sat 2016-04-16 22:50:59 PDT; 364ms ago
        buttonServiceFullOutput = ControlService('feederButtonService', 'status')
        buttonServiceFinalStatus = CleanServiceStatusOutput(buttonServiceFullOutput)

        timeServiceFullOutput = ControlService('feederTimeService', 'status')
        timeServiceFinalStatus = CleanServiceStatusOutput(timeServiceFullOutput)

        return render_template('admin.html'
                               ,buttonServiceFinalStatus=buttonServiceFinalStatus
                               ,timeServiceFinalStatus=timeServiceFinalStatus)
        #return render_template('home.html', LatestXNumberFeedTimes=LatestXNumberFeedTimes,dir=dir,fd=fd)

    except Exception,e:
        return render_template('error.html',resultsSET=e)



@app.route('/feedbuttonclick', methods=['GET', 'POST'])
def feedbuttonclick():
    try:

        dateNowObject = datetime.datetime.now()
        spin = commonTasks.spin_hopper(hopperGPIO, hopperTime)
        dbInsert=commonTasks.db_insert_feedtime(dateNowObject,2)
        updatescreen = commonTasks.print_to_LCDScreen(commonTasks.get_last_feedtime_string())

        flash('Feed success!')
        return redirect(url_for('home_page'))
    except Exception,e:
        return render_template('error.html',resultsSET=e)


@app.route('/scheduleDatetime', methods=['GET', 'POST'])
def scheduleDatetime():
    try:
        scheduleDatetime = [request.form['scheduleDatetime']][0]
        dateobject=datetime.datetime.strptime(scheduleDatetime,'%Y-%m-%dT%H:%M')
        dbInsert = commonTasks.db_insert_feedtime(dateobject, 0)

        flash("Time Scheduled!")
        return redirect(url_for('home_page'))
    except Exception,e:
        return render_template('error.html',resultsSET=e)

@app.route('/deleteRow/<history>', methods=['GET', 'POST'])
def deleteRow(history):
    try:
        deleteRowFromDB=deleteUpcomingFeedingTime(history)
        flash("Scheduled time "+str(history)+" deleted!")
        return redirect(url_for('home_page'))

    except Exception,e:
        return render_template('error.html',resultsSET=e)




@app.route('/startButtonService', methods=['GET', 'POST'])
def startButtonService():
    try:
        myLogTimeServiceFullOutput=ControlService('feederButtonService','start')

        flash('Button Service Started!')
        return redirect(url_for('admin_page'))
    except Exception,e:
        return render_template('error.html',resultsSET=e)


@app.route('/stopButtonService', methods=['GET', 'POST'])
def stopButtonService():
    try:
        myLogTimeServiceFullOutput=ControlService('feederButtonService','stop')

        flash('Button Service Stopped!')
        return redirect(url_for('admin_page'))
    except Exception,e:
        return render_template('error.html',resultsSET=e)

@app.route('/startTimeService', methods=['GET', 'POST'])
def startTimeService():
    try:
        myLogTimeServiceFullOutput = ControlService('feederTimeService', 'start')

        flash('Time Service Started!')
        return redirect(url_for('admin_page'))
    except Exception, e:
        return render_template('error.html', resultsSET=e)

@app.route('/stopTimeService', methods=['GET', 'POST'])
def stopTimeService():
    try:
        myLogTimeServiceFullOutput = ControlService('feederTimeService', 'stop')

        flash('Time Service Stopped!')
        return redirect(url_for('admin_page'))
    except Exception, e:
        return render_template('error.html', resultsSET=e)
# ----------------------------------WEBSITE ONLY METHODS
# def LastFeedingTimes(numberToGet):
#     try:
#         con=commonTasks.connect_db()
#         cur=con.execute(''' select feeddate,completed
#                             from feedtimes
#                             where completed<>0
#                             order by feeddate desc
#                             limit ?''',[str(numberToGet),])
#         LastFeedingTimes = cur.fetchall()
#         cur.close()
#         con.close()
#         return LastFeedingTimes
#     except Exception,e:
#         return render_template('error.html',resultsSET=e)

# def UpcomingFeedingTimes(numberToGet):
#     try:
#         con=commonTasks.connect_db()
#         cur=con.execute(''' select feeddate
#                             from feedtimes
#                             where completed=0
#                             order by feeddate
#                             limit ?''',[str(numberToGet),])
#         UpcomingFeedingTimes = cur.fetchall()
#         cur.close()
#         con.close()
#         return UpcomingFeedingTimes
#     except Exception,e:
#         return render_template('error.html',resultsSET=e)


def deleteUpcomingFeedingTime(dateToDate):
    try:
        con = commonTasks.connect_db()
        cur = con.execute("""delete from feedtimes where feeddate=?""",[str(dateToDate),])
        con.commit()
        cur.close()
        con.close()
        return True
    except Exception,e:
        return render_template('error.html',resultsSET=e)

def ControlService(serviceToCheck,command):
    try:

        process = subprocess.Popen(["sudo", "service", serviceToCheck, command],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
        return process.stdout.read()


    except Exception,e:
        return render_template('error.html',resultsSET=e)

def CleanServiceStatusOutput(serviceOutput):
    try:

        buttonServiceStartString = serviceOutput.find('Active:') + len('Active:')
        buttonServiceEndString = serviceOutput.find('\n', buttonServiceStartString)
        buttonServiceFinalStatus = serviceOutput[buttonServiceStartString:buttonServiceEndString]
        buttonServiceStartString = buttonServiceFinalStatus.find('since')
        buttonServiceEndString = buttonServiceFinalStatus.find('; ', buttonServiceStartString)
        buttonServiceFinalStatus = str(buttonServiceFinalStatus).replace(
        buttonServiceFinalStatus[buttonServiceStartString:buttonServiceEndString], '')

        return buttonServiceFinalStatus


    except Exception,e:
        return render_template('error.html',resultsSET=e)



app.secret_key = SECRETKEY

#main
if __name__ == '__main__':
    app.debug=False #reload on code changes. show traceback
    app.run(host='0.0.0.0',threaded=True)
