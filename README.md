# WARNING: UNDER CONSTRUCTION

## Raspberry Pi 5 Poor Mans NAS / Media Server    

### Outline    
If you have a PI 5 and some old USB3 disks (with their own power supply) and a couple of USB3 hubs laying around,
but can't afford a NAS box nor a 3D printer to print one nor a SATA hat for the Pi etc, then perhaps
cobble together a NAS / Media Server with what you have.

Together with a Pi 5 and an SD card you can use    
- 1 or 2 (say, 4-port) USB3 hubs plugged into the Pi 5 to connect many old USB3 disks to the Pi    
- 1 to 8 old USB3 disks plugged into the USB hubs    

With this harware you can readuly serve up standard SAMBA SMB/CIFS file shares
and media files to devices across your LAN.   

### Why ?
You could use `OpenMediaVault` or `Plex` more easily, but they connect to the internet to do 'stuff'.
I looked at `Plex` years ago and was very uncomfortable with the level of access provided to the vendor
servers directly into my LAN and hence to all the devices on my LAN ... their products essentially gave
them unfettered access. I valued my banking details and documents etc, so refused to go down that route.    

This 'roll your own' approach avoids the pain of getting 'done over' by your own hand - installing
packages known to interact of themselves in essentially unknown ways with (uncontrolled) vendors' servers
on the internet - at the cost of having to deal with more complexity ... safety first.

### General Approach
Say one has 8 old USB3 disks `DISK1` ... `DISK8` all plugged into the (1 or 2) USB3 hubs,
and disk each has a single root folder containing subfolders of media to be served
`ROOTFOLDER1` ... `ROOTFOLDER8`    
```
DISK1 -- ROOTFOLDER1 --|--ClassicMovies
                       |--Documentaries
                       |--Footy-----------|--1997
                       |                  |--1998
                       |--SciFi

DISK2 -- ROOTFOLDER2 --|--ClassicMovies
                       |--Footy-----------|--2000
                       |                  |--2002
                       |--Movies
                       |--Music
                       |--OldMovies
                       |--SciFi
```
Then we can    
- mount the disks individually in fstab so they appear in a consistent way to the system    
- use `overlaysf` (inbuilt in debian) to create a virtual overlayed folder of all of those
root folder trees into a single virtual folder tree for presentation to devices on your LAN    
- use `SAMBA` to serve up the individual USB3 disks in read-write mode for PCs on the LAN to copy new files onto    
- use `SAMBA` to serve up the virtual overlayed folder tree in read-only mode to devices on your LAN    
- use `DLNA` to serve up the virtual overlayed folder in read-only mode to devices on your LAN (eg PCs, ChromeCasts, TVs)    
- use `HD-IDLE` to ensure the USB3 disks all spin down properly between uses and not stay spinning all the time    

One drawback is that if one copies new files onto the individual disks, or modifies existing files on them,
then the Pi needs to be re-booted so that `overlayfs` takes notice of changes. Not so good for a true NAS,
not the end of the world for a media server with infrequent updates;
one could easily setup a nightly Pi reboot at 4:45 am with crontab and say "it'll be up tomorrow" ...    

### Acknowledgements    

#### thagrol    
https://forums.raspberrypi.com/viewtopic.php?p=2236572#p2236547    

Building A Pi Based NAS    
https://forums.raspberrypi.com/viewtopic.php?t=327444    

Using fstab A Beginner's Guide    
https://forums.raspberrypi.com/viewtopic.php?t=302752    

### Outline the steps    

#### ESSENTIAL: Prepare the disks: security, disk volume labels, folder structures, files    
Assuming we have USB3 disks formatted as NTFS on PCs (often used to create media files)
we need to prepare every disk to appear and behave in a consistent way.

For every disk, change it's volume label to be like `DISK1` through to `DISK8`.
If you are unsure how to do that, try
https://www.google.com.au/search?q=how+to+change+an+NTFS+disk+volume+label+in+windows+11    

On every disk, change it's Security so that inbuilt username `everyone` is added with `Full Control` access.
In Windows File Manager
- right click on a drive letter
- choose Properties
- choose Security tab
- click the `Edit` button
- click the `Add` button
- enter the word `everyone` and click the `OK` button
- Ensure `Full control` is ticked and click `Apply`;
if prompted, allow it to change all folders and files on the disk and ignore all errors

On every disk, create a top level folder named like `ROOTFOLDER1` through to `ROOTFOLDER8`, to match the disk volume label number.

