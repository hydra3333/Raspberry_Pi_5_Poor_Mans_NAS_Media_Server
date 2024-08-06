#!/bin/bash
set -x

# Make the operating system notice changes in fstab:
sudo systemctl daemon-reload

sudo blkid

sudo lsblk -o UUID,PARTUUID,NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL

sudo umount -f /srv/media
sudo umount -f /srv/usb3disk1
sudo umount -f /srv/usb3disk2
sudo umount -f /srv/usb3disk3
sudo umount -f /srv/usb3disk4
sudo umount -f /srv/usb3disk5
sudo umount -f /srv/usb3disk6
sudo umount -f /srv/usb3disk7
sudo umount -f /srv/usb3disk8

sudo mount -v -a

sudo lsblk -o UUID,PARTUUID,NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL

sudo mount -v | grep srv

set +x
