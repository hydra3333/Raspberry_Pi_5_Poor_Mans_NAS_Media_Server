import os
import subprocess
from pathlib import Path
import glob
import re
import logging
import pprint

# Configuration
DEBUG_IS_ON = True  # Set to False to disable debug printing

# Set up logging
LOGFILE = "/home/pi/Desktop/media_sync_script.log"
logging.basicConfig(filename=LOGFILE,
                    level=logging.DEBUG if DEBUG_IS_ON else logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

# Set up prettyprint for formatting
TERMINAL_WIDTH = 250
objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)  # facilitates formatting

def debug_print(message):
    """
    Prints debug messages if DEBUG_IS_ON is True, and logs the message.
    """
    logging.debug(message)
    if DEBUG_IS_ON:
        print(f"DEBUG: {message}")

def get_mergerfs_disks_in_LtoR_order_from_fstab():
    """
    Reads the /etc/fstab file to find the disks used in the mergerfs mount line.
    Handles globbing patterns to expand disk entries.
    Returns a list of detected 'mergerfs' underlying disks in LtoR order from fstab.
    Each entry in the list is a dictionary containing 'disk_mount_point' and 'free_disk_space'.
       eg: [ {'disk_mount_point': '/mnt/sda1', 'free_disk_space': free_disk_space} ,
             {'disk_mount_point': '/mnt/sda2', 'free_disk_space': free_disk_space} ,
           ]
    Note: this does not guarantee a detected underlying disk contains a root folder or any 'top level media folders' under it.
    """
    the_mergerfs_disks_in_LtoR_order_from_fstab = []
    try:
        with open('/etc/fstab', 'r') as fstab_file:
            fstab_lines = fstab_file.readlines()
        # Loop through all lines in fstab looking for 'mergerfs' mounts.
        # Keep the valid mergerfs underlying disks in LtoR order
        # so we can use it later to determine the 'ffd', aka 'first found disk', for each 'top media folder' by parsing this list
        fstab_mergerfs_line = ''
        for line in fstab_lines:
            # Example line (without the #) we are looking for
            # "/mnt/hdd*:/mnt/sda1:/mnt/sda2 /mergerfs_root mergerfs category.action=ff,category.create=ff,category.delete=all,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,branches-mount-timeout=300,fsname=mergerfs 0 0"
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            fields = line.split()
            if any('mergerfs' in field.lower() for field in fields):  # Identify mergerfs entries
                fstab_mergerfs_line = line.strip()
                debug_print(f"MergerFS line found: {line.strip()}")
                # fields[0] should contain one or more and/or globbed, underlying file system mount points used by mergerfs
                mount_points = fields[0]
                # Split apart a possible list of underlying file system mount points separated by ':'
                split_disks = mount_points.split(':')
                # Process each underlying file system mount point separately, catering for globbing entries
                for disk in split_disks:
                    # Handle wildcard globbing pattern (eg /mnt/hdd*)
                    if '*' in disk:
                        expanded_paths = glob.glob(disk)
                        the_mergerfs_disks_in_LtoR_order_from_fstab.extend(expanded_paths)
                    elif '{' in disk and '}' in disk:
                        # Handle curly brace globbing pattern (eg /mnt/{hdd1,hdd2})
                        pattern = re.sub(r'\{(.*?)\}', r'(\1)', disk)
                        expanded_paths = glob.glob(pattern)
                        the_mergerfs_disks_in_LtoR_order_from_fstab.extend(expanded_paths)
                    else:
                        # Handle plain (eg /mnt/hdd1 underlying file system mount point
                        the_mergerfs_disks_in_LtoR_order_from_fstab.append(disk)
                # If more than 1 mergerfs line is found, it's a conflict
                if len(the_mergerfs_disks_in_LtoR_order_from_fstab) > 1:
                    logging.error("Multiple mergerfs lines found in 'fstab'. Aborting.")
                    sys.exit(1)  # Exit with a status code indicating an error
    except Exception as e:
        logging.error(f"Error reading /etc/fstab: {e}")
        sys.exit(1)  # Exit with a status code indicating an error

    if len(the_mergerfs_disks_in_LtoR_order_from_fstab) < 1:
        logging.error(f"ZERO Detected 'mergerfs' underlying disks in LtoR order from 'fstab': {the_mergerfs_disks_in_LtoR_order_from_fstab}")
        sys.exit(1)  # Exit with a status code indicating an error

    debug_print(f"Detected 'mergerfs' underlying disks in LtoR order from fstab '{fstab_mergerfs_line}': {the_mergerfs_disks_in_LtoR_order_from_fstab}")
    return the_mergerfs_disks_in_LtoR_order_from_fstab

