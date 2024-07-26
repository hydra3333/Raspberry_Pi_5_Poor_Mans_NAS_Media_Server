# WARNING: UNDER CONSTRUCTION

# DO NOT USE

# NOTHING WORKS YET

# Raspberry Pi 5 Poor Persons NAS Media Server    

## Outline    
If you have a PI 5 and some old USB3 disks (with their own power supply) and a couple of USB3 hubs laying around,
but can't afford a NAS box nor a 3D printer to print one nor a SATA hat for the Pi etc, then perhaps
cobble together a NAS / Media Server with what you have.

Together with a Pi 5 and an SD card you can use    
- 1 or 2 (say, 4-port) USB3 hubs plugged into the Pi 5 to connect many old USB3 disks to the Pi    
- 1 to 8 old USB3 disks plugged into the USB hubs    

With this harware you can readily serve up standard SAMBA SMB/CIFS file shares
and media files to devices across the LAN.   

## Why ?
Most ordinary people cannot afford expensive new bits like multiple NVME drives or Pi Hat's etc,
as shown on youtube 'how-to's !  It's great they show and test those things, but money doesn't grow on trees,
especially if you have kids and/or are retired.    

One could use `OpenMediaVault` or `Plex` more easily, but they connect to the internet to do 'stuff'.
I looked at `Plex` et al years ago and was very uncomfortable with the level of access installed packages potentially
provided to the vendor servers directly into my LAN and hence to all the devices on my LAN
... essentially permitting them unfettered invisible 'remote control' access if they so chose.
I valued my banking details and documents etc, choosing to limit exposure to that potential security hazard.    

This 'roll your own' approach minimises cost, and avoids the pain of getting 'done over' by your own hand - installing
packages known to interact of themselves in essentially unknown ways with (uncontrolled) vendors' servers
on the internet - at the cost of having to deal with more complexity ... safety first.

## General Approach
This assumes you know how to use the nano editor, if not please google it, if using another editor then cool !

If one has, say, 1 to 8 old USB3 disks with volume labels `DISK1` ... `DISK8` all plugged into the (1 or 2) USB3 hubs,
and each disk has a matching single root folder `mergerfs_Root_1` ... `mergerfs_Root_8` containing
subfolders of media to be served (no files are duplicated acorss disks)    
```
DISK1 -- mergerfs_Root_1 --|--ClassicMovies
                           |--Documentaries
                           |--Footy-----------|--1997
                           |                  |--1998
                           |--SciFi

DISK2 -- mergerfs_Root_2 --|--ClassicMovies
                           |--Footy-----------|--2000
                           |                  |--2002
                           |--Movies
                           |--OldMovies

DISK3 -- mergerfs_Root_3 --|--ClassicMovies
                           |--Footy-----------|--2003
                           |                  |--2004
```


## Acknowledgements    

### thagrol    
https://forums.raspberrypi.com/viewtopic.php?p=2236572#p2236547    

Building A Pi Based NAS    
https://forums.raspberrypi.com/viewtopic.php?t=327444    

Using fstab A Beginner's Guide    
https://forums.raspberrypi.com/viewtopic.php?t=302752    

## ESSENTIAL: Prepare disks: security, disk volume labels, folder structures, files    
Assuming we have USB3 disks created as GPT disks (not Dynamic Disks) and formatted as NTFS 
(since Windows PCs are often used to create media files, and WIndows only really likes disks formatted as NTFS)
we need to prepare every disk to appear and behave in a consistent way.

For every disk, change it's volume label to be like `DISK1` through to `DISK8` and unique to each disk.
If you are unsure how to do that, try
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

On each disk, create one top level folder named like `mergerfs_Root_1` through to `mergerfs_Root_8` to match the unique disk volume label number.

Under the top level folder on the disks, place the media files in a reasonably consistent (including filename capitalisation)
subfolder structure of your choice. The same subfolder names and files may or may not exist on every disk, you can
spread out the media files and subfolders across disks ... but do 
**DO NOT duplicate ANY files in ANY of the same level folders named identically across ANY of the disks**
since that may break the software rules. We end up with something like this    
```
DISK1 -- mergerfs_Root_1 --|--ClassicMovies   <- do not have identical filenames in other disks in this folder
                           |--Documentaries
                           |--Footy-----------|--1997
                           |                  |--1998
                           |--SciFi

DISK2 -- mergerfs_Root_2 --|--ClassicMovies   <- do not have identical filenames in other disks in this folder
                           |--Footy-----------|--2000
                           |                  |--2002
                           |--Movies
                           |--OldMovies

DISK3 -- mergerfs_Root_3 --|--ClassicMovies   <- do not have identical filenames in other disks in this folder
                           |--Footy-----------|--2003
                           |                  |--2004
```

In the outline below, we'll assume only 3 USB3 disks. We can add more as needed,
just keep an eye on the disk naming and folder structures in line with the example model above.    

