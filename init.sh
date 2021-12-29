#!/bin/bash

cd ~
echo "[x] Refreshing repos"
sudo apt update

echo "[x] Installing dependencies"
sudo apt install -y ffmpeg fswebcam

echo "[x] Setting up fstab"
sudo mkdir /mnt/usb
sudo chown -R pi:pi /mnt/usb

if ! grep -q 'init-usb' /etc/fstab ; then
    echo '# init-usb' >> /etc/fstab
    echo '/dev/sda1 /mnt/usb vfat defaults,auto,users,rw,nofail,noatime,uid=pi,gid=pi 0 0' >> /etc/fstab
fi

echo "[x] Setting up python"
git clone https://github.com/polymore/CarOS
cd CarOS
chmod +x startup.sh
sudo cp -rv caros.service /lib/systemd/system/

echo "[x] Setting up systemd"
systemctl status caros.service
sudo systemctl enable caros.service

echo "[x] Process done, please create the config.json file in /boot/ and then reboot."
