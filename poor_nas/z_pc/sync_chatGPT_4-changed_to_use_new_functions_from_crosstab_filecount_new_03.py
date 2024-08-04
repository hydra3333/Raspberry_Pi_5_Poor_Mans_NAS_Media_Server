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

import common_functions

def run_command_process_1(command):
    """
    ### early version, not guaranteed to work properly without blocking reads
    Run the command and log stdout and stderr in real-time.
    """
    try:
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as command_process:
            while True:
                reads = [command_process.stdout.fileno(), command_process.stderr.fileno()]
                ret = select.select(reads, [], [])
                for fd in ret[0]:
                    if fd == command_process.stdout.fileno():
                        stdout_line = command_process.stdout.readline()
                        if stdout_line:
                            log_and_print(stdout_line.strip())
                    if fd == command_process.stderr.fileno():
                        stderr_line = command_process.stderr.readline()
                        if stderr_line:
                            error_log_and_print(stderr_line.strip())
                if command_process.poll() is not None:
                    break
            command_process.wait()
        return command_process.returncode
    except subprocess.CalledProcessError as e:
        error_log_and_print(f"Error running command: '{command}'",data=e)
        return e.returncode

def run_command_process_2(command):
    """
    ### early version, not guaranteed to work properly without blocking reads
    Run the command and log stdout and stderr in real-time IN NON READ-BLOCKING MODE
    """
    try:
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as command_process:
            # Set stdout and stderr to non-blocking mode
            os.set_blocking(command_process.stdout.fileno(), False)     # SET NON-BLOCKING READ SINCE PYTHON 3.5
            os.set_blocking(command_process.stderr.fileno(), False)     # SET NON-BLOCKING READ SINCE PYTHON 3.5
            while True:
                reads = [command_process.stdout.fileno(), command_process.stderr.fileno()]
                ret = select.select(reads, [], [])
                for fd in ret[0]:
                    if fd == command_process.stdout.fileno():
                        stdout_line = command_process.stdout.readline()
                        if stdout_line:
                            log_and_print(stdout_line.strip())
                    if fd == command_process.stderr.fileno():
                        stderr_line = command_process.stderr.readline()
                        if stderr_line:
                            error_log_and_print(stderr_line.strip())
                if command_process.poll() is not None:
                    break
            command_process.wait()
        return command_process.returncode
    except subprocess.CalledProcessError as e:
        error_log_and_print(f"Error running command: '{command}'",data=e)
        return e.returncode

def run_command_process_3(command):
    """
    ### early version, not guaranteed to work properly without blocking reads
    Run the command and log stdout and stderr in real-time IN NON READ-BLOCKING MODE
    """
    try:
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as command_process:
            # Set stdout and stderr to non-blocking mode
            os.set_blocking(command_process.stdout.fileno(), False)     # sets stdout to non-blocking read mode.
            os.set_blocking(command_process.stderr.fileno(), False)     # sets stderr to non-blocking read mode.
            while True:
                reads = [command_process.stdout.fileno(), command_process.stderr.fileno()]
                # select.select(reads, [], []) ensures that we only attempt to read from the file descriptors when they are ready.
                # This prevents the loop from blocking or spinning unnecessarily.
                ret = select.select(reads, [], [])      # this may wait forever if nothing gets written
                for fd in ret[0]:
                    if fd == command_process.stdout.fileno():
                        try:
                            stdout_line = command_process.stdout.readline()
                            if stdout_line:
                                log_and_print(stdout_line.strip())
                        except IOError as e:
                            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                                raise
                            pass    # If the exception is EAGAIN or EWOULDBLOCK, it means there's no data available right now, and the loop continues.
                    if fd == command_process.stderr.fileno():
                        try:
                            stderr_line = command_process.stderr.readline()
                            if stderr_line:
                                error_log_and_print(stderr_line.strip())
                        except IOError as e:
                            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                                raise
                            pass    # If the exception is EAGAIN or EWOULDBLOCK, it means there's no data available right now, and the loop continues.
                if command_process.poll() is not None:
                    break
            command_process.wait()
        return command_process.returncode
    except subprocess.CalledProcessError as e:
        error_log_and_print(f"Error running command: '{command}'",data=e)
        return e.returncode

def run_command_process_4(command):
    """
    Run the command and log stdout and stderr in real-time IN NON READ-BLOCKING MODE
    """
    try:
        with subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) as command_process:
            # Set stdout and stderr to non-blocking mode
            os.set_blocking(command_process.stdout.fileno(), False)     # sets stdout to non-blocking read mode.
            os.set_blocking(command_process.stderr.fileno(), False)     # sets stderr to non-blocking read mode.
            timeout = 1.0   # a timeout in seconds just in case nothing gets written to stdout, stderr
            while True:
                reads = [command_process.stdout.fileno(), command_process.stderr.fileno()]
                # Use a short timeout in select.select() to periodically contnue and check if the process has completed
                # select.select(reads, [], []) ensures that we only attempt to read from the file descriptors when they are ready.
                # This prevents the loop from blocking or spinning unnecessarily.
                ret = select.select(reads, [], [], timeout)   # a timeout in seconds just in case nothing gets written to stdout, stderr
                for fd in ret[0]:
                    if fd == command_process.stdout.fileno():
                        try:
                            stdout_line = command_process.stdout.readline()
                            if stdout_line:
                                log_and_print(stdout_line.strip())
                        except IOError as e:
                            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                                raise
                            # If the exception is EAGAIN or EWOULDBLOCK, it means there's no data available right now, and the loop continues.
                            pass
                    if fd == command_process.stderr.fileno():
                        try:
                            stderr_line = command_process.stderr.readline()
                            if stderr_line:
                                error_log_and_print(stderr_line.strip())
                        except IOError as e:
                            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                                raise
                            # If the exception is EAGAIN or EWOULDBLOCK, it means there's no data available right now, and the loop continues.
                            pass
                # Check if the process has terminated
                if command_process.poll() is not None:
                    break
            # Wait for the process to complete
            command_process.wait()
        return command_process.returncode
    except subprocess.CalledProcessError as e:
        error_log_and_print(f"Error running command: '{command}'",data=e)
        return e.returncode

