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

def generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab):
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
    common_functions.DEBUG_IS_ON = False

    TERMINAL_WIDTH = 220
    common_functions.init_PrettyPrinter(TERMINAL_WIDTH)
    common_functions.init_logging(r'./logile.log')

    common_functions.log_and_print('-' * TERMINAL_WIDTH)
    common_functions.log_and_print("Starting 'crosstab_filecount'.")

    # Step 1: Get mergerfs disks in LtoR order from fstab
    common_functions.log_and_print("Finding MergerFS Disks in Left-to-Right Order from /etc/fstab ...")
    mergerfs_disks_in_LtoR_order_from_fstab = common_functions.get_mergerfs_disks_in_LtoR_order_from_fstab()
    
    # Step 2: Detect mergerfs disks having a root folder
    common_functions.log_and_print("Finding MergerFS Disks Having a Root Folder ...")
    mergerfs_disks_having_a_root_folder = common_functions.detect_mergerfs_disks_having_a_root_folder(mergerfs_disks_in_LtoR_order_from_fstab)
    
    # Step 3: Get unique top level media folders and update ffd information
    common_functions.log_and_print("Finding Unique Top-Level Media Folders")
    unique_top_level_media_folders, mergerfs_disks_having_a_root_folder = common_functions.get_unique_top_level_media_folders(
        mergerfs_disks_in_LtoR_order_from_fstab,
        mergerfs_disks_having_a_root_folder
    )

    # Step 4: Generate and log the crosstab report
    common_functions.log_and_print("Generating crosstab_report ...")
    generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab)

    common_functions.log_and_print("Finished 'crosstab_filecount'.")
    common_functions.log_and_print('-' * TERMINAL_WIDTH)

if __name__ == "__main__":
    main()
