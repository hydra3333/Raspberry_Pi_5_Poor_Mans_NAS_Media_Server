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

def log_and_print(message, data=None):
    """
    Logs and prints a message with optional data.
    """
    logging.info(message)
    print(message)
    if data is not None:
        logging.info(pprint.pformat(data))
        objPrettyPrint.pprint(data)

def get_free_disk_space(path):
    """
    Get the free disk space for the given path.
    Returns the free space in bytes.
    """
    st = os.statvfs(path)
    free_space = st.f_bavail * st.f_frsize
    return free_space

def get_mergerfs_disks_in_LtoR_order_from_fstab():
    """
    Reads the /etc/fstab file to find the disks used in the mergerfs mount line.
    Handles globbing patterns to expand disk entries.
    
    Returns:
        list of dict: A list of dictionaries, each representing a detected mergerfs underlying disk in LtoR order from fstab.
        Each dictionary contains:
            - 'disk_mount_point' (str): The mount point path of the disk (e.g., '/mnt/sda1').
            - 'free_disk_space' (int): The free disk space available on the disk in bytes.
    Example:
        [
            {'disk_mount_point': '/mnt/sda1', 'free_disk_space': 1234567890},
            {'disk_mount_point': '/mnt/sda2', 'free_disk_space': 987654321},
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
                    if '*' in disk:
                        # Handle wildcard globbing pattern (eg /mnt/hdd*)
                        expanded_paths = glob.glob(disk)
                        the_mergerfs_disks_in_LtoR_order_from_fstab.extend(
                            [{'disk_mount_point': p, 'free_disk_space': get_free_disk_space(p)} for p in expanded_paths]
                        )
                    elif '{' in disk and '}' in disk:
                        # Handle curly brace globbing pattern (eg /mnt/{hdd1,hdd2})
                        pattern = re.sub(r'\{(.*?)\}', r'(\1)', disk)
                        expanded_paths = glob.glob(pattern)
                        the_mergerfs_disks_in_LtoR_order_from_fstab.extend(
                            [{'disk_mount_point': p, 'free_disk_space': get_free_disk_space(p)} for p in expanded_paths]
                        )
                    else:
                        # Handle plain (eg /mnt/hdd1 underlying file system mount point
                        free_disk_space = get_free_disk_space(disk)
                        the_mergerfs_disks_in_LtoR_order_from_fstab.append({'disk_mount_point': disk, 'free_disk_space': free_disk_space})
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
    
    Args:
        mergerfs_disks_in_LtoR_order_from_fstab (list of dict): A list of dictionaries representing detected mergerfs underlying disks.
            Each dictionary contains:
                - 'disk_mount_point' (str): The mount point path of the disk (e.g., '/mnt/sda1').
                - 'free_disk_space' (int): The free disk space available on the disk in bytes.
    
    Returns:
        dict: A dictionary containing information about disks with root folders and their top-level media folders.
        Key: 'disk_mount_point' (str): The mount point path of the disk (e.g., '/mnt/sda1').
        Value: dict with the following keys:
            - 'root_folder_path' (Path): The path to the root folder (e.g., Path('/mnt/sda1/mergerfs_Root_1')).
            - 'top_level_media_folders' (list of dict): A list of dictionaries, each representing a top-level media folder.
                Each dictionary contains:
                    - 'top_level_media_folder_name' (str): The name of the media folder (e.g., 'Movies').
                    - 'top_level_media_folder_path' (Path): The path to the media folder (e.g., Path('/mnt/sda1/mergerfs_Root_1/Movies')).
                    - 'ffd' (str): Initially an empty string, will be populated later with the first found disk (FFD).
                    - 'number_of_files' (int): The number of files in the media folder.
                    - 'disk_space_used' (int): The disk space used by the media folder in bytes.
    Example:
        {
            '/mnt/sda1': {
                'root_folder_path': Path('/mnt/sda1/mergerfs_Root_1'),
                'top_level_media_folders': [
                    {
                        'top_level_media_folder_name': 'Movies',
                        'top_level_media_folder_path': Path('/mnt/sda1/mergerfs_Root_1/Movies'),
                        'ffd': '',
                        'number_of_files': 1500,
                        'disk_space_used': 12000000000
                    },
                    ...
                ]
            },
            ...
        }
    """
    those_mergerfs_disks_having_a_root_folder = {}
    for disk_info in mergerfs_disks_in_LtoR_order_from_fstab:
        disk_mount_point = disk_info['disk_mount_point']
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
                    found_top_level_media_folders_list = []
                    for top_level_media_folder in found_root_folder_path.iterdir():
                        if top_level_media_folder.is_dir():
                            number_of_files = sum([len(files) for r, d, files in os.walk(top_level_media_folder)])
                            disk_space_used = sum([os.path.getsize(os.path.join(r, file)) for r, d, files in os.walk(top_level_media_folder) for file in files])
                            found_top_level_media_folders_list.append({
                                'top_level_media_folder_name': top_level_media_folder.name,
                                'top_level_media_folder_path': top_level_media_folder,
                                'ffd': '',
                                'number_of_files': number_of_files,
                                'disk_space_used': disk_space_used
                            })

                    # if a disk_mount_point with a known root folder has top level media folders, then save them
                    if found_top_level_media_folders_list:
                        those_mergerfs_disks_having_a_root_folder[disk_mount_point] = {
                            'root_folder_path': found_root_folder_path,
                            'top_level_media_folders': found_top_level_media_folders_list
                        }
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