## Install Raspberry Pi OS with `autologin`    
Run the `Raspberry Pi Imager` on a PC to put the full 64 bit `Raspberry Pi OS` image to an SD card in the usual way    
- Choose to "Edit Settings" and then the GENERAL tab.    
- Set a Hostname you will recognise, eg PINAS64.    
- Set a username as `pi` (if not `pi` then replace username `pi` in this outline with the chosen username) and
the password as something you will remember (you will need to enter it later during `SAMBA` and other setups,
and change all references of `pi` to the username).    
- Set you locale settings and keyboard layout (setting keyboard layout is important if in non-US non-GB country).    
- Choose the SERVICES tab.    
- Enable SSH with password authentification.    
- Choose the OPTIONS tab.    
- Disable telementry.    
Click SAVE.    
Click YES to apply OS customisation.    
Click YES to proceed.    

## Prepare the hardware    
First ensuring that power switch is off where the Pi's power block plugs in,    
- ensure all USB3 disks are powered off and will remain so until required later    
- plug the Pi into a screen with the HDMI cable (sophisticated users may choose to instead use `SSH` or `VNC` or `RaspberryPi Connect` later)    
- plug in the Pi's power cable into the Pi    
- plug in the USB3 hub(s) into the USB3 slots in the Pi, but leave all disks powered off    
- plug the external USB3 disks into the USB3 hubs, but leave all disks powered off    

That's the hardware prepared and plugged in.    

In the outline below, we'll assume only 3 USB3 disks. You can add more as you need,
just keep an eye on the disk naming and folder structures in line with the model above.    

## Install Raspberry Pi OS with `autologin` to the SD card    
Run the `Raspberry Pi Imager` on a PC to put the full 64 bit `Raspberry Pi OS` image to an SD card in the usual way    
- Choose to "Edit Settings" and then the GENERAL tab.    
- Set a Hostname you will recognise, eg PINAS64.    
- Set a username as `pi` (if not `pi` then replace username `pi` in this outline with the chosen username) and
the password as something you will remember (you will need to enter it later during `SAMBA` setup,
and change all references of `pi` to the username).    
- Set you locale settings and keyboard layout (setting keyboard layout is important if in non-US non-GB country).    
- Choose the SERVICES tab.    
- Enable SSH with password authentification.    
- Choose the OPTIONS tab.    
- Disable telementry.    
Click SAVE.    
Click YES to apply OS customisation.    
Click YES to proceed.    

## Boot the Raspberry Pi 5 and update the system    
1. **Order of power up (for this first time)**    
- Ensure the Pi 5 is powered off    
- Plug the SD card into the Pi 5    
- Power on the Pi 5    

2. **Once the Pi has finished booting to the desktop (leave it set to autologin)**    
- Click Start, Preferences, Raspberry Pi Configuration    
- In the Localisation Tab, Set the Locale and then character set UTF-8, Timezone, Keyboard (setting keyboard is important if in non-US non-GB country), WiFi country, then click OK.    
- If prompted to reboot then click YES and reboot back to the desktop.    
- Click Start, Preferences, Raspberry Pi Configuration    
- In the System Tab, set Auto Logon ON, Splash Screen OFF    
- In the Interfaces Tab, sey **VNC ON**, **SSH ON**, **Raspberry Connect OFF**     
- Click OK    
- If prompted to reboot then click YES and reboot.    

Once the Pi has finished booting to the desktop:    

3. **Force PCI Express Gen 3.0 speeds after next boot (8 GT/sec, almost double the speed) on the Pi 5; in a Terminal**    
and per https://www.jeffgeerling.com/blog/2023/forcing-pci-express-gen-30-speeds-on-pi-5     
Edit the firmware's config file:    
```
sudo nano /boot/firmware/config.txt 
```
then check-for/modify/add the following 2 lines so they are at the end of the config file:
```
dtparam=pciex1
dtparam=pciex1_gen=3
```
exit nano with `Control O` `Control X`.    

4. **Enable the external RTC battery, assuming you purchased and installed one**    
Per https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#real-time-clock-rtc    
The Raspberry Pi 5 includes an RTC module. 
This can be battery powered via the J5 (BAT) connector on the board located to the right of the USB-C power connector:     
https://www.raspberrypi.com/documentation/computers/images/j5.png?hash=70853cc7a9a01cd836ed8351ece14d59    
You can set a wake alarm which will switch the board to a very low-power state (approximately 3mA). 
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

**NOTE: Later (not now) after you reboot, recharging with the right voltage setting will take effect.**    
You can check the `sysfs` files to ensure that the charging voltage was correctly set.
```
/sys/devices/platform/soc/soc:rpi_rtc/rtc/rtc0/charging_voltage:0
/sys/devices/platform/soc/soc:rpi_rtc/rtc/rtc0/charging_voltage_max:4400000
/sys/devices/platform/soc/soc:rpi_rtc/rtc/rtc0/charging_voltage_min:1300000
```
Then you can test the battery RTC functionality with:
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

5. **Update the system; in a Terminal**    

```
sudo nano /etc/apt/sources.list
# Now in nano `uncomment` all of the `deb-src` lines by removing the # at the start of those lines.
```
exit nano with `Control O` `Control X`.    
Update the system:
```
sudo apt -y update
sudo apt -y full-upgrade
sudo apt -y dist-upgrade
```
Reboot the Pi now.
This will also cause the change above to take effect.

6. **Run `raspi-config` to configure more system settings; in a Terminal**    

```
sudo raspi-config
```
Using the menu ... stuff here




---












## NOW TESTING `mergerFS` on top of `snapRAID`

### which looks like it will be the bees knees !


# STOP READING NOW

