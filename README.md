# uWaiPi #
*uWaiPi* is a Time-driven Automatic Plant Watering System.

### Features ###
* Time-driven automatic watering system
* Constantly displays the running information
* Schedule and duration can be customizable as per requirements
* Multiple schedules can be setup
* Capable of identifying and running any missed schedules
* Automatically turns off the backlight of the LCD display
* Email features - notification on watering the plant
* Buttons available to execute on adhoc basis or skip the next executions
* Commands can be send via emails

### Platforms ###
*uWaiPi* works on [Raspberry Pi](https://www.raspberrypi.org/). It has been tested in the following versions of Raspberry Pi:

* Raspberry Pi 2 Model B
* Raspberry Pi 3
* Raspberry Pi Zero

The current version of has been developed on Raspbian Jessie. You can download the same from [here](https://www.raspberrypi.org/downloads/raspbian/).

### List of files ###
The downloaded package contatins the list of files and directories as below:
```
uWaiPi
│   install.sh
│   README.md
└───sources
        asyncFunc.py
        createSmtpFile.py
        i2cDriver.py
        keepRunning.sh
        killBgProcess.sh
        loadOnStartup.sh
        mailListener.py
        restartApp.sh
        startup.sh
        uWaiPi.py
```

### Download ###
*uWaiPi* can be downloaded from [Git](https://github.com/ujjaldey/uWaiPi/archive/master.zip). You can run the below command directly from your Raspberry Pi terminal:
```bash
wget https://github.com/ujjaldey/uWaiPi/archive/master.zip
```

### Installation & Configuration ###
*uWaiPi* is pretty simple to install and configure. Just download the package, run the installation script, and follow the on-screen instructions. That should be it! Make sure you are having the lastest stable version of the operating system. The detailed installation steps are described as below:

Once the package is downloaded, extract the package to a temporary directory:
```bash
unzip master.zip
mv uWaiPi-master*/ uWaiPiSrc
```

Change the permissions of the files:
```bash
chmod -R 755 uWaiPiSrc/
```

Go to the directory and run the installation script:
```bash
cd uWaiPiSrc/
./install.sh
```

A banner will be shown as below:
```
      __        __    _ ____  _
  _   \ \      / /_ _(_)  _ \(_)
 | | | \ \ /\ / / _` | | |_) | |
 | |_| |\ V  V / (_| | |  __/| |
  \__,_| \_/\_/ \__,_|_|_|   |_|
================================
Developed by Ujjal Dey, (c) 2016
================================
```

Enter the path where you want to install the application. If the path does not exist, it will prompt whether you want to create it or not. Enter "Y":
```
Enter the installation directory [Hit <Enter> for /home/pi/uWaiPiSrc]: /home/pi/uWaiPi
Entered path does not exist. Do you want to create it? [Y/N] [Hit <Enter> for Y]: Y
Directory created: /home/pi/uWaiPi

uWaiPi will be installed in the directory: /home/pi/uWaiPi/
```

The dependent softwares and packages will start getting installed. It might take a while to download and install the packages:
```
Installing python-rpi...
Installed python-rpi

Installing python-smbus...
Installed python-smbus

Downloading and installing I2C-LCD...
Installed I2C-LCD

Downloading and installing feedparser-5.2.1...
Installed feedparser-5.2.1

Downloading and installing pycrypto-2.6.1...
Installed pycrypto-2.6.1
```

Next, the installation will start:
```
Starting installation...

Copying files...
Files copied

Compiling...
Compiled

Configuring path...
Path configured
```

To enable auto-start after reboot, enter "Y", else "N":
```
Enable auto-start after booting [Y/N] [Hit <Enter> for Y]: y
Adding in cron...
Added in cron
```

Enter the details for configuring the application:
```
Enter the following details for setting up the parameters...
Enter your name: Ujjal Dey
Enter the frequency for logging (in seconds) [Hit <Enter> for 1800]: 900
Enter the display timeout (in seconds) [Hit <Enter> for 30]:
Enter the duration for adhoc run (in seconds) [Hit <Enter> for 20]:
Enter a free port number for listening to commands [Hit <Enter> for 9999]:
Enter the name of the log file [Hit <Enter> for execution.log]: uWaiPi.log
```

To enable email feature, enter "Y", else "N". In case "Y" is entered, provide the email details:
```
Enable email features [Y/N] [Hit <Enter> for Y]: Y
Enter the receiver email address (Comma-separated for multiple): ujjaldey@gmail.com
Enter the number of lines of log to be included in the email [Hit <Enter> for 50]: 100
Enter the frequency of email (in seconds) [Hit <Enter> for 7200]:
Enter the trusted email address for sending commands (Comma-separated for multiple): ujjaldey@gmail.com
```

The parameter file will be created. The parameters can be changed by editing the file manually:
```
Writing parameter file...
Parameter file /home/pi/uWaiPi/parameter.lst created. You can change the parameters later by editing the file manually.
```

To configure the scheduler, enter the following details. Multiple schedules can be configured:
```
Creating scheduler file...
Enter the timing for execution-1 (in HH24:MI format): 08:00
Enter the duration for execution-1 (in seconds): 30
Do you want to add another schedule? [Y/N] [Hit <Enter> for N]: y

Enter the timing for execution-2 (in HH24:MI format): 14:00
Enter the duration for execution-2 (in seconds): 30
Do you want to add another schedule? [Y/N] [Hit <Enter> for N]: y

Enter the timing for execution-3 (in HH24:MI format): 18:30
Enter the duration for execution-3 (in seconds): 20
Do you want to add another schedule? [Y/N] [Hit <Enter> for N]: n
```

The scheduler file will be created. The schedules can be changed by editing the file manually:
```
Writing scheduler file...
Scheduler file /home/pi/uWaiPi/schedule.lst created. You can change the schedules later by editing the file manually.
```

The installer will cleanup the temporary files:
```
Deleting files...
Files deleted
```

In case the email feature is enabled, the installer will ask for the SMTP user details. This email id would be used for sending/receiving the mails:
```
Configuring SMTP details...
Enter SMTP user id: ujjaldey.rpi@gmail.com
Enter SMTP user password:
Enter SMTP server name [smtp.gmail.com]:
Enter SMTP port number [587]:
```

The SMTP file will be created:
```
SMTP file created
```

On completion the following message will be displayed:
```
uWaiPi installation completed. You can now delete the installation files and directory.
Thanks for choosing uWaiPi. For any support please contact: ujjaldey@gmail.com.
If you have enabled auto-start, uWaiPi will be started automatically on boot. You can also run /home/pi/uWaiPi/startup.sh to start it manually.
```

Now the installer will promot to restart the Raspberry Pi. Enter "Y" to reboot now, else "N":
```
You must restart the Raspberry Pi to apply the changes. Do you want to restart it now? [Hit <Enter> for Y]: y
Restarting...
```

If you have enabled auto-start after reboot, *uWaiPi* will start automatically once the Raspberry Pi is restarted. Else use the following script present in your installation path to start the application manually:
```
startup.sh
```

### Interfaces/Controls ###
*uWaiPi* interfaces with the users through a LCD output display and three physical input buttons. The input buttons are having the following functionalities:
* Wakes up the display
* Runs on adhoc basis
* Skips the next executions

*uWaiPi* can also be controlled via email (email feature has to be enabled). A trusted email id has to be setup during the installation. Commands can be sent through the subect line of the email and should be sent to the SMTP mail id (configured during installation). The subject of the email should have the following format:
```
[uWaiPi] <command>
```
Valid commands:

* SEND_LOG - To send the recent execution logs
* RUN_NOW - To run immediately
* SKIP_NEXT - To skip the next execution
* RESTART - To restart the application

### Contact ###
For any bugs/issue/feedback/suggestions, please contact me at my email id ujjaldey@gmail.com. You can also visit my [website](http://ujjaldey.in/project/) for further information.

### Thanks ###
* [The Raspberry Pi Guy](https://github.com/the-raspberry-pi-guy/lcd) - for the I2C library
* [Denis Pleic](https://gist.github.com/DenisFromHR/cc863375a6e19dce359d) - for further enhacements on I2C library

### Copyrights ###
Copyright (c) 2016 [Ujjal Dey](http://ujjaldey.in/)