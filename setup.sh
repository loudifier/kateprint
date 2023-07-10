#!/bin/sh

echo "installing VLC and pip..."
sudo apt-get install -y vlc python3-pip

echo "installing Deepgram and Adafruit thermal printer libraries..."
pip3 install deepgram-sdk adafruit-circuitpython-thermal-printer

echo "configuring serial port..."
sudo raspi-config nonint do_serial 2

# check for deepgram API key
if [ ! -e /home/$USER/kateprint/deepgram-key.txt ]
then
    echo -n "Deepgram API key not found, enter key: "
    read key
    echo $key > /home/$USER/kateprint/deepgram-key.txt
else
    echo "Deepgram API key found"
fi

echo "writing config files to /boot/..."
sudo cp /home/$USER/kateprint/deepgram-key.txt /boot/
sudo cp /home/$USER/kateprint/fwversion.txt /boot/
sudo cp /home/$USER/kateprint/baudrate.txt /boot/

echo "setting transcribe_and_print to run on boot..."
# rc.local might be able to work, but tough to get running
#VLCCMD="su -u $USER -c cvlc -v alsa://plughw:1 --sout '#transcode{acodec=mp3,ab=64,channels=1}:standard{access=http,dst=0.0.0.0:8888/out.mp3}' &"
#PRINTCMD="python3 /home/$USER/kateprint/transcribe_and_print.py &"
#if ! grep -Fxq "$VLCCMD" /etc/rc.local
#then
#     echo "echo"
#     sudo sed -i -e "$i \${VLCCMD}\n" /etc/rc.local
#     sudo sed -i -e "$i \${PRINTCMD}\n" /etc/rc.local
#fi

sudo cp /home/$USER/kateprint/vlcmic.service /lib/systemd/system/
sudo cp /home/$USER/kateprint/transcribeprint.service /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vlcmic.service
sudo systemctl enable transcribeprint.service

echo "setup complete, press ENTER to shut down..."
read key
sudo halt
