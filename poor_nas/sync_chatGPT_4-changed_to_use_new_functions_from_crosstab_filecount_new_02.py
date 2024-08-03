import os
import sys
import subprocess
from pathlib import Path
import glob
import re
import logging
import pprint
import shutil
import datetime

import common_functions

def sync_folders(unique_top_level_media_folders, mergerfs_disks_having_a_root_folder, perform_action=False):
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
            error_log_and_print(f"Error: ffd folder for {media_folder_name} not found on disk {ffd}.")
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
                        error_log_and_print(f"Error: media_folder_name:'{media_folder_name}',ffd:'{ffd_folder}' expected Target folder {target_folder} does not exist to rsync into.")
                        sys.exit(1)  # Exit with a status code indicating an error

                    # Ensure the parent directory exists for the target file on the target disk
                    if not target_folder.exists():
                        log_and_print(f"mkdir {target_folder} -p")
                        #target_folder.mkdir(parents=True, exist_ok=True)
                    # Rsync command to synchronize the FFD folder to the target folder
                    #    -av               Copy files and directories from the source to the target if they are missing in the target.
                    #    --delete          Remove files from the target that are not present in the source.
                    #    --size-only       Ignore timestamps, Update files in the target if their size differs from the corresponding files in the source, .
                    #    --human-readable  Output numbers in a more human-readable format.
                    #    --stats           Print a verbose set of statistics on the file transfer, telling how effective rsync’s delta-transfer algorithm is.
                    sync_command = f"rsync -av --delete --size-only --human-readable --stats {ffd_folder}/ {target_folder}/"

                    try:
                        log_and_print(f"Syncing {media_folder_name} from {ffd_folder} to {target_folder} : ")
                        log_and_print(f"{sync_command}")
                        if perform_action:
                            #subprocess.run(sync_command, shell=True, check=True)
                            with subprocess.Popen(sync_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as process:
                                for line in process.stdout:
                                    log_and_print(line.strip())
                                for line in process.stderr:
                                    log_and_print(line.strip())
                            process.wait()
                            if process.returncode == 0:
                                log_and_print(f"Successfully synced {media_folder_name}")
                            else:
                                log_and_print(f"Failed to sync {media_folder_name}. Error code: {process.returncode}")
                    except subprocess.CalledProcessError as e:
                        log_and_print(f"Failed to sync {media_folder_name}. Error: {e}")
                        error_log_and_print(f"Error syncing {media_folder_name} from {ffd_folder} to {target_folder} using '{sync_command}'")
                        error_log_and_print(f"ERROR: {e}\n... continuing...")
                        error_log_and_print(f"Continuing with sync ...")
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
    common_functions.DEBUG_IS_ON = True

    perform_action = False

    TERMINAL_WIDTH = 200
    common_functions.init_PrettyPrinter(TERMINAL_WIDTH)
    common_functions.init_logging(r'/home/pi/Desktop/logs/sync.log')

    common_functions.DEBUG_IS_ON = False

    common_functions.log_and_print('-' * TERMINAL_WIDTH)

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common_functions.log_and_print(f"Starting media 'SYNC' at {current_time}.")

    mergerfs_disks_in_LtoR_order_from_fstab = common_functions.get_mergerfs_disks_in_LtoR_order_from_fstab()
    if not mergerfs_disks_in_LtoR_order_from_fstab:
        error_log_and_print("No disks found in fstab or mergerfs entry not detected.")
        sys.exit(1)  # Exit with a status code indicating an error

    mergerfs_disks_having_a_root_folder_having_files = common_functions.detect_mergerfs_disks_having_a_root_folder_having_files(mergerfs_disks_in_LtoR_order_from_fstab)
    if not mergerfs_disks_having_a_root_folder_having_files:
        error_log_and_print("No media disks detected with media folders having files.")
        sys.exit(1)  # Exit with a status code indicating an error

    unique_top_level_media_folders, mergerfs_disks_having_a_root_folder_having_files = common_functions.get_unique_top_level_media_folders(
        mergerfs_disks_in_LtoR_order_from_fstab,
        mergerfs_disks_having_a_root_folder_having_files
    )

    common_functions.DEBUG_IS_ON = True
    sync_folders(unique_top_level_media_folders, mergerfs_disks_having_a_root_folder_having_files, perform_action=perform_action)
    common_functions.DEBUG_IS_ON = False

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common_functions.log_and_print(f"Finished 'media 'SYNC' at {current_time}.")
    common_functions.log_and_print('-' * TERMINAL_WIDTH)

if __name__ == "__main__":
    main()
