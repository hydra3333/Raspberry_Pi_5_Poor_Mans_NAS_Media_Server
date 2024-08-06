#!/bin/bash
set -x
#
# /srv probably already exists, try to create it anyway
sudo mkdir -v -m a=rwx /srv
#
# {1..8} for 8 disks, for underlying file system that mergerfs will depend on. More than we use is OK.
sudo mkdir -v -m 777 /srv/usb3disk{1..8}
#
# mount point for mergerfs to present the consolidated underlying file systems
sudo mkdir -v -m a=rwx /srv/media
#
# double-ensure the protections are as we want them by setting them on the tree
sudo chmod -R -v a+rwx /srv
#
# Notes:
# /srv will be shared 'rw' by SAMBA to provide access to the underlying file systems (particularly the 'ffd's)
# /srv/media will be shared 'rw' by SAMBA to provide access to the mergerfs merged disks
#
ls -al /srv/
set +x
