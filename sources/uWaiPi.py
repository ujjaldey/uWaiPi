#!/usr/bin/env python
# -*- coding: utf-8 -*-

###################################################################################################
#      __        __    _ ____  _
#  _   \ \      / /_ _(_)  _ \(_)
# | | | \ \ /\ / / _` | | |_) | |
# | |_| |\ V  V / (_| | |  __/| |
#  \__,_| \_/\_/ \__,_|_|_|   |_|
#
# Copyright (c) 2016 Ujjal Dey
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
# and associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or 
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING
# BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###################################################################################################

##########################################################################################
# Import modules.
##########################################################################################
import ConfigParser
import datetime
import i2cDriver
import os
import smtplib
import socket
import Crypto.Cipher.AES as AES
import RPi.GPIO as GPIO
from asyncFunc import async
from time import time, sleep

#########################################################################################
# Declare constants.
##########################################################################################
# Generic parameters
APP_NAME = "uWaiPi"
DEFAULT_TIMEKEEPER_VALUE = "27-05-2016 00:00|0"
NEWLINE_CHAR = "\n"
SCREEN_REFRESH_FREQ_SEC = 2
DISPLAY_RESET_SEC = 3600

# File details
TIMEKEEPER_FILE = ".timekeeper"
TIMEKEEPER_HISTORY_FILE = ".timekeeperHist"
PARAMETER_FILE = "parameter.lst"
SMTP_FILE = ".smtpDetails"

# GPIO pin configurations
GPIO_PIN_SWITCH = 7
GPIO_PIN_DISPLAY_CONTROL = 12
GPIO_PIN_BUTTON_WAKEUP = 11
GPIO_PIN_BUTTON_RUN_NOW = 13
GPIO_PIN_BUTTON_RUN_SKIP = 15

# GPIO on-off states
GPIO_ON_STATE = 1
GPIO_OFF_STATE = 0

# Button debounce time
BUTTON_DEBOUNCE_SEC = 500

# Exit status codes
EXIT_CODE_SUCCESS = 0
EXIT_CODE_FAILURE_SCHEDULE_FILE = 1
EXIT_CODE_FAILURE_SMTP_FILE = 2

# Log types
LOG_TYPE_ERROR = "E"
LOG_TYPE_WARNING = "W"
LOG_TYPE_INFO = "I"

##########################################################################################
# Gets the parameter values from the parameter.lst and .smtpDetails.
##########################################################################################
def getConfigDetails():
	paramConfig.read(PARAMETER_FILE)
	smtpConfig.read(SMTP_FILE)

##########################################################################################
# Reads a specific parameter value based on the parameter name.
##########################################################################################
def readParameterConfigValue(paramName):
	try:
		# Checks if it is a BasicConfig parameter or not
		paramValue = paramConfig.get("BasicConfig", paramName)
	except ConfigParser.NoOptionError:
		try:
			# If not, checks if it is a AdvanceConfig parameter or not
			paramValue = paramConfig.get("AdvanceConfig", paramName)
		except ConfigParser.NoOptionError:
			# Otherwise the parameter value is null
			paramValue = ""

	return paramValue

##########################################################################################
# Sets and initializes the GPIO pins.
##########################################################################################
def setGPIO():
	GPIO.setmode(GPIO.BOARD)
	GPIO.setwarnings(False)

	# Sets the output pin
	GPIO.setup(GPIO_PIN_SWITCH, GPIO.OUT)
	GPIO.setup(GPIO_PIN_DISPLAY_CONTROL, GPIO.OUT)
	# Sets the input pin
	GPIO.setup(GPIO_PIN_BUTTON_WAKEUP, GPIO.IN)
	GPIO.setup(GPIO_PIN_BUTTON_RUN_NOW, GPIO.IN)
	GPIO.setup(GPIO_PIN_BUTTON_RUN_SKIP, GPIO.IN)

	# Sets the events on clicking he input buttons
	GPIO.add_event_detect(GPIO_PIN_BUTTON_WAKEUP, GPIO.RISING, callback=wakeupDisplay, bouncetime=BUTTON_DEBOUNCE_SEC)
	GPIO.add_event_detect(GPIO_PIN_BUTTON_RUN_NOW, GPIO.RISING, callback=triggerSwitchAdhoc, bouncetime=BUTTON_DEBOUNCE_SEC)
	GPIO.add_event_detect(GPIO_PIN_BUTTON_RUN_SKIP, GPIO.RISING, callback=skipNextRun, bouncetime=BUTTON_DEBOUNCE_SEC)