Under the top level folder on the disks, place you media files in a reasonably consistent (including filename capitalisation)
folder structure of your choice. The same folder names and files may or may not exist on every disk, you can
spread out the media files and folders across disks and even double them up for backup purposes. eg
```
DISK1 -- ROOTFOLDER1 --|--ClassicMovies
                       |--Documentaries
                       |--Footy-----------|--1997
                       |                  |--1998
                       |--SciFi

DISK2 -- ROOTFOLDER2 --|--ClassicMovies
                       |--Footy-----------|--2000
                       |                  |--2002
                       |--Movies
                       |--Music
                       |--OldMovies
                       |--SciFi
```

#### Prepare the hardware    
First ensuring that power switch is off where the Pi's power block plugs in,    
- plug in the Pi's power cable into the Pi    
- plug the Pi into a screen with the HDMI cable (sophisticated users may choose do it with `SSH` or `VNC` or `RaspberryPi Connect`)
- plug in the USB3 hub(s) into the USB3 slots in the Pi    
- ensure the external USB3 disks are powered off then plug them into the USB3 hubs    

That's the hardware prepared and plugged in.    

In the outline below, we'll assume only 2 USB3 disks. You can add more as you need,
just keep an eye on your disk naming and folder structures in line with the model above.    

#### Install Raspberry Pi OS with `autologin`    
Run the `Raspberry Pi Imager` on a PC to put the full 64 bit `Raspberry Pi OS` image to an SD card in the usual way    
- Choose to "Edit Settings" and then the GENERAL tab.    
- Set a Hostname you will recognise, eg PINAS64.    
- Set a username as `pi` (if not `pi` then replace username `pi` in this outline with your chosen username) and
the password as something you will remember (you will need to enter it later during `SAMBA` setup,
and change all references of `pi` to your username).    
- Set you locale settings and keyboard layout (setting keyboard layout is important if in non-US non-GB country).    
- Choose the SERVICES tab.    
- Enable SSH with password authentification.    
- Choose the OPTIONS tab.    
- Disable telementry.    
Click SAVE.    
Click YES to apply OS customisation.    
Click YES to proceed.    

#### Boot the Raspberry Pi 5 and update system software    
Order of power up (at least the first time)
- Ensure the Pi 5 is powered off    
- Plug the SD card into the Pi 5    
- Power on each of the USB3 disks, wait 15 to 30 seconds for them to power-up and spin-up    
- Power on the Pi 5    

Once the Pi has finished booting to the desktop (leave it set to autologin)    
- Click Start, Preferences, Raspberry Pi Configuration    
- In the Localisation Tab, Set the Locale and then character set UTF-8, Timezone, Keyboard (setting keyboard is important if in non-US non-GB country), WiFi country, then click OK.    
- If prompted to reboot then click YES and reboot back to the desktop.    
- Click Start, Preferences, Raspberry Pi Configuration    
- In the System Tab, set Auto Logion ON, Splash Screen OFF    
- In the Interfaces Tab, set SSH ON, Raspberry Connect OFF, VNC ON    
- Click OK    
- If prompted to reboot then click YES and reboot.    

Once the Pi has finished booting to the desktop    
- Start a Terminal then update the system using    
```
sudo apt -y update
sudo apt -y full-upgrade
sudo apt -y dist-upgrade
```
If the Pi tells you to reboot, do so.

We choose to create some `alias` shortcut commands to make life easier, by editing script `~/.bashrc`. 
In Terminal, edit the existing file `~/.bashrc`
```
nano ~/.bashrc
```
Put this at the end of it:
```
# Add shortcut commands
# unalias checktemp
# unalias dir
alias checktemp='vcgencmd measure_temp'
alias dir='ls -alLh --color --group-directories-first'
# Get top process eating cpu
alias pscpu="ps auxf | sort -nr -k 3"
alias pscpu10="ps auxf | sort -nr -k 3 | head -10"
# Get top process eating memory
alias psmem="ps auxf | sort -nr -k 4"
alias psmem10="ps auxf | sort -nr -k 4 | head -10"
```
exit nano with `Control O` `Control X`.   

### Set the Router so this Pi has a Reserved fixed (permanent) DHCP IP Address Lease
In this outline the LAN IP Address range is 10.0.0.0/255.255.255.0 with the Pi 5 knowing itself of course on 127.0.0.1,
and the Router's IP Address lease for the Pi could be something like 10.0.0.18.    

_If you have a different IP Address/Range, substitute in the correct IP and Address range etc in the outline below._     