My intended approach was Bollocks because, having written several python programs
for 'fuzzy matching' of media files needing for file supersedence (eg
`file01_2024.01.001.mp4` with `file_01_new.2024.02.03`) with the old file deleted,
and to synchoronize multiple identical copies of files in folders across disks taking care of
old/new/updated files, and deal with read-only `overlaysf` due to issues its with
staging file updates etc, I gave up.

In a chat with ChatGPT, it put me onto `mergerFS` running on top of `SnapRAID`.

I have used `mergerFS` before but not as smartly as it could be.    

With `SnapRAID` there is a significant known issue with parity data
created and used by the package when deleting folders and wanting recovery,
however for my scenario (a relatively lightly changing archive of media files)
a nightly `sync` and `scrub` (parity check/rebuild) yields acceptable data rebuild risk
such as if/when a disk dies and needs to be replaced by a new one which
has been correctly formatted so that the rebuild can then be initiated.

# JUST SOME NOTES, UPCOMING EXPLORATION

### The question put to ChatGPT
> I have a newly released "Raspberry Pi 5" small computer with operating system "Raspberry Pi OS" based on "Debian Bookworm" which is the current latest supported version. 
> The Pi 5 has a Broadcom BCM2712 SoC with four ARM Cortex-A76 CPU cores clocked at 2.4GHz, and has  2 USB3 ports capable of running at full UB3 speed.
> It runs python3 and debian packages compiled for it.
>
> I have 
> - 4 up to eight 8 old external USB3 disks of various types and sizes ranging from 4Tb to 12 Tb.
> - 2 unpowered USB3 hubs connected to the Pi, with 2 and up to 4 of the USB3 disks conected to each USB3 hub
> - a set of "media folders" with standardized names under a root folder on each disk
> - some of the disks have both (a) blank media folders (b) media folders with files
> 
> Is there a sofwtare package or something to implement some form of disk reliablilty/backup,
> perhaps similar in outcome to a form of raid or something, which does not depend on all disks
> being be present to continue to operate but does ensure backup copies of files
> (perhaps  multiple copies of files on different disks) across the disks, or something similar to that ?
> 
> It would be essential that
> - the disks be able to be mounted and used independently in the normal way if the need arises
> - the disks be pre-formatted as NTFS with a GPT partition, for independent use when attached to a Windows 11 x64 PC
> - the file system appear to the user as one consolidated file system (eappearing to merge the folders under the root folders) with new files able to be copied to it and deleted and moved etc
> 
> Note that 'overlayfs' by itself is not acceptable since it does not spread/backup files across disks
> and new/updated files are staged to an area which apparently needs to then be acted on manually.

### Random Notes arising from the ChatGPT chat:

#### Setting up SnapRaid initially, per ChatGPT    
Had to question it hard, to get the detail required ... which changes its advice.

To find the exact location of the SnapRAID binary on your installed system, you can use the `which` command:
```bash
#This command will return the path to the SnapRAID executable if it is in your system’s PATH.
which snapraid
#Alternatively, you can use the find command to search for it:
sudo find / -name snapraid
# eg it may be one of 
#   /usr/local/bin/snapraid
#   /usr/sbin/snapraid
#   /usr/bin/snapraid
```
Now use the located path in ALL stuff below which uses the folder, eg `crontab`.

#### Configuring Passwordless sudo for snapraid    
Yes it's a bad thing.  Yes I want it anyway. 

