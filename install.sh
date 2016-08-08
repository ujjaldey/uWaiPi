#!/bin/bash
# -*- coding: utf-8 -*-

function changeToUpper()
{
	echo $1 | tr "[:lower:]" "[:upper:]"
}

function getUserInput()
{
	input=""
	dispStr=$1
	if [ "X$3" != "X" ]
	then
		dispStr="${dispStr} [Hit <Enter> for ${3}]"
	fi

	while [ "X$input" == "X" ]
	do
		echo -n $dispStr": " >&2
		read input

		if [ "X$input" == "X" ]
		then
			input=$3
		fi

		if [ "X$2" != "XY" ]
		then
			break
		fi
	done
	echo $input
}

function validatePath()
{
	if [ ! -d "$1" ]
	then
		echo "N"
	else
		echo "Y"
	fi
}

function copyFiles()
{
	\cp ./sources/asyncFunc.py ${installDir} 2> /dev/null
	\cp ./sources/createSmtpFile.py ${installDir} 2> /dev/null
	\cp ./i2cDriver.py ${installDir} 2> /dev/null
	\cp ./sources/mailListener.py ${installDir} 2> /dev/null
	\cp ./sources/uWaiPi.py ${installDir} 2> /dev/null

	\cp ./sources/keepRunning.sh ${installDir} 2> /dev/null
	\cp ./sources/killBgProcess.sh ${installDir} 2> /dev/null
	\cp ./sources/loadOnStartup.sh ${installDir} 2> /dev/null
	\cp ./sources/restartApp.sh ${installDir} 2> /dev/null
	\cp ./sources/startup.sh ${installDir} 2> /dev/null

	\cp ./README.md ${installDir} 2> /dev/null
	
	\chmod 755 ${installDir}/*

	touch ${installDir}/schedule.lst
}

function configurePath()
{
	echo "export UWAIPI_INSTALLATION_PATH=$2" > $1
	chmod 755 $1
}

function addInCron()
{
	line="@reboot sh ${2}/${1}"
	(sudo crontab -l; echo "$line") | sudo crontab -
}

function downloadTParty()
{
	echo "Installing python-rpi..."
	sudo apt-get install python-dev python-rpi.gpio -y > /dev/null 2>&1
	echo "Installed python-rpi"
	echo ""

	echo "Installing python-smbus..."
	sudo apt-get install python-smbus -y > /dev/null 2>&1
	echo "Installed python-smbus"
	echo ""

	echo "Downloading and installing I2C-LCD..."
	wget https://codeload.github.com/the-raspberry-pi-guy/lcd/zip/master > /dev/null 2>&1
	unzip master > /dev/null 2>&1

	revision=`python -c "import RPi.GPIO as GPIO; print GPIO.RPI_REVISION"`

	if [ $revision = "1" ]
	then
		port=0
	else
		port=1
	fi

	cat sources/i2cDriver.py | sed "s/_PORT_/${port}/1" > i2cDriver.py
	sudo cp ./lcd-master/installConfigs/modules /etc/
	sudo cp ./lcd-master/installConfigs/raspi-blacklist.conf /etc/modprobe.d/

	exists=`grep "dtparam=i2c_arm=1" /boot/config.txt`
	if [ "X$exists" = "X" ]
	then
		printf "dtparam=i2c_arm=1\n" | sudo tee -a  /boot/config.txt > /dev/null 2>&1
	fi

	sudo rm -rf master lcd-master > /dev/null 2>&1
	echo "Installed I2C-LCD"
	echo ""

	echo "Downloading and installing feedparser-5.2.1..."
	wget https://pypi.python.org/packages/ca/f4/91a056f11751701c24f86c692d92fee290b0ba3f99f657cdeb85ad3da402/feedparser-5.2.1.tar.gz#md5=d552f7a2a55e8e33b2a3fe1082505b42 > /dev/null 2>&1
	gunzip feedparser-5.2.1.tar.gz > /dev/null 2>&1
	tar -xvf feedparser-5.2.1.tar > /dev/null 2>&1
	cd ./feedparser-5.2.1
	sudo python setup.py install > /dev/null 2>&1
	cd ..
	sudo rm -rf feedparser-5.2.1* > /dev/null 2>&1
	echo "Installed feedparser-5.2.1"
	echo ""

	echo "Downloading and installing pycrypto-2.6.1..."
	wget https://pypi.python.org/packages/60/db/645aa9af249f059cc3a368b118de33889219e0362141e75d4eaf6f80f163/pycrypto-2.6.1.tar.gz#md5=55a61a054aa66812daf5161a0d5d7eda > /dev/null 2>&1
	gunzip pycrypto-2.6.1.tar.gz > /dev/null 2>&1
	tar -xvf pycrypto-2.6.1.tar > /dev/null 2>&1
	cd ./pycrypto-2.6.1
	sudo python setup.py install > /dev/null 2>&1
	cd ..
	sudo rm -rf pycrypto-2.6.1* > /dev/null 2>&1
	echo "Installed pycrypto-2.6.1"
	echo ""
}

function writeParamConfigFile()
{
	> $paramConfigFile
	echo "[BasicConfig]" >> $paramConfigFile
	echo "USER_NAME=${1}" >> $paramConfigFile
	echo "RUN_LOG_FREQ_SEC=${3}" >> $paramConfigFile
	echo "DISPLAY_OFF_DELAY_SEC=${4}" >> $paramConfigFile
	echo "EMAIL_ENABLED=${2}" >> $paramConfigFile
	echo "EMAIL_RECEIVER_ADDRESS=${7}" >> $paramConfigFile
	echo "EMAIL_SUBJECT_RUN=[uWaiPi] Up and Running" >> $paramConfigFile
	echo "EMAIL_SUBJECT_ACTIVE=[uWaiPi] Plants have been watered" >> $paramConfigFile
	echo "EMAIL_LOG_LINE=${8}" >> $paramConfigFile
	echo "EMAIL_FREQ_SEC=${9}" >> $paramConfigFile
	echo "EMAIL_TRUSTED_ADDRESS=${5}" >> $paramConfigFile
	echo "" >> $paramConfigFile
	echo "[AdvanceConfig]" >> $paramConfigFile
	echo "HEARTBEAT_SEC=.1" >> $paramConfigFile
	echo "ADHOC_RUN_DURATION_SEC=${11}" >> $paramConfigFile
	echo "SOCKET_LISTENER_PORT=${6}" >> $paramConfigFile
	echo "LOG_FILE=${10}" >> $paramConfigFile
	echo "SCHEDULER_FILE=schedule.lst" >> $paramConfigFile
	echo "LOG_OUTPUT_ENABLED=Y" >> $paramConfigFile
	echo "CONSOLE_OUTPUT_ENABLED=N" >> $paramConfigFile
}

function createSchedulerFile()
{
	if [ ${execCount} -eq 1 ]
	then
		> ${installDir}/${schedulerFile}
	fi

	time=`getUserInput "Enter the timing for execution-${execCount} (in HH24:MI format)" "Y" ""`
	duration=`getUserInput "Enter the duration for execution-${execCount} (in seconds)" "Y" ""`

	echo "${time}|${duration}" >> ${installDir}/${schedulerFile}

	addAnother=`getUserInput "Do you want to add another schedule? [Y/N]" "Y" "N"`
	addAnother=`changeToUpper $addAnother`

	if [ "X$addAnother" == "XY" ]
	then
		echo ""
		execCount=`expr $execCount + 1`
		createSchedulerFile
	else
		\cat ${installDir}/${schedulerFile} | sort > ${installDir}/${schedulerFile}".tmp"
		\mv ${installDir}/${schedulerFile}".tmp" ${installDir}/${schedulerFile}
	fi
}

#########################################
# Installation script starts from here
#########################################
\clear
echo "      __        __    _ ____  _ "
echo "  _   \ \      / /_ _(_)  _ \(_)"
echo " | | | \ \ /\ / / _\` | | |_) | |"
echo " | |_| |\ V  V / (_| | |  __/| |"
echo "  \__,_| \_/\_/ \__,_|_|_|   |_|"
echo "================================"
echo "Developed by Ujjal Dey, (c) 2016"
echo "================================"
echo ""

currDir=`pwd`
validPath="N"
pathFile=".configurePath"
paramConfigFile="parameter.lst"
schedulerFile="schedule.lst"
startupFile="startup.sh"
execCount=1

while [ "X$validPath" != "XY" ]
do
	installDir=`getUserInput "Enter the installation directory" "Y" $currDir`

	if [[ "${installDir}" != /* ]]
	then
		installDir="${currDir}/${installDir}"
	fi

	validPath=`validatePath $installDir`

	if [ "X$validPath" != "XY" ]
	then
		createDir=`getUserInput "Entered path does not exist. Do you want to create it? [Y/N]" "Y" "Y"`
		createDir=`changeToUpper $createDir`

		if [ "X$createDir" == "XY" ]
		then
			mkdir -p $installDir
			echo "Directory created: ${installDir}"
			echo ""
			break
		fi
	fi
done

echo "uWaiPi will be installed in the directory: ${installDir}/"
echo ""

downloadTParty

echo "Starting installation..."
echo ""

echo "Copying files..."
copyFiles
echo "Files copied"
echo ""

echo "Compiling..."
python -m compileall ${installDir}/. > /dev/null 2>&1
echo "Compiled"
echo ""

echo "Configuring path..."
pathFile="${installDir}/${pathFile}"
configurePath ${pathFile} ${installDir}
echo "Path configured"
echo ""

cronEnabled=`getUserInput "Enable auto-start after booting [Y/N]" "Y" "Y"`
cronEnabled=`changeToUpper $cronEnabled`

if [ "X$cronEnabled" == "XY" ]
then
	echo "Adding in cron..."
	addInCron ${startupFile} ${installDir} > /dev/null 2>&1
	echo "Added in cron"
fi

echo ""
echo "Enter the following details for setting up the parameters..."
userName=`getUserInput "Enter your name" "Y" ""`
runLogFreq=`getUserInput "Enter the frequency for logging (in seconds)" "Y" "1800"`
displayTimeout=`getUserInput "Enter the display timeout (in seconds)" "Y" "30"`
adhocSec=`getUserInput "Enter the duration for adhoc run (in seconds)" "Y" "20"`
listenerPort=`getUserInput "Enter a free port number for listening to commands" "Y" "9999"`
logFile=`getUserInput "Enter the name of the log file" "Y" "execution.log"`

emailEnabled=`getUserInput "Enable email features [Y/N]" "Y" "Y"`
emailEnabled=`changeToUpper $emailEnabled`

if [ "X$emailEnabled" == "XY" ]
then
	emailReceiver=`getUserInput "Enter the receiver email address (Comma-separated for multiple)" "Y" ""`
	emailLogLine=`getUserInput "Enter the number of lines of log to be included in the email" "Y" "50"`
	emailFreq=`getUserInput "Enter the frequency of email (in seconds)" "Y" "7200"`
	emailTrusted=`getUserInput "Enter the trusted email address for sending commands (Comma-separated for multiple)" "Y" ""`
else
	emailReceiver=""
	emailLogLine=""
	emailFreq=""
	emailTrusted=""
fi

echo ""
echo "Writing parameter file..."
paramConfigFile="${installDir}/${paramConfigFile}"
writeParamConfigFile "$userName" "$emailEnabled" "$runLogFreq" "$displayTimeout" "$emailTrusted" "$listenerPort" "$emailReceiver" "$emailLogLine" "$emailFreq" "$logFile" "$adhocSec"
echo "Parameter file ${paramConfigFile} created. You can change the parameters later by editing the file manually."
echo ""

echo "Enter the following details for setting up the schedules..."
createSchedulerFile
echo ""
echo "Writing scheduler file..."
echo "Scheduler file ${installDir}/${schedulerFile} created. You can change the schedules later by editing the file manually."
echo ""

echo "Deleting files..."
\rm -f ${installDir}/*.py > /dev/null 2>&1
\rm -f i2cDriver.py > /dev/null 2>&1
echo "Files deleted"
echo ""

if [ "X$emailEnabled" == "XY" ]
then
	echo "Configuring SMTP details..."
	cd ${installDir}
	python ./createSmtpFile.pyc
	cd ~-
	echo ""
fi

touch ${installDir}/README.md

echo "uWaiPi installation completed. You can now delete the installation files and directory."
echo "Thanks for choosing uWaiPi. For any support please contact: ujjaldey@gmail.com."
echo "If you have enabled auto-start, uWaiPi will be started automatically on boot. You can also run ${installDir}/startup.sh to start it manually."

restart=`getUserInput "You must restart the Raspberry Pi to apply the changes. Do you want to restart it now?" "Y" "Y"`
restart=`changeToUpper $restart`

if [ "X$restart" == "XY" ]
then
	echo "Restarting..."
	sudo reboot now
else
	echo "Please restart the Raspberry Pi manually before using uWaiPi."
fi

echo ""