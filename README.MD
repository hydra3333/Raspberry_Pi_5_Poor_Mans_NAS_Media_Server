## Raspberry Pi 5 Poor Mans NAS / Media Server    

### Outline    
If you have a PI 5 and some old USB3 disks (with their own power) and a couple of USB3 hubs laying around,
but can't afford a NAS box or 3D printer to print one nor a SATA hat for the Pi etc, then perhaps
cobble together a NAS / Media Server with what you have.

A Pi 5 with    
- `SAMBA` for file sharing    
- `overlayfs` (inbuilt in debian) for merging folders into a virtual folder    
- `HD-IDLE` to ensure good disk spin-down times    
- 1 or 2 USB3 hubs plugged into the Pi 5    
- old USB3 disks, plugged into the USB hubs    

can serve up the folders/files across a LAN.

Say one has 8 old USB3 disks `DISK1` ... `DISK8` all plugged into the USB3 hubs,
and disk each has a single root folder containing subfolders of media to be served `ROOT1` ... `ROOT8`,
then we can    
- mount the disks individually in fstab
- create a virtual folder from all of those root folders and mount that in fstab    
- setup `SAMBA` to serve up the individual disks in read-write mode, and the virtual folder in read-only mode    
- setup HD-IDLE to ensure they all spin down properly between uses and not spin all the time    

A drawback is that if one copies new files onto the individual disks, or modifies existing files on them,
then the Pi needs to be re-booted so that overlayfs takes notice of changes. Not so good for a true NAS,
not the end of the world for a media server with infrequent updates;
one could always setup a nightly Pi reboot at 4:45 am with crontab and say "it'll be ready tomorrow" ...    

### Acknowledgemenets    

#### thagrol    
https://forums.raspberrypi.com/viewtopic.php?p=2236572#p2236547    
Building A Pi Based NAS https://forums.raspberrypi.com/viewtopic.php?t=327444    
Using fstab A Beginner's Guide https://forums.raspberrypi.com/viewtopic.php?t=302752    

### This is an outline, not a script    