Normally the Pi will get a temporary DHCP IP Address Lease from the router, which may change over time as leases expire.    
To get a `fixed` IP address:    

On the Pi start a Terminal and do these commands to show the Pi's network name and IP address    
```
hostname -f
hostname -I
#ifconfig
```
The Pi's LAN IP address may be something like 10.0.0.18.    

Login to your router and look at the LAN connected devices, looking for the IP address matching the Pi.    

Head on to the Router's DHCP management area and allocated a Reserved fixed (permanent) DHCP IP address lease
for the Pi and apply/save that in the router. Reboot the Pi, then on the Pi start a Terminal and do    
```
hostname -f
hostname -I
#ifconfig
```
and notice the IP address and hope it matches the IP Address reservation you made on the router.    
If not, check what you have done on the router and fix it and reboot the Pi.    

### Ascertain disks info, specifically PARTUUID and mount point    
At this point, the USB3 disks should already be auto-mounted and you may see links to them on the desktop.
That's OK, we'll change all that to suit the NAS needs.    

Start a Terminal and use `sudo lsblk` to look at the connected disks, and see something like this:
```
sudo lsblk -o UUID,PARTUUID,NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL
```
```
UUID                                 PARTUUID                             NAME        FSTYPE  SIZE MOUNTPOINT          LABEL
                                                                          sda                 3.6T                     
                                     c8c72b90-6c8a-4631-9704-a3816695a6dc ├─sda1              128M                     
96DA1D13DA1CF0EB                     a175d2d3-c2f6-44d4-a5fc-209363280c89 └─sda2      ntfs    3.6T /media/pi/DISK2-4TB DISK2-4TB
                                                                          sdb                 4.5T                     
                                     c542d01e-9ac9-486f-98cb-4521e0fe54f8 ├─sdb1              128M                     
C4D05ABAD05AB302                     2d5599a2-aa11-4aad-9f75-7fca2078b38b └─sdb2      ntfs    4.5T /media/pi/DISK1-5TB DISK1-5TB
                                                                          mmcblk0            29.7G                     
9BE2-1346                            9fd862b3-01                          ├─mmcblk0p1 vfat    512M /boot/firmware      bootfs
12974fe2-889e-4060-b497-1d6ac3fbbb4b 9fd862b3-02                          └─mmcblk0p2 ext4   29.2G /                   rootfs
```
In that output, identify lines showing mount names for the USB3 disks, eg something like these:
```
UUID                                 PARTUUID                             NAME        FSTYPE  SIZE MOUNTPOINT          LABEL
C4D05ABAD05AB302                     2d5599a2-aa11-4aad-9f75-7fca2078b38b └─sdb2      ntfs    4.5T /media/pi/DISK1-5TB DISK1-5TB
96DA1D13DA1CF0EB                     a175d2d3-c2f6-44d4-a5fc-209363280c89 └─sda2      ntfs    3.6T /media/pi/DISK2-4TB DISK2-4TB
```
From each relevant partition we identify, look for the PARTUUID and save these somewhere, as we NEED the PARTUUIDs later.

If we wanted to cross-check disks, we could `sudo mount` like this and amongst them will be something like this:
```
$ sudo mount -l | grep "overlay\|disk"
/dev/sdb2 on /media/pi/DISK1-5TB type ntfs3 (rw,nosuid,nodev,relatime,uid=1000,gid=1000,windows_names,iocharset=utf8,uhelper=udisks2) [DISK1-5TB]
/dev/sda2 on /media/pi/DISK2-4TB type ntfs3 (rw,nosuid,nodev,relatime,uid=1000,gid=1000,windows_names,iocharset=utf8,uhelper=udisks2) [DISK2-4TB]
```

Now we have identified the correct partitions and their PARTUUID, and now need to identify the root folder names on them.    

Start `File Manager` and navigate to each of the partitions, something like:
- the media root folder is under `/media/pi/DISK1-5TB`    
- the media root folder is under `/media/pi/DISK2-4TB`

and locate the root folder in each partition which contains your media files 
... and make a note of these root folder names **alongside** the corresponding PARTUUID.    
So, you will have noted for each partition, the PARTUUID and the root folder name on that partition, eg for
```
# File Manager Folder Name
/media/pi/DISK1-5TB/ROOTFOLDER1
/media/pi/DISK2-4TB/ROOTFOLDER2
```
the [PARTUUID and root folder name] pair would be
```
PARTUUID                              root folder name
2d5599a2-aa11-4aad-9f75-7fca2078b38b  ROOTFOLDER1
a175d2d3-c2f6-44d4-a5fc-209363280c89  ROOTFOLDER2
```

