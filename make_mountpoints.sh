#!/bin/bash
set -x
#
sudo mkdir -v -m a=rwx /srv
sudo chmod -R -v a+rwx /srv
#
# for mergerfs to present the consolidated underlying file systems
sudo mkdir -v -m a=rwx /srv/mediafs
#
# for underlying file system for mergerfs
sudo mkdir -v -m a=rwx /srv/usb3disk1
sudo mkdir -v -m a=rwx /srv/usb3disk2
sudo mkdir -v -m a=rwx /srv/usb3disk3
sudo mkdir -v -m a=rwx /srv/usb3disk4
sudo mkdir -v -m a=rwx /srv/usb3disk5
sudo mkdir -v -m a=rwx /srv/usb3disk6
sudo mkdir -v -m a=rwx /srv/usb3disk7
#
# /srv will be shared 'rw' by SAMBA to provide access to the underlying file systems (particularly the 'ffd's)
# /srv/mediafs will be shared 'rw' by SAMBA to provide access to the mergerfs merged disks
#
set +x