##########################################################################################
# Unsets the GPIO pins.
##########################################################################################
def unsetGPIO():
	GPIO.cleanup()
	
##########################################################################################
# Callback function for GPIO_PIN_BUTTON_WAKEUP button.
##########################################################################################
def wakeupDisplay(channel):
	global displayOn
	global counterDisplayOnOff

	# Updates the displayOn flag to True.
	# This flag is used in __main__ function for controlling the screen display
	displayOn = True
	counterDisplayOnOff = 0

##########################################################################################
# Callback function for GPIO_PIN_BUTTON_RUN_NOW button.
##########################################################################################
def triggerSwitchAdhoc(channel):
	global runNow
	global runActive

	try:
		# Enables the button only the system is not active
		if (not runActive):
			# Updates the runNow flag to True.
			# This flag is used in __main__ function for adhoc trigger
			runNow = True
	finally:
		return
	
##########################################################################################
# Callback function for GPIO_PIN_BUTTON_RUN_SKIP button.
##########################################################################################
def skipNextRun(channel):
	global runActive

	try:
		# Enables the button only the system is not active
		if (not runActive):
			# Gets the upcoming schedule from the .timekeeper file
			currSchedule, currDuration = readTimekeeperFile()
			upcomingSchedule = datetime.datetime.strptime(currSchedule, "%d-%m-%Y %H:%M")

			# Gets the next schedule considering the upcoming schedule
			global scheduleTimeList
			today = datetime.datetime.strptime(currSchedule, "%d-%m-%Y %H:%M").strftime("%d-%m-%Y")
			scheduleList = [datetime.datetime.strptime(str, "%d-%m-%Y %H:%M") for str in [today + " " + hrMi for hrMi in scheduleTimeList]]
			firstScheduleTomorrow = datetime.datetime.strptime(today + " " + scheduleTimeList[0], "%d-%m-%Y %H:%M") + datetime.timedelta(days=1)
			nextSchedule, nextDuration = getNextScheduleDetail(scheduleList, durationList, firstScheduleTomorrow, upcomingSchedule)
			
			# Updates the next schedule in .timekeeper file
			updateTimekeeperFile(nextSchedule.strftime("%d-%m-%Y %H:%M"), nextDuration)
	finally:
		# Wakes up the screen
		wakeupDisplay(channel)

##########################################################################################
# Gets the current date and time.
##########################################################################################
def getCurrentTime():
	return datetime.datetime.fromtimestamp(time())

##########################################################################################
# Prints the debugging line in console and/or log file.
##########################################################################################
def debugger(message, logType = LOG_TYPE_INFO, timestampEnabled = True, printable = "", loggable = ""):
	#Gets the default parameter value if not passed
	if (printable == ""):
		printable = CONSOLE_OUTPUT_ENABLED

	if (loggable == ""):
		loggable = LOG_OUTPUT_ENABLED

	# Prints in the console, if enabled
	if (printable):
		print (message)
	
	# Logs in the file, if enabled
	if (loggable):
		logWriter(message, logType, timestampEnabled)

##########################################################################################
# Writes the data into a log file.
##########################################################################################
def logWriter(message, logType = LOG_TYPE_INFO, timestampEnabled = True):
	# Appends the log type, if set
	if (logType):
		message = logType + "|" + message
	if (LOG_FILE):
		# Writes into the log file
		logFile = open(LOG_FILE, "a")
		if (timestampEnabled):
			message = getCurrentTime().strftime("%d-%m-%Y %H:%M:%S") + "|" + message
		logFile.write(message + NEWLINE_CHAR)
		logFile.close()
	
##########################################################################################
# Checks if a given file exists in the path.
##########################################################################################
def checkIfFileExists(fileName):
	return True if ((os.path.isfile(fileName)) and (os.path.getsize(fileName) > 0)) else False

