import os
import sys
import subprocess
from pathlib import Path
import glob
import re
import logging
import pprint

import common_functions

import shutil
import datetime

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

    - mergerfs_disks_in_LtoR_order_from_fstab
      A list of dict: A list of dictionaries, each representing a detected mergerfs underlying disk in LtoR order from fstab.
      The structure is as follows:
      [
            {
              'disk_mount_point': str,    # The mount point path of the disk (e.g., '/mnt/sda1')
              'free_disk_space':  int    # The free disk space available on the disk in bytes
            }
      ]
      Example:
        [
            {'disk_mount_point': '/mnt/sda1', 'free_disk_space': 1234567890},
            {'disk_mount_point': '/mnt/sda2', 'free_disk_space': 987654321},
            ...
        ]

    - mergerfs_disks_having_a_root_folder_having_files (dict):
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

    # Prepare the header for the crosstab table, rolumns 1..n
    # column 1 = list of top level media folder names
    # column n = totals for the row
    headers = ["Top Level Media Folder"]
    for disk in mergerfs_disks_in_LtoR_order_from_fstab:
        disk_mount_point = disk['disk_mount_point']
        disk_info = mergerfs_disks_having_a_root_folder_having_files.get(disk_mount_point, {}) # .get(key, default_value}
        root_folder_path = disk_info.get('root_folder_path', "")
        if root_folder_path != "":
            #headers.append(f"{disk_mount_point} {root_folder_path}")
            headers.append(f"{disk_mount_point}")
    headers.append("Total")
    common_functions.debug_log_and_print("generate_crosstab_report: headers list:", data=headers)

    # Generate the data rows
    for top_level_media_folder_name, top_level_media_folder_info in unique_top_level_media_folders.items():
        common_functions.debug_log_and_print(f"Top Level Media Folder Name: '{top_level_media_folder_name}' top_level_media_folder_info:", data=top_level_media_folder_info)
        #    'Movies': {
        #        'ffd': '/mnt/sda1',
        #        'disk_info': [
        #            {
        #                'disk_mount_point': '/mnt/sda1',
        #                'is_ffd': True,
        #                'root_folder_path': Path('/mnt/sda1/mergerfs_Root_1'),
        #                'number_of_files': 1500,
        #                'disk_space_used': 12000000000,
        #                'total_free_disk_space': 50000000000
        #            },
        #            {
        #                'disk_mount_point': '/mnt/sda2',
        #                'is_ffd': False,
        #                'root_folder_path': Path('/mnt/sda2/mergerfs_Root_2'),
        #                'number_of_files': 1500,
        #                'disk_space_used': 12000000000,
        #                'total_free_disk_space': 60000000000
        #            },
        #            ...
        #        ]
        #
        # NOTE: top_level_media_folder_info['disk_info'] only has disks which have data for this common folder ...

        for disk in mergerfs_disks_in_LtoR_order_from_fstab:
            disk_mount_point = disk['disk_mount_point']
            # Find the disk_info dictionary for the current disk_mount_point, or use an empty dict if not found
            disk_info = next((info for info in top_level_media_folder_info['disk_info'] if info['disk_mount_point'] == disk_mount_point), {}) # 'next' retrieves first item from the "lazy" generator, default {}
            if disk_info:
                # disk_info is not empty, process it
                common_functions.debug_log_and_print(f"Top Level Media Folder Name: '{top_level_media_folder_name}' disk_mount_point: '{disk_mount_point}' Disk Info: ", data=disk_info)
                is_ffd = disk_info['is_ffd']
                root_folder_path = disk_info['root_folder_path']
                number_of_files = disk_info['number_of_files']
                disk_space_used = disk_info['disk_space_used']
                disk_space_used_gb = round(disk_space_used / (1024**3), 2)  # Convert to GB
                total_free_disk_space = disk_info['total_free_disk_space']
                total_free_disk_space_gb = round(total_free_disk_space / (1024**3), 2)  # Convert to GB
            else:
                # disk_info is empty, handle this case
                common_functions.debug_log_and_print(f"Top Level Media Folder Name: '{top_level_media_folder_name}' disk_mount_point '{disk_mount_point}' does not have Disk Info for this top-level media folder: ", data=disk_info)
                is_ffd = False
                root_folder_path = ""
                number_of_files = 0
                disk_space_used = 0
                disk_space_used_gb = 0  # Convert to GB
                total_free_disk_space = 0
                total_free_disk_space_gb = 0  # Convert to GB
        common_functions.debug_pause()


















