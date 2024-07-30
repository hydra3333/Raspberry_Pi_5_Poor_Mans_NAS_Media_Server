#!/bin/bash
set -x

sudo blkid
sudo lsblk -o UUID,PARTUUID,NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL

# Mount USB3 disks with ntfs (ntfs3 fails)
sudo mount -t ntfs -o defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime /dev/disk/by-partuuid/2d5599a2-aa11-4aad-9f75-7fca2078b38b /srv/usb3disk1
sleep 5
sudo mount -t ntfs -o defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime /dev/disk/by-partuuid/a175d2d3-c2f6-44d4-a5fc-209363280c89 /srv/usb3disk2
sleep 5
sudo mount -t ntfs -o defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime /dev/disk/by-partuuid/9a63b215-bcf1-462b-89d2-56979cec6ed8 /srv/usb3disk3
sleep 5
sudo mount -t ntfs -o defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime /dev/disk/by-partuuid/d6a52d8b-f1e6-424a-8150-dba9453aa7e7 /srv/usb3disk4
sleep 5
sudo mount -t ntfs -o defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime /dev/disk/by-partuuid/cd74d88b-71f1-40b3-bafb-60444215f655 /srv/usb3disk5
sleep 5
sudo mount -t ntfs -o defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime /dev/disk/by-partuuid/e5ff156e-b704-40a9-86d5-5c36c35d6095 /srv/usb3disk6
sleep 5
sudo mount -t ntfs -o defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime /dev/disk/by-partuuid/27891019-f894-4e9b-b326-5f9d10c5c2cf /srv/usb3disk7
sleep 5

sudo blkid
sudo lsblk -o UUID,PARTUUID,NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL

#sudo umount /srv/usb3disk1
#sudo umount /srv/usb3disk2
#sudo umount /srv/usb3disk3
#sudo umount /srv/usb3disk4
#sudo umount /srv/usb3disk5
#sudo umount /srv/usb3disk6
#sudo umount /srv/usb3disk7

set +x