def detect_mergerfs_disks_having_a_root_folder(mergerfs_disks_in_LtoR_order_from_fstab):
    """
    Checks each underlying mergerfs disk_mount_point for the presence of a single root folder like 'mergerfs_Root_1' to 'mergerfs_Root_8'.
    If multiple root folders are found on a single disk_mount_point, it raises an error with details.
    Returns a dictionary those_mergerfs_disks_having_a_root_folder as:
        Key: disk_mount_point path (e.g., '/mnt/sda1')
        Value: a dict {'root_folder_path': found_root_folder_path, 'top_level_media_folders': found_top_level_media_folders_list}
           eg: a dict {'root_folder_path': '/mnt/sda1/mergerfs_Root_1', 'top_level_media_folders': ['top_level_folder_1', 'top_level_folder_2', 'top_level_folder_3']}
    """
    those_mergerfs_disks_having_a_root_folder = {}
    for disk_mount_point in mergerfs_disks_in_LtoR_order_from_fstab:
        try:
            disk_mount_point_path = Path(disk_mount_point)
            if disk_mount_point_path.is_dir():
                candidate_root_folders = [d.name for d in disk_mount_point_path.iterdir() if d.is_dir() and re.match(r'^mergerfs_Root_[1-8]$', d.name)]
                # Check for multiple root folders on the same disk
                if len(candidate_root_folders) > 1:
                    error_message = (f"Error: disk_mount_point {disk_mount_point} has multiple root folders: {candidate_root_folders}."
                                     "Each disk_mount_point should only have one root folder like 'mergerfs_Root_*'.")
                    logging.error(error_message)
                    sys.exit(1)  # Exit with a status code indicating an error
                elif len(candidate_root_folders) == 1:
                    found_root_folder = candidate_root_folders[0]
                    found_root_folder_path = disk_mount_point_path / found_root_folder
                    found_top_level_media_folders_list = [d.name for d in found_root_folder_path.iterdir() if d.is_dir()]
                    # if a disk_mount_point with a known root folder has top level media folders, then save them
                    if found_top_level_media_folders_list:
                        those_mergerfs_disks_having_a_root_folder[disk_mount_point] = {'root_folder_path': found_root_folder_path, 'top_level_media_folders': found_top_level_media_folders_list}
                        debug_print(f"disk_mount_point {disk_mount_point} has root folder '{found_root_folder}' with top level media folders: {found_top_level_media_folders_list}")
                else:
                    pass
        except Exception as e:
            logging.error(f"Error accessing {disk_mount_point}: {e}")
            sys.exit(1)  # Exit with a status code indicating an error

    if len(those_mergerfs_disks_having_a_root_folder) < 1:
        logging.error(f"ZERO Detected 'mergerfs' underlying disks having a root folder AND top_level_media_folders: {mergerfs_disks_in_LtoR_order_from_fstab}")
        sys.exit(1)  # Exit with a status code indicating an error

    debug_print(f"Detected 'mergerfs' underlying disks having a root folder AND top level media folders: {those_mergerfs_disks_having_a_root_folder}")
    return those_mergerfs_disks_having_a_root_folder

 # OK given we have:
 #    get_mergerfs_disks_in_LtoR_order_from_fstab returning a list
 #    detect_mergerfs_disks_having_a_root_folder returning a dict
 # we can create a function to derive a new dict 'full_set_of_top_level_media_folders' sorted in alphabetical order of top_level_media_folder_name, containing
 #    