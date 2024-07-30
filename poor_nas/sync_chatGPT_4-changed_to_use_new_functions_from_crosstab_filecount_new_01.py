import os
import subprocess
from pathlib import Path
import glob
import logging
import pprint

# Configuration
DEBUG_IS_ON = True  # Set to False to disable debug printing

# Installation Instructions:
# --------------------------
# This script requires the `rsync` command-line utility and the Python `logging` module.
# These are typically included with most Linux distributions.
#
# The `logging` module is part of the Python standard library and does not require separate installation.

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

# Assuming the functions get_mergerfs_disks_in_LtoR_order_from_fstab, detect_mergerfs_disks_having_a_root_folder, and get_unique_top_level_media_folders are imported from the common module.

def sync_folders(unique_top_level_media_folders, mergerfs_disks_having_a_root_folder):
    """
    Synchronizes each top-level media folder from its FFD (First Found Disk) to all other disks containing the same top-level media folder.

    Args:
    - unique_top_level_media_folders (list of dict):
      This list contains dictionaries for each unique top-level media folder detected across all disks. 
      Each dictionary has the following structure:
        {
          'top_level_media_folder_name': str,  # The name of the media folder (e.g., 'Movies')
          'ffd': str,  # The first found disk (FFD) where this media folder is located
          'disk_info': [
            {
              'disk_mount_point': str,  # The mount point of the disk (e.g., '/mnt/sda1')
              'is_ffd': bool,  # True if this disk is the FFD for this media folder
              'root_folder_path': Path,  # The path to the root folder on this disk
              'number_of_files': int,  # The number of files in the media folder on this disk
              'disk_space_used': int,  # The space used by the media folder on this disk, in bytes
              'total_free_disk_space': int  # The total free space on this disk, in bytes
            },
            ...
          ]
        }

    - mergerfs_disks_having_a_root_folder (dict):
      This dictionary contains information about the disks that have a root folder and the media folders within them. 
      The structure is as follows:
        {
          'disk_mount_point': str,  # The mount point of the disk (e.g., '/mnt/sda1')
          'root_folder_path': Path,  # The path to the root folder (e.g., '/mnt/sda1/mergerfs_Root_1')
          'top_level_media_folders': [
            {
              'top_level_media_folder_name': str,  # The name of the media folder (e.g., 'Movies')
              'top_level_media_folder_path': Path,  # The path to the media folder (e.g., '/mnt/sda1/mergerfs_Root_1/Movies')
              'ffd': str,  # The first found disk (FFD) where this media folder is located (initially empty)
              'number_of_files': int,  # The number of files in this media folder on this disk
              'disk_space_used': int  # The space used by this media folder on this disk, in bytes
            },
            ...
          ]
        }
      Example:
          [
              {'disk_mount_point': '/mnt/sda1', 'free_disk_space': 1234567890},
              {'disk_mount_point': '/mnt/sda2', 'free_disk_space': 987654321},
          ]

    This function performs the following:
    1. Identifies the FFD for each media folder.
    2. Uses `rsync` to synchronize the contents from the FFD to the corresponding folders on other disks.
    3. Handles errors gracefully, logs synchronization actions, and reports any discrepancies.

    The rsync command uses options
        rsync -av --delete --size-only {ffd_folder}/ {target_folder}/
    to
       -av         Copy files and directories from the source to the target if they are missing in the target.
       --delete    Remove files from the target that are not present in the source.
       --size-only Update files in the target if their size differs from the corresponding files in the source, ignoring timestamps.
    """

    # Loop through each known top level media folder and its ffd
    # These will be used as the source in an rsync command
    for media_folder_info in unique_top_level_media_folders:
        media_folder_name = media_folder_info['top_level_media_folder_name']
        ffd = media_folder_info['ffd']
        ffd_folder = None
        
        # A. Iterate through the root_folder and top_level_folders in the
        # dictionary stored at mergerfs_disks_having_a_root_folder[ffd].
        for disk_mount_point, disk_info in mergerfs_disks_having_a_root_folder.items():
            if disk_mount_point == ffd:
                for folder_info in disk_info['top_level_media_folders']:
                    if folder_info['top_level_media_folder_name'] == media_folder_name:
                        ffd_folder = folder_info['top_level_media_folder_path']
                        break
                if ffd_folder:
                    break
        
        if ffd_folder is None:
            logging.error(f"Error: FFD folder for {media_folder_name} not found on disk {ffd}.")
            sys.exit(1)  # Exit with a status code indicating an error
        
        # B. Use mergerfs_disks_having_a_root_folder by iterating over disks and
        # their associated root folders and top-level media folders.
        for disk_mount_point, disk_info in mergerfs_disks_having_a_root_folder.items():
            if disk_mount_point == ffd:
                continue    # skip the rest of the code for this iteration of this for
            
            for folder_info in disk_info['top_level_media_folders']:
                if folder_info['top_level_media_folder_name'] == media_folder_name:
                    target_folder = folder_info['top_level_media_folder_path']
                    if not target_folder.exists():
                        logging.error(f"Error: Target folder {target_folder} does not exist to rsync into.")
                        sys.exit(1)  # Exit with a status code indicating an error

                    # Ensure the parent directory exists for the target file on the target disk
                    if not target_folder.exists():
                        target_folder.mkdir(parents=True, exist_ok=True)

                    # Rsync command to synchronize the FFD folder to the target folder
                    sync_command = f"rsync -av --delete --size-only {ffd_folder}/ {target_folder}/"
                    try:
                        debug_print(f"Syncing {media_folder_name} from {ffd_folder} to {target_folder} : ")
                        debug_print(f"{sync_command}")
                        subprocess.run(sync_command, shell=True, check=True)
                    except subprocess.CalledProcessError as e:
                        logging.error(f"Error syncing {media_folder_name} from {ffd_folder} to {target_folder} using '{sync_command}': {e} ... continuing")
                        pass  # Considered continuing after an error, adjust as needed

def main():
    """
    Main function to orchestrate the sync process:
    1. Reads the fstab to detect disks used by mergerfs.
    2. Identifies media disks with mergerfs_Root_* folders.
    3. Determines the full set of top level media folders.
    4. Identifies the first found disk (ffd) for each folder.
    5. Syncs folders from the ffd to other disks.
    """
    disks_in_order_from_fstab = get_mergerfs_disks_in_LtoR_order_from_fstab()
    if not disks_in_order_from_fstab:
        logging.error("No disks found in fstab or mergerfs entry not detected.")
        sys.exit(1)  # Exit with a status code indicating an error

    mergerfs_disks_having_a_root_folder = detect_mergerfs_disks_having_a_root_folder(disks_in_order_from_fstab)
    if not mergerfs_disks_having_a_root_folder:
        logging.error("No media disks detected with mergerfs_Root_* folders.")
        sys.exit(1)  # Exit with a status code indicating an error

    unique_top_level_media_folders = get_unique_top_level_media_folders(disks_in_order_from_fstab, mergerfs_disks_having_a_root_folder)

    sync_folders(unique_top_level_media_folders, mergerfs_disks_having_a_root_folder)

if __name__ == "__main__":
    main()