#### Prepare the hardware    
First ensuring that power switch is off where the Pi's power block plugs in,    
- plug in the Pi to its power cable    
- plug the Pi into a screen with the HDMI cable (sophisticated uses had do it with SSH or VNS
- plug in the USB3 hubs into the USB3 slots in the Pi 5    
- ensure the external USB3 disks are powered off then plug them into the USB3 hubs    

In the outline below, we'll assume only 4 USB3 disks, you can add more if you like.

#### Install Raspberry Pi OS with `autologin`    
Install the full image to an SD card in the usual way using the Pi imager. This way, you can use it for other things too.    
During the SD card creation, select and set options so that    
- the username is `pi` (if not then replace username `pi` in the outline with your chosen username)     
- the password is something you will remember (you will need to enter it later during `SAMBA` setup)    
- autologin is set ON    
- VNC is set ON    

#### Boot update the system
- Ensure the Pi 5 is powered off    
- Plug the SD card into the Pi 5    
- Power on all of the USB3 disks, wait 15 seconds for them to power-up and spin-up    
- Power on the Pi 5    
- When the Pi has booted to the desktop, start a terminal then update the system    
```
sudo apt -y update
sudo apt -y full-upgrade
```
- If the Pi tells you to reboot, do so.

At the point, the disks should be auto-mounted. That's OK, well change that later to suit our needs.    

### Set the Router so this Pi has a Reserved fixed (permanent) DHCP IP Address Lease
In this outline the LAN IP Address range is 10.0.0.0/255.255.255.0 with the Pi 5 knowing itself of course on 127.0.0.1,
and the Router's IP Address lease reservation could be 10.0.0.21.
If you need a different IP Address/Range, just substitute in the correct IP and Address range etc in the outline below.     

Normally the Pi will get a DHCP IP Address lease from the router, which may change over time as leases expire.    
On the Pi start a terminal and do    
```
ifconfig
```
and notice the IP address and mac address.

Login to your router and look at the LAN connected devices, noticing the IP address and mac address matching the Pi.    
Head on to the Router's DHCP management area and allocated a Reserved fixed (permanent) IP address and apply/save it.   
Reboot the Pi, then on the Pi start a Terminal and do    
```
ifconfig
```
and notice the IP address and mac address and hope they do match the reservation you made on the router.    
If not, check what you have done on the router and fix it and reboot the Pi.    

### Ascertain the disks ID info, specifically the PARTUUID    
Start a Terminal
```
# Run the following command to get the location of the usb3disk partitions.
# note: (grep -v mmcblk0 discards any results for the SD card)
sudo blkid|grep -v mmcblk0
# List all of the usb3 disk stuff on the Raspberry Pi
sudo lsblk 
sudo lsblk -o UUID,PARTUUID,NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL,MODEL
# Run the following command to get more info on disks
sudo df
```
From each partition, look for the PARTUUID and substitute that for each of `partuuid1/partuuid3/partuuid3/partuuid4` in the outline below.    

Check the folder names on each of the disks partitions,
and write down each disk's root foldername
underneath which the media files to be served exist.    
eg    
```
ls -al \dev\sda1
ls -al \dev\sda2
```

Then look on each disk to find the correct root folder name to use instead of `mp4lib1/mp4lib2/mp4lib3/mp4lib4` in the lines below,    
So, this     
```
/mnt/shared/usb3disk1/mp4lib1
/mnt/shared/usb3disk2/mp4lib2
/mnt/shared/usb3disk3/mp4lib3
/mnt/shared/usb3disk4/mp4lib4
```
could for example become
```
/mnt/shared/usb3disk1/mp4_folder_on_disk_1
/mnt/shared/usb3disk2/mp4_folder_on_disk_2
/mnt/shared/usb3disk3/mpg_folder_on_disk_3
/mnt/shared/usb3disk4/mp3_folder_on_disk_4

```

#### Create mount points for the disks and root folders

Start a Terminal and do (remember, substitute the real folder names for `mp4lib1/mp4lib2/mp4lib3/mp4lib4` in the lines below)    
```
# create the root for SMB/CIFS sharing
cd ~
sudo mkdir -v -m a=rwx /mnt/shared

# create the mount points for the external USB3 disks    
sudo mkdir -v -m a=rwx /mnt/shared/usb3disk1
sudo mkdir -v -m a=rwx /mnt/shared/usb3disk2
sudo mkdir -v -m a=rwx /mnt/shared/usb3disk3
sudo mkdir -v -m a=rwx /mnt/shared/usb3disk4

# create the overlayfs mount point
sudo mkdir -v -m a=rwx /mnt/shared/merged
sudo chown -R -v pi:  /mnt/shared/merged
#sudo chmod -R -v +777 /mnt/shared/merged
sudo chmod -R -v a+rwx /mnt/shared/merged

# ensure the tree has the right ownership and permissions
sudo chown -R -v pi:  /mnt/shared
#sudo chmod -R -v +777 /mnt/shared
sudo chmod -R -v a+rwx /mnt/shared
```

#### Backup and Edit `/etc/fstab`    

To make the mounts happen at boot time, we mus edit `/etc/fstab`.    
Start a Terminal and run the nano editor:    

```
sudo cp -fv /etc/fstab /etc/fstab.bak
sudo nano  /etc/fstab
```

Using the nano editor, change fstab so the following entries are in the specific order below ...    
Remember to    
- substitute your PARTUUID id's for `partuuid1/partuuid3/partuuid3/partuuid4`    
- substitute your root folder names for `mp4lib1/mp4lib2/mp4lib3/mp4lib4`    
```
# https://askubuntu.com/questions/109413/how-do-i-use-overlayfs/1348932#1348932
# To set order/dependency of mounts in fstab file, we will declare systemd option "require" using syntax: x-systemd.require. 
# Argument for this option is mount point of the mount which should be successfully mounted before given mount.
#
# Mount each usb3 disk partition, each subsequent mount depending on the prior mount.
# Careful: "nofail" will cause the process to continue with no errors (avoiding a boot hand when a disk does not mount)
#          however the subsequently dependent mounts will fails as will the overlayfs mount
#             ... but at least we have booted, not halting boot with a failed fstab entry, and can fix that !
PARTUUID=partuuid1 /mnt/shared/usb3disk1 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,x-systemd.device-timeout=60 0 0
PARTUUID=partuuid2 /mnt/shared/usb3disk2 ntfs x-systemd.requires=/mnt/shared/usb3disk1,defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,x-systemd.device-timeout=60 0 0
PARTUUID=partuuid3 /mnt/shared/usb3disk3 ntfs x-systemd.requires=/mnt/shared/usb3disk2,defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,x-systemd.device-timeout=60 0 0
PARTUUID=partuuid4 /mnt/shared/usb3disk4 ntfs x-systemd.requires=/mnt/shared/usb3disk3,defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,x-systemd.device-timeout=60 0 0
#
overlay /mnt/shared/merged overlay x-systemd.requires=/mnt/shared/usb3disk4,defaults,auto,users,ro,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,x-systemd.device-timeout=60,lowerdir=/mnt/shared/usb3disk1/mp4lib1:/mnt/shared/usb3disk2/mp4lib2:/mnt/shared/usb3disk3/mp4lib3:/mnt/shared/usb3disk4/mp4lib4 0 0
#
```
exit nano with `Control O` `Control X`.    

####  Check and Reboot to see what happens with those mounts    
Reboot the Pi 5.    
Start a Terminal
```
# Run the following command to get the location of the usb3disk partitions. grep -v mmcblk0 discards any results for the SD card. 
sudo blkid|grep -v mmcblk0
# List all of the usb3 disk stuff on the Raspberry Pi
sudo lsblk 
sudo lsblk -o UUID,PARTUUID,NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL,MODEL
# Run the following command to get more info on disks
sudo df
```
If the mounts do not match what you specified in `etc/fstab`, then something is astray !  Check what you have done above.    

Do an `ls -al` on each of the mounts and on the `/mnt/shared/merged` folder to check they are visible.    
If the files in the mounts do not match what you expect from `etc/fstab`, then something is astray !  Check what you have done above.    


#### Install and configure `SAMBA`
In a Terminal,    
```
sudo apt -y install samba samba-common-bin smbclient cifs-utils
# create the default user pi in creating the first samba user
sudo smbpasswd -a pi
# if prompted, enter the same password as the default user pi you setup earlier    
```

# https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html

Edit the `SAMBA` config `/etc/samba/smb.conf`.    
```
sudo nano /etc/samba/smb.conf
```

Here are some global `SAMBA` settings in `/etc/samba/smb.conf`, use nano to check for and fix them    
- if they not exist, create them    
- if they are commented out, uncomment them    
- if they contain different values, comment out and create a line underneath with the correct setting

```
workgroup = WORKGROUP
hosts 10.0.0.0/255.255.255.0 127.0.0.1
security = user
deadtime = 15
#socket options = IPTOS_LOWDELAY TCP_NODELAY SO_RCVBUF=65536 SO_SNDBUF=65536 SO_KEEPALIVE
# linux auto tunes SO_RCVBUF=65536 SO_SNDBUF=65536
socket options = IPTOS_LOWDELAY TCP_NODELAY SO_KEEPALIVE
inherit permissions = yes
# OK ... 1 is a sticky bit
# create mask and directory mask actually REMOVE permissions !!!
#   create mask = 0777
#   directory mask = 0777
# force create mode and force directory mode 
# specifies a set of UNIX mode bit permissions that will always be set 
force create mode = 1777
force directory mode = 1777
preferred master = No
local master = No
guest ok = yes
browseable = yes
#guest account = root
public = yes
guest account = pi
allow insecure wide links = yes
follow symlinks = yes
wide links = yes
```

Below are the definition of the 2 new shares. Add them to the end of `/etc/samba/smb.conf`    
```
# DEFINE THE SHARES
[mp4lib]
comment = RO access to combined mp4ibs on USB3 disks from overlayfs
path = /mnt/shared/merged
available = yes
force user = pi
writeable = no
read only = yes
browseable = yes
public=yes
guest ok = yes
guest account = pi
guest only = yes
case sensitive = no
default case = lower
preserve case = yes
allow insecure wide links = yes
follow symlinks = yes
wide links = yes
	
[individual_disks]
comment = rw access to individual USB3 disks
path = /mnt/shared
available = yes
force user = pi
writeable = yes
read only = no
browseable = yes
public=yes
guest ok = yes
guest account = pi
guest only = yes
case sensitive = no
default case = lower
preserve case = yes
allow insecure wide links = yes
follow symlinks = yes
wide links = yes
force create mode = 1777
force directory mode = 1777
inherit permissions = yes
```

exit nano with `Control O` `Control X`.    


The rest of this outliune is yet to bve clarified.

sudo testparm
set +x
echo ""
echo "# Restart Samba service"
echo ""
set -x
sudo systemctl enable smbd
sleep 2s
sudo systemctl stop smbd
sleep 2s
sudo systemctl restart smbd
sleep 2s
set +x
echo ""
echo "# List the new Samba users (which can have different passwords to the Pi itself) and shares"
echo ""
set -x
sudo pdbedit -L -v
sudo net usershare info --long
sudo smbstatus
sudo smbstatus --shares # Will retrieve what's being shared and which machine (if any) is connected to what.
#sudo net rpc share list -U pi
#sudo net rpc share list -U root
#sudo smbclient -L host
#sudo smbclient -L ${server_ip} -U pi
#sudo smbclient -L ${server_ip} -U root
set +x
echo ""
echo "You can now access the defined shares from a Windows machine or from an app that supports the SMB protocol"
echo "eg from Win10 PC in Windows Explorer use the IP address of ${server_name} like ... \\\\${server_ip}\\ "
set -x
sudo hostname
sudo hostname --fqdn
sudo hostname --all-ip-addresses
  




Setup HDIDLE ?????????????