If you want to allow a specific user to run SnapRAID commands with sudo without a password, you need to modify the `sudoers` file:    
Edit `sudoers` File
```bash
 sudo visudo
```
Add a line to allow your user to run SnapRAID commands without a password.    
For example, if your user is 'username' and the snapraid path is correct, add:
```bash
username ALL=(ALL) NOPASSWD: /usr/sbin/snapraid
```
OR, Add the Rule for All Users:
```bash
ALL ALL=(ALL) NOPASSWD: /usr/sbin/snapraid
```
This line means:
```
ALL      : All users can run as follows
ALL=(ALL): All users can execute commands as all users includinf root
NOPASSWD : /usr/sbin/snapraid: No password is required for running /usr/sbin/snapraid```
```
Save the file and exit the editor. The changes will be applied immediately.    
So, when the pi user (or any other user configured in sudoers) runs /usr/sbin/snapraid,
the the MUST use 'sudo' to do so.
For example:
```bash
sudo /usr/sbin/snapraid
```
Since sudo is used, it will check the sudoers configuration to determine if the user
has permission to run the command and if they can do so without a password.

Passwordless sudo: Configuring sudo to run without a password is optional and can be useful for automated tasks but must be done carefully to avoid security risks.
That setup ensures that your SnapRAID jobs run automatically with the necessary permissions, and you won’t need to manually enter a password when doing `snapraid` commands.

#### A word about `mmap` and `SnapRAID`    
While `mmap` can offer performance benefits for file access in some scenarios, 
it's not typically a major factor for media serving via `Samba` and `miniDLNA`. 
These applications handle large files efficiently using traditional file I/O methods. 
Therefore, in this setup, `mmap` is unlikely to provide significant benefits, 
and focusing on disk performance, network speed, and proper configuration of 
`MergerFS`, `SnapRAID`, `Samba`, and `miniDLNA` will be more impactful for optimizing media file access and streaming.


#### Official home pages and GitHub for `MergerFS` and `SnapRAID`:

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

#### ChatGPT advice for adding a new disk to existing `SnapRAID` setup

1. **Prepare the New Disk**:
- **Move Existing Files**: Move any existing files on the new disk to a folder outside of the new disk's proposed `MergerFS` root.
```bash
mkdir /mnt/new_disk/old_files
mv /mnt/new_disk/* /mnt/new_disk/old_files/
```

2. **Create MergerFS Top-Level Folder**:
- **Create Folder**: Create the top-level folder on the new disk.
```bash
mkdir /mnt/new_disk/media
```

3. **Update MergerFS**:
- **Configure MergerFS**: Add the new disk to the MergerFS pool, eg in `fstab`
```bash
/mnt/hdd*:/mnt/sda1 /mergerfs_root mergerfs category.action=mfs,category.create=mfs,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,branches-mount-timeout=300,fsname=mergerfs 0 0
#
#https://github.com/trapexit/mergerfs?tab=readme-ov-file#functions--policies--categories
#CHANGEDFROM THEIR DEFAULTS:
#moveonenospc=true
#dropcacheonclose=true
#cache.readdir=true
#cache.files=partial
#category.action=mfs
#category.create=mfs
#category.search=all
#fsname=mergerfs
#lazy-umount-mountpoint=true
#branches-mount-timeout=300
```

4. **Update SnapRAID**:
- **Add New Disk to SnapRAID**: Add the new disk and its top-level folder to SnapRAID’s configuration, eg
```bash
disk d7 /mnt/new_disk/media
```

5. **Move Files**:
- **Redistribute Files**: Move files from the folder outside the MergerFS root into the MergerFS pool.
Spread them across disks so you manually achieve some levelling. eg
```bash
sudo rsync -av /mnt/new_disk/old_files/* /mnt/mergerfs_pool/
```

6. **Sync and Scrub SnapRAID**:
- **Run Sync**: Update the parity data to include the new files.
- **Run Scrub**: Verify the integrity of the data and ensure parity consistency.
```bash
sudo snapraid sync
sudo snapraid scrub
```

7. **Check you had added the cron jobs to sync 2-hourly, and another to scrub and also check everything nightly**
- **SnapRAID tasks**:
Since SnapRAID typically requires root privileges, it’s best to add the cron jobs to the root user’s crontab.    
Add the jobs to the root’s crontab ensures they run with the necessary privileges of root.    
You can edit the root’s crontab by running:
```bash
sudo crontab -e
```
```bash
# Run SnapRAID Sync every 2 hours (use the correct paths below)
0 */2 * * * /usr/sbin/snapraid sync >> /var/log/snapraid.log 2>&1
# Run SnapRAID tasks sequentially starting at 3 AM, with each command on a new line,
#    using ';' each task runs independently of the success of the prior task
0 3 * * * \
/usr/sbin/snapraid status >> /var/log/snapraid.log 2>&1 ; \
/usr/sbin/snapraid sync >> /var/log/snapraid.log 2>&1 ; \
/usr/sbin/snapraid scrub >> /var/log/snapraid.log 2>&1
```

**Summary of Adjusted Steps**
1. Prepare the new disk by moving existing files out of the MergerFS top-level folder.
2. Create the MergerFS top-level folder on the new disk.
3. Update the MergerFS configuration to include the new disk.
4. Add the new disk to SnapRAID's configuration.
5. Move files into the MergerFS pool.
6. Run SnapRAID sync and scrub to update and verify the parity data.

By following this sequence, you ensure that all files are properly integrated into the MergerFS pool and that SnapRAID is synchronized and consistent with the new data.

### Additional Tips

- **Verify Disk Health**: Before adding the NTFS disk to SnapRAID, ensure it is healthy and free from errors.
- **Monitor Logs**: Check the MergerFS and SnapRAID logs for any issues during the process.
- **Backup**: Ensure you have backups of critical data before making significant changes.

By following these steps, you can efficiently add a new disk with existing files to your MergerFS and SnapRAID setup, ensuring that the files are balanced and parity data is correctly updated.




#### Miscellaneous ChatGPT Notes

If you need the disks to be mountable independently on Windows 11 from time to time, 
you'll need to avoid traditional RAID configurations that require all
disks to be present and synchronized on the Pi 5.

Traditional RAID setups (like RAID 0, 1, 5, 6, 10) typically require the disks
to be used together and aren't easily separable for independent use on another system.

Here are the options that allow disks to be used independently on Windows 11:

### SnapRAID

SnapRAID is specifically designed for media collections and allows the disks to be mounted and used independently.
It uses parity files to provide redundancy and recovery capabilities, and since it operates at the file level,
each disk remains a standard filesystem (e.g., NTFS) that can be mounted and used separately.

My note: With SnapRAID there is a significant known issue with parity data created and used by the package
when deleting folders and wanting recovery, however for this scenario 
(a relatively lightly changing archive of media files) 
a nightly sync and scrub (parity check/rebuild) yields acceptable data rebuild risk
such as if/when a disk dies and needs to be replaced by a new one which has been correctly
NTFS formatted with security 'everyone' having 'Full Control' and the root folder created on it
to be use in an updated fstab for mounts to occur properly ... 
so that `scrub` a rebuild can then be initiated.

### Using SnapRAID with MergerFS

Combining SnapRAID with MergerFS gives you a consolidated view of your files and redundancy,
while still allowing each disk to be independently mountable.

1. **MergerFS** provides a union filesystem that allows you to access multiple disks as a single cohesive filesystem.
2. **SnapRAID** provides redundancy and parity for file recovery, without requiring the disks to be part of a single RAID array.

### Steps to Ensure Independent Disk Use on Windows 11:

1. **Format Disks as NTFS**:
Format each disk as NTFS with a GPT partition table i.e. a GPT disk not anything else. This ensures they are compatible with both Linux and Windows 11.

2. **Configure SnapRAID**:
Set up SnapRAID, making sure each disk is listed as a data disk in the SnapRAID configuration
and spread the parity data across the maximum number of disks that SnapRAID can be configured to use.

3. **Use MergerFS**:
Use MergerFS to create a pooled view of your files on the Raspberry Pi, ensuring easy access and management.
** warning** check the documentation on the effects of configuring policies, eg
https://perfectmediaserver.com/02-tech-stack/mergerfs/ says    

The default create policy is `epmfs`.
That is a path preserving algorithm.
With such a policy for mkdir and create with a set of empty drives it will select only 1 drive when the first directory is created.
Anything, files or directories, created in that first directory will be placed on the same branch because it is preserving paths.
**This catches a lot of new users off guard** but changing the default would break the setup for many existing users.
If you do not care about path preservation and wish your **files to be spread across all your drives change to `mfs`**.

Info

Take a moment to read this issue on the mergerfs GitHub if you're a looking for more context on create policies - they can be a bit confusing to begin with.

You might find the best all round option to use in your /etc/fstab entry for mergerfs is category.create=mfs. This will fill all disks at roughly the same rate but not colocate entire "blobs". In otherwords, episodes from the same TV show might end up all over all your disks - in practice this doesn't matter but it might matter to you if you're a neat freak.

If you do want path preservation you'll need to perform the manual act of creating paths on the drives you want the data to land on before transferring your data3.



4. **Disk Mounting on Windows 11**:
If you need to use a disk independently, unmount it from the Raspberry Pi and connect it to the Windows 11 machine. Windows will recognize the NTFS filesystem, allowing you to read/write files directly.

### Example Configuration for SnapRAID and MergerFS

**SnapRAID Configuration (snapraid.conf)**:
```conf
parity /mnt/disk1/snapraid.parity
content /mnt/disk1/snapraid.content
content /mnt/disk2/snapraid.content
content /mnt/disk3/snapraid.content