#### Create new 'standardized' mount points for disks and 'virtual overlayed folder'
Start a Terminal and create some folders etc
```
# create a new mount point for SAMBA sharing
cd ~
sudo mkdir -v -m a=rwx /mnt/shared

# create new 'standardized' mount points for the external USB3 disks    
sudo mkdir -v -m a=rwx /mnt/shared/usb3disk1
sudo mkdir -v -m a=rwx /mnt/shared/usb3disk2

# create a new 'overlayfs' mount point for 'virtual overlayed folder' sharing via SAMBA and dlna and set protections
sudo mkdir -v -m a=rwx /mnt/shared/overlay
sudo chown -R -v pi:   /mnt/shared/overlay
sudo chmod -R -v a+rwx /mnt/shared/overlay

# ensure the 'shared' tree has the right ownership and permissions
sudo chown -R -v pi:  /mnt/shared
sudo chmod -R -v a+rwx /mnt/shared
```

#### Backup and Edit `/etc/fstab`    
To make the USB3 disk mounts happen at boot time into the mount points we just created, we must edit `/etc/fstab` and
use, for each partition, the PARTUUID and the root folder name on that partition which we collected earlier.    
Start a Terminal and run the nano editor:    
```
sudo cp -fv /etc/fstab /etc/fstab.bak
sudo nano  /etc/fstab
```

Using the nano editor, change fstab and add the following entries which must be in the specific order below.    
**Remember to change the `PARTUUID` values and the `overlay` `lowerdir=` values to correspond to the values we determined !**    
**Of course, if we have more disks then we**     
- **add more lines, one for each disk, remembering to update each `x-systemd.requires=` so they are
all in sequence and each new line requires the mount of the prior line**     
- **amend the `x-systemd.requires=` on the `overlay` line to reference the last disk mount line above**    
- **add more `lowerdir=` root folder names to the `overlay` line**    

So in our example it becomes
```
# https://askubuntu.com/questions/109413/how-do-i-use-overlayfs/1348932#1348932
# To set order/dependency of mounts in fstab file, we will declare systemd option "require" using syntax: x-systemd.require. 
# Argument for this option is mount point of the mount which should be successfully mounted before given mount.
# Mount each usb3 disk partition, each subsequent mount depending on the prior mount.
# Careful: "nofail" will cause the process to continue with no errors (avoiding a boot hand when a disk does not mount)
#          however the subsequently dependent mounts will fails as will the overlayfs mount
#             ... but at least we have booted, not halting boot with a failed fstab entry, and can fix that !
PARTUUID=2d5599a2-aa11-4aad-9f75-7fca2078b38b /mnt/shared/usb3disk1 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail 0 0
PARTUUID=a175d2d3-c2f6-44d4-a5fc-209363280c89 /mnt/shared/usb3disk2 ntfs x-systemd.requires=/mnt/shared/usb3disk1,defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail 0 0
# Create the overlayfs virtual folder, by overlaying the 2 root folders. 
# The overlayfs lowerdir folders in order Left to Right takes precedence when duplicate files are found.
overlay /mnt/shared/overlay overlay lowerdir=/mnt/shared/usb3disk1/ROOTFOLDER1:/mnt/shared/usb3disk2/ROOTFOLDER2,defaults,auto,noatime,nodiratime,nofail,users,ro,exec,x-systemd.mount-timeout=60,x-systemd.requires=/mnt/shared/usb3disk2,noatime,nodiratime,nofail 0 0
#
```

exit nano with `Control O` `Control X`.    

####  Reboot to see what happens with those mounts    
Reboot the Pi 5.    
Start a Terminal
```
# find our disks and overlays
sudo mount -l |  grep "overlay\|disk"
sudo df  |  grep "overlay\|disk"
```

If the mounts do not match what you specified in `etc/fstab`, then something is astray !  Check what you have done above.    

In a Terminal do an `ls -al` on each of the mounts, eg on `/mnt/shared/usb3disk1`, and also on the `/mnt/shared/overlay` folder to check they are visible.    

**If the files in the mounts do not match what you expect from `/etc/fstab`, then something is astray !  Check what has been done above.**    


#### Install and configure `SAMBA`
In a Terminal,    
```
sudo apt -y install samba samba-common-bin smbclient cifs-utils
# create the default user pi in creating the first samba user
sudo smbpasswd -a pi
# if prompted, enter the same password as the default user pi you setup earlier    
```


