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

import ConfigParser
import feedparser
import imaplib
import os
import smtplib
import socket
import subprocess
import sys
import time
import Crypto.Cipher.AES as AES

# File details
PARAMETER_FILE = "parameter.lst"
SMTP_FILE = ".smtpDetails"

VALID_COMMANDS = ["RUN_NOW", "SKIP_NEXT", "SEND_LOG", "RESTART"]

##########################################################################################
# Runs any shell command.
##########################################################################################
def runCommand(command):
	proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
	(output, err) = proc.communicate()
	return output

##########################################################################################
# Validates whether the sender of the email is valid or not.
##########################################################################################
def validateSender(sender):
	trustedList = EMAIL_TRUSTED_ADDRESS.lower().replace(" ", "").split(",")
	return (sender.lower() in trustedList)

##########################################################################################
# Validates whether a sent command is valid or not.
##########################################################################################
def validateCommand(command):
	return (command in VALID_COMMANDS)

##########################################################################################
# Checks if a given file exists in the path.
##########################################################################################
def checkIfFileExists(fileName):
	return True if ((os.path.isfile(fileName)) and (os.path.getsize(fileName) > 0)) else False

##########################################################################################
# Sends email. Gets all the details from parameter.lst and .smtpDetails files
##########################################################################################
def sendEmail(type, sender="", command=""):
	time.sleep(0.1)

	#try:
	mailSubject = "Response from uWaiPi"
	# Composes the mail string
	mailStr = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (SMTP_USER_ID, ", ".join(sender.split(",")), mailSubject)
	if (type == "UNAUTHORIZED_EMAIL"):
		mailStr += "Hey there!\n\nThis mail id is not authorized to send commands through mail%s!"
	elif (type == "INVALID_COMMAND"):
		mailStr += "Hey there!\n\nThe command [%s] is not valid! Please use either of the following commands:\n\n\t[uWaiPi] RUN_NOW\n\t[uWaiPi] SKIP_NEXT\n\t[uWaiPi] SEND_LOG\n\t[uWaiPi] RESTART"
	elif (type == "SUCCESS"):
		mailStr += "Hey there!\n\nYour last command [%s] has been received and would be processed soon!"

	mailStr += "\n\n\nRegards,\nuWaiPi"

	# SMPT server details
	server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
	server.starttls()
	server.ehlo()
	server.login(SMTP_USER_ID, SMTP_USER_PASSWORD)
	server.set_debuglevel(0)
	# Sends the email
	server.sendmail(SMTP_USER_ID, sender, mailStr % command)
	server.quit()

def checkRelevancy(subject):
	return (subject[:8].lower() == "[uwaipi]")

##########################################################################################
# Main program starts here.
##########################################################################################
if (__name__ == "__main__"):
	# Creates an object for crypt
	crypt = AES.new("This is a key123", AES.MODE_CBC, "This is an IV456")

	paramConfig = ConfigParser.RawConfigParser()
	smtpConfig = ConfigParser.RawConfigParser()
	paramConfig.read(PARAMETER_FILE)
	smtpConfig.read(SMTP_FILE)

	EMAIL_ENABLED = paramConfig.get("BasicConfig", "EMAIL_ENABLED")
	SOCKET_LISTENER_PORT = paramConfig.get("AdvanceConfig", "SOCKET_LISTENER_PORT")

	if ((EMAIL_ENABLED == "Y") and (checkIfFileExists(SMTP_FILE))):
		SMTP_USER_ID = smtpConfig.get("SMTP", "SMTP_USER_ID")
		SMTP_USER_PASSWORD = crypt.decrypt(smtpConfig.get("SMTP", "SMTP_USER_PASSWORD")).strip()
		SMTP_SERVER = smtpConfig.get("SMTP", "SMTP_SERVER")
		SMTP_PORT = smtpConfig.get("SMTP", "SMTP_PORT")
		EMAIL_TRUSTED_ADDRESS = paramConfig.get("BasicConfig", "EMAIL_TRUSTED_ADDRESS")

		while True:
			try:
				details = feedparser.parse("https://" + SMTP_USER_ID + ":" + SMTP_USER_PASSWORD + "@mail.google.com/gmail/feed/atom")
				unreadCount = int(details["feed"]["fullcount"])

				if unreadCount > 0:
					sender = details["items"][0].author_detail.email
					subject = details["items"][0].title

					if (checkRelevancy(subject)):
						command = subject[8:].upper().strip()

						obj = imaplib.IMAP4_SSL("imap.gmail.com", "993")
						obj.login(SMTP_USER_ID, SMTP_USER_PASSWORD)
						obj.select("Inbox")  
						type, data = obj.search(None, "UnSeen")
						obj.store(data[0].replace(" ", ", "), "+FLAGS", "\Seen")

						if (validateSender(sender)):
							if (validateCommand(command)):
								try:
									s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
									s.connect(("localhost", int(SOCKET_LISTENER_PORT)))
									s.sendall(command)
									s.close()
								
									if (command == "RESTART"):
										runCommand("touch ./.restart")

									sendEmail("SUCCESS", sender, command)
								except Exception, x:
									print x
									pass
							else:
								sendEmail("INVALID_COMMAND", sender, command)
						else:
							sendEmail("UNAUTHORIZED_EMAIL", sender)
			except KeyboardInterrupt:
				exit(0)
			except:
				pass

			time.sleep(1)