data /mnt/disk2
data /mnt/disk3

exclude *.bak
```

**MergerFS Mount Command**:
```bash
sudo mergerfs -o defaults,category.action=mfs,category.create=mfs,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,branches-mount-timeout=300,fsname=mergerfs /mnt/disk2:/mnt/disk3 /mnt/pool
```
**MergerFS fstab**:
```bash
/mnt/hdd*:/mnt/sda1 /mergerfs_root mergerfs category.action=mfs,category.create=mfs,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,branches-mount-timeout=300,fsname=mergerfs 0 0
**MergerFS Mount Command**:
```

This setup ensures:
- **File Distribution and Redundancy**: Files are distributed across disks with redundancy provided by SnapRAID.
- **Independent Disk Usage**: Each disk remains a standard NTFS filesystem that can be independently mounted on Windows 11 if needed.
- **Consolidated View**: MergerFS provides a single, consolidated view of all your files.

By using SnapRAID in combination with MergerFS, you achieve a balance of redundancy and flexibility, allowing disks to be independently mountable on Windows 11.


### Unedited notes

#### readdir caching
As of version 4.20 Linux supports readdir caching. This can have a significant impact on directory traversal.
Especially when combined with entry (cache.entry) and attribute (cache.attr) caching. 
Setting cache.readdir=true will result in requesting readdir caching from the kernel on each opendir. 
If the kernel doesn't support readdir caching setting the option to true has no effect. 
This option is configurable at runtime via xattr user.mergerfs.cache.readdir.


To have the pool mounted at boot or otherwise accessible from related tools use /etc/fstab.

# <file system>        <mount point>  <type>    <options>             <dump>  <pass>
```
/mnt/hdd*:/mnt/ssd    /media          mergerfs  minfreespace=16G      0       0
```
will use all mount points in /mnt prefixed with hdd, as well as just ssd

```
Category	FUSE Functions
action	    chmod, chown, link, removexattr, rename, rmdir, setxattr, truncate, unlink, utimens
create	    create, mkdir, mknod, symlink
search	    access, getattr, getxattr, ioctl (directories), listxattr, open, readlink
N/A	        fchmod, fchown, futimens, ftruncate, fallocate, fgetattr, fsync, ioctl (files), read, readdir, release, statfs, write, copy_file_range
```

#### TO INSTALL
NOTE: for mounting via fstab to work you must have mount.fuse installed. For Ubuntu/Debian it is included in the fuse package ?fuse3?.

```
sudo apt show fuse3
sudo apt-cache showpkg fuse3
sudo apt-cache show fuse3
sudo apt-cache policy fuse3
sudo apt show fuse3 
sudo dpkg -l | grep fuse3
```

```
# get and install
wget https://github.com/trapexit/mergerfs/releases/download/<ver>/mergerfs_<ver>.debian-<rel>_<arch>.deb
dpkg -i mergerfs_<ver>.debian-<rel>_<arch>.deb
#
https://github.com/trapexit/mergerfs/releases/download/2.40.2/mergerfs_2.40.2.debian-bookworm_arm64.deb
dpkg -i mergerfs_2.40.2.debian-bookworm_arm64.deb
```


---


# SUPERSEDED, COMPLETE BOLLOCKS BELOW



. **Install some software; in a Terminal**    
```
# Install disk params checker, eg sudo hdparm -Tt /dev/sda
sudo apt -y install hdparm
# Install a tool which can be used to turn EOL inside text files from windows type to unix type
sudo apt install -y dos2unix
# Install the curl and wget tools to download support files if required
sudo apt install -y curl
sudo apt install -y wget
```

6. **Add user `pi` into groups `plugdev` and `systemd-journal`; in a Terminal**    
```
sudo usermod -a -G plugdev pi
sudo usermod -a -G systemd-journal pi
# plugdev:         Allows members to mount (only with the options nodev and nosuid, for security reasons) and umount removable devices through pmount.
# systemd-journal: Since Debian 8 (Jessie), members of this group can use the command 'journalctl' and read log files of systemd (in /var/log/journal).
```

7. **Make this server IPv4 only, by disabling IPv6; in a Terminal**    
```
sudo sysctl net.ipv6.conf.all.disable_ipv6=1 
sudo sysctl -p
sudo sed -i.bak "s;net.ipv6.conf.all.disable_ipv6;#net.ipv6.conf.all.disable_ipv6;g" "/etc/sysctl.conf"
echo net.ipv6.conf.all.disable_ipv6=1 | sudo tee -a "/etc/sysctl.conf"
sudo sysctl -p
```

8. **Increase system parameter `fs.inotify.max_user_watches` from default 8192 (used by miniDLNA to monitor changes to filesystems); in a Terminal**    
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

9. **We choose to create some `alias` shortcut commands to make life easier, by editing script `~/.bashrc`; in a Terminal**    
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

10. **Reboot the Pi 5 for everything to take effect; in a Terminal**    
```
sudo reboot now
```

## Set the Router so this Pi has a Reserved fixed (permanent) DHCP IP Address Lease
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

Login to the router and look at the LAN connected devices, looking for the IP address matching the Pi.    

Head on to the Router's DHCP management area and allocated a Reserved fixed (permanent) DHCP IP address lease
for the Pi and apply/save that in the router. Reboot the Pi, then on the Pi start a Terminal and do    
```
hostname -f
hostname -I
#ifconfig
```
and notice the IP address and hope it matches the IP Address reservation you made on the router.    
If not, check what you have done on the router and fix it and reboot the Pi.    

## Ascertain disks info, specifically DISK-UUID, PARTUUID, and MOUNTPOINT    
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
From each relevant partition we identify, look for the disk UUID, PARTUUID, NAME (eg `sda`) and save these somewhere, as we NEED the PARTUUIDs later.

If we wanted to cross-check disks, we could `sudo mount` like this and amongst them will be something like this:
```
$ sudo mount -l | grep "overlay\|disk"
/dev/sdb2 on /media/pi/DISK1-5TB type ntfs3 (rw,nosuid,nodev,relatime,uid=1000,gid=1000,windows_names,iocharset=utf8,uhelper=udisks2) [DISK1-5TB]
/dev/sda2 on /media/pi/DISK2-4TB type ntfs3 (rw,nosuid,nodev,relatime,uid=1000,gid=1000,windows_names,iocharset=utf8,uhelper=udisks2) [DISK2-4TB]
```

Now we have identified the correct disks, partitions and their PARTUUID, and now need to identify the root folder names on them.    

Start `File Manager` and navigate to each of the partitions, something like:
- the media root folder is under `/media/pi/DISK1-5TB`    
- the media root folder is under `/media/pi/DISK2-4TB`

and locate the root folder in each partition which contains the media files 
... and make a note of these root folder names **alongside** the corresponding PARTUUID.    
So, you will have noted for each disk UUID, partition PARTUUID. and the root folder name on that partition, eg for
```
# File Manager Folder Name
/media/pi/DISK1-5TB/ROOTFOLDER1
/media/pi/DISK2-4TB/ROOTFOLDER2
```
the [UUID, PARTUUID, root folder name] quadruplet would be
```
DISK-UUID         PARTUUID                              NAME    root folder name
C4D05ABAD05AB302  2d5599a2-aa11-4aad-9f75-7fca2078b38b  sdb     ROOTFOLDER1
96DA1D13DA1CF0EB  a175d2d3-c2f6-44d4-a5fc-209363280c89  sda     ROOTFOLDER2
```

## Create new 'standardized' mount points for disks and 'virtual overlayed folder'
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

## Backup and Edit `/etc/fstab` so disks are mounted consistently     
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

##  Reboot to see what happens with those mounts    
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

## Setup `HD-IDLE` to ensure disks are not constantly spun up
Per `https://www.htpcguides.com/spin-down-and-manage-hard-drive-power-on-raspberry-pi/`
some WD external USB3 disks won't spin down on idle and HDPARM and SDPARM don't work on them
... the `adelolmo` version of `hd-idle` appears to work, so let's use that.  

