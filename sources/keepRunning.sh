#!/bin/bash
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

##############################################################################
# Script to run in background and calls restartApp.sh whenever requires
##############################################################################

. .configurePath

cd $UWAIPI_INSTALLATION_PATH

restartFile="${UWAIPI_INSTALLATION_PATH}/.restart"

# Checks if the .restart file present. If yes, then calls restartApp.sh to restart
# the application, else continue in infinite loop
if [ -f $restartFile ]
then
    sudo ./restartApp.sh
	# Removes the .restart file
	sudo \rm -f $restartFile
fi

# Sleeps for 15 seconds and then calls the same script
sleep 15
$0 &