Edit the `SAMBA` config `/etc/samba/smb.conf`.    
```
sudo nano /etc/samba/smb.conf
```
Per https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html    
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
[overlayed_root_folders]
comment = RO access to overlayed root folders on USB3 disks using overlayfs
path = /mnt/shared/overlay
available = yes
force user = pi
writeable = no
read only = yes
browseable = yes
public=yes
guest ok = yes
guest only = yes
case sensitive = no
default case = lower
preserve case = yes
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
guest only = yes
case sensitive = no
default case = lower
preserve case = yes
follow symlinks = yes
wide links = yes
force create mode = 1777
force directory mode = 1777
inherit permissions = yes
```
exit nano with `Control O` `Control X`.    

Test the new SAMBA parameters in a Terminal:
```
sudo testparm
```

Restart Samba service, waiting 2 secs in between each command
```
sudo systemctl enable smbd
# wait 2 secs
sudo systemctl stop smbd
# wait 2 secs
sudo systemctl restart smbd
```

List the new Samba users (which can have different passwords to the Pi itself) and shares

```
sudo pdbedit -L -v
sudo net usershare info --long
sudo smbstatus
sudo smbstatus --shares # Will retrieve what's being shared and which machine (if any) is connected to what.
sudo hostname
sudo hostname --fqdn
sudo hostname --all-ip-addresses
```

You can now access the defined shares from a Windows machine or from an app that supports the SMB protocol.    
eg on a Windows 11 PC in Windows Explorer use the IP address of the Pi, eg ...    
`\\\\10.0.0.18\\`




#### Setup HD-IDLE ?????????????
Doing this: `sudo apt -y install hd-idle` and then these
```
sudo apt-cache show hd-idle
sudo apt list --installed | grep hd-idle
dpkg -l | grep hd-idle
```
all show version `1.05+ds-2+b1` which is very old.

This `https://github.com/adelolmo/hd-idle` shows at least release `1.21 / 2023-10-22` in    
`https://github.com/adelolmo/hd-idle/releases/download/v1.21/hd-idle_1.21_arm64.deb`

So, remove any existing install of hd-idle 
`sudo apt -y purge hd-idle`