##########################################################################################
# Creats the timekeeper file if not exists or zero sized. Uses the default value as the 
# content.
##########################################################################################
def createTimekeeperFile():
	# Writes into the timekeeper file
	timekeeperFile = open(TIMEKEEPER_FILE, "w")
	timekeeperFile.write(DEFAULT_TIMEKEEPER_VALUE)
	timekeeperFile.close()

	debugger("Timekeeper file '%s' created." % (TIMEKEEPER_FILE))

##########################################################################################
# Creats the history timekeeper file if not exists or zero sized. Uses the default value as the 
# content.
##########################################################################################
def createHistoryTimekeeperFile():
	# Writes into the timekeeper file
	timekeeperFile = open(TIMEKEEPER_HISTORY_FILE, "w")
	timekeeperFile.write(DEFAULT_TIMEKEEPER_VALUE)
	timekeeperFile.close()

	debugger("History timekeeper file '%s' created." % (TIMEKEEPER_HISTORY_FILE))

##########################################################################################
# Reads the schedule file and returns the content as list.
##########################################################################################
def readSchedulerFile():
	# Reads the schedule file
	schedulerFile = open(SCHEDULER_FILE, "r")
	lines = schedulerFile.read().splitlines() 
	schedulerFile.close()
	return lines

##########################################################################################
# Reads the timekeeper file and returns the next schedule time and duration.
##########################################################################################
def readTimekeeperFile():
	# Reads the timekeeper file
	timekeeperFile = open(TIMEKEEPER_FILE, "r")
	schedule, duration = timekeeperFile.read().rstrip(NEWLINE_CHAR).split("|")
	timekeeperFile.close()
	return schedule, int(duration)

##########################################################################################
# Reads the history timekeeper file and returns the next schedule time and duration.
##########################################################################################
def readHistoryTimekeeperFile():
	# Reads the timekeeper file
	timekeeperFile = open(TIMEKEEPER_HISTORY_FILE, "r")
	schedule, duration = timekeeperFile.read().rstrip(NEWLINE_CHAR).split("|")
	timekeeperFile.close()
	return schedule, int(duration)

##########################################################################################
# Sends email asynchronously. Gets all the details from parameter.lst and .smtpDetails files
##########################################################################################
@async
def sendEmail(subject):
	# Checks if email is enabled or not
	if (EMAIL_ENABLED == "Y"):
		sleep(0.1)

		try:
			# Composes the mail string
			mailStr = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (SMTP_USER_ID, ", ".join(EMAIL_RECEIVER_ADDRESS.split(",")), subject + " [" + getCurrentTime().strftime("%d-%m-%Y %H:%M:%S") + "]")
			mailStr += "Hey there!\n\nBelow are the last %s lines from the log file:\n\n" % EMAIL_LOG_LINE

			# Gets the lines from the log file and appends into the email's body
			stdin, stdout = os.popen2("tail -%s %s" % (EMAIL_LOG_LINE, LOG_FILE))
			lines = stdout.readlines()
			stdin.close()
			stdout.close()

			mailStr += "-----------------------\n"
			mailStr += "".join(lines)
			mailStr += "-----------------------"
			mailStr += "\n\n\nRegards,\nuWaiPi"

			# SMPT server details
			server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
			server.starttls()
			server.ehlo()
			server.login(SMTP_USER_ID, SMTP_USER_PASSWORD)
			server.set_debuglevel(0)
			# Sends the email
			server.sendmail(SMTP_USER_ID, EMAIL_RECEIVER_ADDRESS.replace(" ", "").split(","), mailStr)
			server.quit()

			debugger ("Mail sent.")
		except:
			debugger ("Mail could not be sent.", LOG_TYPE_ERROR)

