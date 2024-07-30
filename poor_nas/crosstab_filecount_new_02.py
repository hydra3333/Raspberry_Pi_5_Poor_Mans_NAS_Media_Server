import os
import sys
import subprocess
from pathlib import Path
import glob
import re
import logging
import pprint

import common_functions

def generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder):
    """
    Generates and logs a crosstab report showing:
    - Left-hand side: unique top-level media folder names
    - Top: disk mount points
    - Cells: a combination of number of files, used disk space (in GB), and is_ffd status for each top-level media folder on each disk
    - Bottom row: column totals for number of files, used disk space, and total free disk space
    """
    headers = ['Media Folder']
    for disk in mergerfs_disks_in_LtoR_order_from_fstab:
        disk_mount_point = disk['disk_mount_point']
        free_space = disk['free_disk_space'] / (1024 ** 3)  # Convert bytes to GB
        headers.append(f"{disk_mount_point} (Free: {free_space:.2f} GB)")

    rows = []
    for folder_info in unique_top_level_media_folders:
        row = [folder_info['top_level_media_folder_name']]
        for disk in mergerfs_disks_in_LtoR_order_from_fstab:
            disk_mount_point = disk['disk_mount_point']
            media_info = next((media for media in folder_info['disk_info'] if media['disk_mount_point'] == disk_mount_point), None)
            if media_info:
                is_ffd = 'FFD' if media_info['is_ffd'] else ''
                num_files = media_info['number_of_files']
                space_used = media_info['disk_space_used'] / (1024 ** 3)  # Convert bytes to GB
                row.append(f"{is_ffd}\nFiles: {num_files}\nUsed: {space_used:.2f} GB")
            else:
                row.append("")

        rows.append(row)

    # Add totals row
    total_row = ['Total']
    for disk in mergerfs_disks_in_LtoR_order_from_fstab:
        disk_mount_point = disk['disk_mount_point']
        total_files = sum(media['number_of_files'] for folder_info in unique_top_level_media_folders
                          for media in folder_info['disk_info'] if media['disk_mount_point'] == disk_mount_point)
        total_used_space = sum(media['disk_space_used'] for folder_info in unique_top_level_media_folders
                               for media in folder_info['disk_info'] if media['disk_mount_point'] == disk_mount_point) / (1024 ** 3)
        free_space = disk['free_disk_space'] / (1024 ** 3)  # Convert bytes to GB
        total_row.append(f"Files: {total_files}\nUsed: {total_used_space:.2f} GB\nFree: {free_space:.2f} GB")

    rows.append(total_row)

    # Print the crosstab report
    objPrettyPrint.pprint(headers)
    for row in rows:
        objPrettyPrint.pprint(row)

    # Log the crosstab report
    logging.info("Crosstab Report:")
    logging.info(headers)
    for row in rows:
        logging.info(row)


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
    generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder)

    common_functions.log_and_print("Finished 'crosstab_filecount'.")
    common_functions.log_and_print('-' * TERMINAL_WIDTH)

if __name__ == "__main__":
    main()
