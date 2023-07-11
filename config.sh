#!/bin/sh

echo "getting config files from /boot/..."
echo ""
cp /boot/deepgram-key.txt /home/$USER/kateprint/
cp /boot/fwversion.txt /home/$USER/kateprint/
cp /boot/baudrate.txt /home/$USER/kateprint/

#check for deepgram API key
if [ ! -e /home/$USER/kateprint/deepgram-key.txt ]
then
    echo -n "Deepgram API key not found, enter key: "
    read key
    echo $key > /home/$USER/kateprint/deepgram-key.txt
else
    key=`cat /home/$USER/kateprint/deepgram-key.txt`
    echo "Deepgram API key found: $key"
    echo -n "Enter new key or leave blank to keep current key:"
    read key
    if [ ! -z "$key" ]
    then
        echo $key > /home/$USER/kateprint/deepgram-key.txt
    fi
fi
echo ""

#check for printer fw version
if [ ! -e /home/$USER/kateprint/fwversion.txt ]
then
    echo -n "Printer FW version not found, enter version (just the number, e.g. '2.69'):"
    read version
    echo $version > /home/$USER/kateprint/fwversion.txt
else
    version=`cat /home/$USER/kateprint/fwversion.txt`
    echo "Printer FW version found: $version"
    echo -n "Enter new FW version or leave blank to keep current version (just the number, e.g. '2.69'):"
    read version
    if [ ! -z "$version" ]
    then
        echo $version > /home/$USER/kateprint/fwversion.txt
    fi
fi
echo ""

#check for printer baudrate
if [ ! -e /home/$USER/kateprint/baudrate.txt ]
then
    echo -n "Printer baudrate not found, enter baudrate:"
    read baudrate
    echo $baudrate > /home/$USER/kateprint/baudrate.txt
else
    baudrate=`cat /home/$USER/kateprint/baudrate.txt`
    echo "Printer baudrate found: $baudrate"
    echo -n "Enter new baudrate or leave blank to keep current baudrate:"
    read baudrate
    if [ ! -z "$baudrate" ]
    then
        echo $baudrate > /home/$USER/kateprint/baudrate.txt
    fi
fi
echo ""

echo "Writing configs to /boot/..."
sudo cp /home/$USER/kateprint/deepgram-key.txt /boot/
sudo cp /home/$USER/kateprint/fwversion.txt /boot/
sudo cp /home/$USER/kateprint/baudrate.txt /boot/
echo ""

echo "Restarting cups..."
sudo lpadmin -p thermal -E -v serial:/dev/serial0?baud=$baudrate -P /home/$USER/zj-58/ZJ-58.ppd
sudo systemctl restart cups

echo "restarting transcription..."
sudo systemctl restart vlcmic.service
sudo systemctl restart transcribeprint.service