def get_unique_top_level_media_folders(mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder):
    """
    Consolidates and derives unique top-level media folder names from the detected disks.
    Also determines the first found disk (FFD) for each unique media folder and additional information.
    
    Args:
        mergerfs_disks_having_a_root_folder (dict): A dictionary containing information about disks with root folders and their top-level media folders.
            Key: 'disk_mount_point' (str): The mount point path of the disk (e.g., '/mnt/sda1').
            Value: dict with the following keys:
                - 'root_folder_path' (Path): The path to the root folder.
                - 'top_level_media_folders' (list of dict): A list of dictionaries, each representing a top-level media folder.
                    - 'top_level_media_folder_name' (str): The name of the media folder.
                    - 'top_level_media_folder_path' (Path): The path to the media folder.
                    - 'ffd' (str): Initially an empty string, will be populated later with the FFD.
                    - 'number_of_files' (int): The number of files in the media folder.
                    - 'disk_space_used' (int): The disk space used by the media folder in bytes.
        mergerfs_disks_in_LtoR_order_from_fstab (list of dict): A list of dictionaries representing detected mergerfs underlying disks.
            Each dictionary contains:
                - 'disk_mount_point' (str): The mount point path of the disk (e.g., '/mnt/sda1').
                - 'free_disk_space' (int): The free disk space available on the disk in bytes.
    
    Returns:
        dict: A dictionary containing unique top-level media folders and related derived information.
        Key: 'top_level_media_folder_name' (str): The unique name of the top-level media folder (e.g., 'Movies').
        Value: dict with the following keys:
            - 'ffd' (str): The first found disk for this media folder.
            - 'disk_info' (list of dict): A list of dictionaries with information about each disk containing this media folder.
                Each dictionary contains:
                    - 'disk_mount_point' (str): The mount point path of the disk.
                    - 'is_ffd' (bool): Whether this disk is the FFD for the media folder.
                    - 'root_folder_path' (Path): The path to the root folder.
                    - 'number_of_files' (int): The number of files in this media folder on this disk.
                    - 'disk_space_used' (int): The disk space used by this media folder on this disk.
                    - 'total_free_disk_space' (int): The total free disk space on this disk.
    Example:
        {
            'Movies': {
                'ffd': '/mnt/sda1',
                'disk_info': [
                    {
                        'disk_mount_point': '/mnt/sda1',
                        'is_ffd': True,
                        'root_folder_path': Path('/mnt/sda1/mergerfs_Root_1'),
                        'number_of_files': 1500,
                        'disk_space_used': 12000000000,
                        'total_free_disk_space': 50000000000
                    },
                    {
                        'disk_mount_point': '/mnt/sda2',
                        'is_ffd': False,
                        'root_folder_path': Path('/mnt/sda2/mergerfs_Root_2'),
                        'number_of_files': 1500,
                        'disk_space_used': 12000000000,
                        'total_free_disk_space': 60000000000
                    },
                    ...
                ]
            },
            ...
        }
    """
    unique_top_level_media_folders = {}

    # Step 1: Gather all unique top-level media folders
    for disk_info in mergerfs_disks_having_a_root_folder.values():
        for media_folder_info in disk_info['top_level_media_folders']:
            top_level_media_folder_name = media_folder_info['top_level_media_folder_name']
            if top_level_media_folder_name not in unique_top_level_media_folders:
                unique_top_level_media_folders[top_level_media_folder_name] = {
                    'top_level_media_folder_name': top_level_media_folder_name,
                    'ffd': '',
                    'disk_info': []
                }

    # Step 2: Determine the ffd (first found disk) for each top-level media folder
    for top_level_media_folder_name, folder_info in unique_top_level_media_folders.items():
        for disk_info in mergerfs_disks_in_LtoR_order_from_fstab:
            disk_mount_point = disk_info['disk_mount_point']
            if disk_mount_point in mergerfs_disks_having_a_root_folder:
                disk_root_folder_info = mergerfs_disks_having_a_root_folder[disk_mount_point]
                for media_folder_info in disk_root_folder_info['top_level_media_folders']:
                    if media_folder_info['top_level_media_folder_name'] == top_level_media_folder_name:
                        if folder_info['ffd'] == '':
                            folder_info['ffd'] = disk_mount_point
                        is_ffd = (disk_mount_point == folder_info['ffd'])
                        folder_info['disk_info'].append({
                            'disk_mount_point': disk_mount_point,
                            'is_ffd': is_ffd,
                            'root_folder_path': str(disk_root_folder_info['root_folder_path']),
                            'number_of_files': media_folder_info['number_of_files'],
                            'disk_space_used': media_folder_info['disk_space_used'],
                            'total_free_disk_space': disk_info['free_disk_space']
                        })

    # Step 3: Update ffd for each folder in mergerfs_disks_having_a_root_folder
    for disk_info in mergerfs_disks_having_a_root_folder.values():
        for media_folder_info in disk_info['top_level_media_folders']:
            media_folder_name = media_folder_info['top_level_media_folder_name']
            media_folder_info['ffd'] = unique_top_level_media_folders[media_folder_name]['ffd']

    return unique_top_level_media_folders, mergerfs_disks_having_a_root_folder