**Do NOT do this:**
```
sudo apt -y install hd-idle
# and then these
sudo apt-cache show hd-idle
sudo apt list --installed | grep hd-idle
dpkg -l | grep hd-idle
```
since all show version `1.05+ds-2+b1` which is very old.

This `https://github.com/adelolmo/hd-idle` shows a minimum of release `1.21 / 2023-10-22` in
`https://github.com/adelolmo/hd-idle/releases/download/v1.21/hd-idle_1.21_arm64.deb`

Remove any prior install of `hd-idle`. In a Terminal,
```
sudo systemctl disable hd-idle
sudo systemctl stop hd-idle
# wait 2 seconds, then
sudo dpkg -l hd-idle
sudo dpkg -P hd-idle 
sudo apt -y purge hd-idle
sudo rm -vf /var/log/hd-idle.log
```

Install the more up-to-date release of 'adelolmo' version of `hd-idle` direct from the author.
In a Terminal
```
# https://github.com/adelolmo/hd-idle
cd ~/Desktop
rm -fvr ./hd-idle
mkdir -pv hd-idle
cd hd-idle
sudo touch /var/log/hd-idle.log
sudo chmod +777 /var/log/hd-idle.log
sudo rm -vf hd-idle_1.21_arm64.deb
wget https://github.com/adelolmo/hd-idle/releases/download/v1.21/hd-idle_1.21_arm64.deb
sudo dpkg -i "./hd-idle_1.21_arm64.deb"
sudo dpkg -l hd-idle
cd ~/Desktop
```