##########################################################################################
# Gets the next schedule time and duration. Runs through the list of schedules and breaks
# once the immediate next schedule is found. If the current time is still greater than
# the max of the schedules in the list, it takes the first schedule in the next day.
# This helps in getting the first schedule of the next day during the date change.
##########################################################################################
def getNextScheduleDetail(scheduleList, durationList, firstScheduleTomorrow, currTime):
	nextSchedule = ""
	scheduleIndex = 0

	# Loops through the list of schedules
	for counter in range(len(scheduleList)):
		if (scheduleList[counter] > currTime):
			scheduleIndex = counter
			nextSchedule = scheduleList[counter]
			break

	# If no next schedule found for the current date, it gets the first schedule from the next day
	if (nextSchedule == ""):
		nextSchedule = firstScheduleTomorrow

	return nextSchedule, durationList[scheduleIndex]

##########################################################################################
# Switches on the system by setting the GPIO_PIN_SWITCH pin to higher state.
##########################################################################################
def switchOn():
	GPIO.output(int(GPIO_PIN_SWITCH), GPIO_ON_STATE)
	debugger("Switched on.")

##########################################################################################
# Switches off the system by setting the GPIO_PIN_SWITCH pin to lower state.
##########################################################################################
def switchOff():
	GPIO.output(int(GPIO_PIN_SWITCH), GPIO_OFF_STATE)
	debugger("Switched off.")

##########################################################################################
# Triggers the switch asynchronously. It first switches on the system, then keep it on for
# certain duration, and then switches it off. Also calculates the next schedule and duration
# and updates the timekeeper file accordingl the next schedule and duration
# and updates the timekeeper file accordingly.
##########################################################################################
@async
def triggerSwitch(currSchedule, currDuration, durationList, adhocRun = False):
	try:
		sleep(.5)
		# Switches on the system
		switchOn()
		# Runs through a loop for displaying the active message
		for counter in range(currDuration):
			displayActiveMsg(currDuration - counter - 1, counter)
			sleep(.7)
		# Switches off the system
		switchOff()

		# Gets the next execution schedule and duration
		nextSchedule, nextDuration = getNextExecutionDetail(currSchedule, currDuration, durationList)

		# Logs the event
		if (adhocRun):
			debugger("Triggered (Adhoc). Current schedule: [%s, %s sec]. Next schedule:[%s, %s sec]." % (currSchedule, currDuration, nextSchedule,  nextDuration))
		else:
			debugger("Triggered. Current schedule: [%s, %s sec]. Next schedule:[%s, %s sec]." % (currSchedule, currDuration, nextSchedule,  nextDuration))

		# Updates the timekeeper files with the next schedule and duration
		updateTimekeeperFile(nextSchedule, nextDuration)
		updateHistoryTimekeeperFile(currSchedule, currDuration)

		# Sends email and display message
		sendEmail(EMAIL_SUBJECT_ACTIVE)
		displayEmailMsg()
	except KeyboardInterrupt:
		return

##########################################################################################
# Fetches the schedule list internally and calls getNextScheduleDetail() for getting the 
# next schedule and duration.
##########################################################################################
def getNextExecutionDetail(currSchedule, currDuration, durationList):
	# Gets today's date and the schedule list
	today = datetime.datetime.fromtimestamp(time()).strftime("%d-%m-%Y")
	scheduleList = [datetime.datetime.strptime(str, "%d-%m-%Y %H:%M") for str in [today + " " + hrMi for hrMi in scheduleTimeList]]

	# Gets the first schedule from tomorrow
	firstScheduleTomorrow = datetime.datetime.strptime(today + " " + scheduleTimeList[0], "%d-%m-%Y %H:%M") + datetime.timedelta(days=1)

	# Get the next schedule and duration
	nextSchedule, nextDuration = getNextScheduleDetail(scheduleList, durationList, firstScheduleTomorrow, getCurrentTime())
	nextSchedule = nextSchedule.strftime("%d-%m-%Y %H:%M")
	
	return nextSchedule, nextDuration

##########################################################################################
# Writes the next schedule and duration in the timekeeper file.
##########################################################################################
def updateTimekeeperFile(nextSchedule, nextDuration):
	sleep(.05)
	tkFile = open(TIMEKEEPER_FILE, "w")
	tkFile.write("%s|%s" % (nextSchedule, nextDuration))
	tkFile.close()
	sleep(.1)