```
#############################################################################################################################################
if [[ ${do_setup_hdidle} = true ]]; then
#############################################################################################################################################
#
echo "#-------------------------------------------------------------------------------------------------------------------------------------"
echo "#-------------------------------------------------------------------------------------------------------------------------------------"
echo ""
echo "# Install 'hd-idle' so that external USB3 disks spin down when idle and not wear out quickly."
echo ""
echo "# Some WD external USB3 disks won't spin down on idle and HDPARM and SDPARM don't work on them."
echo "# ... 'adelolmo' version of hd-idle appears to work, so let's use that."
echo ""
# https://www.htpcguides.com/spin-down-and-manage-hard-drive-power-on-raspberry-pi/
echo ""
echo "# FIRST USB3 DISK"
echo "#     USB3_DISK_NAME_1=${USB3_DISK_NAME_1}"
echo "#   USB3_DEVICE_NAME_1=${USB3_DEVICE_NAME_1}"
echo "#   USB3_DEVICE_UUID_1=${USB3_DEVICE_UUID_1}"
if [[ "${SecondDisk}" = "y" ]]; then
	echo "# SECOND USB3 DISK"
	echo "#    USB3_DISK_NAME_2=${USB3_DISK_NAME_2}"
	echo "#  USB3_DEVICE_NAME_2=${USB3_DEVICE_NAME_2}"
	echo "#  USB3_DEVICE_UUID_2=${USB3_DEVICE_UUID_2}"
fi
echo "# Attributes of FIRST USB3 DISK"
set -x
sudo blkid
sudo df
sudo lsblk
sudo blkid -U ${USB3_DEVICE_UUID_1}
sudo df -l /dev/${USB3_DISK_NAME_1}
sudo lsblk /dev/${USB3_DISK_NAME_1}
set +x
if [[ "${SecondDisk}" = "y" ]]; then
	echo "# Attributes of SECOND USB3 DISK"
	set -x
	sudo blkid -U ${USB3_DEVICE_UUID_2}
	sudo df -l /dev/${USB3_DISK_NAME_2}
	sudo lsblk /dev/${USB3_DISK_NAME_2}
	set +x
fi
echo ""
echo "# List and Remove any prior hd-idle package"
echo ""
set -x
sudo systemctl disable hd-idle
sleep 2s
sudo dpkg -l hd-idle
sudo dpkg -P hd-idle 
# dpkg -P is the one that works for us, also use 'apt purge' in case an old one was instaleld via apt
sudo apt purge -y hd-idle
set +x
#
echo ""
echo "# Install the more up-to-date release of 'adelolmo' version of hd-idle"
echo ""
# https://github.com/adelolmo/hd-idle
set -x
cd ~/Desktop
rm -fvr ./hd-idle
mkdir -pv hd-idle
cd hd-idle
hdidle_ver=1.16
hdidle_deb=hd-idle_${hdidle_ver}_arm64.deb
hdidle_url=https://github.com/adelolmo/hd-idle/releases/download/v${hdidle_ver}/${hdidle_deb}
sudo rm -vf "./${hdidle_deb}"
wget ${hdidle_url}
sudo dpkg -i "./${hdidle_deb}"
sudo dpkg -l hd-idle
cd ~/Desktop
set +x
echo ""
# option -d = debug
##Double check hd-idle works with your hard drive
##sudo hd-idle -t ${server_USB3_DEVICE_NAME} -d
#   #Command line options:
#   #-a name Set device name of disks for subsequent idle-time parameters -i. This parameter is optional in the sense that there's a default entry for all disks which are not named otherwise by using this parameter. This can also be a symlink (e.g. /dev/disk/by-uuid/...)
#   #-i idle_time Idle time in seconds for the currently named disk(s) (-a name) or for all disks.
#   #-c command_type Api call to stop the device. Possible values are scsi (default value) and ata.
#   #-s symlink_policy Set the policy to resolve symlinks for devices. If set to 0, symlinks are resolve only on start. If set to 1, symlinks are also resolved on runtime until success. By default symlinks are only resolve on start. If the symlink doesn't resolve to a device, the default configuration will be applied.
#   #-l logfile Name of logfile (written only after a disk has spun up or spun down). Please note that this option might cause the disk which holds the logfile to spin up just because another disk had some activity. On single-disk systems, this option should not cause any additional spinups. On systems with more than one disk, the disk where the log is written will be spun up. On raspberry based systems the log should be written to the SD card.
#   #-t disk Spin-down the specified disk immediately and exit.
#   #-d Debug mode. It will print debugging info to stdout/stderr (/var/log/syslog if started with systemctl)
#   #-h Print usage information.
## observe output
##Use Ctrl+C to stop hd-idle in the terminal
echo ""
echo ""
echo "# Modify the hd-idle configuration file to enable the service to automatically start and spin down drives"
echo ""
set -x
sudo systemctl stop hd-idle
sleep 2s
# default timeout 300s = 5 mins
# sda     timeout 900s = 15 mins
the_default_timeout=300
the_sda_timeout=900
set +x
echo ""
idle_opts="HD_IDLE_OPTS=\"-i ${the_default_timeout} "
idle_opts+=" -a ${USB3_DISK_NAME_1} -i ${the_sda_timeout} "
if [[ "${SecondDisk}" = "y" ]]; then
	idle_opts+=" -a ${USB3_DISK_NAME_2} -i ${the_sda_timeout} "
fi
idle_opts+=" -l /var/log/hd-idle.log\n\""
echo "Setting idle_opts=${idle_opts}"
echo ""
set -x
sudo cp -fv "/etc/default/hd-idle" "/etc/default/hd-idle.old"
sudo sed -i "s;START_HD_IDLE=;#START_HD_IDLE=;g" "/etc/default/hd-idle"
sudo sed -i "s;HD_IDLE_OPTS=;#HD_IDLE_OPTS=;g" "/etc/default/hd-idle"
sudo sed -i "1 i START_HD_IDLE=true" "/etc/default/hd-idle" # insert at line 1
sudo sed -i "$ a ${idle_opts}" "/etc/default/hd-idle" # insert as last line
sudo cat "/etc/default/hd-idle"
set +x
#sudo diff -U 10 "/etc/default/hd-idle.old" "/etc/default/hd-idle"
# start and enable start at system boot, per instructions https://github.com/adelolmo/hd-idle/
sudo systemctl stop hd-idle
sudo systemctl enable hd-idle
sudo systemctl restart hd-idle
sleep 2s
set +x
echo ""
sleep 2s
sudo cat /var/log/hd-idle.log
set +x
echo ""
echo "# Finished installation of hd-idle so that external USB3 disks spin down when idle and not wear out quickly."
echo ""
#
#############################################################################################################################################
fi ### if [[ ${do_setup_hdidle} ]]; then
#############################################################################################################################################
#
#
```

