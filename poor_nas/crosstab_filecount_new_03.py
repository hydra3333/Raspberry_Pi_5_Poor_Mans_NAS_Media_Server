import os
import sys
import subprocess
from pathlib import Path
import glob
import re
import logging
import pprint

import common_functions

import pandas as pd

def generate_crosstab_report_pandas(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder):
    """
    Generates a crosstab report using pandas to show the relationship between media folders and disks.
    Each cell will contain details like whether the disk is the first found disk (ffd), number of files, and disk space used.
    """
    # Create a list of disk mount points and a separate list of root folders for display in the header
    disk_mount_points = [disk['disk_mount_point'] for disk in mergerfs_disks_in_LtoR_order_from_fstab]
    root_folders = [disk['root_folder_path'] for disk in mergerfs_disks_in_LtoR_order_from_fstab]

    # Initialize an empty dictionary for data storage
    crosstab_data = {disk_mount_point: [] for disk_mount_point in disk_mount_points}

    # Iterate through each unique top-level media folder to populate the data
    for media_folder_info in unique_top_level_media_folders:
        media_folder_name = media_folder_info['top_level_media_folder_name']
        ffd_disk = media_folder_info['ffd']
        
        for disk in mergerfs_disks_in_LtoR_order_from_fstab:
            disk_mount_point = disk['disk_mount_point']
            disk_info = next(
                (info for info in media_folder_info['disk_info'] if info['disk_mount_point'] == disk_mount_point),
                None
            )
            
            if disk_info:
                is_ffd = "FFD" if disk_mount_point == ffd_disk else ""
                number_of_files = disk_info['number_of_files']
                disk_space_used_gb = disk_info['disk_space_used'] / (1024 ** 3)
                cell_info = f"{is_ffd}\nFiles: {number_of_files}\nUsed: {disk_space_used_gb:.2f} GB"
            else:
                cell_info = ""
            
            crosstab_data[disk_mount_point].append(cell_info)
    
    # Convert the data into a pandas DataFrame
    df = pd.DataFrame(crosstab_data, index=[info['top_level_media_folder_name'] for info in unique_top_level_media_folders])

    # Print or log the DataFrame
    logging.info("Crosstab Report:\n")
    logging.info("\n" + df.to_string())

    # Also print to the console if needed
    print("Crosstab Report:\n")
    print(df.to_string())

def main():
    """
    Main function to coordinate the gathering of disk and media folder information and print the results.
    """
    #common_functions.DEBUG_IS_ON = True
    common_functions.DEBUG_IS_ON = False

    TERMINAL_WIDTH = 220
    common_functions.init_PrettyPrinter(TERMINAL_WIDTH)
    common_functions.init_logging(r'./logile.log')

    common_functions.log_and_print('-' * TERMINAL_WIDTH)
    common_functions.log_and_print("Starting 'crosstab_filecount'.")

    # Step 1: Get mergerfs disks in LtoR order from fstab
    common_functions.log_and_print("Finding MergerFS Disks in Left-to-Right Order from /etc/fstab ...")
    mergerfs_disks_in_LtoR_order_from_fstab = common_functions.get_mergerfs_disks_in_LtoR_order_from_fstab()
    #common_functions.log_and_print("MergerFS Disks in Left-to-Right Order from /etc/fstab:", data=mergerfs_disks_in_LtoR_order_from_fstab)
    #common_functions.log_and_print('-' * TERMINAL_WIDTH)
    
    # Step 2: Detect mergerfs disks having a root folder
    common_functions.log_and_print("Finding MergerFS Disks Having a Root Folder ...")
    mergerfs_disks_having_a_root_folder = common_functions.detect_mergerfs_disks_having_a_root_folder(mergerfs_disks_in_LtoR_order_from_fstab)
    #common_functions.log_and_print("MergerFS Disks Having a Root Folder:", data=mergerfs_disks_having_a_root_folder)
    #common_functions.log_and_print('-' * TERMINAL_WIDTH)
    
    # Step 3: Get unique top level media folders and update ffd information
    common_functions.log_and_print("Finding Unique Top-Level Media Folders")
    unique_top_level_media_folders, mergerfs_disks_having_a_root_folder = common_functions.get_unique_top_level_media_folders(
        mergerfs_disks_in_LtoR_order_from_fstab,
        mergerfs_disks_having_a_root_folder
        )
    #common_functions.log_and_print("Unique Top-Level Media Folders:", data=unique_top_level_media_folders)
    #common_functions.log_and_print('-' * TERMINAL_WIDTH)

    # Step 4: Generate and log the crosstab report
    common_functions.log_and_print("Generating crosstab_report ...")
    generate_crosstab_report_pandas(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder)

    common_functions.log_and_print("Finished 'crosstab_filecount'.")
    common_functions.log_and_print('-' * TERMINAL_WIDTH)

if __name__ == "__main__":
    main()