##########################################################################################
# Writes the last schedule and duration in the history timekeeper file.
##########################################################################################
def updateHistoryTimekeeperFile(lastSchedule, lastDuration):
	sleep(.05)
	tkFile = open(TIMEKEEPER_HISTORY_FILE, "w")
	tkFile.write("%s|%s" % (lastSchedule, lastDuration))
	tkFile.close()
	sleep(.1)

##########################################################################################
# Controls whether to switch on the LCD or not. The GPIO pin GPIO_PIN_DISPLAY_CONTROL
# should be connected to the Base of 2N-2222 transistor.
##########################################################################################
def controlDisplayOnOff(onFlg):
	GPIO.output(GPIO_PIN_DISPLAY_CONTROL, onFlg)

##########################################################################################
# Greets the user with Morning/Afternoon/Evening while displaying the welcome message
##########################################################################################
def greetingTime():
	timeStr = ""
	thisTime = getCurrentTime()

	if (thisTime.hour < 12):
		timeStr = "Morning"
	elif (12 <= thisTime.hour < 18):
		timeStr = "Afternoon"
	else:
		timeStr = "Evening"

	return "Good " + timeStr + "!"

##########################################################################################
# Displays the welcome message upon starting.
##########################################################################################
def displayWelcomeMsg():
	sleep(.05)
	controlDisplayOnOff(True)
	lcd.lcd_clear()
	for i in range(len(APP_NAME)):
		lcd.lcd_display_string_pos(APP_NAME[i], 1, i)
		sleep(.3)
	lcd.lcd_display_string_pos("-Ujjal Dey", 2, 6)
	sleep(2)
	lcd.lcd_clear()
	lcd.lcd_display_string(greetingTime(), 1)
	lcd.lcd_display_string(" " + USER_NAME, 2)
	sleep(3)
	lcd.lcd_clear()

##########################################################################################
# Displays the running message alternatively. Loops through the Next Run and the Current
# Time values.
##########################################################################################
def displayRunningMsg(currTime, lastSchedule, lastDuration, nextSchedule, nextDuration):
	global runningMsgInd
	sleep(.05)

	try:
		lcd.lcd_clear()

		# Displays the Next Run and the Current time based on runningMsgInd
		if (runningMsgInd == 0):
			lcd.lcd_display_string("Last run (%is):" % (lastDuration), 1)
			lcd.lcd_display_string(lastSchedule, 2)
			runningMsgInd += 1
		elif (runningMsgInd == 1):
			lcd.lcd_display_string("Current time:", 1)
			lcd.lcd_display_string(currTime.strftime("%d-%m-%Y %H:%M"), 2)
			runningMsgInd += 1
		else:
			lcd.lcd_display_string("Next run (%is):" % (nextDuration), 1)
			lcd.lcd_display_string(nextSchedule, 2)
			runningMsgInd = 0
	except KeyboardInterrupt:
		return

##########################################################################################
# Displays the message while the system is switched on. This function is called in loop
# to display the running counter.
##########################################################################################
def displayActiveMsg(timeLeft, counter):
	sleep(.05)
	
	try:
		# Displays the time left
		if (counter == 0):
			lcd.lcd_clear()
			lcd.lcd_display_string("Activating...", 1)
			sleep(.5)

		lcd.lcd_clear()
		lcd.lcd_display_string("Activated!", 1)
		lcd.lcd_display_string("Time left: %is" % timeLeft, 2)
	except KeyboardInterrupt:
		return

##########################################################################################
# Displays a message before starting the adhoc run.
##########################################################################################
def displayAdhocRunMsg():
	sleep(.05)
	lcd.lcd_clear()
	lcd.lcd_display_string("Adhoc run....", 1)
	sleep(.1)

##########################################################################################
# Displays a message while sending emails.
##########################################################################################
def displayEmailMsg():
	sleep(.05)
	lcd.lcd_clear()
	lcd.lcd_display_string("Sending email...", 1)
	sleep(.1)

##########################################################################################
# Displays the goodbye message upon closing/terminating the system.
##########################################################################################
def displayGoodbyeMsg():
	sleep(.05)
	lcd.lcd_clear()
	controlDisplayOnOff(True)
	lcd.lcd_display_string("Good bye...", 1)
	sleep(2)
	lcd.lcd_clear()
	controlDisplayOnOff(False)