Noting previously the [UUID, PARTUUID, root folder name] quadruplet of each disk
```
DISK-UUID         PARTUUID                              NAME    root folder name
C4D05ABAD05AB302  2d5599a2-aa11-4aad-9f75-7fca2078b38b  sdb     ROOTFOLDER1
96DA1D13DA1CF0EB  a175d2d3-c2f6-44d4-a5fc-209363280c89  sda     ROOTFOLDER2
```

Stop `hd-idle`
```
sudo systemctl stop hd-idle
```

After edit `etc/default/hd-idle` to change `hd-idle` parameters
```
sudo nano /etc/default/hd-idle
# enabling hd-idle auto start by changing line 'START_HD_IDLE=false' to have a value **true**
START_HD_IDLE=true
# Adding lines at the end for every disk, using the noted NAME
# option -d = debug
##Double check hd-idle works with the hard drive
##sudo hd-idle -t ??? -d
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
# sda etc     timeout 900s = 15 mins
HD_IDLE_OPTS="-i 300 -a /dev/sdb -i 900 -a /dev/sda -i 900 -l /var/log/hd-idle.log"
```

To enable `hd-idle` on reboot and then restart, in a Terminal:
```
sudo systemctl enable hd-idle   
sudo systemctl stop hd-idle
sudo systemctl restart hd-idle
# wait 2 secs
sudo cat /var/log/hd-idle.log
journalctl -u hd-idle.service | grep hd-idle| tail -n 50
sudo systemctl status hd-idle.service | tail -n 50
```

Test `hd-idle`
```
sudo hd-idle -t /dev/sdb -d -l /var/log/hd-idle.log
sudo hd-idle -t /dev/sda -d -l /var/log/hd-idle.log
# wait 2 secs
sudo cat /var/log/hd-idle.log
journalctl -u hd-idle.service | grep hd-idle| tail -n 50
sudo systemctl status hd-idle.service | tail -n 50
```

## Install and configure `SAMBA`to create file shares on the LAN
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
[overlayed_media_root]
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

Test the new `SAMBA` parameters in a Terminal:
```
sudo testparm
```

Restart the `SAMBA` service, waiting 2 secs in between each command
```
sudo systemctl enable smbd
# wait 2 secs
sudo systemctl stop smbd
# wait 2 secs
sudo systemctl restart smbd
```

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

You can now access the defined shares from a Windows machine or from an app that supports the SMB protocol.    
eg on a Windows 11 PC in Windows Explorer use the IP address of the Pi, eg ...    
```
REM read-only virtual folder of overlayed disk folders
\\10.0.0.18\overlayed_media_root
REM DISK1 as read-write (copy new media to subfolders here, depending on how full this disk is)
\\10.0.0.18\individual_disks\DISK1
REM DISK2 root folder as read-write (copy new media to subfolders here, depending on how full this disk is)
\\10.0.0.18\individual_disks\DISK2\ROOTFOLDER2
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
sudo rm -vfR "/mnt/shared/usb3disk1/minidlna"
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
sudo mkdir -pv                 "/mnt/shared/usb3disk1/minidlna"
sudo chmod -c a=rwx -R         "/mnt/shared/usb3disk1/minidlna"
sudo chown -c -R pi:minidlna   "/mnt/shared/usb3disk1/minidlna"
#
sudo chmod -c a=rwx -R         "/run/minidlna"
sudo chown -c -R pi:minidlna   "/run/minidlna"
#
sudo touch                     "/run/minidlna/minidlna.pid"
sudo chmod -c a=rwx -R         "/run/minidlna/minidlna.pid"
sudo chown -c -R pi:minidlna   "/run/minidlna/minidlna.pid"
#
sudo mkdir -pv                 "/mnt/shared/usb3disk1/minidlna/cache"
sudo chmod -c a=rwx -R         "/mnt/shared/usb3disk1/minidlna/cache"
sudo chown -c -R pi:minidlna   "/mnt/shared/usb3disk1/minidlna/cache"
#
sudo mkdir -pv                 "/mnt/shared/usb3disk1/minidlna/log"
sudo touch                     "/mnt/shared/usb3disk1/minidlna/log/minidlna.log"
sudo chmod -c a=rwx -R         "/mnt/shared/usb3disk1/minidlna/log"
sudo chown -c -R pi:minidlna   "/mnt/shared/usb3disk1/minidlna/log"
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
##minidlna_refresh_log_file=/mnt/shared/usb3disk1/minidlna/log/minidlna_refresh.log
##minidlna_refresh_sh_file=/mnt/shared/usb3disk1/minidlna/minidlna_refresh.sh
##minidlna_restart_refresh_sh_file=/mnt/shared/usb3disk1/minidlna/minidlna_restart_refresh.sh

# Find and change line `media_dir=/var/lib/minidlna` to comment it out:
##media_dir=/var/lib/minidlna

# Find and change line `album_art_names=` to comment it out:
##album_art_names=

# Find and uncomment and/or change/add line `#friendly_name=` to:
friendly_name=PINAS64-minidlna

