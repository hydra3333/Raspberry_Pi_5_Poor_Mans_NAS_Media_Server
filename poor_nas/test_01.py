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
    common_functions.log_and_print("Crosstab Report for Top Level Media Folders:")
    common_functions.log_and_print(" | ".join(headers))
    
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
        common_functions.log_and_print(" | ".join(row))

    # Totals row
    total_row = ["Total"]
    for disk in mergerfs_disks_in_LtoR_order_from_fstab:
        disk_mount_point = disk['disk_mount_point']
        free_space = disk['free_disk_space']
        total_row.append(f"Free: {free_space} bytes")
    total_row.append("")  # Placeholder for the final column
    common_functions.log_and_print(" | ".join(total_row))
    common_functions.log_and_print("End of Crosstab Report.")

def main():
    """
    Main function
    """
    #common_functions.DEBUG_IS_ON = True
    common_functions.DEBUG_IS_ON = False

    TERMINAL_WIDTH = 220
    common_functions.init_PrettyPrinter(TERMINAL_WIDTH)
    common_functions.init_logging(r'./logile.log')

    common_functions.log_and_print('-' * TERMINAL_WIDTH)

    # Step 1: Get mergerfs disks in LtoR order from fstab
    common_functions.log_and_print("Finding MergerFS Disks in Left-to-Right Order from /etc/fstab ...")
    mergerfs_disks_in_LtoR_order_from_fstab = common_functions.get_mergerfs_disks_in_LtoR_order_from_fstab()
    common_functions.log_and_print("MergerFS Disks in Left-to-Right Order from /etc/fstab:", data=mergerfs_disks_in_LtoR_order_from_fstab)
    common_functions.log_and_print('-' * TERMINAL_WIDTH)
    
    # Step 2: Detect mergerfs disks having a root folder
    common_functions.log_and_print("Finding MergerFS Disks Having a Root Folder ...")
    mergerfs_disks_having_a_root_folder = common_functions.detect_mergerfs_disks_having_a_root_folder(mergerfs_disks_in_LtoR_order_from_fstab)
    common_functions.log_and_print("MergerFS Disks Having a Root Folder:", data=mergerfs_disks_having_a_root_folder)
    common_functions.log_and_print('-' * TERMINAL_WIDTH)
    
    # Step 3: Get unique top level media folders and update ffd information
    common_functions.log_and_print("Finding Unique Top-Level Media Folders")
    unique_top_level_media_folders, mergerfs_disks_having_a_root_folder = common_functions.get_unique_top_level_media_folders(
        mergerfs_disks_in_LtoR_order_from_fstab,
        mergerfs_disks_having_a_root_folder
        )
    common_functions.log_and_print("Unique Top-Level Media Folders:", data=unique_top_level_media_folders)
    common_functions.log_and_print('-' * TERMINAL_WIDTH)
    # Step 4: Generate and log the crosstab report
    #generate_crosstab_report(unique_top_level_media_folders, mergerfs_disks_in_LtoR_order_from_fstab, mergerfs_disks_having_a_root_folder)

if __name__ == "__main__":
    main()
