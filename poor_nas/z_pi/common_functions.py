### Changed the mergerfs mount to mount the disk AND the top level folder
### eg from     /srv/usb3disk1    to    /srv/usb3disk1/mediaroot
### So we changed all this code to suit that. Hopefuilly it works.

# REMEMBER
# REMEMBER: In Python, when you assign or pass a **mutable object (like a dictionary)** to another variable or function,
# REMEMBER:            it doesn't create a copy but rather a **reference** to the same object.
# REMEMBER:            BEING BY REFERENCE, updates to that variable makes updates TO THE ORIGINAL OBJECT.
# REMEMBER

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

# Configuration
DEBUG_IS_ON = False  # Set to True to enable debug printing
objPrettyPrint = None

# Constants
MEDIAROOT_FOLDER_NAME = r"mediaroot"

def init_PrettyPrinter(TERMINAL_WIDTH):
    # Set up prettyprint for formatting
    global objPrettyPrint
    objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)  # facilitates formatting
    return

def init_logging(log_filename):
    # Set up logging, enable for DEBUG upward to ensure capturing everything
    logging.basicConfig(filename=log_filename,
                        level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s: %(message)s')

def debug_pause():
    if DEBUG_IS_ON:
        message = f"DEBUG: Press Enter to continue..."
        logging.debug(message)
        print(message, flush=True)
        input()

def debug_log_and_print(message, data=None):
    """
    Logs and prints a message with optional data, if DEBUG is on.
    """
    if DEBUG_IS_ON:
        logging.debug(message)
        print(f"DEBUG: {message}", flush=True)
        if data is not None:
            logging.debug(f"\n" + objPrettyPrint.pformat(data))
            print(objPrettyPrint.pformat(data), flush=True)

def warning_log_and_print(message, data=None):
    """
    Logs and prints a message with optional data
    """
    logging.warning(message)
    print(f"WARNING: {message}", flush=True)
    if data is not None:
        logging.warning(f"\n" + objPrettyPrint.pformat(data))
        print(f"\n" + objPrettyPrint.pformat(data), flush=True)

def error_log_and_print(message, data=None):
    """
    Logs and prints a message with optional data
    """
    logging.error(message)
    print(f"ERROR: {message}", flush=True)
    if data is not None:
        logging.error(f"\n" + objPrettyPrint.pformat(data))
        print(f"\n" + objPrettyPrint.pformat(data), flush=True)

def log_and_print(message, data=None):
    """
    Logs and prints a message with optional data.
    """
    logging.info(message)
    print(f"{message}", flush=True)
    if data is not None:
        logging.info(f"\n" + objPrettyPrint.pformat(data))
        print(objPrettyPrint.pformat(data), flush=True)

def find_mount_point_from_path(path):
    """
    Returns the status, error number, error string, and the mount point from a path.
    """
    status = True
    error_number = 0
    error_string = ""
    resolved_mount_point_str = ""
    try:
        resolved_path = Path(path).resolve(strict=True)
        while not resolved_path.is_mount():
            resolved_path = resolved_path.parent
        resolved_mount_point_str = str(resolved_path)
    except OSError as e:
        error_number = e.errno
        error_string = e.strerror
        status = False
    except Exception as e:
        error_number = getattr(e, 'errno', None)
        error_string = str(e)
        status = False
    return status, error_number, error_string, resolved_mount_point_str

def get_top_level_folder_from_path(path):
    """
    Returns the status, error number, error string, and the topmost folder underneath the mount point from a path.
    """
    # REMEMBER
    # REMEMBER: In Python, when you assign or pass a **mutable object (like a dictionary)** to another variable or function,
    # REMEMBER:            it doesn't create a copy but rather a **reference** to the same object.
    # REMEMBER:            BEING BY REFERENCE, updates to that variable makes updates TO THE ORIGINAL OBJECT.
    # REMEMBER
    status = True
    error_number = 0
    error_string = ""
    resolved_top_level_folder_str = ""
    try:
        resolved_path = Path(path).resolve(strict=True)
    except OSError as e:
        error_number = e.errno
        error_string = e.strerror
        status = False
        return status, error_number, error_string, resolved_top_level_folder_str
    except Exception as e:
        error_number = getattr(e, 'errno', None)
        error_string = str(e)
        status = False
        return status, error_number, error_string, resolved_top_level_folder_str
    status, error_number, error_string, resolved_mount_point = find_mount_point_from_path(resolved_path)
    if not status or not resolved_mount_point:
        return status, error_number, error_string, resolved_top_level_folder_str
    try:
        resolved_path_under_mount = resolved_path.relative_to(resolved_mount_point)
        resolved_top_level_folder_str = resolved_path_under_mount.parts[0] if resolved_path_under_mount.parts else ""
    except OSError as e:
        error_number = e.errno
        error_string = e.strerror
        status = False
    except Exception as e:
        error_number = getattr(e, 'errno', None)
        error_string = str(e)
        status = False
    return status, error_number, error_string, resolved_top_level_folder_str

def extract_five_path_components(path):
    """
    Returns a status, error number, error string, and 5 path components:
    - status: boolean indicating if the whole process succeeded
    - error_number: the error number if an exception occurred, otherwise 0
    - error_string: the error string if an exception occurred, otherwise an empty string
    - the resolved path
    - the resolved mount point
    - the resolved path underneath the mount point
    - the resolved topmost folder underneath the mount point
    - the resolved remaining path underneath the topmost folder
    from a given path.
    Called:
        status, error_number, error_string, resolved_path, resolved_mount_point, resolved_path_under_mount, resolved_top_level_folder, resolved_path_under_top_level_folder = extract_five_path_components(path)
    """
    # REMEMBER
    # REMEMBER: In Python, when you assign or pass a **mutable object (like a dictionary)** to another variable or function,
    # REMEMBER:            it doesn't create a copy but rather a **reference** to the same object.
    # REMEMBER:            BEING BY REFERENCE, updates to that variable makes updates TO THE ORIGINAL OBJECT.
    # REMEMBER
    status = True
    error_number = 0
    error_string = ""
    resolved_path_str = ""
    resolved_mount_point_str = ""
    resolved_path_under_mount_str = ""
    resolved_top_level_folder_str = ""
    resolved_path_under_top_level_folder_str = ""

    if status:
        try:
            resolved_path = Path(path).resolve(strict=True)
            resolved_path_str = str(resolved_path)
        except OSError as e:
            error_number = e.errno
            error_string = e.strerror
            status = False
        except Exception as e:
            error_number = getattr(e, 'errno', None)
            error_string = str(e)
            status = False
    if status:
        try:
            resolved_mount_point = resolved_path
            while not resolved_mount_point.is_mount():
                resolved_mount_point = resolved_mount_point.parent
            resolved_mount_point_str = str(resolved_mount_point)
        except OSError as e:
            error_number = e.errno
            error_string = e.strerror
            status = False
        except Exception as e:
            error_number = getattr(e, 'errno', None)
            error_string = str(e)
            status = False
    if status:
        try:
            resolved_path_under_mount = resolved_path.relative_to(resolved_mount_point)
            resolved_path_under_mount_str = str(resolved_path_under_mount) if str(resolved_path_under_mount) != "." else ""
        except OSError as e:
            error_number = e.errno
            error_string = e.strerror
            status = False
        except Exception as e:
            error_number = getattr(e, 'errno', None)
            error_string = str(e)
            status = False
    if status:
        try:
            resolved_top_level_folder = resolved_path_under_mount.parts[0] if resolved_path_under_mount.parts else ""
            resolved_top_level_folder_str = str(resolved_top_level_folder)
        except OSError as e:
            error_number = e.errno
            error_string = e.strerror
            status = False
        except Exception as e:
            error_number = getattr(e, 'errno', None)
            error_string = str(e)
            status = False
    if status:
        try:
            resolved_path_under_top_level_folder = Path(*resolved_path_under_mount.parts[1:]) if len(resolved_path_under_mount.parts) > 1 else Path()
            resolved_path_under_top_level_folder_str = str(resolved_path_under_top_level_folder)
        except OSError as e:
            error_number = e.errno
            error_string = e.strerror
            status = False
        except Exception as e:
            error_number = getattr(e, 'errno', None)
            error_string = str(e)
            status = False
    return status, error_number, error_string, resolved_path_str, resolved_mount_point_str, resolved_path_under_mount_str, resolved_top_level_folder_str, resolved_path_under_top_level_folder_str

def get_free_disk_space(path):
    """
    Get the free disk space for the given path.
    Returns a tuple:
    - status: boolean indicating if the whole process succeeded
    - error_number: the error number if an exception occurred, otherwise 0
    - error_string: the error string if an exception occurred, otherwise an empty string
    - free_space: the free space in bytes, or 0 if an error occurred
    """
    # REMEMBER
    # REMEMBER: In Python, when you assign or pass a **mutable object (like a dictionary)** to another variable or function,
    # REMEMBER:            it doesn't create a copy but rather a **reference** to the same object.
    # REMEMBER:            BEING BY REFERENCE, updates to that variable makes updates TO THE ORIGINAL OBJECT.
    # REMEMBER
    status = True
    error_number = 0
    error_string = ""
    free_space = 0

    try:
        st = os.statvfs(path)
        free_space = st.f_bavail * st.f_frsize
    except OSError as e:
        error_number = e.errno
        error_string = e.strerror
        status = False
    except Exception as e:
        error_number = getattr(e, 'errno', None)
        error_string = str(e)
        status = False
    return status, error_number, error_string, free_space

def get_mergerfs_disks_in_LtoR_order_from_fstab():
    """
    Reads the /etc/fstab file to find the disks used in the mergerfs mount line.
    Handles globbing patterns to expand disk entries.
    
    Returns:
        list of dict: A list of dictionaries, each representing a detected mergerfs underlying disk in LtoR order from fstab.
        Each dictionary contains:
            - 'disk_mount_point' (str): The mount point path of the disk (e.g., '/srv/usb3disk1').
            - 'free_disk_space' (int): The free disk space available on the disk in bytes.
            - 'root_folder_path' (str): The path mergerfs uses as the "head" of its mount (e.g., '/srv/usb3disk1/mediaroot').
    Example:
        [
            {'disk_mount_point': '/srv/usb3disk1', 'free_disk_space': 1234567890, 'root_folder_path': '/srv/usb3disk1/mediaroot'},
            {'disk_mount_point': '/srv/usb3disk2', 'free_disk_space': 987654321}, 'root_folder_path': '/srv/usb3disk2/mediaroot'},
        ]
    Notes: this does not guarantee a detected underlying disk contains a root folder or any 'top level media folders' under it.
           Handle disks referenced but not mounted in /etc/fstab.
           If a top-level root folder specified in the mergerfs mount does not exist, the disk is skipped for this run.
           Skips unmounted disks for this run.
           Skips disks where MEDIAROOT_FOLDER_NAME is not a part of the string underneath the mount point, or does not exist ... i.e. disks without a valid root
    """
    # REMEMBER
    # REMEMBER: In Python, when you assign or pass a **mutable object (like a dictionary)** to another variable or function,
    # REMEMBER:            it doesn't create a copy but rather a **reference** to the same object.
    # REMEMBER:            BEING BY REFERENCE, updates to that variable makes updates TO THE ORIGINAL OBJECT.
    # REMEMBER
    #
    # ITEMS FROM THIS LIST WILL ALWAYS BE RETURNED IN THE ORDER THEY WERE ADDED.
    # THIS IS REQUIRED BEHAVIOUR FOR THIS CODE BASE TO WORK

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
            #         /srv/usb3disk*/mediaroot /srv/media mergerfs defaults,category.action=ff,category.create=ff,category.search=all,moveonenospc=true,dropcacheonclose=true,cache.readdir=true,cache.files=partial,lazy-umount-mountpoint=true 0 0
            debug_log_and_print(f"A line was read from /etc/fstab:\n", data=line)
            if line.startswith('#') or not line.strip():
                continue
            fields = line.split()
            if any('mergerfs' in field.lower() for field in fields):  # Identify mergerfs entries
                number_of_mergerfs_lines += 1
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
                        debug_log_and_print(f"MergerFS line Handling wildcard globbing pattern ... expanded_paths:\n", data=expanded_paths)
                        # Iterate over each path in the expanded paths
                        for ep in expanded_paths:
                            # if it is detected as valid (i.e. it is mounted and the rest of it is valid and exists) then find the free disk space and add it to the_mergerfs_disks_in_LtoR_order_from_fstab 
                            efpc_status, efpc_error_number, efpc_error_string, efpc_resolved_path, efpc_resolved_mount_point, efpc_resolved_path_under_mount, efpc_resolved_top_level_folder, efpc_resolved_path_under_top_level_folder = extract_five_path_components(ep)
                            if (not efpc_status) or (efpc_resolved_mount_point == "") or (not re.match(rf'^{re.escape(MEDIAROOT_FOLDER_NAME)}$', efpc_resolved_path_under_mount)):
                                continue # disk perhaps not mounted etc, skip to the end of this FOR iteration
                            # Get the free disk space
                            fds_status, fds_error_number, fds_error_string, fds_free_disk_space = get_free_disk_space(efpc_resolved_mount_point)
                            the_mergerfs_disks_in_LtoR_order_from_fstab.append({'disk_mount_point': efpc_resolved_mount_point, 'free_disk_space': fds_free_disk_space, 'root_folder_path': efpc_resolved_path})
                    elif '{' in disk and '}' in disk:
                        # Handle curly brace globbing pattern (eg /mnt/{hdd1,hdd2})
                        pattern = re.sub(r'\{(.*?)\}', r'(\1)', disk)
                        expanded_paths = sorted(glob.glob(pattern))
                        # Iterate over each path in the expanded paths
                        for ep in expanded_paths:
                            # if it is detected as valid (i.e. it is mounted and the rest of it is valid and exists) then find the free disk space and add it to the_mergerfs_disks_in_LtoR_order_from_fstab 
                            efpc_status, efpc_error_number, efpc_error_string, efpc_resolved_path, efpc_resolved_mount_point, efpc_resolved_path_under_mount, efpc_resolved_top_level_folder, efpc_resolved_path_under_top_level_folder = extract_five_path_components(ep)
                            if (not efpc_status) or (efpc_resolved_mount_point == "") or (not re.match(rf'^{re.escape(MEDIAROOT_FOLDER_NAME)}$', efpc_resolved_path_under_mount)):
                                continue # disk perhaps not mounted etc, skip to the end of this FOR iteration
                            # Get the free disk space
                            fds_status, fds_error_number, fds_error_string, fds_free_disk_space = get_free_disk_space(efpc_resolved_mount_point)
                            the_mergerfs_disks_in_LtoR_order_from_fstab.append({'disk_mount_point': efpc_resolved_mount_point, 'free_disk_space': fds_free_disk_space, 'root_folder_path': efpc_resolved_path})
                    else:
                        # Handle plain (eg /mnt/hdd1 underlying file system mount point
                        # Do not care if there is an error from get_free_disk_space ... the free disk space will be returned as zero which is OK
                        efpc_status, efpc_error_number, efpc_error_string, efpc_resolved_path, efpc_resolved_mount_point, efpc_resolved_path_under_mount, efpc_resolved_top_level_folder, efpc_resolved_path_under_top_level_folder = extract_five_path_components(disk)
                        if (not efpc_status) or (efpc_resolved_mount_point == "") or (not re.match(rf'^{re.escape(MEDIAROOT_FOLDER_NAME)}$', efpc_resolved_path_under_mount)):
                            continue # disk perhaps not mounted etc, skip to the end of this FOR iteration
                        fds_status, fds_error_number, fds_error_string, fds_free_disk_space = get_free_disk_space(efpc_resolved_mount_point)
                        the_mergerfs_disks_in_LtoR_order_from_fstab.append({'disk_mount_point': efpc_resolved_mount_point, 'free_disk_space': fds_free_disk_space, 'root_folder_path': efpc_resolved_path})
    except Exception as e:
        error_log_and_print(f"Error reading /etc/fstab: {e}")
        sys.exit(1)  # Exit with a status code indicating an error

    # If more than 1 mergerfs line is found, it's a conflict
    if number_of_mergerfs_lines > 1:
        error_log_and_print(f"Multiple mergerfs lines found in 'fstab'. Aborting.")
        sys.exit(1)  # Exit with a status code indicating an error

    if (number_of_mergerfs_lines < 1) or (len(the_mergerfs_disks_in_LtoR_order_from_fstab) < 1) :
        error_log_and_print(f"ZERO detections of 'mergerfs' underlying disks in LtoR order from 'fstab':\n", data=the_mergerfs_disks_in_LtoR_order_from_fstab)
        sys.exit(1)  # Exit with a status code indicating an error

    debug_log_and_print(f"Detected 'mergerfs' underlying disks in LtoR order from fstab '{fstab_mergerfs_line}'\n", data=the_mergerfs_disks_in_LtoR_order_from_fstab)
    return the_mergerfs_disks_in_LtoR_order_from_fstab

def detect_mergerfs_disks_having_a_root_folder_having_files(mergerfs_disks_in_LtoR_order_from_fstab):
    """
    Checks each underlying mergerfs disk_mount_point for the presence of a single root folder like 'mediaroot'.
    If multiple root folders are found on a single disk_mount_point, it raises an error with details.
    
    Args:
        mergerfs_disks_in_LtoR_order_from_fstab (list of dict): A list of dictionaries representing detected mergerfs underlying disks.
        Each dictionary contains:
            - 'disk_mount_point' (str): The mount point path of the disk (e.g., '/srv/usb3disk1').
            - 'free_disk_space' (int): The free disk space available on the disk in bytes.
            - 'root_folder_path' (str): The path mergerfs uses as the "head" of its mount (e.g., '/srv/usb3disk1/mediaroot').
            Example:
                [
                    {'disk_mount_point': '/srv/usb3disk1', 'free_disk_space': 1234567890, 'root_folder_path': '/srv/usb3disk1/mediaroot'},
                    {'disk_mount_point': '/srv/usb3disk2', 'free_disk_space': 987654321}, 'root_folder_path': '/srv/usb3disk2/mediaroot'},
                ]
    Returns:
        dict: A dictionary containing information about disks with root folders and their top-level media folders.
        Key: 'disk_mount_point' (str): The mount point path of the disk (e.g., '/srv/usb3disk1').
        Value: dict with the following keys:
            - 'disk_mount_point': (str): yes it is a key above as well as a key/value pair here
            - 'root_folder_path' (Path): The path to the root folder (e.g., Path('/srv/usb3disk1/mediaroot')).
            - 'top_level_media_folders' (list of dict): A list of dictionaries, each representing a top-level media folder.
                Each dictionary contains:
                    - 'top_level_media_folder_name' (str): The name of the media folder (e.g., 'Movies').
                    - 'top_level_media_folder_path' (Path): The path to the media folder (e.g., Path('/srv/usb3disk1/mediaroot/Movies')).
                    - 'ffd' (str): Initially an empty string, will be populated later with the first found disk (FFD).
                    - 'number_of_files' (int): The number of files in the media folder.
                    - 'disk_space_used' (int): The disk space used by the media folder in bytes.
    Example:
        {
            '/srv/usb3disk1': {
                'root_folder_path': Path('/srv/usb3disk1/mediaroot'),
                'top_level_media_folders': [
                    {
                        'top_level_media_folder_name': 'Movies',
                        'top_level_media_folder_path': Path('/srv/usb3disk1/mediaroot/Movies'),
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
    # REMEMBER
    # REMEMBER: In Python, when you assign or pass a **mutable object (like a dictionary)** to another variable or function,
    # REMEMBER:            it doesn't create a copy but rather a **reference** to the same object.
    # REMEMBER:            BEING BY REFERENCE, updates to that variable makes updates TO THE ORIGINAL OBJECT.
    # REMEMBER

    those_mergerfs_disks_having_a_root_folder_having_files = {}
    for disk_info in mergerfs_disks_in_LtoR_order_from_fstab:
        disk_mount_point = disk_info['disk_mount_point']    # 'disk_mount_point' in mergerfs_disks_in_LtoR_order_from_fstab are ONLY the mountpoint eg '/srv/usb3disk1'
        root_folder_path = disk_info['root_folder_path']    # 'root_folder_path' comes from the fstab mergerfs mount, is a valid resolved path to the root folder '/srv/usb3disk1/mediaroot'
        try:
            if Path(root_folder_path).is_dir():
                found_top_level_media_folders_list = []
                for top_level_media_folder in sorted(Path(root_folder_path).iterdir()):
                    if Path(top_level_media_folder).is_dir():
                        number_of_files = sum([len(files) for r, d, files in os.walk(top_level_media_folder)])
                        disk_space_used = sum([os.path.getsize(os.path.join(r, file)) for r, d, files in os.walk(top_level_media_folder) for file in files])
                        if number_of_files > 0:
                            found_top_level_media_folders_list.append({
                                'top_level_media_folder_name': top_level_media_folder.name,
                                'top_level_media_folder_path': top_level_media_folder,
                                'ffd': '',
                                'number_of_files': number_of_files,
                                'disk_space_used': disk_space_used
                            })
                # if a disk_mount_point with a known root folder has top level media folders having files, then save them
                if found_top_level_media_folders_list:
                    those_mergerfs_disks_having_a_root_folder_having_files[disk_mount_point] = {
                        'disk_mount_point': disk_mount_point,
                        'root_folder_path': root_folder_path,
                        'top_level_media_folders': found_top_level_media_folders_list
                    }
                    debug_log_and_print(f"disk_mount_point '{disk_mount_point}' has root folder '{root_folder_path}' with top level media folders having files:\n", data=found_top_level_media_folders_list)
            else:
                error_log_and_print(f"Error pre-detected disk/root does not exist: disk_mount_point: {disk_mount_point} root_folder_path: {root_folder_path}\n{e}")
                sys.exit(1)  # Exit with a status code indicating an error
        except Exception as e:
            error_number = getattr(e, 'errno', None)
            error_string = str(e)
            error_log_and_print(f"Error accessing disk_mount_point: '{disk_mount_point}' root_folder_path: '{root_folder_path}' Error: {e}")
            error_log_and_print(f"Error accessing disk_mount_point: Error: '{error_number}' '{error_string}'")
            sys.exit(1)  # Exit with a status code indicating an error
    #
    if len(those_mergerfs_disks_having_a_root_folder_having_files) < 1:
        error_log_and_print(f"ZERO Detected 'mergerfs' underlying disks having a root folder AND top_level_media_folders having files:\n", data=mergerfs_disks_in_LtoR_order_from_fstab)
        sys.exit(1)  # Exit with a status code indicating an error

    debug_log_and_print(f"Detected 'mergerfs' underlying disks having a root folder AND top level media folders having files:\n", data=those_mergerfs_disks_having_a_root_folder_having_files)
    return those_mergerfs_disks_having_a_root_folder_having_files

def get_unique_top_level_media_folders(mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder_having_files):
    """
    Consolidates and derives unique top-level media folder names from the detected disks.
    Also determines the first found disk (FFD) for each unique media folder and additional information.
    
    Args:
        mergerfs_disks_having_a_root_folder_having_files (dict): A dictionary containing information about disks with root folders and their top-level media folders.
            Key: 'disk_mount_point' (str): The mount point path of the disk (e.g., '/srv/usb3disk1').
            Value: dict with the following keys:
                - 'disk_mount_point': (str): yes it is a key above as well as a key/value pair here
                - 'root_folder_path' (Path): The path to the root folder.
                - 'top_level_media_folders' (list of dict): A list of dictionaries, each representing a top-level media folder.
                    - 'top_level_media_folder_name' (str): The name of the media folder.
                    - 'top_level_media_folder_path' (Path): The path to the media folder.
                    - 'ffd' (str): Initially an empty string, will be populated later with the FFD.
                    - 'number_of_files' (int): The number of files in the media folder.
                    - 'disk_space_used' (int): The disk space used by the media folder in bytes.
        mergerfs_disks_in_LtoR_order_from_fstab (list of dict): A list of dictionaries representing detected mergerfs underlying disks.
        Each dictionary contains:
            - 'disk_mount_point' (str): The mount point path of the disk (e.g., '/srv/usb3disk1').
            - 'free_disk_space' (int): The free disk space available on the disk in bytes.
            - 'root_folder_path' (str): The path mergerfs uses as the "head" of its mount (e.g., '/srv/usb3disk1/mediaroot').
            Example:
                [
                    {'disk_mount_point': '/srv/usb3disk1', 'free_disk_space': 1234567890, 'root_folder_path': '/srv/usb3disk1/mediaroot'},
                    {'disk_mount_point': '/srv/usb3disk2', 'free_disk_space': 987654321}, 'root_folder_path': '/srv/usb3disk2/mediaroot'},
                ]
    
    Returns:
        dict: A dictionary containing unique top-level media folders and related derived information.
        Key: 'top_level_media_folder_name' (str): The unique name of the top-level media folder (e.g., 'Movies').
        Value: dict with the following keys:
            - 'top_level_media_folder_name' (str): yes it is a key above as well as a key/value pair here
            - 'ffd' (str): The first found disk for this media folder.
            - 'ffd_root_folder_path': the root path of the ffd.
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
                'top_level_media_folder_name': 'Movies',
                'ffd': '/srv/usb3disk1',
                'ffd_root_folder_path': '/srv/usb3disk1/mediaroot',
                'disk_info': [
                    {
                        'disk_mount_point': '/srv/usb3disk1',
                        'is_ffd': True,
                        'root_folder_path': Path('/srv/usb3disk1/mediaroot'),
                        'number_of_files': 1500,
                        'disk_space_used': 12000000000,
                        'total_free_disk_space': 50000000000
                    },
                    {
                        'disk_mount_point': '/srv/usb3disk2',
                        'is_ffd': False,
                        'root_folder_path': Path('/srv/usb3disk2/mediaroot'),
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
    # REMEMBER
    # REMEMBER: In Python, when you assign or pass a **mutable object (like a dictionary)** to another variable or function,
    # REMEMBER:            it doesn't create a copy but rather a **reference** to the same object.
    # REMEMBER:            BEING BY REFERENCE, updates to that variable makes updates TO THE ORIGINAL OBJECT.
    # REMEMBER

    # AFTER SORTING USING ORDEREDDICT, ITEMS FROM THIS DICT WILL ALWAYS BE RETURNED IN THE ORDER THEY WERE ADDED.
    # THIS IS REQUIRED BEHAVIOUR FOR THIS CODE BASE TO WORK

    unique_top_level_media_folders = {}

    # Step 1: Gather all unique top-level media folder names (name only, not paths)
    #         Determining draft ffd depends on SORTED mergerfs_disks_having_a_root_folder_having_files
    for disk_info in mergerfs_disks_having_a_root_folder_having_files.values():
        for media_folder_info in disk_info['top_level_media_folders']:
            top_level_media_folder_name = media_folder_info['top_level_media_folder_name']
            if top_level_media_folder_name not in unique_top_level_media_folders:    # if it is the FIRST disk found having the folder name (and files)
                unique_top_level_media_folders[top_level_media_folder_name] = {
                    'top_level_media_folder_name': top_level_media_folder_name,
                    'ffd': disk_info['disk_mount_point'],                                       # draft ffd: disk_info['disk_mount_point']
                    'ffd_root_folder_path': disk_info['root_folder_path'],    # draft ffd_root_folder_path: disk_info['root_folder_path']
                    'disk_info': []                                                                            # blank since we are only seeing the FIRST unique top-level media folder name that we find
                }
    # To ensure dict items are always returned in order of key,
    # make it an ORDEREDDICT sorted by keys
    unique_top_level_media_folders = OrderedDict(sorted(unique_top_level_media_folders.items()))
    debug_log_and_print(f"get_unique_top_level_media_folders AFTER STEP 1 unique_top_level_media_folders:\n", data=unique_top_level_media_folders)

    # REMEMBER
    # REMEMBER: In Python, when you assign or pass a **mutable object (like a dictionary)** to another variable or function,
    # REMEMBER:            it doesn't create a copy but rather a **reference** to the same object.
    # REMEMBER:            BEING BY REFERENCE, updates to that variable makes updates TO THE ORIGINAL OBJECT.
    # REMEMBER
    # Step 2: Determine the ffd (first found disk) for each top-level media folder
    for top_level_media_folder_name in sorted(unique_top_level_media_folders): # ORDEREDDICT IS PRE-SORTED, DO THIS AS A LEFTOVER SORT FROM USING AN UNORDERED DICT
        folder_info = unique_top_level_media_folders[top_level_media_folder_name]
        for disk_info in mergerfs_disks_in_LtoR_order_from_fstab:
            disk_mount_point = disk_info['disk_mount_point']
            if disk_mount_point in mergerfs_disks_having_a_root_folder_having_files:
                disk_root_folder_info = mergerfs_disks_having_a_root_folder_having_files[disk_mount_point]
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
                        debug_log_and_print(f"get_unique_top_level_media_folders INSIDE STEP 2 APPENDING TO 'folder_info['disk_info']':\n", data=folder_info['disk_info'])
    debug_log_and_print(f"get_unique_top_level_media_folders AFTER STEP 2 unique_top_level_media_folders:\n", data=unique_top_level_media_folders)

    # REMEMBER
    # REMEMBER: In Python, when you assign or pass a **mutable object (like a dictionary)** to another variable or function,
    # REMEMBER:            it doesn't create a copy but rather a **reference** to the same object.
    # REMEMBER:            BEING BY REFERENCE, updates to that variable makes updates TO THE ORIGINAL OBJECT.
    # REMEMBER
    # Step 3: Update ffd for each folder in mergerfs_disks_having_a_root_folder_having_files
    for disk_info in mergerfs_disks_having_a_root_folder_having_files.values():
        for media_folder_info in disk_info['top_level_media_folders']:
            media_folder_name = media_folder_info['top_level_media_folder_name']
            media_folder_info['ffd'] = unique_top_level_media_folders[media_folder_name]['ffd']
    debug_log_and_print(f"get_unique_top_level_media_folders AFTER STEP 3 unique_top_level_media_folders:\n", data=unique_top_level_media_folders)
    return unique_top_level_media_folders, mergerfs_disks_having_a_root_folder_having_files

def get_list_of_media_folder_ffd_disks_to_sync(unique_top_level_media_folders):
    """
    Parses unique top-level media folder names from the detected disks to return a dict,
    of media folder names and from-disk to-disk which can be used for performing backups.
    The 'from-disk' is the 'ffd' (in mergerfs terms)
    and the 'to-disk' is a 'backup' disk to make copies of files onto.
      Args:
        dict: A dictionary containing unique top-level media folders and related derived information.
        Key: 'top_level_media_folder_name' (str): The unique name of the top-level media folder (e.g., 'Movies').
        Value: dict with the following keys:
            - 'top_level_media_folder_name' (str): yes it is a key above as well as a key/value pair here
            - 'ffd' (str): The first found disk for this media folder.
            - 'ffd_root_folder_path': the root path of the ffd.
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
                'top_level_media_folder_name': 'Movies',
                'ffd': '/srv/usb3disk1',
                'ffd_root_folder_path': '/srv/usb3disk1/mediaroot',
                'disk_info': [
                    {
                        'disk_mount_point': '/srv/usb3disk1',
                        'is_ffd': True,
                        'root_folder_path': Path('/srv/usb3disk1/mediaroot'),
                        'number_of_files': 1500,
                        'disk_space_used': 12000000000,
                        'total_free_disk_space': 50000000000
                    },
                    {
                        'disk_mount_point': '/srv/usb3disk2',
                        'is_ffd': False,
                        'root_folder_path': Path('/srv/usb3disk2/mediaroot'),
                        'number_of_files': 1500,
                        'disk_space_used': 12000000000,
                        'total_free_disk_space': 60000000000
                    },
                    ...
                ]
            },
            ...
        }
      Returns:
        a list: a list of candiates to rsync from to
            - a top_level_media_folder_name
            - a path to copy from : disk_mount_point / top_level_media_folder_name
            - a path to copy to   : disk_mount_point / top_level_media_folder_name
    """
    # REMEMBER
    # REMEMBER: In Python, when you assign or pass a **mutable object (like a dictionary)** to another variable or function,
    # REMEMBER:            it doesn't create a copy but rather a **reference** to the same object.
    # REMEMBER:            BEING BY REFERENCE, updates to that variable makes updates TO THE ORIGINAL OBJECT.
    # REMEMBER

    # Loop, cross-check entries, create a list of candidates to rsync from and to
    list_of_media_folder_ffd_disks_to_sync = []
    # Ensure the dictionary is sorted by key
    sorted_unique_top_level_media_folders = OrderedDict(sorted(unique_top_level_media_folders.items()))
    for top_level_media_folder_name, utlmf in sorted_unique_top_level_media_folders.items():
        debug_log_and_print(f"get_list_of_media_folder_ffd_disks_to_sync: Processing top_level_media_folder_name: '{top_level_media_folder_name}'")
        # Access the top-level media folder information
        top_level_media_folder_name = utlmf['top_level_media_folder_name']
        ffd = utlmf['ffd']
        ffd_root_folder_path = utlmf['ffd_root_folder_path']
        # Process each disk information entry
        for disk_info in utlmf['disk_info']:
            disk_mount_point = disk_info['disk_mount_point']
            is_ffd = disk_info['is_ffd']
            root_folder_path = disk_info['root_folder_path']
            number_of_files = disk_info['number_of_files']
            disk_space_used = disk_info['disk_space_used']
            total_free_disk_space = disk_info['total_free_disk_space']
            debug_log_and_print(f"get_list_of_media_folder_ffd_disks_to_sync: IN LOOP top_level_media_folder_name:'{top_level_media_folder_name}' ffd_root_folder_path: '{ffd_root_folder_path}' utlmf:", data=utlmf)
            if disk_info['is_ffd']:
                if disk_info['root_folder_path'] != utlmf['ffd_root_folder_path']:
                   error_log_and_print(f"ERROR: get_list_of_media_folder_ffd_disks_to_sync: '{utlmf['top_level_media_folder_name']}' disk '{disk_info['disk_mount_point']}' says is_ffd='{disk_info['is_ffd']}' yet  dict ffd mismatches '{utlmf['ffd_root_folder_path']}' != '{disk_info['root_folder_path']}'", data=sorted_unique_top_level_media_folders)
                   sys.exit(1)
            if utlmf['ffd_root_folder_path'] == disk_info['root_folder_path']:
                continue    # skip to end of this iteration if flooking at the ffd
                #error_log_and_print(f"ERROR: get_list_of_media_folder_ffd_disks_to_sync: '{utlmf['top_level_media_folder_name']}' from: ffd_root_folder_path '{utlmf['ffd_root_folder_path']}' must never equal : root_folder_path '{disk_info['root_folder_path']}'", data=sorted_unique_top_level_media_folders)
                #sys.exit(1)
            if disk_info['root_folder_path'] < utlmf['ffd_root_folder_path']:
                warning_log_and_print(f"WARNING: get_list_of_media_folder_ffd_disks_to_sync: '{utlmf['top_level_media_folder_name']}' disk '{disk_info['root_folder_path']}' is less than ffd '{utlmf['ffd_root_folder_path']}'", data=sorted_unique_top_level_media_folders)
            # Joining paths using pathlib "/"
            list_of_media_folder_ffd_disks_to_sync.append([ utlmf['top_level_media_folder_name'], Path(utlmf['ffd_root_folder_path']) / utlmf['top_level_media_folder_name'], Path(disk_info['root_folder_path']) / utlmf['top_level_media_folder_name'] ])
    debug_log_and_print(f"get_list_of_media_folder_ffd_disks_to_sync: list_of_media_folder_ffd_disks_to_sync:", data=list_of_media_folder_ffd_disks_to_sync)
    return list_of_media_folder_ffd_disks_to_sync                

def run_command_process(command):
    """
    Run the command and log stdout and stderr in real-time IN NON READ-BLOCKING MODE
    """
    try:
        debug_log_and_print(f"run_command_process: START command:\n{command}")
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as command_process:
            # Set stdout and stderr to non-blocking mode
            os.set_blocking(command_process.stdout.fileno(), False)  # sets stdout to non-blocking read mode.
            os.set_blocking(command_process.stderr.fileno(), False)  # sets stderr to non-blocking read mode.
            timeout = 1.0  # a timeout in seconds just in case nothing gets written to stdout, stderr
            stdout_buffer = ""
            stderr_buffer = ""
            while True:
                reads = [command_process.stdout.fileno(), command_process.stderr.fileno()]
                # Use a short timeout in select.select() to periodically continue and check if the process has completed
                # select.select(reads, [], []) ensures that we only attempt to read from the file descriptors when they are ready.
                # This prevents the loop from blocking or spinning unnecessarily.
                ret = select.select(reads, [], [], timeout)  # a timeout in seconds just in case nothing gets written to stdout, stderr
                for fd in ret[0]:
                    if fd == command_process.stdout.fileno():
                        try:
                            # This 'read' may read a chunk of data possibly including multiple lines and perhaps even ending with a residual partial line
                            # Thus we use a 'read buffer' for processing it and leaving any residual partial line at the start of the buffer for the next iteration
                            stdout_data = command_process.stdout.read()
                            if stdout_data:
                                stdout_buffer += stdout_data
                                # Process each complete line in the buffer
                                while '\n' in stdout_buffer:
                                    # Split at the first newline character
                                    line, stdout_buffer = stdout_buffer.split('\n', 1)
                                    log_and_print(line.strip())
                                # At this point, stdout_buffer contains only residual data with no newline
                        except IOError as e:
                            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                                raise
                            # If the exception is EAGAIN or EWOULDBLOCK, it means there's no data available right now, and the loop continues.
                            pass
                    if fd == command_process.stderr.fileno():
                        try:
                            # This 'read' may read a chunk of data possibly including multiple lines and perhaps even ending with a residual partial line
                            # Thus we use a 'read buffer' for processing it and leaving any residual partial line at the start of the buffer for the next iteration
                            stderr_data = command_process.stderr.read()
                            if stderr_data:
                                stderr_buffer += stderr_data
                                # Process each complete line in the buffer
                                while '\n' in stderr_buffer:
                                    # Split at the first newline character
                                    line, stderr_buffer = stderr_buffer.split('\n', 1)
                                    error_log_and_print(line.strip())
                                # At this point, stderr_buffer contains only residual data with no newline
                        except IOError as e:
                            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                                raise
                            # If the exception is EAGAIN or EWOULDBLOCK, it means there's no data available right now, and the loop continues.
                            pass
                # Check if the process has terminated
                if command_process.poll() is not None:
                    break
            # Log any remaining data in the buffers
            # This handles any data that was in the buffer but didn't end with a newline
            if stdout_buffer:
                log_and_print(stdout_buffer.strip())
            if stderr_buffer:
                error_log_and_print(stderr_buffer.strip())
            # Wait for the process to complete
            command_process.wait()
        debug_log_and_print(f"run_command_process: FINISHED command:\n{command}")
        return command_process.returncode
    except subprocess.CalledProcessError as e:
        error_log_and_print(f"Error: run_command_process: command: '{command}'", data=e)
        return e.returncode