##########################################################################################
# Displays the restart message upon receiving restart sygnal.
##########################################################################################
def displayRestartMsg():
	sleep(.05)
	lcd.lcd_clear()
	controlDisplayOnOff(True)
	lcd.lcd_display_string("Restarting...", 1)
	sleep(2)
	lcd.lcd_clear()
	controlDisplayOnOff(False)

##########################################################################################
# Displays the error message upon failing the validations.
##########################################################################################
def displayErrorMsg(msgStr):
	sleep(.05)
	lcd.lcd_clear()
	controlDisplayOnOff(True)
	lcd.lcd_display_string("Error...", 1)
	lcd.lcd_display_string(msgStr[:16], 2)
	sleep(2)
	lcd.lcd_clear()
	displayGoodbyeMsg()

##########################################################################################
# Initializes the socket.
##########################################################################################
def initializeSocket():
	soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	soc.bind(("localhost", int(SOCKET_LISTENER_PORT)))
	soc.listen(1)
	soc.settimeout(.01)
	return soc

##########################################################################################
# Keep listening to the socket for any incoming messages. Once any message is received,
# it calls triggerAction() method to trigger the appropriate methods.
##########################################################################################
def socketListener(soc):
	try:
		conn, addr = soc.accept()
		conn.settimeout(.01)
		data = conn.recv(1024)
		conn.close()
		triggerAction(data)
	except:
		pass

##########################################################################################
# Calls the appropriate methods based on the listener commands.
##########################################################################################
def triggerAction(command):
	channel = ""
	debugger("Command received for %s" % (command))
	sleep(.2)

	if (command == "RUN_NOW"):
		triggerSwitchAdhoc(channel)
	elif (command == "SKIP_NEXT"):
		skipNextRun(channel)
	elif (command == "SEND_LOG"):
		sendEmail(EMAIL_SUBJECT_RUN)
		displayEmailMsg()
	elif (command == "RESTART"):
		global keepRunning
		global restart
		keepRunning = False
		restart = True

###################################################################################################
###################################################################################################
###################################################################################################

