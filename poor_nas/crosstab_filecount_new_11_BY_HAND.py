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

def generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder_having_files):
    """
    Generates a crosstab report summarizing the state of top-level media folders across different disks.

    Parameters:
    - unique_top_level_media_folders (list of dict):
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
                'ffd': '/srv/usb3disk1',
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

    - mergerfs_disks_in_LtoR_order_from_fstab
      A list of dict: A list of dictionaries, each representing a detected mergerfs underlying disk in LtoR order from fstab.
      The structure is as follows:
      [
            {
              'disk_mount_point': str,    # The mount point path of the disk (e.g., '/srv/usb3disk1')
              'free_disk_space':  int    # The free disk space available on the disk in bytes
            }
      ]
      Example:
        [
            {'disk_mount_point': '/srv/usb3disk1', 'free_disk_space': 1234567890},
            {'disk_mount_point': '/srv/usb3disk2', 'free_disk_space': 987654321},
            ...
        ]

    - mergerfs_disks_having_a_root_folder_having_files (dict):
      This dictionary contains information about the disks that have a root folder and the media folders within them. 
      The structure is as follows:
        {
          'disk_mount_point': str,  # The mount point of the disk (e.g., '/srv/usb3disk1')
          'root_folder_path': Path,  # The path to the root folder (e.g., '/srv/usb3disk1/mediaroot')
          'top_level_media_folders': [
            {
              'top_level_media_folder_name': str,  # The name of the media folder (e.g., 'Movies')
              'top_level_media_folder_path': Path,  # The path to the media folder (e.g., '/srv/usb3disk1/mediaroot/Movies')
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
    def center_string(source_string, target_length):
        """
        Centers a source string within a target length string.

        Args:
        - source_string (str): The string to center.
        - target_length (int): The fixed size of the target string.

        Returns:
        - str: The centered string with padding.
        """
        if target_length < len(source_string):
            raise ValueError("Target length must be greater than the length of the source string.")
        # Calculate total padding needed to reach the target length
        total_padding = target_length - len(source_string)
        if total_padding < 0:
            raise ValueError("Target length must be greater than the length of the source string.")
        # Determine padding on the left and right sides
        left_padding = total_padding // 2
        right_padding = total_padding - left_padding
        # Construct the centered string
        centered_string = f"{' ' * left_padding}{source_string}{' ' * right_padding}"
        return centered_string

    # --------------------------------------
    # Main code for generate_crosstab_report
    # --------------------------------------

    # Prepare the header for the crosstab table, rolumns 1..n
    # column 1 = list of top level media folder names
    # column n = totals for the row
    headers = ["Top Level Media Folder"]
    for disk in mergerfs_disks_in_LtoR_order_from_fstab:
        disk_mount_point = disk['disk_mount_point']
        disk_info = mergerfs_disks_having_a_root_folder_having_files.get(disk_mount_point, {}) # .get(key, default_value}
        root_folder_path = disk_info.get('root_folder_path', "")
        if root_folder_path != "":
            headers.append(f"{disk_mount_point}")
            #headers.append(f"{disk_mount_point} {root_folder_path}")
    headers.append("Total Used")
    gigantic_list = [headers]
    #common_functions.debug_log_and_print("\n\nAPPENDED into 'gigantic_list' 'headers' (len={len(headers)}):", data=headers)
    #common_functions.debug_pause()

    # Generate the data rows
    for top_level_media_folder_name, top_level_media_folder_info in unique_top_level_media_folders.items():
        common_functions.debug_log_and_print(f"Top Level Media Folder Name: '{top_level_media_folder_name}' top_level_media_folder_info:", data=top_level_media_folder_info)
        # NOTE: top_level_media_folder_info['disk_info'] only has disks which have data for this common folder ...
        row_a = [top_level_media_folder_name]
        row_b = [""]
        row_c = [""]
        row_number_of_files = 0
        row_disk_space_used = 0
        for disk in mergerfs_disks_in_LtoR_order_from_fstab:
            disk_mount_point = disk['disk_mount_point']
            # check if the mergerfs_disks_in_LtoR_order_from_fstab disk we are looking at now
			# is in mergerfs_disks_having_a_root_folder_having_files.
			# if YES then it means it has a root folder and top level mediafolders and has files under them
            has_info = mergerfs_disks_having_a_root_folder_having_files.get(disk_mount_point, {}) # .get(key, default_value}
            if has_info:
                # Find the disk_info dictionary for the current disk_mount_point in top_level_media_folder_info, or use an empty dict if not found
                disk_info = next((info for info in top_level_media_folder_info['disk_info'] if info['disk_mount_point'] == disk_mount_point), {}) # 'next' retrieves first item from the "lazy" generator, default {}
                if disk_info:
                    # disk_info is not empty, it must have files in this top level media folder, so process it
                    common_functions.debug_log_and_print(f"Top Level Media Folder Name: '{top_level_media_folder_name}' disk_mount_point: '{disk_mount_point}' Disk Info: ", data=disk_info)
                    is_ffd = disk_info['is_ffd']
                    root_folder_path = disk_info['root_folder_path']
                    number_of_files = disk_info['number_of_files']
                    disk_space_used = disk_info['disk_space_used']
                    disk_space_used_gb = round(disk_space_used / (1024**3), 2)  # Convert to GB
                    total_free_disk_space = disk_info['total_free_disk_space']
                    total_free_disk_space_gb = round(total_free_disk_space / (1024**3), 2)  # Convert to GB
                else:
                    # disk_info is empty, has NO files in this top level media folder
                    common_functions.debug_log_and_print(f"Top Level Media Folder Name: '{top_level_media_folder_name}' disk_mount_point '{disk_mount_point}' does not have Disk Info for this top-level media folder: ", data=disk_info)
                    is_ffd = False
                    root_folder_path = ""
                    number_of_files = 0
                    disk_space_used = 0
                    disk_space_used_gb = 0  # Convert to GB
                    total_free_disk_space = 0
                    total_free_disk_space_gb = 0  # Convert to GB
                # OK for this disk, within a top level media, folder now we have data we can use
                row_number_of_files += number_of_files
                row_disk_space_used += disk_space_used
                if number_of_files > 0 or disk_space_used_gb > 0 or is_ffd:
                    row_a.append(f"{number_of_files:,} files")  	# Comma separator for number_of_files
                    row_b.append(f"{disk_space_used_gb:,.2f} GB")   # Comma separator for GB
                    row_c.append(f"ffd:{is_ffd}")
                else:
                    row_a.append("")
                    row_b.append("")
                    row_c.append("")
        # Add totals for the row
        row_a.append(f"{row_number_of_files:,} files")
        row_b.append(f"{row_disk_space_used / (1024**3):,.2f} GB")  # Convert to GB with commas
        row_c.append("")
        gigantic_list.append(row_a)
        gigantic_list.append(row_b)
        gigantic_list.append(row_c)
        #common_functions.debug_log_and_print("\n\nAPPENDED into 'gigantic_list' 'row_a' (len={len(row_a)}):", data=row_a)
        #common_functions.debug_log_and_print("\n\nAPPENDED into 'gigantic_list' 'row_b' (len={len(row_b)}):", data=row_b)
        #common_functions.debug_log_and_print("\n\nAPPENDED into 'gigantic_list' 'row_c' (len={len(row_c)}):", data=row_c)
        #common_functions.debug_pause()

    # Calculate free space per disk for the last row
    free_space_row = ["Free Disk Space"]
    for disk in mergerfs_disks_in_LtoR_order_from_fstab:
        disk_mount_point = disk['disk_mount_point']
        disk_info = mergerfs_disks_having_a_root_folder_having_files.get(disk_mount_point, {}) # .get(key, default_value}
        root_folder_path = disk_info.get('root_folder_path', "")
        if root_folder_path != "":
            free_space = disk.get('free_disk_space', 0)  # Safely handle missing 'free_disk_space'
            free_space_gb = round(free_space / (1024**3), 2)  # Convert to GB
            free_space_row.append(f"{free_space_gb:,.2f} GB")  # Comma separator for free space
    free_space_row.append("")   # For the totals columns
    gigantic_list.append(free_space_row)
    #common_functions.debug_log_and_print("\n\nAPPENDED into 'gigantic_list' 'free_space_row' (len={len(free_space_row)}):", data=free_space_row)
    #common_functions.debug_pause()

    # Calculate the maximum length of each column
    max_column_lengths = [0] * len(gigantic_list[0])
    for g_row in gigantic_list:
        for index, cell in enumerate(g_row):
            max_column_lengths[index] = max(max_column_lengths[index], len(cell))
            if max_column_lengths[index] % 2 != 0:
                max_column_lengths[index] += 1

    # Print the rows
    common_functions.log_and_print(f"*** Start Of Crosstab")
    len_formatted_row = 0
    for g_row in gigantic_list:
        # Format the first column with left alignment
        formatted_first_column = "{:<{width}}".format(g_row[0], width=max_column_lengths[0])
        # Center the rest of the columns
        remaining_columns = [ center_string(g_row[index], max_column_lengths[index]) for index in range(1, len(g_row)) ]
        formatted_row = formatted_first_column + " | " + " | ".join(remaining_columns) + "  |"
        len_formatted_row = max(len_formatted_row, len(formatted_row))
        if g_row[0] != "":
            common_functions.log_and_print("-" * len_formatted_row)
        common_functions.log_and_print(formatted_row)
    common_functions.log_and_print("-" * len_formatted_row)
    common_functions.log_and_print(f"*** End Of Crosstab")

def main():
    """
    Main function to coordinate the gathering of disk and media folder information and print the results.
    """
    common_functions.DEBUG_IS_ON = False
    #common_functions.DEBUG_IS_ON = True

    TERMINAL_WIDTH = 200
    common_functions.init_PrettyPrinter(TERMINAL_WIDTH)
    common_functions.init_logging(r'/home/pi/Desktop/logs/sync.log')

    common_functions.log_and_print('-' * TERMINAL_WIDTH)
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common_functions.log_and_print(f"Starting 'crosstab_report' at {current_time}.")

    # Step 1: Get mergerfs disks in LtoR order from fstab
    common_functions.log_and_print("Finding MergerFS Disks in Left-to-Right Order from /etc/fstab ...")
    mergerfs_disks_in_LtoR_order_from_fstab = common_functions.get_mergerfs_disks_in_LtoR_order_from_fstab()
    #common_functions.log_and_print("MergerFS Disks in Left-to-Right Order from /etc/fstab :", data=mergerfs_disks_in_LtoR_order_from_fstab)
    #common_functions.debug_pause()
    
    # Step 2: Detect mergerfs disks having a root folder
    common_functions.log_and_print("Finding MergerFS Disks Having a Root Folder ...")
    mergerfs_disks_having_a_root_folder_having_files = common_functions.detect_mergerfs_disks_having_a_root_folder_having_files(mergerfs_disks_in_LtoR_order_from_fstab)
    #common_functions.log_and_print("MergerFS Disks Having a Root Folder :", data=mergerfs_disks_having_a_root_folder_having_files)
    #common_functions.debug_pause()
    
    # Step 3: Get unique top level media folders and update ffd information
    common_functions.log_and_print("Finding Unique Top-Level Media Folders")
    unique_top_level_media_folders, mergerfs_disks_having_a_root_folder_having_files = common_functions.get_unique_top_level_media_folders(
        mergerfs_disks_in_LtoR_order_from_fstab,
        mergerfs_disks_having_a_root_folder_having_files
    )
    #common_functions.log_and_print("MergerFS Disks Having a Root Folder BACK-UPDATED WITH FFD :", data=mergerfs_disks_having_a_root_folder_having_files)
    #common_functions.log_and_print("Unique Top-Level Media Folders :", data=unique_top_level_media_folders)
    #common_functions.debug_pause()

    # Step 4: Generate and log the crosstab report
    common_functions.log_and_print("Generating crosstab_report ...")
    generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder_having_files)
    
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common_functions.log_and_print(f"Finished 'crosstab_report' at {current_time}.")
    
    common_functions.log_and_print('-' * TERMINAL_WIDTH)

if __name__ == "__main__":
    main()
