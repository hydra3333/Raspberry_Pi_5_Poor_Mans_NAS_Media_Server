# WARNING: UNDER CONSTRUCTION

# DO NOT USE

# NOTHING WORKS YET

# Raspberry Pi 5 Poor Persons NAS Media Server    

## Outline    
If we have a PI 5 and some old USB3 disks (with their own power supply) and a couple of USB3 hubs laying around,
but can't afford a NAS box nor a 3D printer to print one nor a SATA hat for the Pi etc, then perhaps
cobble together a NAS / Media Server with what we have.

Together with a Pi 5 and an SD card we can use    
- 1 or 2 (say, 4-port) USB3 hubs plugged into the Pi 5 to connect many old USB3 disks to the Pi    
- 1 to 8 old USB3 disks plugged into the USB hubs    

With this harware we can readily serve up standard SAMBA SMB/CIFS file shares
and media files to devices across the LAN.   

## Why ?
Most ordinary people cannot afford expensive new bits like multiple NVME drives or Pi Hat's etc,
as shown on youtube 'how-to's !  It's great they show and test those things, but money doesn't grow on trees,
especially if we have kids and/or are retired.    

One could use `OpenMediaVault` or `Plex` more easily, but they connect to the internet to do 'stuff'.
I looked at `Plex` et al years ago and was very uncomfortable with the level of access installed packages potentially
provided to the vendor servers directly into my LAN and hence to all the devices on my LAN
... essentially permitting them unfettered invisible 'remote control' access if they so chose.
I valued my banking details and documents etc, choosing to limit exposure to that potential security hazard.    

This 'roll our own' approach minimises cost, and avoids the pain of getting 'done over' by our own hand - installing
packages known to interact of themselves in essentially unknown ways with (uncontrolled) vendors' servers
on the internet - at the cost of having to deal with more complexity ... safety first.

---

## General Approach
If one has, say, 1 to 8 old USB3 disks with volume labels `DISK1` ... `DISK8` all plugged into the one or two USB3 hubs,
and each disk has a single root folder `mediaroot` containing subfolders 
(these subfolders underneath `mediaroot` will be called 'top level media folder's) of media to be served.    
Note that some 'top level media folder's are duplicated across 2 or more other disks as backups.
```
DISK1 -- mediaroot --|--ClassicMovies
                     |--Footy-----------|--1997
                     |                  |--1998
                     |                  |--2003
                     |                  |--2004

DISK2 -- mediaroot --|--ClassicMovies
                     |--Documentaries
                     |--Footy-----------|--1997
                     |                  |--1998
                     |                  |--2003
                     |                  |--2004
                     |--Movies
                     |--SciFi

DISK3 -- mediaroot --|--ClassicMovies
                     |--Documentaries
                     |--Footy-----------|--1997
                     |                  |--1998
                     |                  |--2003
                     |                  |--2004
                     |--OldMovies
                     |--SciFi
```

This outline assumes we know how to use the nano editor, if not please google it, if using another editor then cool !

---

## Acknowledgements    

### thagrol    
https://forums.raspberrypi.com/viewtopic.php?p=2236572#p2236547    

Building A Pi Based NAS    
https://forums.raspberrypi.com/viewtopic.php?t=327444    

Using fstab A Beginner's Guide    
https://forums.raspberrypi.com/viewtopic.php?t=302752    

---

## Essential Preparation    
### First, prepare the disks, security, disk volume labels, folder structures, files    
Assuming we have USB3 disks created as GPT disks (not Dynamic Disks) and formatted as NTFS    
(since Windows PCs are often used to create media files, and WIndows only really likes disks formatted as NTFS)
we need to prepare every disk to appear and behave in a consistent way.

For every disk, change it's disk volume label to be like `DISK1`  **in strict numerical sequence** through to `DISK8` 
and ensure they are definitely unique across disks. If we are unsure how to do that, try    
https://www.google.com.au/search?q=how+to+change+an+NTFS+disk+volume+label+in+windows+11    

On every disk, in Windows change it's Security so that inbuilt username `everyone` is added with `Full Control` access.
In Windows File Manager
- right click on a drive letter
- choose Properties
- choose Security tab
- click the `Edit` button
- click the `Add` button
- enter the word `everyone` and click the `OK` button
- Ensure `Full control` is ticked and click `Apply`;
if prompted, allow it to change all folders and files on the disk and ignore all errors