##########################################################################################
# Main program starts here.
##########################################################################################
if (__name__ == "__main__"):
	# Loads the LCD driver
	lcd = i2cDriver.lcd()
	# Creates an object for crypt
	crypt = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')

	# Sets to read the config files
	paramConfig = ConfigParser.RawConfigParser()
	smtpConfig = ConfigParser.RawConfigParser()
	getConfigDetails()
	# Sets the GPIO pins
	setGPIO()

	# Declares the variables with values from parameter file
	USER_NAME = readParameterConfigValue("USER_NAME")
	EMAIL_ENABLED = readParameterConfigValue("EMAIL_ENABLED")
	RUN_LOG_FREQ_SEC = long(readParameterConfigValue("RUN_LOG_FREQ_SEC"))
	DISPLAY_OFF_DELAY_SEC = long(readParameterConfigValue("DISPLAY_OFF_DELAY_SEC"))
	HEARTBEAT_SEC = float(readParameterConfigValue("HEARTBEAT_SEC"))
	ADHOC_RUN_DURATION_SEC = readParameterConfigValue("ADHOC_RUN_DURATION_SEC")
	SCHEDULER_FILE = readParameterConfigValue("SCHEDULER_FILE")
	LOG_FILE = readParameterConfigValue("LOG_FILE")
	LOG_OUTPUT_ENABLED = True if (readParameterConfigValue("LOG_OUTPUT_ENABLED") == "Y") else False
	CONSOLE_OUTPUT_ENABLED = True if (readParameterConfigValue("CONSOLE_OUTPUT_ENABLED") == "Y") else False
	SOCKET_LISTENER_PORT = readParameterConfigValue("SOCKET_LISTENER_PORT")

	# If email is enabled
	if (EMAIL_ENABLED == "Y"):
		EMAIL_RECEIVER_ADDRESS = readParameterConfigValue("EMAIL_RECEIVER_ADDRESS")
		EMAIL_SUBJECT_RUN = readParameterConfigValue("EMAIL_SUBJECT_RUN")
		EMAIL_SUBJECT_ACTIVE = readParameterConfigValue("EMAIL_SUBJECT_ACTIVE")
		EMAIL_LOG_LINE = readParameterConfigValue("EMAIL_LOG_LINE")
		EMAIL_FREQ_SEC = long(readParameterConfigValue("EMAIL_FREQ_SEC"))
	else:
		EMAIL_RECEIVER_ADDRESS = ""
		EMAIL_SUBJECT_RUN = ""
		EMAIL_SUBJECT_ACTIVE = ""
		EMAIL_LOG_LINE = ""
		EMAIL_FREQ_SEC = 0

	# Initializes the socket for receiving messages
	soc = initializeSocket()

	debugger("", "", False)
	debugger(APP_NAME + " started.")

	displayWelcomeMsg()

	lcd.lcd_clear_line(2)
	lcd.lcd_display_string("Validating...", 1)
	sleep(.2)

	# Checks if scheduler file is present and non-empty. Else exit from the system.
	if (not checkIfFileExists(SCHEDULER_FILE)):
		debugger ("Scheduler file '%s' is either not found or empty." % (SCHEDULER_FILE), LOG_TYPE_ERROR)
		displayErrorMsg("No schedule file")
		exit (EXIT_CODE_FAILURE_SCHEDULE_FILE)

	# Checks if SMTP file is present and non-empty if email flag is on. Else exit from the system.
	if ((EMAIL_ENABLED == "Y") and (not checkIfFileExists(SMTP_FILE))):
		debugger ("SMTP file '%s' is either not found or empty. Please run 'python createSmtpFile.pyc' first." % (SMTP_FILE), LOG_TYPE_ERROR)
		displayErrorMsg("No SMTP file")
		exit (EXIT_CODE_FAILURE_SMTP_FILE)
	elif ((EMAIL_ENABLED == "Y") and (checkIfFileExists(SMTP_FILE))):
		SMTP_USER_ID = smtpConfig.get("SMTP", "SMTP_USER_ID")
		SMTP_USER_PASSWORD = crypt.decrypt(smtpConfig.get("SMTP", "SMTP_USER_PASSWORD")).strip()
		SMTP_SERVER = smtpConfig.get("SMTP", "SMTP_SERVER")
		SMTP_PORT = smtpConfig.get("SMTP", "SMTP_PORT")
	else:
		SMTP_USER_ID = ""
		SMTP_USER_PASSWORD = ""
		SMTP_SERVER = ""
		SMTP_PORT = ""

	# Checks if timekeeper files is present and non-empty. Else creates a new timekeeper file with default value.
	if (not checkIfFileExists(TIMEKEEPER_FILE)):
		debugger ("Timekeeper file '%s' is either not found or empty." % (TIMEKEEPER_FILE), LOG_TYPE_WARNING)
		createTimekeeperFile()
	if (not checkIfFileExists(TIMEKEEPER_HISTORY_FILE)):
		debugger ("History timekeeper file '%s' is either not found or empty." % (TIMEKEEPER_HISTORY_FILE), LOG_TYPE_WARNING)
		createHistoryTimekeeperFile()

	lcd.lcd_clear_line(2)
	lcd.lcd_display_string("Starting...", 1)
	sleep(.5)
	lcd.lcd_clear()
	sleep(.1)

	# Reads the scheduler file. Creates two lists for schedule times and the durations
	schedulerFileContent = readSchedulerFile()
	scheduleTimeList = [str.split("|")[0] for str in schedulerFileContent]
	durationList = [str.split("|")[1] for str in schedulerFileContent]

	try:
		# Initializes the variables
		keepRunning = True
		restart = False
		runActive = False
		displayOn = True
		runNow = False
		adhocRun = False
		runningMsgInd = 0
		counterScreenRefresh = 0
		counterRunningLog = 0
		counterSendEmail = 0
		counterDisplayOnOff = 0
		counterDisplayReset = 0

		# Starts the infinite loop
		while keepRunning:
			# Listen to socket for receiving the messages
			socketListener(soc)

			# Reads the current schedule and duration from the timekeeper file
			currSchedule, currDuration = readTimekeeperFile()
			lastSchedule, lastDuration = readHistoryTimekeeperFile()
			upcomingSchedule = datetime.datetime.strptime(currSchedule, "%d-%m-%Y %H:%M")
			
			# Controls the screen's backlight
			controlDisplayOnOff(displayOn)

			# Refresh the running message at specific intervals
			if (((counterScreenRefresh == 0) or (counterScreenRefresh >= int(SCREEN_REFRESH_FREQ_SEC / HEARTBEAT_SEC))) and (not runActive)):
				displayRunningMsg(getCurrentTime(), lastSchedule, lastDuration, currSchedule, currDuration)
				counterScreenRefresh = 0

			# Logs the running message at specific intervals
			if ((counterRunningLog == 0) or (counterRunningLog >= int(RUN_LOG_FREQ_SEC / HEARTBEAT_SEC))):
				debugger ("Running. Next schedule: [%s, %s sec]." % (upcomingSchedule.strftime("%d-%m-%Y %H:%M"), currDuration))
				counterRunningLog = 0

			# Sends email at specific intervals
			if ((counterSendEmail == 0) or (counterSendEmail >= int(EMAIL_FREQ_SEC / HEARTBEAT_SEC))):
				if (EMAIL_ENABLED == "Y"):
					displayOn = True
					sendEmail(EMAIL_SUBJECT_RUN)
					displayEmailMsg()
					counterDisplayOnOff = 0
				counterSendEmail = 0

			# Enables/Disables the LCD backlight	
			if ((counterDisplayOnOff >= int(DISPLAY_OFF_DELAY_SEC / HEARTBEAT_SEC)) and (not runActive)):
				displayOn = False
				counterDisplayOnOff = 0

			# Resets the LCD screen periodically
			if ((counterDisplayReset >= int(DISPLAY_RESET_SEC / HEARTBEAT_SEC)) and (not runActive)):
				# Reloads the LCD driver
				sleep(.1)
				lcd = i2cDriver.lcd()
				sleep(.3)
				counterDisplayReset = 0

			# Triggers an adhoc execcution. It updates the timekeeper file with current time and default duration.
			# So during the next loop, the system reads these values from the timekeeper file and triggers the 
			# adhoc run
			if (runNow and (not runActive)):
				adhocRun = True
				displayAdhocRunMsg()
				updateTimekeeperFile(getCurrentTime().strftime("%d-%m-%Y %H:%M"), ADHOC_RUN_DURATION_SEC)
				runNow = False

			# Triggers the switch if the current time is greater than or equal to the upcoming schedule read from
			# the timekeeper file
			if (getCurrentTime() >= upcomingSchedule):
				# Triggers only if it's not already triggered. This check is required because trigger switch is
				# an asynchronous function. Otherwise the system will be triggered multiple times while it's already
				# triggered
				if (not runActive):
					# Resets few flags
					sleep(.1)
					runActive = True
					displayOn = True
					runNow = False
					counterSendEmail = 0
					counterDisplayOnOff = 0

					# Triggers the switch asynchronously
					triggerSwitch(currSchedule, currDuration, durationList, adhocRun)
					adhocRun = False
			else:
				if (runActive):
					counterDisplayOnOff = 0
				runActive = False

			# Increments the counter at the end of each loop
			counterScreenRefresh += 1
			counterRunningLog += 1
			counterSendEmail += 1
			counterDisplayOnOff += 1
			counterDisplayReset += 1

			# Sleeps for some time so that the processor can take up other works
			sleep(float(HEARTBEAT_SEC))

		# After exiting from the infinite while loop
		if (not restart):
			displayGoodbyeMsg()
		else:
			displayRestartMsg()

		sleep(.3)
	except KeyboardInterrupt:
		# Interrupts the loop when ^C is pressed
		debugger("Interrupted.")
		# Displays the Goodbye message and shutdowns the system
		displayGoodbyeMsg()
		sleep(.3)
	except Exeption, error:
		debugger("Something went terribly wrong! Error: %s" % (error))
	finally:
		# Finally unsers the GPIO pins
		unsetGPIO()
		# Exits the system with proper exit code
		exit (EXIT_CODE_SUCCESS)