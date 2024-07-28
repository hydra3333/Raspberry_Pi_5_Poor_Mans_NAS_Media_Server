import os
import subprocess
from pathlib import Path
import glob
import logging
import pprint

# Configuration
DEBUG_IS_ON = True  # Set to False to disable debug printing
LOGFILE = "/var/log/sync_script.log"

# Installation Instructions:
# --------------------------
# This script requires the `rsync` command-line utility and the Python `logging` module.
# These are typically included with most Linux distributions, but you can ensure they are installed as follows:
#
# To install rsync:
#     sudo apt update
#     sudo apt install rsync
#
# The `logging` module is part of the Python standard library and does not require separate installation.

# Set up logging
logging.basicConfig(filename=LOGFILE, level=logging.DEBUG if DEBUG_IS_ON else logging.INFO,
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

def get_disks_in_order_from_fstab():
    """
    Reads the /etc/fstab file to find the disks used in the mergerfs mount line.
    Handles globbing patterns to expand disk entries.
    Returns a list of disks detected.
    """
    the_disks_in_order_from_fstab = []
    try:
        with open('/etc/fstab', 'r') as fstab_file:
            fstab_lines = fstab_file.readlines()
        # Loop through all lines in fstab looking for mergerfs mounts
        # Keep the valid mergerfs disk, in struct order of left to right,
        # so we can use it later to determine the 'ffd', 'first found disk' for each 'top media folder'.
        for line in fstab_lines:
            # Example line (without the #) we are looking for
            #"/mnt/hdd*:/mnt/sda1:/mnt/sda2 /mergerfs_root mergerfs category.action=ff,category.create=ff,category.delete=all,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,branches-mount-timeout=300,fsname=mergerfs 0 0"
            # Skip comments and empty lines
            if line.startswith('#') or not line.strip():
                continue
            fields = line.split()
            if any('mergerfs' in field.lower() for field in fields):  # Identify mergerfs entries
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
                        the_disks_in_order_from_fstab.extend(expanded_paths)
                    elif '{' in disk and '}' in disk:
                        # Handle curly brace globbing pattern (eg /mnt/{hdd1,hdd2})
                        pattern = re.sub(r'\{(.*?)\}', r'(\1)', disk)
                        expanded_paths = glob.glob(pattern)
                        the_disks_in_order_from_fstab.extend(expanded_paths)
                    else:
                        # Handle plain (eg /mnt/hdd1 underlying file system mount point
                        the_disks_in_order_from_fstab.append(disk)

                # If more than 1 mergerfs line is found, it's a conflict
                if len(the_disks_in_order_from_fstab) > 1:
                    logging.error("Multiple mergerfs entries found in fstab. Aborting.")
                    sys.exit(1)  # Exit with a status code indicating an error

    except Exception as e:
        logging.error(f"Error reading /etc/fstab: {e}")
        sys.exit(1)  # Exit with a status code indicating an error

    debug_print(f"Detected disks: {the_disks_in_order_from_fstab}")
    return the_disks_in_order_from_fstab

def detect_media_disks_having_a_root_folder(disks_in_order_from_fstab):
    """
    Checks each disk for the presence of root folders like 'mergerfs_Root_*'.
    Returns a dictionary with disk paths as keys and lists of media folders under each root folder, as values.
    The dictionary structure of those_media_disks_having_a_root_folder is:
       Key: Disk path (e.g., /mnt/sda1)
          Value: Itself a Dictionary with:
       Key: The root folder (e.g., mergerfs_Root_X)
          Value: A list of top-level media folders under that root folder.
    If multiple root folders are found on a single disk, it raises an error with details.
    """
    those_media_disks_having_a_root_folder = {}
    for disk in disks_in_order_from_fstab:
        try:
            disk_path = Path(disk)
            if disk_path.is_dir():
                potential_root_folders = [d.name for d in disk_path.iterdir() if d.is_dir()]
                root_folders = [f for f in potential_root_folders if f.startswith('mergerfs_Root_')]

                # Check for multiple root folders
                if len(root_folders) > 1:
                    error_message = (f"Error: Disk {disk} has multiple root folders: {root_folders}. "
                                     "Each disk should only have one root folder like 'mergerfs_Root_*'.")
                    logging.error(error_message)
                    sys.exit(1)  # Exit with a status code indicating an error
                elif len(root_folders) == 1:
                    root_folder = root_folders[0]
                    root_folder_path = disk_path / root_folder
                    top_level_media_folders = [d.name for d in root_folder_path.iterdir() if d.is_dir()]
                    # if a disk with a known root folder has media folders, save them
                    if top_level_media_folders:
                        those_media_disks_having_a_root_folder[disk] = {root_folder: top_level_media_folders}
                        debug_print(f"Disk {disk} has root folder '{root_folder}' with top level media folders: {top_level_media_folders}")
        except Exception as e:
            logging.error(f"Error accessing {disk}: {e}")
            sys.exit(1)  # Exit with a status code indicating an error


    return those_media_disks_having_a_root_folder

def get_full_set_of_top_level_media_folders(media_disks_having_a_root_folder):
    """
    Aggregates all unique top level media folder names across all detected disks.
    Returns a set of media folder names.
    The dictionary structure of media_disks_having_a_root_folder is:
       Key: Disk path (e.g., /mnt/sda1)
          Value: Itself a Dictionary with:
       Key: The root folder (e.g., mergerfs_Root_X)
          Value: A list of top-level media folders under that root folder.
    """
    set_of_top_level_media_folders = set()
    for top_level_media_folders in media_disks_having_a_root_folder.values():
        for top_level_media_folder in top_level_media_folders.values():
            set_of_top_level_media_folders.update(top_level_media_folder)
    debug_print(f"Full set of top level media folders across all disks: {set_of_top_level_media_folders}")
    return set_of_top_level_media_folders

def find_ffd_for_media(media_disks_having_a_root_folder, full_set_of_top_level_media_folders, disks_in_order_from_fstab):
    """
    Determines the first found disk (ffd) for each top level media folder in the full set.
    Returns a dictionary mapping each media folder to its ffd.
    The ffd is chosen based on the order of disks as listed in fstab (leftmost first).
    The dictionary structure of media_disks_having_a_root_folder is:
       Key: Disk path (e.g., /mnt/sda1)
          Value: Itself a Dictionary with:
       Key: The root folder (e.g., mergerfs_Root_X)
          Value: A list of top-level media folders under that root folder.
    """
    the_ffd_map = {}
    for folder in full_set_of_top_level_media_folders:
        for disk in disks_in_order_from_fstab:
            if disk in media_disks_having_a_root_folder:
                root_folders = media_disks_having_a_root_folder[disk]
                for root_folder, top_level_folders in root_folders.items():
                    if folder in top_level_folders:
                        the_ffd_map[folder] = disk
                        debug_print(f"FFD for {folder}: {disk}")
                        break
                if folder in the_ffd_map:
                    break
    return the_ffd_map

def sync_folders(ffd_for_each_top_level_media_folder, media_disks_having_a_root_folder):
    """
    Synchronizes each top-level media folder from its ffd to all other disks containing the same top-level media folder.
    Uses rsync to ensure efficient copying and updating of files.
    The rsync command
        rsync -av --delete --size-only {ffd_folder}/ {target_folder}/
    with options
        -av --delete --size-only will:
    - Copy files and directories from the source to the target if they are missing in the target.
    - Remove files from the target that are not present in the source.
    - Update files in the target if their size differs from the corresponding files in the source, ignoring timestamps.
    The dictionary structure of media_disks_having_a_root_folder is:
       Key: Disk path (e.g., /mnt/sda1)
          Value: Itself a Dictionary with:
       Key: The root folder (e.g., mergerfs_Root_X)
          Value: A list of top-level media folders under that root folder.
    """
    # Loop throough each known top level media folder and its ffd
    # These will be used as the source in an rsync command
    for media_folder, ffd in ffd_for_each_top_level_media_folder.items():
        ffd_folder = None
        #
        # For A. and B. below:
        # The dictionary structure of media_disks_having_a_root_folder is:
        # Key: Disk path (e.g., /mnt/sda1)
        #    Value: Itself a Dictionary with:
        # Key: The root folder (e.g., mergerfs_Root_X)
        #    Value: A list of top-level media folders under that root folder.
        # Both the construction and usage of media_disks_having_a_root_folder
        # align with its structure, and the logic in sync_folders is consistent with this interpretation.
        # Any confusion arising may have arisen from different parts of the data structure
        # being accessed in different contexts, but they are consistent with the initial construction.
        #
        # A. Iterate through the root_folder and top_level_folders in the
        # dictionary stored at media_disks_having_a_root_folder[ffd].
        # It assumes that the value for each disk key is a dictionary with root folders as keys
        # and lists of media folders as values, which matches the construction in detect_media_disks_having_a_root_folder.
        for root_folder, top_level_folders in media_disks_having_a_root_folder[ffd].items():
            if media_folder in top_level_folders:
                # Set the path for the source folder on the FFD
                ffd_folder = Path(ffd) / root_folder / media_folder
                break
        if ffd_folder is None:
            logging.error(f"Error: FFD folder for {media_folder} not found on disk {ffd}.")
            sys.exit(1)  # Exit with a status code indicating an error
        # B. Use media_disks_having_a_root_folder by iterating over disks and
        # their associated root folders and top-level media folders.
        for disk, root_folders in media_disks_having_a_root_folder.items():
            if disk == ffd:
                continue    # skip the rest of the code for this iteration of this for
            for root_folder, top_level_folders in root_folders.items():
                if media_folder in top_level_folders:
                    # Set the path for the target folder on the target disk
                    target_folder = Path(disk) / root_folder / media_folder
                    if not target_folder.exists():
                        logging.error(f"Error: Target folder {target_folder} does not exist to rsync into.")
                        sys.exit(1)  # Exit with a status code indicating an error

                    # Ensure the parent directory exists for the target file on the target disk
                    if not target_folder.exists():
                        target_folder.mkdir(parents=True, exist_ok=True)

                    # Rsync command to synchronize the FFD folder to the target folder
                    sync_command = f"rsync -av --delete --size-only {ffd_folder}/ {target_folder}/"
                    try:
                        debug_print(f"Syncing {media_folder} from {ffd_folder} to {target_folder} : ")
                        debug_print(f"{sync_command}")
                        subprocess.run(sync_command, shell=True, check=True)
                    except subprocess.CalledProcessError as e:
                        logging.error(f"Error syncing {media_folder} from {ffd_folder} to {target_folder} using '{sync_command}': {e} ... continuing")
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
    disks_in_order_from_fstab = get_disks_in_order_from_fstab()
    if not disks_in_order_from_fstab:
        logging.error("No disks found in fstab or mergerfs entry not detected.")
        sys.exit(1)  # Exit with a status code indicating an error

    media_disks_having_a_root_folder = detect_media_disks_having_a_root_folder(disks_in_order_from_fstab)
    if not media_disks_having_a_root_folder:
        logging.error("No media disks detected with mergerfs_Root_* folders.")
        sys.exit(1)  # Exit with a status code indicating an error

    full_set_of_top_level_media_folders = get_full_set_of_top_level_media_folders(media_disks_having_a_root_folder)
    map_of_ffd_for_each_top_level_media_folder = find_ffd_for_media(media_disks_having_a_root_folder, full_set_of_top_level_media_folders, disks_in_order_from_fstab)
    sync_folders(map_of_ffd_for_each_top_level_media_folder, media_disks_having_a_root_folder)

if __name__ == "__main__":
    main()