def bad_generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab):
    """
    Generates a crosstab report showing the status of each top-level media folder on each disk.
    
    Args:
        unique_top_level_media_folders (dict): A dictionary containing unique top-level media folders and related derived information.
        mergerfs_disks_in_LtoR_order_from_fstab (list of dict): A list of dictionaries representing detected mergerfs underlying disks.
    """
    # Extract disk mount points and headers
    disks = {disk['disk_mount_point']: disk['free_disk_space'] for disk in mergerfs_disks_in_LtoR_order_from_fstab}
    disk_headers = list(disks.keys())
    
    # Prepare data structure for results
    result = {folder: {disk: {'file_count': 0, 'disk_space_used': 0, 'ffd': '', 'total_free_space': 0} for disk in disks} for folder in unique_top_level_media_folders.keys()}
    free_space = {}

    # Populate the result dictionary
    for folder_name, folder_info in unique_top_level_media_folders.items():
        for disk_info in folder_info['disk_info']:
            disk = disk_info['disk_mount_point']
            result[folder_name][disk] = {
                'file_count': disk_info['number_of_files'],
                'disk_space_used': disk_info['disk_space_used'],
                'ffd': disk_info['is_ffd'],
                'total_free_space': disk_info['total_free_disk_space']
            }

    # Populate free space data
    for disk in disks:
        free_space[disk] = round(disks[disk] / (1024**3), 2)  # Convert to GB

    # Calculate the fixed column width based on the longest header and data values
    max_count_length = max(len(f"{info['file_count']}") for folder in result.values() for info in folder.values())
    max_size_length = max(len(f"{info['disk_space_used'] / (1024**3):.2f} GB") for folder in result.values() for info in folder.values())
    max_header_length = max(len(header) for header in disk_headers)
    column_width = max(30, max_count_length + max_size_length + 10, max_header_length + 2)  # Adjust width

    # Generate the cross-tabulation header
    header = "{:<40}".format("Folder_Name") + "".join(f"{disk}".rjust(column_width) for disk in disks)
    print(header)
    print("-" * len(header))

    # Generate the data rows
    for media_folder, disk_data in result.items():
        row = "{:<40}".format(media_folder)
        for disk, info in disk_data.items():
            file_count = info['file_count']
            total_size_gb = info['disk_space_used'] / (1024**3)
            is_ffd = "FFD" if info['ffd'] else ""
            row += f"{file_count} / {total_size_gb:.2f} GB {is_ffd}".rjust(column_width)
        print(row)
        print("-" * len(header))

    # Add the free disk space row
    free_space_row = "{:<40}".format("Free Disk Space")
    for disk in disks:
        free_space_row += f"{free_space[disk]:.2f} GB".rjust(column_width)
    print(free_space_row)
    print("-" * len(header))


def main():
    """
    Main function to coordinate the gathering of disk and media folder information and print the results.
    """
    #common_functions.DEBUG_IS_ON = False
    common_functions.DEBUG_IS_ON = True

    TERMINAL_WIDTH = 220
    common_functions.init_PrettyPrinter(TERMINAL_WIDTH)
    common_functions.init_logging(r'./logile.log')

    common_functions.log_and_print('-' * TERMINAL_WIDTH)
    common_functions.log_and_print("Starting 'crosstab_filecount'.")

    # Step 1: Get mergerfs disks in LtoR order from fstab
    common_functions.log_and_print("Finding MergerFS Disks in Left-to-Right Order from /etc/fstab ...")
    mergerfs_disks_in_LtoR_order_from_fstab = common_functions.get_mergerfs_disks_in_LtoR_order_from_fstab()
    common_functions.log_and_print("MergerFS Disks in Left-to-Right Order from /etc/fstab :", data=mergerfs_disks_in_LtoR_order_from_fstab)
    common_functions.debug_pause()
    
    # Step 2: Detect mergerfs disks having a root folder
    common_functions.log_and_print("Finding MergerFS Disks Having a Root Folder ...")
    mergerfs_disks_having_a_root_folder_having_files = common_functions.detect_mergerfs_disks_having_a_root_folder_having_files(mergerfs_disks_in_LtoR_order_from_fstab)
    common_functions.log_and_print("MergerFS Disks Having a Root Folder :", data=mergerfs_disks_having_a_root_folder_having_files)
    common_functions.debug_pause()
    
    # Step 3: Get unique top level media folders and update ffd information
    common_functions.log_and_print("Finding Unique Top-Level Media Folders")
    unique_top_level_media_folders, mergerfs_disks_having_a_root_folder_having_files = common_functions.get_unique_top_level_media_folders(
        mergerfs_disks_in_LtoR_order_from_fstab,
        mergerfs_disks_having_a_root_folder_having_files
    )
    common_functions.log_and_print("Unique Top-Level Media Folders :", data=unique_top_level_media_folders)
    common_functions.debug_pause()

    # Step 4: Generate and log the crosstab report
    common_functions.log_and_print("Generating crosstab_report ...")
    generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder_having_files)

    common_functions.log_and_print("Finished 'crosstab_filecount'.")
    common_functions.log_and_print('-' * TERMINAL_WIDTH)

if __name__ == "__main__":
    main()
