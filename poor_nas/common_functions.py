import os
import sys
import subprocess
from pathlib import Path
import glob
import re
import logging
import pprint

# Configuration
DEBUG_IS_ON = False  # Set to True to enable debug printing
objPrettyPrint = None
#

def init_PrettyPrinter(TERMINAL_WIDTH):
    # Set up prettyprint for formatting
    global objPrettyPrint
    objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)  # facilitates formatting
    return

def init_logging(log_filename):
    # Set up logging
    logging.basicConfig(filename=log_filename,
                        level=logging.DEBUG if DEBUG_IS_ON else logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s')

def debug_log_and_print(message, data=None):
    """
    Logs and prints a message with optional data, if DEBUG is on.
    """
    if DEBUG_IS_ON:
        logging.debug(message)
        print(f"DEBUG: {message}", flush=True)
        if data is not None:
            logging.debug(objPrettyPrint.pformat(data))
            print(f"{objPrettyPrint.pformat(data)}", flush=True)

def error_log_and_print(message, data=None):
    """
    Logs and prints a message with optional data, if DEBUG is on.
    """
    logging.error(message)
    print(f"ERROR: {message}", flush=True)
    if data is not None:
        logging.error(objPrettyPrint.pformat(data))
        print(f"{objPrettyPrint.pformat(data)}", flush=True)

def log_and_print(message, data=None):
    """
    Logs and prints a message with optional data.
    """
    logging.info(message)
    print(message, flush=True)
    if data is not None:
        logging.info(objPrettyPrint.pformat(data))
        print(f"{objPrettyPrint.pformat(data)}", flush=True)

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
        number_of_mergerfs_lines = 0
        for line in fstab_lines:
            # Example line (without the #) we are looking for
            # ... when delete, only delete the first found, backup copies of a file are unaffected
            # ...     /srv/usb3disk* /mergerfs_root mergerfs category.action=ff,category.create=ff,category.delete=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,branches-mount-timeout=300,fsname=mergerfs 0 0
            # ... when delete, only delete it and all backup copies of a file
            # ...     /srv/usb3disk* /mergerfs_root mergerfs category.action=ff,category.create=ff,category.delete=all,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true,branches-mount-timeout=300,fsname=mergerfs 0 0
            # Skip comments and empty lines
            debug_log_and_print(f"A line was read from /etc/fstab:", data=line)
            if line.startswith('#') or not line.strip():
                continue
            fields = line.split()
            if any('mergerfs' in field.lower() for field in fields):  # Identify mergerfs entries
                number_of_mergerfs_lines = number_of_mergerfs_lines + 1
                fstab_mergerfs_line = line.strip()
                debug_log_and_print(f"MergerFS line found: {line.strip()}")
                # fields[0] should contain one or more and/or globbed, underlying file system mount points used by mergerfs
                mount_points = fields[0]
                # Split apart a possible list of underlying file system mount points separated by ':'
                split_disks = mount_points.split(':')
                # Process each underlying file system mount point separately, catering for globbing entries
                for disk in split_disks:
                    if '*' in disk:
                        # Handle wildcard globbing pattern (eg /mnt/hdd*)
                        expanded_paths = sorted(glob.glob(disk))
                        debug_log_and_print(f"MergerFS line Handling wildcard globbing pattern ... expanded_paths:", data=expanded_paths)
                        the_mergerfs_disks_in_LtoR_order_from_fstab.extend(
                            [{'disk_mount_point': p, 'free_disk_space': get_free_disk_space(p)} for p in expanded_paths]
                        )
                    elif '{' in disk and '}' in disk:
                        # Handle curly brace globbing pattern (eg /mnt/{hdd1,hdd2})
                        pattern = re.sub(r'\{(.*?)\}', r'(\1)', disk)
                        expanded_paths = sorted(glob.glob(pattern))
                        debug_log_and_print(f"MergerFS line Handling wcurly brace globbing pattern... expanded_paths:", data=expanded_paths)
                        the_mergerfs_disks_in_LtoR_order_from_fstab.extend(
                            [{'disk_mount_point': p, 'free_disk_space': get_free_disk_space(p)} for p in expanded_paths]
                        )
                    else:
                        # Handle plain (eg /mnt/hdd1 underlying file system mount point
                        free_disk_space = get_free_disk_space(disk)
                        the_mergerfs_disks_in_LtoR_order_from_fstab.append({'disk_mount_point': disk, 'free_disk_space': free_disk_space})
    except Exception as e:
        error_log_and_print(f"Error reading /etc/fstab: {e}")
        sys.exit(1)  # Exit with a status code indicating an error

    # If more than 1 mergerfs line is found, it's a conflict
    if number_of_mergerfs_lines > 1:
        error_log_and_print("Multiple mergerfs lines found in 'fstab'. Aborting.")
        sys.exit(1)  # Exit with a status code indicating an error

    if (number_of_mergerfs_lines < 1) or (len(the_mergerfs_disks_in_LtoR_order_from_fstab) < 1) :
        error_log_and_print(f"ZERO detected 'mergerfs' underlying disks in LtoR order from 'fstab': {the_mergerfs_disks_in_LtoR_order_from_fstab}")
        sys.exit(1)  # Exit with a status code indicating an error

    debug_log_and_print(f"Detected 'mergerfs' underlying disks in LtoR order from fstab '{fstab_mergerfs_line}': {the_mergerfs_disks_in_LtoR_order_from_fstab}")
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
                    error_log_and_print(error_message)
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
                        debug_log_and_print(f"disk_mount_point {disk_mount_point} has root folder '{found_root_folder}' with top level media folders: {found_top_level_media_folders_list}")
                else:
                    pass
        except Exception as e:
            error_log_and_print(f"Error accessing {disk_mount_point}: {e}")
            sys.exit(1)  # Exit with a status code indicating an error

    if len(those_mergerfs_disks_having_a_root_folder) < 1:
        error_log_and_print(f"ZERO Detected 'mergerfs' underlying disks having a root folder AND top_level_media_folders: {mergerfs_disks_in_LtoR_order_from_fstab}")
        sys.exit(1)  # Exit with a status code indicating an error

    debug_log_and_print(f"Detected 'mergerfs' underlying disks having a root folder AND top level media folders: {those_mergerfs_disks_having_a_root_folder}")
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
