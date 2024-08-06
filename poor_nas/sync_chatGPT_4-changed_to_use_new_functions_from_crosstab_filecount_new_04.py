import os
import sys
import subprocess
import select
from collections import OrderedDict
from pathlib import Path
import glob
import re
import shutil
import datetime
import logging
import pprint

import common_functions

def sync_folders(unique_top_level_media_folders, perform_action=False, TERMINAL_WIDTH=200):
    """
    Synchronizes each top-level media folder from its FFD (First Found Disk) to all other disks containing the same top-level media folder.
    """
    list_of_media_folder_ffd_disks_to_sync = common_functions.get_list_of_media_folder_ffd_disks_to_sync(unique_top_level_media_folders)
    
    for candidate in list_of_media_folder_ffd_disks_to_sync:
        # candidate is an item in a list, itself a list: [ a top_level_media_folder_name, a path to copy from, a path to copy to ]
        if any(item == "" or item is None for item in candidate):
            common_functions.error_log_and_print(f"ERROR: sync_folders: one of list_of_media_folder_ffd_disks_to_sync has no value: {candidate}")
            sys.exit(1)  # Exit with a status code indicating an error
        top_level_media_folder_name, source_path, target_path = candidate
        source_path = Path(source_path)
        target_path = Path(target_path)
        if not source_path.exists():
            common_functions.error_log_and_print(f"Error: sync_folders: top_level_media_folder_name:'{top_level_media_folder_name}', expected source_path '{source_path}' does not exist to rsync from.")
            sys.exit(1)  # Exit with a status code indicating an error
        if not target_path.exists():
            common_functions.error_log_and_print(f"Error: sync_folders: top_level_media_folder_name:'{top_level_media_folder_name}', expected target_path '{target_path}' does not exist to rsync into.")
            sys.exit(1)  # Exit with a status code indicating an error

        # rsync command to synchronize the FFD folder to the target folder
        #    -av               Copy files and directories from the source to the target if they are missing in the target.
        #    --delete          Remove files from the target that are not present in the source.
        #    --size-only       Ignore timestamps, Update files in the target if their size differs from the corresponding files in the source.
        #    --human-readable  Output numbers in a more human-readable format.
        #    --stats           Print a verbose set of statistics on the file transfer, telling how effective rsync’s delta-transfer algorithm is.
        #    --dry-run         This makes rsync perform a trial run that doesn’t make any changes (and produces mostly the same output  as a real run).
        rsync_options = "-av --delete --size-only --human-readable --stats"

        common_functions.log_and_print(f"")
        common_functions.log_and_print('-' * TERMINAL_WIDTH)
        if perform_action:
            rsync_command = f"rsync {rsync_options} '{source_path}/' '{target_path}/'   # for '{top_level_media_folder_name}'"
            common_functions.log_and_print(f"sync_folders: Syncing '{top_level_media_folder_name}' from '{source_path}' to '{target_path}' with rsync command: \n{rsync_command}")
            common_functions.log_and_print(f"")
        else:
            rsync_options = " --dry-run " + rsync_options
            rsync_command = f"rsync {rsync_options} '{source_path}/' '{target_path}/' # DRY RUN for '{top_level_media_folder_name}'"
            common_functions.log_and_print(f"sync_folders: DRY RUN: Syncing '{top_level_media_folder_name}' from '{source_path}' to '{target_path}' with rsync command: \n{rsync_command}")
            common_functions.log_and_print(f"")

        return_code = common_functions.run_command_process(rsync_command)
        if return_code == 0:
            common_functions.log_and_print(f"")
            common_functions.log_and_print(f"sync_folders: Successfully completed syncing '{top_level_media_folder_name}' from '{source_path}' to '{target_path}' with rsync command: \n{rsync_command}")
        else:
            common_functions.log_and_print(f"")
            common_functions.error_log_and_print(f"FAILED: sync_folders: syncing '{top_level_media_folder_name}' from '{source_path}' to '{target_path}' with rsync command: \n{rsync_command}")
            common_functions.error_log_and_print(f"sync_folders: Continuing with syncing remaining 'top level media folder name's ...")
            pass
        common_functions.log_and_print('-' * TERMINAL_WIDTH)
        common_functions.log_and_print(f"")

def main():
    """
    Main function to orchestrate the sync process:
    1. Reads the fstab to detect disks used by mergerfs.
    2. Identifies media disks with mergerfs_Root_* folders.
    3. Determines the full set of top level media folders.
    4. Identifies the first found disk (ffd) for each folder.
    5. Syncs folders from the ffd to other disks.
    """
    common_functions.DEBUG_IS_ON = False

    TERMINAL_WIDTH = 200
    common_functions.init_PrettyPrinter(TERMINAL_WIDTH)
    common_functions.init_logging(r'/home/pi/Desktop/logs/sync.log')
    common_functions.log_and_print('-' * TERMINAL_WIDTH)

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common_functions.log_and_print(f"Starting media 'SYNC' at {current_time}.")

    mergerfs_disks_in_LtoR_order_from_fstab = common_functions.get_mergerfs_disks_in_LtoR_order_from_fstab()
    if not mergerfs_disks_in_LtoR_order_from_fstab:
        common_functions.error_log_and_print("No disks found in fstab or mergerfs entry not detected.")
        sys.exit(1)  # Exit with a status code indicating an error

    mergerfs_disks_having_a_root_folder_having_files = common_functions.detect_mergerfs_disks_having_a_root_folder_having_files(mergerfs_disks_in_LtoR_order_from_fstab)
    if not mergerfs_disks_having_a_root_folder_having_files:
        common_functions.error_log_and_print("No media disks detected with media folders having files.")
        sys.exit(1)  # Exit with a status code indicating an error

    unique_top_level_media_folders, mergerfs_disks_having_a_root_folder_having_files = common_functions.get_unique_top_level_media_folders(
        mergerfs_disks_in_LtoR_order_from_fstab,
        mergerfs_disks_having_a_root_folder_having_files
    )

    perform_action = True
    common_functions.DEBUG_IS_ON = True
    sync_folders(unique_top_level_media_folders, perform_action=perform_action, TERMINAL_WIDTH=TERMINAL_WIDTH)
    common_functions.DEBUG_IS_ON = False

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common_functions.log_and_print(f"Finished media 'SYNC' at {current_time}.")
    common_functions.log_and_print('-' * TERMINAL_WIDTH)

if __name__ == "__main__":
    main()