# Find and uncomment and/or change/add line `#model_name=` to:
model_name=PINAS64-miniDLNA

# Find and uncomment and/or change/add line `#merge_media_dirs=` to:
merge_media_dirs=no

# Find and uncomment and/or change/add line `#db_dir=/var/cache/minidlna` to:
db_dir=/mnt/shared/usb3disk1/minidlna/cache

# Find and uncomment and/or change/add line `#log_dir=/var/log/minidlna` to:
log_dir=/mnt/shared/usb3disk1/minidlna/log

# inotify=yes and notify_interval=895 work together fopr miniDLNA to discover added and modified files
# Find and uncomment and/or change/add line `#inotify=yes` to:
inotify=yes
# Find and uncomment and/or change/add line `#notify_interval=895` (5 seconds under 15 minutes) to:
notify_interval=895

# Find and uncomment and/or change/add line `#strict_dlna=no` to:
strict_dlna=yes

# Find and uncomment and/or change/add line `#max_connections=50` to a number expected for this LAN:
# (many clients open several simultaneous connections while streaming)
max_connections=24

# Find and uncomment and/or change/add line `#log_level=general,artwork,database,inotify,scanner,metadata,http,ssdp,tivo=warn` to:
log_level=general,artwork,database,inotify,scanner,metadata,http,ssdp,tivo=info

# Find and uncomment and/or change/add line `#wide_links=no` to:
wide_links=yes

# now ADD the line to expose the overlayed media folder ...
root_container=PVA,/mnt/shared/overlay
##media_dir=PVA,/mnt/shared/overlay

# now ADD any lines where wish to expose folders
# separately to, but as well as in, the overlayed folder tree, eg
# THE ENTRIES BELOW MUST EXACTLY MATCH THE FOLDERS YOU WISH DLNA TO EXPOSE
media_dir=PVA,/mnt/shared/overlay/ClassicMovies
media_dir=PVA,/mnt/shared/overlay/Documentaries
media_dir=PVA,/mnt/shared/overlay/Footy
media_dir=PVA,/mnt/shared/overlay/Movies
media_dir=PVA,/mnt/shared/overlay/Music
media_dir=PVA,/mnt/shared/overlay/OldMovies
media_dir=PVA,/mnt/shared/overlay/SciFi
```
Restart miniDLNA and force a db reload.
```
sudo systemctl stop minidlna 
sudo systemctl restart minidlna 
sudo systemctl force-reload minidlna 
sudo systemctl status minidlna | tail -n 50
tail -n 50 /mnt/shared/usb3disk1/minidlna/log/minidlna.log
```
The minidlna service comes with an internal small web server and webinterface.    
This webinterface is just for informational purposes.    
You will not be able to configure anything here.    
However, it gives you a nice and short information screen how many files have been found by minidlna.    
To access the webinterface, open your browser of choice and enter url http://127.0.0.1:8200    
```
curl -i http://127.0.0.1:8200
```

**Under COnstruction**    
```
minidlna_refresh_sh_file=/mnt/shared/usb3disk1/minidlna/minidlna_refresh.sh
minidlna_refresh_log_file=/mnt/shared/usb3disk1/minidlna/log/minidlna_refresh.log
minidlna_restart_refresh_sh_file=/mnt/shared/usb3disk1/minidlna/minidlna_restart_refresh.sh
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
echo "# You will not be able to configure anything here. "
echo "# However, it gives you a nice and short information screen how many files have been found by minidlna. "
echo "# minidlna comes with it’s own webserver integrated. "
echo "# This means that no additional webserver is needed in order to use the webinterface."
echo "# To access the webinterface, open your browser of choice and enter url http://127.0.0.1:8200"
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
# You will now see on the left side a category which is called Local Network. 
# Click on Universal Plug’n’Play which is under the Local Network category. 
# You will then see a list of available DLNA service within your local network. 
# In this list you should see your DLNA server. 
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

You can set a wake alarm which will switch the board to a very low-power state (approximately 3mA). 
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
You can test the battery RTC functionality with:
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