---

def generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder):
    """
    Generates a crosstab report summarizing the state of top-level media folders across different disks.

    Parameters:
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

    The function outputs a formatted crosstab report showing:
    - Top-level media folder names as row headers.
    - Disk mount points as column headers.
    - Cells contain the number of files, disk space used, and whether the disk is the FFD.
    - A row for totals, showing the aggregate number of files and disk space used/free per disk.
    """

    # Prepare the header for the crosstab table
    headers = ["Top Level Media Folder"]
    for disk in mergerfs_disks_in_LtoR_order_from_fstab:
        disk_mount_point = disk['disk_mount_point']
        disk_info = mergerfs_disks_having_a_root_folder.get(disk_mount_point, {})
        root_folder_path = disk_info.get('root_folder_path', 'Unknown')
        headers.append(f"{disk_mount_point} ({root_folder_path})")
    headers.append("Total")

    # Log and print the header
    log_and_print("Crosstab Report for Top Level Media Folders:")
    log_and_print(" | ".join(headers))
    
    # Prepare the rows for each top level media folder
    for media_folder, data in unique_top_level_media_folders.items():
        row = [media_folder]
        total_files = 0
        total_disk_space = 0
        for disk in mergerfs_disks_in_LtoR_order_from_fstab:
            disk_mount_point = disk['disk_mount_point']
            media_info = next((info for info in data['disk_info'] if info['disk_mount_point'] == disk_mount_point), None)
            if media_info:
                is_ffd = media_info['is_ffd']
                ffd_indicator = "(FFD)" if is_ffd else ""
                files = media_info['number_of_files']
                space_used = media_info['disk_space_used']
                total_files += files
                total_disk_space += space_used
                row.append(f"{files} files, {space_used} bytes {ffd_indicator}")
            else:
                row.append("N/A")
        row.append(f"{total_files} files, {total_disk_space} bytes")
        log_and_print(" | ".join(row))

    # Totals row
    total_row = ["Total"]
    for disk in mergerfs_disks_in_LtoR_order_from_fstab:
        disk_mount_point = disk['disk_mount_point']
        free_space = disk['free_disk_space']
        total_row.append(f"Free: {free_space} bytes")
    total_row.append("")  # Placeholder for the final column
    log_and_print(" | ".join(total_row))
    log_and_print("End of Crosstab Report.")

def main():
    """
    Main function to coordinate the gathering of disk and media folder information and print the results.
    """
    # Step 1: Get mergerfs disks in LtoR order from fstab
    mergerfs_disks_in_LtoR_order_from_fstab = get_mergerfs_disks_in_LtoR_order_from_fstab()
    log_and_print("MergerFS Disks in Left-to-Right Order from /etc/fstab:", mergerfs_disks_in_LtoR_order_from_fstab)
    
    # Step 2: Detect mergerfs disks having a root folder
    mergerfs_disks_having_a_root_folder = detect_mergerfs_disks_having_a_root_folder(mergerfs_disks_in_LtoR_order_from_fstab)
    log_and_print("MergerFS Disks Having a Root Folder:", mergerfs_disks_having_a_root_folder)
    
    # Step 3: Get unique top level media folders and update ffd information
    unique_top_level_media_folders, mergerfs_disks_having_a_root_folder = get_unique_top_level_media_folders(
        mergerfs_disks_in_LtoR_order_from_fstab,
        mergerfs_disks_having_a_root_folder
    )
    log_and_print("Unique Top-Level Media Folders:", unique_top_level_media_folders)
    
    # Step 4: Generate and log the crosstab report
    generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder)

if __name__ == "__main__":
    main()