def sync_folders(unique_top_level_media_folders, perform_action=False):
    """
    Synchronizes each top-level media folder from its FFD (First Found Disk) to all other disks containing the same top-level media folder.
    """
    list_of_media_folder_ffd_disks_to_sync = get_list_of_media_folder_ffd_disks_to_sync(unique_top_level_media_folders)
    
    for candidate in list_of_media_folder_ffd_disks_to_sync:
        # candidate is an item in a list, itself a list: [ a top_level_media_folder_name, a path to copy from, a path to copy to ]
        if any(item == "" or item is None for item in candidate):
            error_log_and_print(f"ERROR: one of list_of_media_folder_ffd_disks_to_sync has no value: {candidate}")
            sys.exit(1)  # Exit with a status code indicating an error
        top_level_media_folder_name, source_path, target_path = candidate
        source_path = Path(source_path)
        target_path = Path(target_path)
        if not source_path.exists():
            error_log_and_print(f"Error: top_level_media_folder_name:'{top_level_media_folder_name}', expected source_path '{source_path}' does not exist to rsync from.")
            sys.exit(1)  # Exit with a status code indicating an error
        if not target_path.exists():
            error_log_and_print(f"Error: top_level_media_folder_name:'{top_level_media_folder_name}', expected target_path '{target_path}' does not exist to rsync into.")
            sys.exit(1)  # Exit with a status code indicating an error

        # rsync command to synchronize the FFD folder to the target folder
        #    -av               Copy files and directories from the source to the target if they are missing in the target.
        #    --delete          Remove files from the target that are not present in the source.
        #    --size-only       Ignore timestamps, Update files in the target if their size differs from the corresponding files in the source.
        #    --human-readable  Output numbers in a more human-readable format.
        #    --stats           Print a verbose set of statistics on the file transfer, telling how effective rsync’s delta-transfer algorithm is.
        #    --dry-run         This makes rsync perform a trial run that doesn’t make any changes (and produces mostly the same output  as a real run).
        rsync_options = "--dry-run -av --delete --size-only --human-readable --stats"
        if not perform_action:
            rsync_options = " --dry-run " + rsync_options

        rsync_command = f"rsync {rsync_options} '{source_path}/' '{target_path}/'   # for '{top_level_media_folder_name}'"
        if perform_action:
            log_and_print(f"Syncing {top_level_media_folder_name} from '{source_path}' to '{target_path}' with rsync command: ", data=rsync_command)
        else:
            log_and_print(f"DRY RUN: Syncing {top_level_media_folder_name} from '{source_path}' to '{target_path}' with rsync command: ", data=rsync_command)

        return_code = run_command_process_4(rsync_command)  # latest version of code from ChatGPT discussion is "4"
        if return_code == 0:
            log_and_print(f"Successfully completed syncing {top_level_media_folder_name} from '{source_path}' to '{target_path}' with rsync command: ", data=rsync_command)
        else:
            error_log_and_print(f"FAILED syncing {top_level_media_folder_name} from '{source_path}' to '{target_path}' with rsync command: ", data=rsync_command)
            error_log_and_print(f"Continuing with syncing remaining 'top level mediafolder name's ...")
            pass

def main():
    """
    Main function to orchestrate the sync process:
    1. Reads the fstab to detect disks used by mergerfs.
    2. Identifies media disks with mergerfs_Root_* folders.
    3. Determines the full set of top level media folders.
    4. Identifies the first found disk (ffd) for each folder.
    5. Syncs folders from the ffd to other disks.
    """
    common_functions.DEBUG_IS_ON = False
    perform_action = False

    TERMINAL_WIDTH = 200
    common_functions.init_PrettyPrinter(TERMINAL_WIDTH)
    common_functions.init_logging(r'/home/pi/Desktop/logs/sync.log')
    common_functions.log_and_print('-' * TERMINAL_WIDTH)

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common_functions.log_and_print(f"Starting media 'SYNC' at {current_time}.")

    mergerfs_disks_in_LtoR_order_from_fstab = common_functions.get_mergerfs_disks_in_LtoR_order_from_fstab()
    if not mergerfs_disks_in_LtoR_order_from_fstab:
        error_log_and_print("No disks found in fstab or mergerfs entry not detected.")
        sys.exit(1)  # Exit with a status code indicating an error

    mergerfs_disks_having_a_root_folder_having_files = common_functions.detect_mergerfs_disks_having_a_root_folder_having_files(mergerfs_disks_in_LtoR_order_from_fstab)
    if not mergerfs_disks_having_a_root_folder_having_files:
        error_log_and_print("No media disks detected with media folders having files.")
        sys.exit(1)  # Exit with a status code indicating an error

    unique_top_level_media_folders, mergerfs_disks_having_a_root_folder_having_files = common_functions.get_unique_top_level_media_folders(
        mergerfs_disks_in_LtoR_order_from_fstab,
        mergerfs_disks_having_a_root_folder_having_files
    )

    common_functions.DEBUG_IS_ON = True
    sync_folders(unique_top_level_media_folders, perform_action=perform_action)
    common_functions.DEBUG_IS_ON = False

    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    common_functions.log_and_print(f"Finished media 'SYNC' at {current_time}.")
    common_functions.log_and_print('-' * TERMINAL_WIDTH)

if __name__ == "__main__":
    main()