On each disk, create one root folder named like `mediaroot` containing subfolders 
(these subfolders underneath `mediaroot` will be called 'top level media folder's.

Under the 'top level media folder's on the disks, place the media files in a reasonably consistent
(including filename capitalisation) subfolder structure of our choice.
The same subfolder names and files could exist on every disk or we could
spread out the media files and subfolders across disks to balance disk usage...    

Note that some 'top level media folder' trees are duplicated across 2 or more disks to make a backup.  
**There will a regular `sync` process for mirroring 'main' 'top level media folder's onto 'backup' disks.**    
The 'main' disk is always the 'first found disk' having a nominated 'top level media folder' (eg 'Footy')
where a 'first found disk' ('ffd') is determined by the leftmost underlying disk in the
linux fstab entry for 'mergerfs' (these are specified in left to right order).    

So, in the example below - assuming the LtoR mount order in the fstab entry for package `mergerfs`
is `DISK1,DISK2,DISK3` - then the 'ffd' for each 'top level media folder' will be:
- `ClassicMovies` : `DISK1 mediaroot`
- `Documentaries` : `DISK2 mediaroot`
- `Footy        ` : `DISK1 mediaroot`
- `Movies       ` : `DISK2 mediaroot`
- `OldMovies    ` : `DISK3 mediaroot`
- `SciFi        ` : `DISK2 mediaroot`    

Also note that all of the 'top level media folders' are important enough to have a backup (eg 'Movies', 'OldMovies'). 
```
DISK1 -- mediaroot --|--ClassicMovies
                     |--Footy-----------|--1997
                     |                  |--1998
                     |                  |--2003
                     |                  |--2004

DISK2 -- mediaroot --|--ClassicMovies
                     |--Documentaries
                     |--Footy-----------|--1997
                     |                  |--1998
                     |                  |--2003
                     |                  |--2004
                     |--Movies
                     |--SciFi

DISK3 -- mediaroot --|--ClassicMovies
                     |--Documentaries
                     |--Footy-----------|--1997
                     |                  |--1998
                     |                  |--2003
                     |                  |--2004
                     |--OldMovies
                     |--SciFi
```

In this outline we'll assume we have only the USB3 disks. We can add more as needed,
just keep an eye on the mandatory 'disk volume label' naming (eg `DISK1`) 
in line with the example model above.    

The 'top level media folder's (eg `Movies`) can be named anything we like, just ensure
consistency in capitalization across disks and do not use `space` characters and
especially not `special characters` anywhere !   

Later, we could manually shuffle individual 'top level media folder' trees from one disk to another 
(by copying/moving between the underlying linux disk mounts) to perhaps balance
disk space usage etc; the next `sync` process wll automatically detect it and stick
with its 'fdd' rule in single-directional mirroring from 'ffd' to 'backup's.    

---

## Prepare the hardware    
A quick note: we leave disks **strictly** powered off at this point
because for the first few times the Pi 5 is powered on,
the process of the Pi 5 seeing and recognising the
USB3 disks is **fraught with issues** when the USB3 disks are all powered.    
I have seen it freeze multiple times and not proceed to finishing the boot process.    
We need to baby the Pi 5 and power them on slowly and carefully, later.    

First ensuring that power switch is off where the Pi's power block plugs in,    
- ensure all USB3 disks are powered off and will remain so until required later    
- plug the Pi into a screen with the HDMI cable (sophisticated users may choose to instead use `SSH` or `RaspberryPi Connect` later, `VNC` is unavailable until set `ON` after first boot)    
- plug in the Pi's power cable into the Pi    
- plug in the USB3 hub(s) into the USB3 slots in the Pi, but leave all disks powered off    
- plug the external USB3 disks into the USB3 hubs, but leave all disks powered off    

That's the hardware prepared and plugged in ... and still powered off.    

In the outline below, we'll assume only 3 USB3 disks. we can add more as we need,
just keep an eye on the disk naming and folder structures in line with the model above.    

---

## Install Raspberry Pi OS with `autologin` to the SD card    
Run the `Raspberry Pi Imager` on a PC to put the full 64 bit `Raspberry Pi OS` image to an SD card in the usual way    
- Choose to "Edit Settings" and then the GENERAL tab.    
- Set a Hostname we will recognise, eg PINAS64.    
- Set a username as `pi` (if not `pi` then replace username `pi` in this outline with the chosen username) and
the password as something we will remember (we will need to enter it later during `SAMBA` setup,
and change all references of `pi` to the username).    
- Set we locale settings and keyboard layout (setting keyboard layout is important if in non-US non-GB country).    
- Choose the SERVICES tab.    
- Enable SSH with password authentification.    
- Choose the OPTIONS tab.    
- Disable telementry.    
Click SAVE.    
Click YES to apply OS customisation.    
Click YES to proceed.    

---

## Boot the Raspberry Pi 5 and update the system    
**1. Order of power up (for this first time)**    
- Ensure the Pi 5 is powered off    
- Plug the SD card into the Pi 5    
- Power on the Pi 5    


**2. Once the Pi has finished booting to the desktop (leave it set to autologin)**    
For me, the the Pi does not properly recognise the country and keyboard I specify whilst creating the SD card image.    
Set our locale settings and keyboard layout and WiFi country (setting keyboard layout is important if in non-US non-GB country).    
- Click Start, Preferences, Raspberry Pi Configuration    
- In the System Tab, set **Auto Logon ON**, **Splash Screen OFF**   
- In the Interfaces Tab, sey **VNC ON**, **SSH ON**, perhaps **Raspberry Connect OFF**    
- Find the right Tab and set **usb_max_current_enable ON**     
- In the Localisation Tab, Set the Locale and then character-set UTF-8, Timezone, Keyboard (setting keyboard is important if in non-US non-GB country), WiFi country, then click OK.    
- If prompted to reboot then click YES and reboot back to the desktop.    
- Click OK    
- If prompted to reboot then click YES and reboot.    

If it reboots, then once the Pi has finished booting to the desktop:    


**3. Force PCI Express Gen 3.0 speeds after next boot (8 GT/sec, almost double the speed) on the Pi 5; in a Terminal**    
and per https://www.jeffgeerling.com/blog/2023/forcing-pci-express-gen-30-speeds-on-pi-5     
Edit the firmware's config file:    
```
sudo nano /boot/firmware/config.txt 
```
then check-for/modify/add the following 3 lines so they are at the end of the config file ...    
also, to disable WiFi and BlueTooth add the 3 lines after  that:    
```
# Enable PCIE v3
dtparam=pciex1
dtparam=pciex1_gen=3
# Disable WiFi and BlueTooth
dtoverlay=disable-wifi
dtoverlay=disable-bt
```
exit nano with `Control O` `Control X`.    


**4. Enable the external RTC battery, assuming we purchased and installed one**    
Per https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#real-time-clock-rtc    
The Raspberry Pi 5 includes an RTC module. 
This can be battery powered via the J5 (BAT) connector on the board located to the right of the USB-C power connector:     
https://www.raspberrypi.com/documentation/computers/images/j5.png?hash=70853cc7a9a01cd836ed8351ece14d59    
We can set a wake alarm which will switch the board to a very low-power state (approximately 3mA). 
When the alarm time is reached, the board will power back on. 
This can be useful for periodic jobs like time-lapse imagery.
To support the low-power mode for wake alarms, edit the bootloader configuration:    
```
sudo -E rpi-eeprom-config --edit
```
add the following two lines.
```
POWER_OFF_ON_HALT=1
WAKE_ON_GPIO=0
```
The RTC is equipped with a **constant-current (3mA) constant-voltage charger**.    
Charging of the battery is disabled by default.    
To constantly charge the battery at the proper voltage, add `rtc_bbat_vchg` to `/boot/firmware/config.txt`:
```
sudo nano /boot/firmware/config.txt
```
add
```
dtparam=rtc_bbat_vchg=3000000
```
exit nano with `Control O` `Control X`.   

**NOTE: Later (not now) after we reboot, trickle recharging with the right voltage setting will take effect.**    
We can check the `sysfs` files to ensure that the charging voltage was correctly set.
```
/sys/devices/platform/soc/soc:rpi_rtc/rtc/rtc0/charging_voltage:0
/sys/devices/platform/soc/soc:rpi_rtc/rtc/rtc0/charging_voltage_max:4400000
/sys/devices/platform/soc/soc:rpi_rtc/rtc/rtc0/charging_voltage_min:1300000
```
If we like we could test the battery RTC functionality with:
```
echo +10 | sudo tee /sys/class/rtc/rtc0/wakealarm
sudo halt
```
That will halt the board into a very low-power state, then wake and restart after 10 seconds.    
The RTC also provides the time on boot e.g. in `dmesg`, for use cases that lack access to NTP:
```
[    1.295799] rpi-rtc soc:rpi_rtc: setting system clock to 2023-08-16T15:58:50 UTC (1692201530)
```
NOTE: The RTC is still usable even when there is no backup battery attached to the J5 connector.    


**5. Check/Enable `usb_max_current_enable` manually; in a Terminal**    
We'll try to avoid issues with several USB3 disks at boot time.    
Info in  https://www.raspberrypi.com/documentation/computers/configuration.html    
Use nano to edit `/boot/firmware/config.txt`.    
```
sudo nano /boot/firmware/config.txt
```
add it if it doesn't already exist in the config file    
```
usb_max_current_enable=1
```
exit nano with `Control O` `Control X`. 


**6. Disable USB Autosuspend; in a Terminal**    
It has been written that Autosuspend might cause issues with certain USB devices. 
We can disable it by adding `usbcore.autosuspend=-1` to the file `/boot/firmware/cmdline.txt`.
```
sudo nano /boot/firmware/cmdline.txt
```
and add a space and then this ` usbcore.autosuspend=-1` at very end of the single line.
exit nano with `Control O` `Control X`.


**7. Update the system; in a Terminal**    

Use nano to edit the APT sources for updates:    
```
sudo nano /etc/apt/sources.list
# Now in nano `un-comment` all of the `deb-src` lines by removing the # at the start of those lines.
```
exit nano with `Control O` `Control X`.    
Update the system; in a Terminal:    
```
sudo apt -y update
sudo apt -y full-upgrade
sudo apt -y dist-upgrade
```


**8. Run `raspi-config` to configure more system settings; in a Terminal**    

Use 
```
sudo raspi-config
```
Reboot the Pi now. In a Terminal:
```
sudo reboot now
```
This will also cause all of the changes above to take effect.


**9. Install some software; in a Terminal**    
```
cd ~/Desktop
#
# Install disk params checker, eg sudo hdparm -Tt /dev/sda
sudo apt -y install hdparm
#
# Install a tool which can be used to turn EOL inside text files from windows type to unix type
sudo apt install -y dos2unix
#
# Install the curl and wget tools to download support files if required
sudo apt install -y curl
sudo apt install -y wget
#
```

See hd-idle here `https://github.com/adelolmo/hd-idle`     
Note: that site shows a minimum of release `1.21 / 2023-10-22` in    
`https://github.com/adelolmo/hd-idle/releases/download/v1.21/hd-idle_1.21_arm64.deb`    
Download and Install the most up-to-date release of the 'adelolmo' version of `hd-idle` direct from the author:    
```
cd ~/Desktop
touch /home/pi/Desktop/hd-idle.log
chmod -c a=rw -R /home/pi/Desktop/hd-idle.log
#
sudo rm -vf hd-idle_1.21_arm64.deb
wget https://github.com/adelolmo/hd-idle/releases/download/v1.21/hd-idle_1.21_arm64.deb
sudo dpkg -i "./hd-idle_1.21_arm64.deb"
sudo dpkg -l hd-idle
#Stop `hd-idle`
sudo systemctl stop hd-idle
cd ~/Desktop
```

See `mergerfs` here `https://github.com/trapexit/mergerfs/releases`    
Download and Install the most up-to-date release of `mergerfs` direct from the author:    
```
# For this to run on Pi 4 and newer:
#    <ver>=2.40.2
#    <rel>=bookworm
#    <arch>=arm64
# wget https://github.com/trapexit/mergerfs/releases/download/<ver>/mergerfs_<ver>.debian-<rel>_<arch>.deb
# dpkg -i mergerfs_<ver>.debian-<rel>_<arch>.deb
# sudo apt-get install -f
#
cd ~/Desktop
wget -v https://github.com/trapexit/mergerfs/releases/download/2.40.2/mergerfs_2.40.2.debian-bookworm_arm64.deb
sudo dpkg --install mergerfs_2.40.2.debian-bookworm_arm64.deb
sudo dpkg --status mergerfs
# Fix any missing dependencies or conflicts.
sudo apt-get install -f
```

Install SAMBA to serve up standard SAMBA SMB/CIFS file shares across the network
```
sudo apt -y install samba samba-common-bin smbclient cifs-utils
sudo systemctl stop smbd
```

Install miniDLNA and then stop the service so we can configure it    
```
sudo apt install -y minidlna
sudo systemctl stop minidlna 
sudo systemctl enable minidlna
```


**10. Add user `pi` into groups `plugdev` and `systemd-journal`; in a Terminal**    
```
sudo usermod -a -G plugdev pi
sudo usermod -a -G systemd-journal pi
# plugdev:         Allows members to mount (only with the options nodev and nosuid, for security reasons) and umount removable devices through pmount.
# systemd-journal: Since Debian 8 (Jessie), members of this group can use the command 'journalctl' and read log files of systemd (in /var/log/journal).
```


**11. Make this server IPv4 only, by disabling IPv6; in a Terminal**    
```
sudo sysctl net.ipv6.conf.all.disable_ipv6=1 
sudo sysctl -p
sudo sed -i.bak "s;net.ipv6.conf.all.disable_ipv6;#net.ipv6.conf.all.disable_ipv6;g" "/etc/sysctl.conf"
echo net.ipv6.conf.all.disable_ipv6=1 | sudo tee -a "/etc/sysctl.conf"
sudo sysctl -p
```


**12. Increase system parameter `fs.inotify.max_user_watches` from default 8192 (used by miniDLNA to monitor changes to filesystems); in a Terminal**    
```
# max_user_watches=262144
# Per https://wiki.debian.org/minidlna and https://wiki.archlinux.org/title/ReadyMedia
# To avoid Inotify errors, Increase the number for the system :
# In /etc/sysctl.conf Add: 'fs.inotify.max_user_watches=262144' in a blank line by itself.
# Increase system max_user_watches to avoid this error:
# WARNING: Inotify max_user_watches [8192] is low or close to the number of used watches [2] and I do not have permission to increase this limit.  Please do so manually by writing a higher value into /proc/sys/fs/inotify/max_user_watches.
# set a new TEMPORARY limit with:
# sudo sed -i.bak "s;8192;262144;g" "/proc/sys/fs/inotify/max_user_watches" # this fails with no permissions
# ... So,
#set a new TEMPORARY limit with:
sudo cat /proc/sys/fs/inotify/max_user_watches
sudo sysctl fs.inotify.max_user_watches=262144
sudo sysctl -p
# set a new PERMANENT limit with ('sudo tee -a' is used so sudo can get us access to append to the target file):
sudo sed -i.bak "s;fs.inotify.max_user_watches=;#fs.inotify.max_user_watches=;g" "/etc/sysctl.conf"
echo fs.inotify.max_user_watches=262144 | sudo tee -a "/etc/sysctl.conf"
sudo sysctl -p
```


**13. We choose to create some `alias` shortcut commands to make life easier, by editing script `~/.bashrc`; in a Terminal**    
```
# Edit the existing file '~/.bashrc'
nano ~/.bashrc
```
Put this at the end of it:
```
# Add shortcut commands
# unalias checktemp
# unalias dir
alias checktemp='vcgencmd measure_temp'
alias dir='ls -alLh --color --group-directories-first'
# Show top process using cpu
alias pscpu="ps auxf | sort -nr -k 3"
alias pscpu20="ps auxf | sort -nr -k 3 | head -20"
# Show top process using memory
alias psmem="ps auxf | sort -nr -k 4"
alias psmem20="ps auxf | sort -nr -k 4 | head -20"
#
# Use in a Terminal like:
#    checktemp
#    dir \etc
#    pscpu20
#    psmem20
```
exit nano with `Control O` `Control X`.   


**14. Set the LAN Router so this Pi has a Reserved fixed (permanent) DHCP IP Address Lease**    
Normally the Pi will get a temporary DHCP IP Address Lease from the router, which may change over time as leases expire.    

In this outline the LAN IP Address range is 10.0.0.0/255.255.255.0 with the Pi 5 knowing itself of course on 127.0.0.1,
and the Router's IP Address lease for the Pi could be something like 10.0.0.18.    

_If we have a different IP Address/Range, substitute in the correct IP and Address range etc._     

To allocate a `fixed` IP address, on the Pi start a Terminal and do these commands
to show the Pi's network name and IP address lease     
```
hostname -f
hostname -I
#ifconfig
```
The Pi's LAN IP address may be something like 10.0.0.18.    

Login to the router, look at the LAN connected devices, looking for the IP address matching the Pi.    

Go to the Router's DHCP management area and allocated a Reserved fixed (permanent) DHCP IP address lease
for the Pi and apply/save that in the router.    

Reboot the Pi, then on the Pi start a Terminal and do    
```
hostname -f
hostname -I
#ifconfig
```
and notice the IP address and hope it matches the IP Address reservation we made on the router.    
If not, check what we have done on the router and fix it and reboot the Pi.    


**15. Reboot the Pi 5 for everything to take effect; in a Terminal**    
```
sudo reboot
```

---

## Tell the Pi about the new Disks

**BEFORE TURNING ON ANY DISKS**    
Per this thread    
https://forums.raspberrypi.com/viewtopic.php?t=374341#p2240823    

The **automount** feature may (and does, for unlucky users!) freeze our system and stop it from booting.    

**1. DISABLE THE AUTOMOUNT FEATURE BEFORE TURNING ON ANY DISKS !!**    

**When the Pi is booted to the desktop, start a Terminal:**    
**In the Desktop start 'File Manager'**    

**- menu Edit -> Preferences**    
**- click Volume Management**    
**UNTICK these 3:**    
**[ ] Mount mountable volumes automatically on program startup (this is the automounter, not fstab processing)**    
**[ ] Mount removable media automatically when they are inserted**    
**[ ] Show available options for removable media when they are inserted**    

**then click Close**    


**2. Create folders to contain the disk mount points; in a Terminal**    
Even if we have less than 8 disks, create the other mount points anyway so that later we can easily add more disks.
```
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
```

**3. Gracefully shutdown for all that to take effect at next boot**    
Shut down the Pi in the standard way; in a Terminal    
```
sudo shutdown
```
and wait for it to finish runnning all of the graceful shutdown tasks and power off.    


**4. Power on all disks, then power on the Pi**
Boot the Pi 5 to the desktop.


**5. Identify the Disk PARTUUID for all USB3 disks, create fstab entries to mount disks at boot**    
This is where it becomes important that we have already named all of our disk volumes properly
and have created a root folder in each where the root folder's name matches the disk label.    

IE:    
- For every disk, it's disk volume label should be like `DISK1`  **in strict numerical sequence** through to `DISK8` 
and ensure they are definitely unique across disks.    
- On each disk, we must have created one root folder named like `mediaroot`.

OK, we are going to neeed 2 `Terminal` windows open to do this.
Start 2 `Terminal`s and position them side by side. 
Overlapping windows is OK, as long as we can see most of each window and easily click between then to change window focus.

In the leftmost window, edit `/etc/fstab` ready to add new items.
```
sudo nano /etc/fstab
```
Preparation: add these lines to the end of `fstab`:    
```
#
# x-systemd.wants=srv-usb3disk1.mount       Means it wants (not requires) the nominated mount point but does not cause a fail if it does not.
# x-systemd.after=srv-usb3disk1.mount       Means it wouldo like to be mounted after the nominated mount point but does not cause a fail if it does not.
#
# UN-COMMENT A LINE BELOW FOR EACH DISK WE HAVE, DEPENDING ON HOW MANY DISKS WE HAVE, AND POP IN THE CORRECT PARTUUID FOR EACH DISK
#PARTUUID= /srv/usb3disk1 /srv/usb3disk1 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount 0 0
#PARTUUID= /srv/usb3disk2 /srv/usb3disk2 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount 0 0
#PARTUUID= /srv/usb3disk3 /srv/usb3disk3 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount 0 0
#PARTUUID= /srv/usb3disk4 /srv/usb3disk4 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount 0 0
#PARTUUID= /srv/usb3disk5 /srv/usb3disk5 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount 0 0
#PARTUUID= /srv/usb3disk6 /srv/usb3disk6 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount 0 0
#PARTUUID= /srv/usb3disk7 /srv/usb3disk7 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount 0 0
#PARTUUID= /srv/usb3disk8 /srv/usb3disk8 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk7.mount 0 0
#
# UN-COMMENT ONE OF THE LINES BELOW DEPENDNG ON HOW MANY DISKS WE HAVE
# for disks 1 to 1:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk1.mount 0 0
# for disks 1 to 2:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount 0 0
# for disks 1 to 3:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount 0 0
# for disks 1 to 4:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount 0 0
# for disks 1 to 5:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount 0 0
# for disks 1 to 6:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount 0 0
# for disks 1 to 7:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk7.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk7.mount 0 0
# for disks 1 to 8:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk8.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk7.mount,x-systemd.after=srv-usb3disk8.mount 0 0
#
```
Now **un-comment ONLY** lines to match the number if disks we have, eg: for 3 disks it would be:
```
# UN-COMMENT A LINE BELOW FOR EACH DISK WE HAVE, DEPENDING ON HOW MANY DISKS WE HAVE, AND POP IN THE CORRECT PARTUUID FOR EACH DISK
PARTUUID= /srv/usb3disk1 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount 0 0
PARTUUID= /srv/usb3disk2 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount 0 0
PARTUUID= /srv/usb3disk3 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount 0 0
#PARTUUID= /srv/usb3disk4 /srv/usb3disk4 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount 0 0
#PARTUUID= /srv/usb3disk5 /srv/usb3disk5 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount 0 0
#PARTUUID= /srv/usb3disk6 /srv/usb3disk6 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount 0 0
#PARTUUID= /srv/usb3disk7 /srv/usb3disk7 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount 0 0
#PARTUUID= /srv/usb3disk8 /srv/usb3disk8 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk7.mount 0 0
```
Leave `nano` open editing `fstab` in that `Terminal` and swap to the other `Terminal` to enter other commands.

Now we have taken some time editing that, allowing the disks to be recognised by the OS biut not mounted,
use these commands to see if we can find them:
```
sudo blkid
sudo lsblk -o UUID,PARTUUID,NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL
```
Eventually, we "should" see the disks appear (notice lines with the disk labels appears)
similar to the below .. if not check our connections etc.

```
sudo lsblk -o UUID,PARTUUID,NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL
```
In this example it looks like this, notice the disk `LABEL` column showing out partitions and their corresponding `PARTUUID`:
```
UUID                                 PARTUUID                             NAME        FSTYPE  SIZE MOUNTPOINT     LABEL
                                                                          sda                 4.5T                
                                     c542d01e-9ac9-486f-98cb-4521e0fe54f8 sda1              128M                
C4D05ABAD05AB302                     2d5599a2-aa11-4aad-9f75-7fca2078b38b sda2        ntfs    4.5T                DISK1-5TB
                                                                          sdb                 3.6T                
                                     417f0090-5de0-41c8-be32-af5d4634bfc9 sdb1               16M                
04EC17A9EC179450                     e5ff156e-b704-40a9-86d5-5c36c35d6095 sdb2        ntfs    3.6T                DISK6-4Tb
                                                                          sdc                 3.6T                
                                     c8c72b90-6c8a-4631-9704-a3816695a6dc sdc1              128M                
96DA1D13DA1CF0EB                     a175d2d3-c2f6-44d4-a5fc-209363280c89 sdc2        ntfs    3.6T                DISK2-4TB
                                                                          sdd                10.9T                
E2E6E093E6E068ED                     d6a52d8b-f1e6-424a-8150-dba9453aa7e7 sdd1        ntfs   10.9T                DISK4-12Tb
                                                                          sde                 9.1T                
704645134644DC0A                     cd74d88b-71f1-40b3-bafb-60444215f655 sde1        ntfs    9.1T                DISK5-10Tb
                                                                          sdf                 7.3T                
121E55501E552E4B                     27891019-f894-4e9b-b326-5f9d10c5c2cf sdf1        ntfs    7.3T                DISK7-8Tb
                                                                          sdg                 5.5T                
10D23DFDD23DE81C                     9a63b215-bcf1-462b-89d2-56979cec6ed8 sdg1        ntfs    5.5T                DISK3-6Tb
                                                                          mmcblk0            29.7G                
9BE2-1346                            4b536088-01                          mmcblk0p1   vfat    512M /boot/firmware bootfs
12974fe2-889e-4060-b497-1d6ac3fbbb4b 4b536088-02                          mmcblk0p2   ext4   29.2G /              rootfs
```
Now, identify the partitions to mount (check the disk `LABEL`), 
then select/copy the **full `PARTUUID`** for
that disk and paste it immediately to the right of the `=` sign for that disk (no spaces).    
In this example the result of doing that with 3 disks looks like this:
```
# UN-COMMENT A LINE BELOW FOR EACH DISK WE HAVE, DEPENDING ON HOW MANY DISKS WE HAVE, AND POP IN THE CORRECT PARTUUID FOR EACH DISK
PARTUUID=2d5599a2-aa11-4aad-9f75-7fca2078b38b /srv/usb3disk1 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount 0 0
PARTUUID=a175d2d3-c2f6-44d4-a5fc-209363280c89 /srv/usb3disk2 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount 0 0
PARTUUID=9a63b215-bcf1-462b-89d2-56979cec6ed8 /srv/usb3disk3 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount 0 0
#PARTUUID= /srv/usb3disk4 /srv/usb3disk4 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount 0 0
#PARTUUID= /srv/usb3disk5 /srv/usb3disk5 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount 0 0
#PARTUUID= /srv/usb3disk6 /srv/usb3disk6 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount 0 0
#PARTUUID= /srv/usb3disk7 /srv/usb3disk7 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount 0 0
#PARTUUID= /srv/usb3disk8 /srv/usb3disk8 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk7.mount 0 0
```
For the moment LEAVE AS COMMENTED-OUT ALL OF THESE LINES below including the one matching the number of disks we have (in this example, 3)
```
#
# UN-COMMENT ONE OF THE LINES BELOW DEPENDNG ON HOW MANY DISKS WE HAVE
# for disks 1 to 1:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk1.mount 0 0
# for disks 1 to 2:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount 0 0
# for disks 1 to 3:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount 0 0
# for disks 1 to 4:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount 0 0
# for disks 1 to 5:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount 0 0
# for disks 1 to 6:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount 0 0
# for disks 1 to 7:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk7.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk7.mount 0 0
# for disks 1 to 8:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk8.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk7.mount,x-systemd.after=srv-usb3disk8.mount 0 0
#
```
save and exit nano with `Control O` `Control X`.     

Make the operating system notice these new changes in fstab:
```
sudo systemctl daemon-reload
```
Attempt to mount the disks via `fstab`. We should see something like the output below.    
If not, immediatelty re-edit fstab and comment out the lines and save `fstab` before we then fix what
has happened by cross-checking all of the relevant lines ! And repeat this step.    
```
sudo mount -v -a
```
which should yield something like this:
```
/proc                    : already mounted
/boot/firmware           : already mounted
/                        : ignored
/srv/usb3disk1           : successfully mounted
/srv/usb3disk2           : successfully mounted
/srv/usb3disk3           : successfully mounted
```
Congratulations, the USB3 disks are now mounted and will be mounted during every boot from now on.    
Check what's mounted using:
```
sudo mount -v | grep srv
```
```
mount -v | grep srv
/dev/sda2 on /srv/usb3disk1 type fuseblk (rw,nosuid,nodev,noatime,user_id=0,group_id=0,default_permissions,allow_other,blksize=4096,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount)
/dev/sdc2 on /srv/usb3disk2 type fuseblk (rw,nosuid,nodev,noatime,user_id=0,group_id=0,default_permissions,allow_other,blksize=4096,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount)
/dev/sdf1 on /srv/usb3disk3 type fuseblk (rw,nosuid,nodev,noatime,user_id=0,group_id=0,default_permissions,allow_other,blksize=4096,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount)
```
Notice in the last line `1/` `2/` `3/` means it is `usb3disk1` `usb3disk2` `usb3disk3` in that Left-to-Right order.    
They only mounted correctly in that order due to the mount dependencies we set in the individual mounts above.    


---

## Configure `HD-IDLE` to ensure disks are not constantly spun up

Per `https://www.htpcguides.com/spin-down-and-manage-hard-drive-power-on-raspberry-pi/`
some WD an other external USB3 disks won't spin down on idle and HDPARM and SDPARM don't work on them
... the `adelolmo` version of `hd-idle` appears to work, so let's use that.  

**Do NOT install like this** since, above, we instead installed the newer version direct from the author:
```
# since this show versions `1.05+ds-2+b1` which is very old.
sudo apt -y install hd-idle
# and then these
sudo apt-cache show hd-idle
sudo apt list --installed | grep hd-idle
dpkg -l | grep hd-idle
```

Note the `/dev` entries for our disk `LABEL`s below:    
```
ls -al /dev/disk/by-label
```
```
total 0
drwxr-xr-x 2 root root 140 Aug  1 17:44 .
drwxr-xr-x 9 root root 180 Aug  1 17:44 ..
lrwxrwxrwx 1 root root  15 Aug  1 17:44 bootfs -> ../../mmcblk0p1
lrwxrwxrwx 1 root root  10 Aug  1 17:44 DISK1-5TB -> ../../sda2
lrwxrwxrwx 1 root root  10 Aug  1 17:44 DISK2-4TB -> ../../sdb2
lrwxrwxrwx 1 root root  10 Aug  1 17:44 DISK3-6Tb -> ../../sdc1
lrwxrwxrwx 1 root root  15 Aug  1 17:44 rootfs -> ../../mmcblk0p2

```
See the **first 3 letters** of where it points to, denoting which device it is assigned.    
In this instance the disks are:
```
sda
sdb
sdc
```

To configure `hd-idle` for those disks:

Ensure `hd-idle` is stopped:
```
sudo systemctl stop hd-idle
```

After edit `etc/default/hd-idle` to change `hd-idle` parameters
```
sudo nano /etc/default/hd-idle
```
```
# note: https://github.com/adelolmo/hd-idle/
#
# 1. Change line near the top from
# START_HD_IDLE=false
#    to 
# START_HD_IDLE=true
#
# 2. Then add another line at the end:
#    adding EVERY DISK, using the noted '/dev/sda' etc
#
#Double check hd-idle works with the hard drive
#   #Command line options:
#   #-a name Set device name of disks for subsequent idle-time parameters -i. This parameter is optional in the sense that there's a default entry for all disks which are not named otherwise by using this parameter. This can also be a symlink (e.g. /dev/disk/by-uuid/...)
#   #-i idle_time Idle time in seconds for the currently named disk(s) (-a name) or for all disks.
#   #-c command_type Api call to stop the device. Possible values are scsi (default value) and ata.
#   #-s symlink_policy Set the policy to resolve symlinks for devices. If set to 0, symlinks are resolve only on start. If set to 1, symlinks are also resolved on runtime until success. By default symlinks are only resolve on start. If the symlink doesn't resolve to a device, the default configuration will be applied.
#   #-l logfile Name of logfile (written only after a disk has spun up or spun down). Please note that this option might cause the disk which holds the logfile to spin up just because another disk had some activity. On single-disk systems, this option should not cause any additional spinups. On systems with more than one disk, the disk where the log is written will be spun up. On raspberry based systems the log should be written to the SD card.
#   #-t disk Spin-down the specified disk immediately and exit.
#   #-d Debug mode. It will print debugging info to stdout/stderr (/var/log/syslog if started with systemctl)
#   #-h Print usage information.
# default timeout 300s = 5 mins
# sda sdb sdc etc     timeout 900s = 15 mins
START_HD_IDLE=true
# UN-COMMENT ONE OF THESE LINES IF sda,sd...etc MATCHES ALL OF YOUR USB3 DISKS AND ONLY THOSE USB3 DISKS
#HD_IDLE_OPTS="-i 300 -l /home/pi/Desktop/hd-idle.log -a /dev/sda -i 900"
#HD_IDLE_OPTS="-i 300 -l /home/pi/Desktop/hd-idle.log -a /dev/sda -i 900 -a /dev/sdb -i 900"
#HD_IDLE_OPTS="-i 300 -l /home/pi/Desktop/hd-idle.log -a /dev/sda -i 900 -a /dev/sdb -i 900 -a /dev/sdc -i 900"
#HD_IDLE_OPTS="-i 300 -l /home/pi/Desktop/hd-idle.log -a /dev/sda -i 900 -a /dev/sdb -i 900 -a /dev/sdc -i 900 -a /dev/sdd -i 900"
#HD_IDLE_OPTS="-i 300 -l /home/pi/Desktop/hd-idle.log -a /dev/sda -i 900 -a /dev/sdb -i 900 -a /dev/sdc -i 900 -a /dev/sdd -i 900 -a /dev/sde -i 900"
#HD_IDLE_OPTS="-i 300 -l /home/pi/Desktop/hd-idle.log -a /dev/sda -i 900 -a /dev/sdb -i 900 -a /dev/sdc -i 900 -a /dev/sdd -i 900 -a /dev/sde -i 900 -a /dev/sdf -i 900"
#HD_IDLE_OPTS="-i 300 -l /home/pi/Desktop/hd-idle.log -a /dev/sda -i 900 -a /dev/sdb -i 900 -a /dev/sdc -i 900 -a /dev/sdd -i 900 -a /dev/sde -i 900 -a /dev/sdf -i 900 -a /dev/sdg -i 900"
#HD_IDLE_OPTS="-i 300 -l /home/pi/Desktop/hd-idle.log -a /dev/sda -i 900 -a /dev/sdb -i 900 -a /dev/sdc -i 900 -a /dev/sdd -i 900 -a /dev/sde -i 900 -a /dev/sdf -i 900 -a /dev/sdg -i 900 -a /dev/sdh -i 900"
```

To enable `hd-idle` on reboot and then restart, in a Terminal:
```
sudo systemctl enable hd-idle   
sudo systemctl stop hd-idle
sudo systemctl restart hd-idle
# wait 2 secs
sudo cat /home/pi/Desktop/hd-idle.log
#
sudo journalctl -u hd-idle.service | grep hd-idle| tail -n 20
#
sudo systemctl status hd-idle.service | tail -n 20
```
Look at the status and logs:
```
# wait 2 secs
sudo cat /home/pi/Desktop/hd-idle.log
#
# Display the status of the service
sudo systemctl status hd-idle.service | tail -n 20
# Display some fo the system log
sudo journalctl -u hd-idle.service | grep hd-idle| tail -n 20
```

---

## Configure `mergerfs` for a virtual disk    
### Virtual "merge" disks for serving as if one disk    
#### finds media using "first found disk" in Left to Right mount order    

**1. Configure mergerfs ...**    

Check the mount definitions for underlying disks to be 'merged' are correctly in `fstab` as you need them:    
```
sudo cat /etc/fstab
```
So, `fstab` should look something like this, with the individual disk mounts
un-commented and the `mergerfs` mounts still commented out.    
```
# UN-COMMENT A LINE BELOW FOR EACH DISK WE HAVE, DEPENDING ON HOW MANY DISKS WE HAVE, AND POP IN THE CORRECT PARTUUID FOR EACH DISK
PARTUUID=2d5599a2-aa11-4aad-9f75-7fca2078b38b /srv/usb3disk1 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount 0 0
PARTUUID=a175d2d3-c2f6-44d4-a5fc-209363280c89 /srv/usb3disk2 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount 0 0
PARTUUID=9a63b215-bcf1-462b-89d2-56979cec6ed8 /srv/usb3disk3 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount 0 0
#PARTUUID= /srv/usb3disk4 /srv/usb3disk4 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount 0 0
#PARTUUID= /srv/usb3disk5 /srv/usb3disk5 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount 0 0
#PARTUUID= /srv/usb3disk6 /srv/usb3disk6 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount 0 0
#PARTUUID= /srv/usb3disk7 /srv/usb3disk7 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount 0 0
#PARTUUID= /srv/usb3disk8 /srv/usb3disk8 ntfs defaults,auto,nofail,users,rw,exec,umask=000,dmask=000,fmask=000,uid=pi,gid=pi,noatime,nodiratime,nofail,x-systemd.device-timeout=240,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk7.mount 0 0
#
# UN-COMMENT ONE OF THE LINES BELOW DEPENDNG ON HOW MANY DISKS WE HAVE
# for disks 1 to 1:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk1.mount 0 0
# for disks 1 to 2:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount 0 0
# for disks 1 to 3:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount 0 0
# for disks 1 to 4:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount 0 0
# for disks 1 to 5:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount 0 0
# for disks 1 to 6:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount 0 0
# for disks 1 to 7:
/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk7.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk7.mount 0 0
# for disks 1 to 8:
#/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk8.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk4.mount,x-systemd.after=srv-usb3disk5.mount,x-systemd.after=srv-usb3disk6.mount,x-systemd.after=srv-usb3disk7.mount,x-systemd.after=srv-usb3disk8.mount 0 0
#
```
The individual disk mount lines have soft dependencies so that each disk tries to get mounted after the previous disk in the sequence.    
Notice that The `mergerfs` lines have dependencies 

Notice the lines at the end of `fstab` starting with `/srv/usb3disk*/mediaroot`.   
When we un-comment this and remount disks, it will permit `mergerfs` to mount all disks in order `/srv/usb3disk1` ...    

So, edit `fstab`    
```
sudo nano /etc/fstab
```
and remove the '#' from the start of that line so it looks a bit like:    
```
# for disks 1 to 3:
/srv/usb3disk*/mediaroot /srv/media mergerfs defaults,ro,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,x-systemd.wants=srv-usb3disk3.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount,x-systemd.after=srv-usb3disk3.mount 0 0
```
exit nano with `Control O` `Control X`. 

**2. Re-load `fstab` and mount unmounted disks**    
```
sudo systemctl daemon-reload
sudo mount -v -a
```
Check the results:    
```
sudo mount -v | grep srv
```
which should look a bit like:    
```
/dev/sda2 on /srv/usb3disk1 type fuseblk (rw,nosuid,nodev,noatime,user_id=0,group_id=0,default_permissions,allow_other,blksize=4096,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount)
/dev/sdc2 on /srv/usb3disk2 type fuseblk (rw,nosuid,nodev,noatime,user_id=0,group_id=0,default_permissions,allow_other,blksize=4096,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount)
/dev/sdf1 on /srv/usb3disk3 type fuseblk (rw,nosuid,nodev,noatime,user_id=0,group_id=0,default_permissions,allow_other,blksize=4096,x-systemd.mount-timeout=240,x-systemd.wanted-by=srv-media.mount,x-systemd.after=srv-usb3disk1.mount,x-systemd.after=srv-usb3disk2.mount)
1/mediaroot:2/mediaroot:3/mediaroot on /srv/media type fuse.mergerfs (ro,relatime,user_id=0,group_id=0,default_permissions,allow_other)
```

**3. See the "merged" disks/folders appear as one folder**    
```
ls -al /srv/media
```
```
drwxrwxrwx  1 pi   pi     12288 Aug  1 17:37 .
drwxr-xr-x 11 root root    4096 Aug  1 16:45 ..
drwxrwxrwx  1 pi   pi    524288 Jul 25 23:35 ClassicMovies
drwxrwxrwx  1 pi   pi    196608 Jul 24 14:17 Documentaries
drwxrwxrwx  1 pi   pi     49152 Jul 26 00:08 Footy
drwxrwxrwx  1 pi   pi         0 Jul 21 22:51 Movies
drwxrwxrwx  1 pi   pi         0 Jul 22 00:55 OldMovies
drwxrwxrwx  1 pi   pi    163840 Jul 26 01:21 SciFi
```

We'll serve up this merged folder `/srv/media` via `SAMBA` and `miniDLNA`, 
so that devices on the lan need not know which disk things are on.

---

## Configure `SAMBA`to create file shares on the LAN

**1. Ensure `SAMBA` is stopped; in a Terminal:**    
```
sudo systemctl stop smbd
```

**2. Configure `SAMBA` user; in a Terminal:**    
Create the default user pi in creating the first samba user
```
sudo smbpasswd -a pi
# if prompted, enter the same password as the default user pi we setup earlier    
```

**3. Configure `SAMBA`; in a Terminal:**    
Set up a folder for the `SAMBA` log.    
```
cd ~/Desktop
#
touch /home/pi/Desktop/samba.log
chmod -c a=rw -R /home/pi/Desktop/samba.log
#
cd ~/Desktop
```

Edit the `SAMBA` config `/etc/samba/smb.conf`    
```
sudo nano /etc/samba/smb.conf
```
Per https://www.samba.org/samba/docs/current/man-html/smb.conf.5.html    
Here are some `[global]` `SAMBA` settings in `/etc/samba/smb.conf`.    
Use nano to check for and fix each of them in the `[global]` section      
- if they do not exist, create them    
- if they are commented out, un-comment and fix them    
- if they contain different values, comment that line out and create a new line underneath with the correct setting

```
workgroup = WORKGROUP
hosts 10.0.0.1/255.255.255.0 127.0.0.1
log file = /home/pi/Desktop/samba.log.%m
max log size = 20000
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

Below are the definitions for 3 live shares, with 5 more commented out.    
Copy and paste it to the end of `/etc/samba/smb.conf` and un-comment any shared we need to make live.     
```
# DEFINE THE SHARES
[media]
comment = ReadOnly access to merged 'top level media folders' on USB3 disks
path = /srv/media
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

[usb3disk1]
comment = rw access to USB3 disk usb3disk1
path = /srv/usb3disk1
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

[usb3disk2]
comment = rw access to USB3 disk usb3disk2
path = /srv/usb3disk2
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

[usb3disk3]
comment = rw access to USB3 disk usb3disk3
path = /srv/usb3disk3
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

#[usb3disk4]
#comment = rw access to USB3 disk usb3disk4
#path = /srv/usb3disk4
#available = yes
#force user = pi
#writeable = yes
#read only = no
#browseable = yes
#public=yes
#guest ok = yes
#guest only = yes
#case sensitive = no
#default case = lower
#preserve case = yes
#follow symlinks = yes
#wide links = yes
#force create mode = 1777
#force directory mode = 1777
#inherit permissions = yes

#[usb3disk5]
#comment = rw access to USB3 disk usb3disk5
#path = /srv/usb3disk5
#available = yes
#force user = pi
#writeable = yes
#read only = no
#browseable = yes
#public=yes
#guest ok = yes
#guest only = yes
#case sensitive = no
#default case = lower
#preserve case = yes
#follow symlinks = yes
#wide links = yes
#force create mode = 1777
#force directory mode = 1777
#inherit permissions = yes

#[usb3disk6]
#comment = rw access to USB3 disk usb3disk6
#path = /srv/usb3disk6
#available = yes
#force user = pi
#writeable = yes
#read only = no
#browseable = yes
#public=yes
#guest ok = yes
#guest only = yes
#case sensitive = no
#default case = lower
#preserve case = yes
#follow symlinks = yes
#wide links = yes
#force create mode = 1777
#force directory mode = 1777
#inherit permissions = yes

#[usb3disk7]
#comment = rw access to USB3 disk usb3disk7
#path = /srv/usb3disk7
#available = yes
#force user = pi
#writeable = yes
#read only = no
#browseable = yes
#public=yes
#guest ok = yes
#guest only = yes
#case sensitive = no
#default case = lower
#preserve case = yes
#follow symlinks = yes
#wide links = yes
#force create mode = 1777
#force directory mode = 1777
#inherit permissions = yes

#[usb3disk8]
#comment = rw access to USB3 disk usb3disk8
#path = /srv/usb3disk8
#available = yes
#force user = pi
#writeable = yes
#read only = no
#browseable = yes
#public=yes
#guest ok = yes
#guest only = yes
#case sensitive = no
#default case = lower
#preserve case = yes
#follow symlinks = yes
#wide links = yes
#force create mode = 1777
#force directory mode = 1777
#inherit permissions = yes
```
exit nano with `Control O` `Control X`.    


**4. Test the new `SAMBA` parameters; in a Terminal:**    

Test the new `SAMBA` parameters
```
sudo testparm
```

**5. Restart the `SAMBA` service; in a Terminal:**    

Restart the `SAMBA` service, waiting 2 secs in between each command    
```
sudo systemctl enable smbd
# wait 2 secs

sudo systemctl stop smbd
# wait 2 secs

sudo systemctl restart smbd
```

**6. List the new `SAMBA` users; in a Terminal:**    

List the new `SAMBA` users (which can have different passwords to the Pi itself) and shares    
```
sudo pdbedit -L -v
sudo net usershare info --long
sudo smbstatus
sudo smbstatus --shares # Will retrieve what's being shared and which machine (if any) is connected to what.
sudo hostname
sudo hostname --fqdn
sudo hostname --all-ip-addresses
```

**7. How to access the Pi shares from Windows**    

We can now access the `SAMBA` shares on the Pi from a Windows PC or from an app that supports the SMB protocol.    
eg on a Windows PC in Windows Explorer, use the IP address of the Pi in the folder path text bar at the top, eg ...    

Assuming the Pi 5's IP address on the LAN is 10.0.0.18, then:    
```
REM read-only virtual folder of 'merged' disk folders, eg for consumption by media players
\\10.0.0.18\media

REM Below are are-write 'file shares' use for copy/delete new media to
REM 'ffd' into 'top level media folder' and subfolders on various disks,
REM according to our 'ffd's and 'top level media folder's backup strategy.
REM The nightly SYNC process will take care of rippling changes to all 'ffd's for 'top level media folder's
REM over to other disks containing backups of files in 'top level media folder's.

REM DISK1 as read-write ... copy/delete new media to 'ffd' subfolders here, according to disk spreading and diska backup strategy
\\10.0.0.18\usb3disk1

REM DISK2 as read-write (copy new media to subfolders here, depending on how full this disk is)
\\10.0.0.18\usb3disk2

REM DISK3 as read-write (copy new media to subfolders here, depending on how full this disk is)
\\10.0.0.18\usb3disk3
```

---

## Install and configure `miniDLNA` to serve media on the LAN via DLNA

#### NOTE: we install the miniDLNA index db onto USB3 DISK1 rather than the SD card    
####       since it is faster, and the SD card won't wear out quicker due to index rebuilds    

1. **Ensure we un-install any prior `miniDLNA`; in a Terminal**    
```
sudo systemctl stop minidlna
```

2. **Remove any prior config items and index db; in a Terminal**    
```
sudo rm -vfR "/var/log/minidlna.log"
sudo rm -vfR "/run/minidlna"
# note: the next lines may fail, ignore any fails:
sudo rm -vfR "/home/pi/Desktop/minidlna"
```

3. **Add users to `miniDLNA` Groups, and vice versa; in a Terminal**    
```
sudo usermod -a -G pi minidlna
sudo usermod -a -G minidlna pi
sudo usermod -a -G minidlna root
sudo usermod -a -G root minidlna
```

4. **Fix ownerships etc, create folders for db and log at the top of external USB3 disk DISK1; in a Terminal**    

```
sudo chmod -c a=rwx -R         "/etc/minidlna.conf"
sudo chown -c -R pi:minidlna   "/etc/minidlna.conf"
#
sudo mkdir -pv                 "/home/pi/Desktop/minidlna"
sudo chmod -c a=rwx -R         "/home/pi/Desktop/minidlna"
sudo chown -c -R pi:minidlna   "/home/pi/Desktop/minidlna"
#
sudo chmod -c a=rwx -R         "/run/minidlna"
sudo chown -c -R pi:minidlna   "/run/minidlna"
#
sudo touch                     "/run/minidlna/minidlna.pid"
sudo chmod -c a=rwx -R         "/run/minidlna/minidlna.pid"
sudo chown -c -R pi:minidlna   "/run/minidlna/minidlna.pid"
#
sudo mkdir -pv                 "/home/pi/Desktop/minidlna/cache"
sudo chmod -c a=rwx -R         "/home/pi/Desktop/minidlna/cache"
sudo chown -c -R pi:minidlna   "/home/pi/Desktop/minidlna/cache"
#
sudo touch                     "/home/pi/Desktop/minidlna/minidlna.log"
sudo chmod -c a=rwx            "/home/pi/Desktop/minidlna/minidlna.log"
sudo chown -c -R pi:minidlna   "/home/pi/Desktop/minidlna/minidlna.log"
```

5. **Change the config to align with out disk/folder arrangement etc; in a Terminal**    

Backup and edit the miniDLNA config file:    
```
sudo cp -fv "/etc/minidlna.conf" "/etc/minidlna.conf.original"
sudo nano "/etc/minidlna.conf"
```
now in nano,
```
# ignore these 3 lines which are commented out...
##minidlna_refresh_log_file=/home/pi/Desktop/minidlna/minidlna_refresh.log
##minidlna_refresh_sh_file=/home/pi/Desktop/minidlna/minidlna_refresh.sh
##minidlna_restart_refresh_sh_file=/home/pi/Desktop/minidlna/minidlna_restart_refresh.sh

# Find and change line `media_dir=/var/lib/minidlna` to comment it out with a preceding #:
##media_dir=/var/lib/minidlna

# Find and change line `album_art_names=` to comment it out with a preceding #:
##album_art_names=

# Find and un-comment and/or change/add line `#friendly_name=` to:
friendly_name=PINAS64-minidlna

# Find and un-comment and/or change/add line `#model_name=` to:
model_name=PINAS64-miniDLNA

# Find and un-comment and/or change/add line `#merge_media_dirs=` to:
merge_media_dirs=no

# Find and un-comment and/or change/add line `#db_dir=/var/cache/minidlna` to:
db_dir=/home/pi/Desktop/minidlna/cache

# Find and un-comment and/or change/add line `#log_dir=/var/log/minidlna` to:
log_dir=/home/pi/Desktop/minidlna

# inotify=yes and notify_interval=895 work together for miniDLNA to discover added and modified files
# Find and un-comment and/or change/add line `#inotify=yes` to:
inotify=yes

# inotify=yes and notify_interval=895 work together for miniDLNA to discover added and modified files
# Find and un-comment and/or change/add line `#notify_interval=895` (5 seconds under 15 minutes) to:
notify_interval=895

# Find and un-comment and/or change/add line `#strict_dlna=no` to:
strict_dlna=yes

# Find and un-comment and/or change/add line `#max_connections=50` to a number expected for this LAN:
# (many clients open several simultaneous connections while streaming)
max_connections=30

# Find and un-comment and/or change/add line `#log_level=general,artwork,database,inotify,scanner,metadata,http,ssdp,tivo=warn` to:
log_level=general,artwork,database,inotify,scanner,metadata,http,ssdp,tivo=info

# Find and un-comment and/or change/add line `#wide_links=no` to:
wide_links=yes

# now ADD the line to expose the mergerfs media folder ...
root_container=PVA,/srv/media
##media_dir=PVA,/srv/media

# now ADD any lines to match the folders we need to expose from with the merged folder tree
# THE ENTRIES BELOW MUST EXACTLY MATCH THE FOLDERS WE WISH DLNA TO EXPOSE
# THE EXAMPLE BELOW INCLUDES COMMENTED-OUT UNUSED FOLDERS
#media_dir=PVA,/srv/media/BigIdeas
#media_dir=PVA,/srv/media/ClassicDocumentaries
media_dir=PVA,/srv/media/ClassicMovies
media_dir=PVA,/srv/media/Documentaries
#media_dir=PVA,/srv/media/Family_Photos
media_dir=PVA,/srv/media/Footy
media_dir=PVA,/srv/media/Movies
#media_dir=PVA,/srv/media/Movies_unsorted
media_dir=PVA,/srv/media/Music
#media_dir=PVA,/srv/media/MusicVideos
media_dir=PVA,/srv/media/OldMovies
media_dir=PVA,/srv/media/SciFi
#media_dir=PVA,/srv/media/Series
```
Restart miniDLNA and force a db reload, whihc will take a long time to index
```
sudo systemctl stop minidlna 
sudo systemctl restart minidlna 
sudo systemctl reload minidlna
sudo systemctl force-reload minidlna 
sudo systemctl status minidlna | tail -n 50
tail -n 50 /home/pi/Desktop/minidlna/minidlna.log
```
The minidlna service comes with a small internal web server and web-interface.    
This web-interface is just for informational purposes.    
We will not be able to configure anything in it.    
However, it gives us a short information screen indicating how many files have been found by minidlna.    
To access the web-interface, open our browser of choice and enter url http://127.0.0.1:8200    
```
curl -i http://127.0.0.1:8200
curl -i http://10.0.0.18:8200
```

Debian miniDLNA man page:    
```
minidlnad	[-f config_file] [-d] [-v] [-u user] [-i interface] [-p port] [-s serial] [-m model_number] [-t notify_interval] [-P pid_filename] [-w url] [-S] [-L] [-R]
minidlnad	[-h | -V]

DESCRIPTION
The minidlnad daemon is a DLNA/UPnP-AV server sharing media files (video, music and pictures) to clients on your network. 
Clients are typically multimedia players such as vlc, totem and xbmc, and devices such as portable media players, 
smartphones, televisions, video game entertainment systems and blu-ray players.

By default, minidlnad listens on all the network interfaces (except loopback) for clients. 
This behavior can be changed on the command-line using the -i option, or in the configuration file 
through the network_interface option (see minidlna.conf(5) for details).

OPTIONS
Most of the options below can also be set in a configuration file, as described in minidlna.conf(5).

-d					Activate debug mode (do not daemonize).
-f config_file		Specify the location of the configuration file. Uses /etc/minidlna.conf by default.
-h					Show help and exit.
-i interface		Network interface to listen on. Can be specified more than once.
-L					Do not create playlists.
-m model_number		Model number the daemon will report to clients in its XML description.
-P pid_filename		PID file to use; the default is /run/minidlna/minidlna.pid.
-p port				Port number to listen on.
-R					Forces a full rescan of the media files. First it will remove all cached data and database. Any bookmarks will be lost.
-r					Do a non-destructive rescan of the media files on start-up.
-S					Stay foreground. Can be used when minidlnad is being managed by systemd
-s serial			Serial number the daemon will report to clients in its XML description.
-t notify_interval	Notify interval, in seconds; defaults to 895 seconds.
-u user				Specify which user minidlnad should run as, instead of root; user can either be a numerical UID or a user name.
-V					Show the program version and exit.
-v					Verbose output.
-w url				Sets the presentation url; the default is http address.
```



## UNDER CONSTRUCTION for miniDLNA

**Under Construction for miniDLNA**    
```
minidlna_refresh_sh_file=/home/pi/Desktop/minidlna/minidlna_refresh.sh
minidlna_refresh_log_file=/home/pi/Desktop/minidlna/log/minidlna_refresh.log
minidlna_restart_refresh_sh_file=/home/pi/Desktop/minidlna/minidlna_restart_refresh.sh
```


#### create an outline from an older miniDLNA setup script from this:    
```

set +x
echo ""
sudo rm -vf "${minidlna_main_log_file}"
sudo rm -vf "${minidlna_refresh_log_file}"
sudo touch "${minidlna_refresh_log_file}"
echo ""
echo "Create the .sh used by crontab to refresh the db every night. ${minidlna_refresh_sh_file}"
echo ""
set -x
sudo rm -vf "${minidlna_refresh_sh_file}"
sudo touch "${minidlna_refresh_sh_file}"
sudo chmod -c a=rwx "${minidlna_refresh_sh_file}"
set +x
echo "#!/bin/bash" >> "${minidlna_refresh_sh_file}"
echo "set -x" >> "${minidlna_refresh_sh_file}"
echo "# ${minidlna_refresh_sh_file}" >> "${minidlna_refresh_sh_file}"
echo "# used by crontab to refresh the the db every night" >> "${minidlna_refresh_sh_file}"
echo "sudo systemctl stop minidlna" >> "${minidlna_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_refresh_sh_file}"
echo "sudo systemctl restart minidlna" >> "${minidlna_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_refresh_sh_file}"
echo "echo 'Wait 15 minutes for minidlna to index media files'" >> "${minidlna_refresh_sh_file}"
echo "echo 'For progress do in another terminal window: cat ${main_log_dir}'" >> "${minidlna_refresh_sh_file}"
echo "sleep 900s" >> "${minidlna_refresh_sh_file}"
echo "set +x" >> "${minidlna_refresh_sh_file}"
echo "# ${minidlna_refresh_sh_file}" >> "${minidlna_refresh_sh_file}"
set -x
sudo cat "${minidlna_refresh_sh_file}"
set +x
echo ""
echo "Create the .sh used by a user to manually refresh the minidlna db. ${minidlna_restart_refresh_sh_file}"
echo ""
set -x
sudo rm -vf "${minidlna_restart_refresh_sh_file}"
sudo touch "${minidlna_restart_refresh_sh_file}"
sudo chmod -c a=rwx "${minidlna_restart_refresh_sh_file}"
set +x
echo "#!/bin/bash" >> "${minidlna_restart_refresh_sh_file}"
echo "set -x" >> "${minidlna_restart_refresh_sh_file}"
echo "# ${minidlna_restart_refresh_sh_file}" >> "${minidlna_restart_refresh_sh_file}"
echo "# used in ~/Desktop for a user to manually refresh the the db" >> "${minidlna_restart_refresh_sh_file}"
echo "sudo systemctl stop minidlna" >> "${minidlna_restart_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_restart_refresh_sh_file}"
echo "sudo systemctl restart minidlna" >> "${minidlna_restart_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_restart_refresh_sh_file}"
echo "echo 'Wait 15 minutes for minidlna to index media files'" >> "${minidlna_restart_refresh_sh_file}"
echo "echo 'For progress do in another terminal window: cat ${main_log_dir}'" >> "${minidlna_restart_refresh_sh_file}"
echo "sleep 900s" >> "${minidlna_restart_refresh_sh_file}"
echo "#" >> "${minidlna_restart_refresh_sh_file}"
echo "cat \"${minidlna_main_log_file}\"" >> "${minidlna_restart_refresh_sh_file}"
echo "#" >> "${minidlna_restart_refresh_sh_file}"
echo "set +x" >> "${minidlna_restart_refresh_sh_file}"
echo "# ${minidlna_restart_refresh_sh_file}" >> "${minidlna_restart_refresh_sh_file}"
set -x
sudo cat "${minidlna_restart_refresh_sh_file}"
set +x
echo ""
echo "Add the 2:00 am nightly crontab job to re-index miniDLNA (${minidlna_refresh_sh_file})"
echo ""
# https://stackoverflow.com/questions/610839/how-can-i-programmatically-create-a-new-cron-job
#The layout for a cron entry is made up of six components: minute, hour, day of month, month of year, day of week, and the command to be executed.
# m h  dom mon dow   command
# * * * * *  command to execute
# ┬ ┬ ┬ ┬ ┬
# │ │ │ │ │
# │ │ │ │ │
# │ │ │ │ └───── day of week (0 - 7) (0 to 6 are Sunday to Saturday, or use names; 7 is Sunday, the same as 0)
# │ │ │ └────────── month (1 - 12)
# │ │ └─────────────── day of month (1 - 31)
# │ └──────────────────── hour (0 - 23)
# └───────────────────────── min (0 - 59)
# https://stackoverflow.com/questions/610839/how-can-i-programmatically-create-a-new-cron-job
# <minute> <hour> <day> <month> <dow> <tags and command>
echo "#"
echo "# crontab List BEFORE contab ADD:"
echo "#"
set -x
sudo crontab -l # before
crontab -l # before
set +x
echo "#"
echo "# Adding crontab as user pi (no sudo):"
echo "#"
# escaped path for use in: sed "/findstring/d"
EscapedPath=`echo "${minidlna_refresh_sh_file}" | sed 's:/:\\\/:g'`
set -x
cd ~/Desktop
sudo rm -vf "./local_crontab.txt" "./local_crontab_tmp.txt"
crontab -l > "./local_crontab.txt"
sed -i "/no crontab for $(whoami)/d" "./local_crontab.txt"
cat "./local_crontab.txt"
sed -i "/${EscapedPath}/d" "./local_crontab.txt"
cat "./local_crontab.txt"
echo "0 2 * * * ${minidlna_refresh_sh_file} 2>&1 >> ${minidlna_refresh_log_file}" >> "./local_crontab.txt"
cat "./local_crontab.txt" | sort | uniq  > "./local_crontab_tmp.txt"
mv -fv "./local_crontab_tmp.txt" "./local_crontab.txt"
cat "./local_crontab.txt"
crontab "./local_crontab.txt"
rm -vf "./local_crontab.txt"
set +x
echo "#"
echo "# crontab List AFTER contab ADD:"
echo "#"
set -x
sudo crontab -l # after
crontab -l # after
set +x
echo "#"
echo "# syslog AFTER contab ADD:"
echo "#"
set -x
sudo grep CRON /var/log/syslog
set +x
echo ""
echo "# Start miniDLNA: Force a re-load of miniDLNA to ensure it starts re-looking for new files."
echo ""
set -x
sudo ls -al "/run/minidlna"
sudo systemctl stop minidlna
sleep 2s
sudo systemctl restart minidlna
sleep 2s
set +x
echo "#"
echo "# The minidlna service comes with a small webinterface. "
echo "# This webinterface is just for informational purposes. "
echo "# We will not be able to configure anything here. "
echo "# However, it gives we a nice and short information screen how many files have been found by minidlna. "
echo "# minidlna comes with it’s own webserver integrated. "
echo "# This means that no additional webserver is needed in order to use the webinterface."
echo "# To access the webinterface, open our browser of choice and enter url http://127.0.0.1:8200"
echo ""
set -x
curl -i http://127.0.0.1:8200
set +x
echo ""
# The actual streaming process
# A short overview how a connection from a client to the configured and running minidlna server could work. 
# In this scenario we simply use a computer which is in the same local area network than the server. 
# As the client software we use the Video Lan Client (VLC). 
# Simple, robust, cross-platform and open source. 
# After starting VLC, go to the playlist mode by pressing CTRL+L in windows. 
# We will now see on the left side a category which is called Local Network. 
# Click on Universal Plug’n’Play which is under the Local Network category. 
# We will then see a list of available DLNA service within our local network. 
# In this list we should see our DLNA server. 
# Navigate through the different directories for music, videos and pictures and select a file to start the streaming process
echo ""
#
set -x
sudo ls -al "/run/minidlna"
set +x
echo ""
set -x
sudo ls -al "${minidlna_main_log_file}"
sudo cat "${minidlna_main_log_file}"
set +x
echo ""
set -x
sudo ls -al "${minidlna_refresh_log_file}"
sudo cat "${minidlna_refresh_log_file}"
set +x
echo ""
#
```

---

---

---

---

---

---

---





# END OF LEGITIMATE TEXT Here

# IGNORE EVERYTHING BELOW



```
MergerFS
   Homepage:          https://github.com/trapexit/mergerfs
   GitHub Repository: https://github.com/trapexit/mergerfs
   Other              https://github.com/trapexit/mergerfs/wiki/Real-World-Deployments
                      https://perfectmediaserver.com/02-tech-stack/mergerfs/

                      https://docs.readthedocs.io/en/latest/intro/getting-started-with-sphinx.html
SnapRAID
   Homepage:          https://www.snapraid.it/
   GitHub Repository: https://github.com/amadvance/snapraid/ ... not https://github.com/snapraid/snapraid
   Other              https://www.snapraid.it/manual
                      https://sourceforge.net/projects/snapraid/
                      https://sourceforge.net/p/snapraid/discussion/1677233/
```




## Install and configure `miniDLNA` to serve media on the LAN via DLNA

# UNDER CONSTRUCTION

#### NOTE: we install the miniDLNA index db onto USB3 DISK1 rather than the SD card    
####       since it is faster, and the SD car won't wear out quicker due to index rebuilds    

1. **Ensure we un-install any prior `miniDLNA`; in a Terminal**    
```
sudo systemctl stop minidlna
sleep 2s
sudo systemctl disable minidlna
sleep 2s
sudo apt purge minidlna -y
sudo apt autoremove -y
```

2. **Remove any prior config items and index db; in a Terminal**    
```
sudo rm -vfR "/etc/minidlna.conf"
sudo rm -vfR "/var/log/minidlna.log"
sudo rm -vfR "/run/minidlna"
# note: the next lines may fail, ignore any fails:
sudo rm -vfR "/srv/usb3disk1/minidlna"
```

3. **Install `miniDLNA`, enable, and then stop the service so we can configure it; in a Terminal**    
```
sudo apt install -y minidlna
sudo systemctl stop minidlna 
sudo systemctl enable minidlna
```

4. **Add users to `miniDLNA` Groups and vice versa; in a Terminal**    
```
sudo usermod -a -G pi minidlna
sudo usermod -a -G minidlna pi
sudo usermod -a -G minidlna root
sudo usermod -a -G root minidlna
```

5. **Fix ownerships etc, create folders for db and log at the top of external USB3 disk DISK1; in a Terminal**    

```
sudo chmod -c a=rwx -R         "/etc/minidlna.conf"
sudo chown -c -R pi:minidlna   "/etc/minidlna.conf"
#
sudo mkdir -pv                 "/srv/usb3disk1/minidlna"
sudo chmod -c a=rwx -R         "/srv/usb3disk1/minidlna"
sudo chown -c -R pi:minidlna   "/srv/usb3disk1/minidlna"
#
sudo chmod -c a=rwx -R         "/run/minidlna"
sudo chown -c -R pi:minidlna   "/run/minidlna"
#
sudo touch                     "/run/minidlna/minidlna.pid"
sudo chmod -c a=rwx -R         "/run/minidlna/minidlna.pid"
sudo chown -c -R pi:minidlna   "/run/minidlna/minidlna.pid"
#
sudo mkdir -pv                 "/srv/usb3disk1/minidlna/cache"
sudo chmod -c a=rwx -R         "/srv/usb3disk1/minidlna/cache"
sudo chown -c -R pi:minidlna   "/srv/usb3disk1/minidlna/cache"
#
sudo mkdir -pv                 "/srv/usb3disk1/minidlna/log"
sudo touch                     "/srv/usb3disk1/minidlna/log/minidlna.log"
sudo chmod -c a=rwx -R         "/srv/usb3disk1/minidlna/log"
sudo chown -c -R pi:minidlna   "/srv/usb3disk1/minidlna/log"
```

6. **Change the config to align with out disk/folder arrangement etc; in a Terminal**    

```
# backup and edit the miniDLNA config file
sudo cp -fv "/etc/minidlna.conf" "/etc/minidlna.conf.original"
sudo nano "/etc/minidlna.conf"
```
now in nano,
```
# ignore these 3 ...
##minidlna_refresh_log_file=/srv/usb3disk1/minidlna/log/minidlna_refresh.log
##minidlna_refresh_sh_file=/srv/usb3disk1/minidlna/minidlna_refresh.sh
##minidlna_restart_refresh_sh_file=/srv/usb3disk1/minidlna/minidlna_restart_refresh.sh

# Find and change line `media_dir=/var/lib/minidlna` to comment it out:
##media_dir=/var/lib/minidlna

# Find and change line `album_art_names=` to comment it out:
##album_art_names=

# Find and un-comment and/or change/add line `#friendly_name=` to:
friendly_name=PINAS64-minidlna

# Find and un-comment and/or change/add line `#model_name=` to:
model_name=PINAS64-miniDLNA

# Find and un-comment and/or change/add line `#merge_media_dirs=` to:
merge_media_dirs=no

# Find and un-comment and/or change/add line `#db_dir=/var/cache/minidlna` to:
db_dir=/srv/usb3disk1/minidlna/cache

# Find and un-comment and/or change/add line `#log_dir=/var/log/minidlna` to:
log_dir=/srv/usb3disk1/minidlna/log

# inotify=yes and notify_interval=895 work together fopr miniDLNA to discover added and modified files
# Find and un-comment and/or change/add line `#inotify=yes` to:
inotify=yes
# Find and un-comment and/or change/add line `#notify_interval=895` (5 seconds under 15 minutes) to:
notify_interval=895

# Find and un-comment and/or change/add line `#strict_dlna=no` to:
strict_dlna=yes

# Find and un-comment and/or change/add line `#max_connections=50` to a number expected for this LAN:
# (many clients open several simultaneous connections while streaming)
max_connections=24

# Find and un-comment and/or change/add line `#log_level=general,artwork,database,inotify,scanner,metadata,http,ssdp,tivo=warn` to:
log_level=general,artwork,database,inotify,scanner,metadata,http,ssdp,tivo=info

# Find and un-comment and/or change/add line `#wide_links=no` to:
wide_links=yes

# now ADD the line to expose the overlayed media folder ...
root_container=PVA,/srv/overlay
##media_dir=PVA,/srv/overlay

# now ADD any lines where wish to expose folders
# separately to, but as well as in, the overlayed folder tree, eg
# THE ENTRIES BELOW MUST EXACTLY MATCH THE FOLDERS WE WISH DLNA TO EXPOSE
media_dir=PVA,/srv/overlay/ClassicMovies
media_dir=PVA,/srv/overlay/Documentaries
media_dir=PVA,/srv/overlay/Footy
media_dir=PVA,/srv/overlay/Movies
media_dir=PVA,/srv/overlay/Music
media_dir=PVA,/srv/overlay/OldMovies
media_dir=PVA,/srv/overlay/SciFi
```
Restart miniDLNA and force a db reload.
```
sudo systemctl stop minidlna 
sudo systemctl restart minidlna 
sudo systemctl force-reload minidlna 
sudo systemctl status minidlna | tail -n 50
tail -n 50 /srv/usb3disk1/minidlna/log/minidlna.log
```
The minidlna service comes with an internal small web server and webinterface.    
This webinterface is just for informational purposes.    
We will not be able to configure anything here.    
However, it gives us a nice and short information screen how many files have been found by minidlna.    
To access the webinterface, open our browser of choice and enter url http://127.0.0.1:8200    
```
curl -i http://127.0.0.1:8200
```

????????????????????????????????????????????????????????????????????????????????????????

**Under Construction**    
```
minidlna_refresh_sh_file=/srv/usb3disk1/minidlna/minidlna_refresh.sh
minidlna_refresh_log_file=/srv/usb3disk1/minidlna/log/minidlna_refresh.log
minidlna_restart_refresh_sh_file=/srv/usb3disk1/minidlna/minidlna_restart_refresh.sh
```


#### create an outline from an older miniDLNA setup script from this:    
```

set +x
echo ""
sudo rm -vf "${minidlna_main_log_file}"
sudo rm -vf "${minidlna_refresh_log_file}"
sudo touch "${minidlna_refresh_log_file}"
echo ""
echo "Create the .sh used by crontab to refresh the db every night. ${minidlna_refresh_sh_file}"
echo ""
set -x
sudo rm -vf "${minidlna_refresh_sh_file}"
sudo touch "${minidlna_refresh_sh_file}"
sudo chmod -c a=rwx "${minidlna_refresh_sh_file}"
set +x
echo "#!/bin/bash" >> "${minidlna_refresh_sh_file}"
echo "set -x" >> "${minidlna_refresh_sh_file}"
echo "# ${minidlna_refresh_sh_file}" >> "${minidlna_refresh_sh_file}"
echo "# used by crontab to refresh the the db every night" >> "${minidlna_refresh_sh_file}"
echo "sudo systemctl stop minidlna" >> "${minidlna_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_refresh_sh_file}"
echo "sudo systemctl restart minidlna" >> "${minidlna_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_refresh_sh_file}"
echo "echo 'Wait 15 minutes for minidlna to index media files'" >> "${minidlna_refresh_sh_file}"
echo "echo 'For progress do in another terminal window: cat ${main_log_dir}'" >> "${minidlna_refresh_sh_file}"
echo "sleep 900s" >> "${minidlna_refresh_sh_file}"
echo "set +x" >> "${minidlna_refresh_sh_file}"
echo "# ${minidlna_refresh_sh_file}" >> "${minidlna_refresh_sh_file}"
set -x
sudo cat "${minidlna_refresh_sh_file}"
set +x
echo ""
echo "Create the .sh used by a user to manually refresh the minidlna db. ${minidlna_restart_refresh_sh_file}"
echo ""
set -x
sudo rm -vf "${minidlna_restart_refresh_sh_file}"
sudo touch "${minidlna_restart_refresh_sh_file}"
sudo chmod -c a=rwx "${minidlna_restart_refresh_sh_file}"
set +x
echo "#!/bin/bash" >> "${minidlna_restart_refresh_sh_file}"
echo "set -x" >> "${minidlna_restart_refresh_sh_file}"
echo "# ${minidlna_restart_refresh_sh_file}" >> "${minidlna_restart_refresh_sh_file}"
echo "# used in ~/Desktop for a user to manually refresh the the db" >> "${minidlna_restart_refresh_sh_file}"
echo "sudo systemctl stop minidlna" >> "${minidlna_restart_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_restart_refresh_sh_file}"
echo "sudo systemctl restart minidlna" >> "${minidlna_restart_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_restart_refresh_sh_file}"
echo "echo 'Wait 15 minutes for minidlna to index media files'" >> "${minidlna_restart_refresh_sh_file}"
echo "echo 'For progress do in another terminal window: cat ${main_log_dir}'" >> "${minidlna_restart_refresh_sh_file}"
echo "sleep 900s" >> "${minidlna_restart_refresh_sh_file}"
echo "#" >> "${minidlna_restart_refresh_sh_file}"
echo "cat \"${minidlna_main_log_file}\"" >> "${minidlna_restart_refresh_sh_file}"
echo "#" >> "${minidlna_restart_refresh_sh_file}"
echo "set +x" >> "${minidlna_restart_refresh_sh_file}"
echo "# ${minidlna_restart_refresh_sh_file}" >> "${minidlna_restart_refresh_sh_file}"
set -x
sudo cat "${minidlna_restart_refresh_sh_file}"
set +x
echo ""
echo "Add the 2:00 am nightly crontab job to re-index miniDLNA (${minidlna_refresh_sh_file})"
echo ""
# https://stackoverflow.com/questions/610839/how-can-i-programmatically-create-a-new-cron-job
#The layout for a cron entry is made up of six components: minute, hour, day of month, month of year, day of week, and the command to be executed.
# m h  dom mon dow   command
# * * * * *  command to execute
# ┬ ┬ ┬ ┬ ┬
# │ │ │ │ │
# │ │ │ │ │
# │ │ │ │ └───── day of week (0 - 7) (0 to 6 are Sunday to Saturday, or use names; 7 is Sunday, the same as 0)
# │ │ │ └────────── month (1 - 12)
# │ │ └─────────────── day of month (1 - 31)
# │ └──────────────────── hour (0 - 23)
# └───────────────────────── min (0 - 59)
# https://stackoverflow.com/questions/610839/how-can-i-programmatically-create-a-new-cron-job
# <minute> <hour> <day> <month> <dow> <tags and command>
echo "#"
echo "# crontab List BEFORE contab ADD:"
echo "#"
set -x
sudo crontab -l # before
crontab -l # before
set +x
echo "#"
echo "# Adding crontab as user pi (no sudo):"
echo "#"
# escaped path for use in: sed "/findstring/d"
EscapedPath=`echo "${minidlna_refresh_sh_file}" | sed 's:/:\\\/:g'`
set -x
cd ~/Desktop
sudo rm -vf "./local_crontab.txt" "./local_crontab_tmp.txt"
crontab -l > "./local_crontab.txt"
sed -i "/no crontab for $(whoami)/d" "./local_crontab.txt"
cat "./local_crontab.txt"
sed -i "/${EscapedPath}/d" "./local_crontab.txt"
cat "./local_crontab.txt"
echo "0 2 * * * ${minidlna_refresh_sh_file} 2>&1 >> ${minidlna_refresh_log_file}" >> "./local_crontab.txt"
cat "./local_crontab.txt" | sort | uniq  > "./local_crontab_tmp.txt"
mv -fv "./local_crontab_tmp.txt" "./local_crontab.txt"
cat "./local_crontab.txt"
crontab "./local_crontab.txt"
rm -vf "./local_crontab.txt"
set +x
echo "#"
echo "# crontab List AFTER contab ADD:"
echo "#"
set -x
sudo crontab -l # after
crontab -l # after
set +x
echo "#"
echo "# syslog AFTER contab ADD:"
echo "#"
set -x
sudo grep CRON /var/log/syslog
set +x
echo ""
echo "# Start miniDLNA: Force a re-load of miniDLNA to ensure it starts re-looking for new files."
echo ""
set -x
sudo ls -al "/run/minidlna"
sudo systemctl stop minidlna
sleep 2s
sudo systemctl restart minidlna
sleep 2s
set +x
echo "#"
echo "# The minidlna service comes with a small webinterface. "
echo "# This webinterface is just for informational purposes. "
echo "# We will not be able to configure anything here. "
echo "# However, it gives we a nice and short information screen how many files have been found by minidlna. "
echo "# minidlna comes with it’s own webserver integrated. "
echo "# This means that no additional webserver is needed in order to use the webinterface."
echo "# To access the webinterface, open our browser of choice and enter url http://127.0.0.1:8200"
echo ""
set -x
curl -i http://127.0.0.1:8200
set +x
echo ""
# The actual streaming process
# A short overview how a connection from a client to the configured and running minidlna server could work. 
# In this scenario we simply use a computer which is in the same local area network than the server. 
# As the client software we use the Video Lan Client (VLC). 
# Simple, robust, cross-platform and open source. 
# After starting VLC, go to the playlist mode by pressing CTRL+L in windows. 
# We will now see on the left side a category which is called Local Network. 
# Click on Universal Plug’n’Play which is under the Local Network category. 
# We will then see a list of available DLNA service within our local network. 
# In this list we should see our DLNA server. 
# Navigate through the different directories for music, videos and pictures and select a file to start the streaming process
echo ""
#
set -x
sudo ls -al "/run/minidlna"
set +x
echo ""
set -x
sudo ls -al "${minidlna_main_log_file}"
sudo cat "${minidlna_main_log_file}"
set +x
echo ""
set -x
sudo ls -al "${minidlna_refresh_log_file}"
sudo cat "${minidlna_refresh_log_file}"
set +x
echo ""
#
```







#### Official home pages and GitHub for `MergerFS`:

```
MergerFS
   Homepage:          https://github.com/trapexit/mergerfs
   GitHub Repository: https://github.com/trapexit/mergerfs
   Other              https://github.com/trapexit/mergerfs/wiki/Real-World-Deployments
                      https://perfectmediaserver.com/02-tech-stack/mergerfs/


```






## Install and configure `miniDLNA` to serve media on the LAN via DLNA

# UNDER CONSTRUCTION

#### NOTE: we install the miniDLNA index db onto USB3 DISK1 rather than the SD card    
####       since it is faster, and the SD car won't wear out quicker due to index rebuilds    

1. **Ensure we un-install any prior `miniDLNA`; in a Terminal**    
```
sudo systemctl stop minidlna
sleep 2s
sudo systemctl disable minidlna
sleep 2s
sudo apt purge minidlna -y
sudo apt autoremove -y
```

2. **Remove any prior config items and index db; in a Terminal**    
```
sudo rm -vfR "/etc/minidlna.conf"
sudo rm -vfR "/var/log/minidlna.log"
sudo rm -vfR "/run/minidlna"
# note: the next lines may fail, ignore any fails:
sudo rm -vfR "/srv/usb3disk1/minidlna"
```

3. **Install `miniDLNA`, enable, and then stop the service so we can configure it; in a Terminal**    
```
sudo apt install -y minidlna
sudo systemctl stop minidlna 
sudo systemctl enable minidlna
```

4. **Add users to `miniDLNA` Groups and vice versa; in a Terminal**    
```
sudo usermod -a -G pi minidlna
sudo usermod -a -G minidlna pi
sudo usermod -a -G minidlna root
sudo usermod -a -G root minidlna
```

5. **Fix ownerships etc, create folders for db and log at the top of external USB3 disk DISK1; in a Terminal**    

```
sudo chmod -c a=rwx -R         "/etc/minidlna.conf"
sudo chown -c -R pi:minidlna   "/etc/minidlna.conf"
#
sudo mkdir -pv                 "/srv/usb3disk1/minidlna"
sudo chmod -c a=rwx -R         "/srv/usb3disk1/minidlna"
sudo chown -c -R pi:minidlna   "/srv/usb3disk1/minidlna"
#
sudo chmod -c a=rwx -R         "/run/minidlna"
sudo chown -c -R pi:minidlna   "/run/minidlna"
#
sudo touch                     "/run/minidlna/minidlna.pid"
sudo chmod -c a=rwx -R         "/run/minidlna/minidlna.pid"
sudo chown -c -R pi:minidlna   "/run/minidlna/minidlna.pid"
#
sudo mkdir -pv                 "/srv/usb3disk1/minidlna/cache"
sudo chmod -c a=rwx -R         "/srv/usb3disk1/minidlna/cache"
sudo chown -c -R pi:minidlna   "/srv/usb3disk1/minidlna/cache"
#
sudo mkdir -pv                 "/srv/usb3disk1/minidlna/log"
sudo touch                     "/srv/usb3disk1/minidlna/log/minidlna.log"
sudo chmod -c a=rwx -R         "/srv/usb3disk1/minidlna/log"
sudo chown -c -R pi:minidlna   "/srv/usb3disk1/minidlna/log"
```

6. **Change the config to align with out disk/folder arrangement etc; in a Terminal**    

```
# backup and edit the miniDLNA config file
sudo cp -fv "/etc/minidlna.conf" "/etc/minidlna.conf.original"
sudo nano "/etc/minidlna.conf"
```
now in nano,
```
# ignore these 3 ...
##minidlna_refresh_log_file=/srv/usb3disk1/minidlna/log/minidlna_refresh.log
##minidlna_refresh_sh_file=/srv/usb3disk1/minidlna/minidlna_refresh.sh
##minidlna_restart_refresh_sh_file=/srv/usb3disk1/minidlna/minidlna_restart_refresh.sh

# Find and change line `media_dir=/var/lib/minidlna` to comment it out:
##media_dir=/var/lib/minidlna

# Find and change line `album_art_names=` to comment it out:
##album_art_names=

# Find and un-comment and/or change/add line `#friendly_name=` to:
friendly_name=PINAS64-minidlna

# Find and un-comment and/or change/add line `#model_name=` to:
model_name=PINAS64-miniDLNA

# Find and un-comment and/or change/add line `#merge_media_dirs=` to:
merge_media_dirs=no

# Find and un-comment and/or change/add line `#db_dir=/var/cache/minidlna` to:
db_dir=/srv/usb3disk1/minidlna/cache

# Find and un-comment and/or change/add line `#log_dir=/var/log/minidlna` to:
log_dir=/srv/usb3disk1/minidlna/log

# inotify=yes and notify_interval=895 work together fopr miniDLNA to discover added and modified files
# Find and un-comment and/or change/add line `#inotify=yes` to:
inotify=yes
# Find and un-comment and/or change/add line `#notify_interval=895` (5 seconds under 15 minutes) to:
notify_interval=895

# Find and un-comment and/or change/add line `#strict_dlna=no` to:
strict_dlna=yes

# Find and un-comment and/or change/add line `#max_connections=50` to a number expected for this LAN:
# (many clients open several simultaneous connections while streaming)
max_connections=24

# Find and un-comment and/or change/add line `#log_level=general,artwork,database,inotify,scanner,metadata,http,ssdp,tivo=warn` to:
log_level=general,artwork,database,inotify,scanner,metadata,http,ssdp,tivo=info

# Find and un-comment and/or change/add line `#wide_links=no` to:
wide_links=yes

# now ADD the line to expose the overlayed media folder ...
root_container=PVA,/srv/overlay
##media_dir=PVA,/srv/overlay

# now ADD any lines where wish to expose folders
# separately to, but as well as in, the overlayed folder tree, eg
# THE ENTRIES BELOW MUST EXACTLY MATCH THE FOLDERS WE WISH DLNA TO EXPOSE
media_dir=PVA,/srv/overlay/ClassicMovies
media_dir=PVA,/srv/overlay/Documentaries
media_dir=PVA,/srv/overlay/Footy
media_dir=PVA,/srv/overlay/Movies
media_dir=PVA,/srv/overlay/Music
media_dir=PVA,/srv/overlay/OldMovies
media_dir=PVA,/srv/overlay/SciFi
```
Restart miniDLNA and force a db reload.
```
sudo systemctl stop minidlna 
sudo systemctl restart minidlna 
sudo systemctl force-reload minidlna 
sudo systemctl status minidlna | tail -n 50
tail -n 50 /srv/usb3disk1/minidlna/log/minidlna.log
```
The minidlna service comes with an internal small web server and webinterface.    
This webinterface is just for informational purposes.    
We will not be able to configure anything here.    
However, it gives us a nice and short information screen how many files have been found by minidlna.    
To access the webinterface, open our browser of choice and enter url http://127.0.0.1:8200    
```
curl -i http://127.0.0.1:8200
```

**Under COnstruction**    
```
minidlna_refresh_sh_file=/srv/usb3disk1/minidlna/minidlna_refresh.sh
minidlna_refresh_log_file=/srv/usb3disk1/minidlna/log/minidlna_refresh.log
minidlna_restart_refresh_sh_file=/srv/usb3disk1/minidlna/minidlna_restart_refresh.sh
```






#### create an outline from an older miniDLNA setup script from this:    
```

set +x
echo ""
sudo rm -vf "${minidlna_main_log_file}"
sudo rm -vf "${minidlna_refresh_log_file}"
sudo touch "${minidlna_refresh_log_file}"
echo ""
echo "Create the .sh used by crontab to refresh the db every night. ${minidlna_refresh_sh_file}"
echo ""
set -x
sudo rm -vf "${minidlna_refresh_sh_file}"
sudo touch "${minidlna_refresh_sh_file}"
sudo chmod -c a=rwx "${minidlna_refresh_sh_file}"
set +x
echo "#!/bin/bash" >> "${minidlna_refresh_sh_file}"
echo "set -x" >> "${minidlna_refresh_sh_file}"
echo "# ${minidlna_refresh_sh_file}" >> "${minidlna_refresh_sh_file}"
echo "# used by crontab to refresh the the db every night" >> "${minidlna_refresh_sh_file}"
echo "sudo systemctl stop minidlna" >> "${minidlna_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_refresh_sh_file}"
echo "sudo systemctl restart minidlna" >> "${minidlna_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_refresh_sh_file}"
echo "echo 'Wait 15 minutes for minidlna to index media files'" >> "${minidlna_refresh_sh_file}"
echo "echo 'For progress do in another terminal window: cat ${main_log_dir}'" >> "${minidlna_refresh_sh_file}"
echo "sleep 900s" >> "${minidlna_refresh_sh_file}"
echo "set +x" >> "${minidlna_refresh_sh_file}"
echo "# ${minidlna_refresh_sh_file}" >> "${minidlna_refresh_sh_file}"
set -x
sudo cat "${minidlna_refresh_sh_file}"
set +x
echo ""
echo "Create the .sh used by a user to manually refresh the minidlna db. ${minidlna_restart_refresh_sh_file}"
echo ""
set -x
sudo rm -vf "${minidlna_restart_refresh_sh_file}"
sudo touch "${minidlna_restart_refresh_sh_file}"
sudo chmod -c a=rwx "${minidlna_restart_refresh_sh_file}"
set +x
echo "#!/bin/bash" >> "${minidlna_restart_refresh_sh_file}"
echo "set -x" >> "${minidlna_restart_refresh_sh_file}"
echo "# ${minidlna_restart_refresh_sh_file}" >> "${minidlna_restart_refresh_sh_file}"
echo "# used in ~/Desktop for a user to manually refresh the the db" >> "${minidlna_restart_refresh_sh_file}"
echo "sudo systemctl stop minidlna" >> "${minidlna_restart_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_restart_refresh_sh_file}"
echo "sudo systemctl restart minidlna" >> "${minidlna_restart_refresh_sh_file}"
echo "sleep 2s" >> "${minidlna_restart_refresh_sh_file}"
echo "echo 'Wait 15 minutes for minidlna to index media files'" >> "${minidlna_restart_refresh_sh_file}"
echo "echo 'For progress do in another terminal window: cat ${main_log_dir}'" >> "${minidlna_restart_refresh_sh_file}"
echo "sleep 900s" >> "${minidlna_restart_refresh_sh_file}"
echo "#" >> "${minidlna_restart_refresh_sh_file}"
echo "cat \"${minidlna_main_log_file}\"" >> "${minidlna_restart_refresh_sh_file}"
echo "#" >> "${minidlna_restart_refresh_sh_file}"
echo "set +x" >> "${minidlna_restart_refresh_sh_file}"
echo "# ${minidlna_restart_refresh_sh_file}" >> "${minidlna_restart_refresh_sh_file}"
set -x
sudo cat "${minidlna_restart_refresh_sh_file}"
set +x
echo ""
echo "Add the 2:00 am nightly crontab job to re-index miniDLNA (${minidlna_refresh_sh_file})"
echo ""
# https://stackoverflow.com/questions/610839/how-can-i-programmatically-create-a-new-cron-job
#The layout for a cron entry is made up of six components: minute, hour, day of month, month of year, day of week, and the command to be executed.
# m h  dom mon dow   command
# * * * * *  command to execute
# ┬ ┬ ┬ ┬ ┬
# │ │ │ │ │
# │ │ │ │ │
# │ │ │ │ └───── day of week (0 - 7) (0 to 6 are Sunday to Saturday, or use names; 7 is Sunday, the same as 0)
# │ │ │ └────────── month (1 - 12)
# │ │ └─────────────── day of month (1 - 31)
# │ └──────────────────── hour (0 - 23)
# └───────────────────────── min (0 - 59)
# https://stackoverflow.com/questions/610839/how-can-i-programmatically-create-a-new-cron-job
# <minute> <hour> <day> <month> <dow> <tags and command>
echo "#"
echo "# crontab List BEFORE contab ADD:"
echo "#"
set -x
sudo crontab -l # before
crontab -l # before
set +x
echo "#"
echo "# Adding crontab as user pi (no sudo):"
echo "#"
# escaped path for use in: sed "/findstring/d"
EscapedPath=`echo "${minidlna_refresh_sh_file}" | sed 's:/:\\\/:g'`
set -x
cd ~/Desktop
sudo rm -vf "./local_crontab.txt" "./local_crontab_tmp.txt"
crontab -l > "./local_crontab.txt"
sed -i "/no crontab for $(whoami)/d" "./local_crontab.txt"
cat "./local_crontab.txt"
sed -i "/${EscapedPath}/d" "./local_crontab.txt"
cat "./local_crontab.txt"
echo "0 2 * * * ${minidlna_refresh_sh_file} 2>&1 >> ${minidlna_refresh_log_file}" >> "./local_crontab.txt"
cat "./local_crontab.txt" | sort | uniq  > "./local_crontab_tmp.txt"
mv -fv "./local_crontab_tmp.txt" "./local_crontab.txt"
cat "./local_crontab.txt"
crontab "./local_crontab.txt"
rm -vf "./local_crontab.txt"
set +x
echo "#"
echo "# crontab List AFTER contab ADD:"
echo "#"
set -x
sudo crontab -l # after
crontab -l # after
set +x
echo "#"
echo "# syslog AFTER contab ADD:"
echo "#"
set -x
sudo grep CRON /var/log/syslog
set +x
echo ""
echo "# Start miniDLNA: Force a re-load of miniDLNA to ensure it starts re-looking for new files."
echo ""
set -x
sudo ls -al "/run/minidlna"
sudo systemctl stop minidlna
sleep 2s
sudo systemctl restart minidlna
sleep 2s
set +x
echo "#"
echo "# The minidlna service comes with a small webinterface. "
echo "# This webinterface is just for informational purposes. "
echo "# We will not be able to configure anything here. "
echo "# However, it gives us a nice and short information screen how many files have been found by minidlna. "
echo "# minidlna comes with it’s own webserver integrated. "
echo "# This means that no additional webserver is needed in order to use the webinterface."
echo "# To access the webinterface, open our browser of choice and enter url http://127.0.0.1:8200"
echo ""
set -x
curl -i http://127.0.0.1:8200
set +x
echo ""
# The actual streaming process
# A short overview how a connection from a client to the configured and running minidlna server could work. 
# In this scenario we simply use a computer which is in the same local area network than the server. 
# As the client software we use the Video Lan Client (VLC). 
# Simple, robust, cross-platform and open source. 
# After starting VLC, go to the playlist mode by pressing CTRL+L in windows. 
# We will now see on the left side a category which is called Local Network. 
# Click on Universal Plug’n’Play which is under the Local Network category. 
# We will then see a list of available DLNA service within our local network. 
# In this list we should see our DLNA server. 
# Navigate through the different directories for music, videos and pictures and select a file to start the streaming process
echo ""
#
set -x
sudo ls -al "/run/minidlna"
set +x
echo ""
set -x
sudo ls -al "${minidlna_main_log_file}"
sudo cat "${minidlna_main_log_file}"
set +x
echo ""
set -x
sudo ls -al "${minidlna_refresh_log_file}"
sudo cat "${minidlna_refresh_log_file}"
set +x
echo ""
#
```


# Notes to self about the Pi5       
Nothing to do with the NAS / Media Server.    

## Commands to Enable the external RTC battery    
Per https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#real-time-clock-rtc    
The Raspberry Pi 5 includes an RTC module. 
This can be battery powered via the J5 (BAT) connector on the board located to the right of the USB-C power connector:     
https://www.raspberrypi.com/documentation/computers/images/j5.png?hash=70853cc7a9a01cd836ed8351ece14d59    

We can set a wake alarm which will switch the board to a very low-power state (approximately 3mA). 
When the alarm time is reached, the board will power back on. 
This can be useful for periodic jobs like time-lapse imagery.
To support the low-power mode for wake alarms, edit the bootloader configuration:
```
sudo -E rpi-eeprom-config --edit
```
adding the following two lines.
```
POWER_OFF_ON_HALT=1
WAKE_ON_GPIO=0
```
The RTC is equipped with a **constant-current (3mA) constant-voltage charger**.    
Charging of the battery is disabled by default.    
To charge the battery at a set voltage, add `rtc_bbat_vchg` to `/boot/firmware/config.txt`:
```
sudo nano /boot/firmware/config.txt
```
add
```
dtparam=rtc_bbat_vchg=3000000
```
Reboot with `sudo reboot now` to use the new voltage setting.    
Check the `sysfs` files to ensure that the charging voltage was correctly set.
```
/sys/devices/platform/soc/soc:rpi_rtc/rtc/rtc0/charging_voltage:0
/sys/devices/platform/soc/soc:rpi_rtc/rtc/rtc0/charging_voltage_max:4400000
/sys/devices/platform/soc/soc:rpi_rtc/rtc/rtc0/charging_voltage_min:1300000
```
We can test the battery RTC functionality with:
```
echo +600 | sudo tee /sys/class/rtc/rtc0/wakealarm
sudo halt
```
That will halt the board into a very low-power state, then wake and restart after 10 minutes.    
The RTC also provides the time on boot e.g. in `dmesg`, for use cases that lack access to NTP:
```
[    1.295799] rpi-rtc soc:rpi_rtc: setting system clock to 2023-08-16T15:58:50 UTC (1692201530)
```
NOTE: The RTC is still usable even when there is no backup battery attached to the J5 connector.    
