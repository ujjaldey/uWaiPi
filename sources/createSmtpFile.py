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

import getpass
import Crypto.Cipher.AES as AES

def getUserInput(dispMsg, defaultValue = ""):
	if defaultValue:
		dispMsg = dispMsg + " [" + defaultValue + "]"

	inputStr = raw_input(dispMsg + ": ")

	if inputStr:
		return inputStr
	else:
		return defaultValue	

def getUserInputPassword(dispMsg):
	return getpass.getpass(dispMsg + ": ")

def padPassword(smtpPassword):
	pwdLen = len(smtpPassword)
	return smtpPassword.ljust(16 * ((pwdLen / 16) + 1))

def createSmtpFile(smtpUser, smtpPasswordEnc, smtpServer, smtpPort):
	smtpFile = open(SMTP_FILE_NAME,"w")
	smtpFile.write("[SMTP]\n")
	smtpFile.write("SMTP_USER_ID=" + smtpUser + "\n")
	smtpFile.write("SMTP_USER_PASSWORD=" + smtpPasswordEnc + "\n")
	smtpFile.write("SMTP_SERVER=" + smtpServer + "\n")
	smtpFile.write("SMTP_PORT=" + smtpPort + "\n")
	smtpFile.close()

############################################################
# Main program starts here
############################################################
SMTP_FILE_NAME = ".smtpDetails"
DEFAULT_SMTP_SERVER = "smtp.gmail.com"
DEFAULT_SMTP_PORT = "587"

AES_KEY = "Key for uWaiPi"
AES_IV = "IV for uWaiPi"

smtpUser = getUserInput("Enter SMTP user id")
smtpPassword = getUserInputPassword("Enter SMTP user password")
smtpServer = getUserInput("Enter SMTP server name", DEFAULT_SMTP_SERVER)
smtpPort = getUserInput("Enter SMTP port number", DEFAULT_SMTP_PORT)

obj = AES.new('This is a key123', AES.MODE_CBC, 'This is an IV456')
smtpPasswordEnc = obj.encrypt(padPassword(smtpPassword))

createSmtpFile(smtpUser, smtpPasswordEnc, smtpServer, smtpPort)

print "SMTP file created"
exit (0)
