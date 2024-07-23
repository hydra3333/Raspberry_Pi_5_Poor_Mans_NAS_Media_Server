import os
import sys
import re
import argparse
from datetime import datetime
import pytz 
import ctypes
from ctypes import wintypes
from ctypes import *        # for mediainfo ... load via ctypes.CDLL(r'.\MediaInfo.dll')
from typing import Union    # for mediainfo
from pathlib import Path
import json
import xml.etree.ElementTree as ET
import subprocess
import pprint
#from MediaInfoDLL3 import MediaInfo, Stream, Info, InfoOption
from pymediainfo import MediaInfo
import pprint

def get_disks_with_root_folders_and_labels(root_folder_names):
    import os
    import psutil
    import ctypes
    from ctypes import wintypes
    import traceback
    import time
    # Initialize empty dictionaries to store the disk information
    disks_and_root_folders = {}
    disks_info = {}
    # Define DWORDLONG as c_ulonglong
    DWORDLONG = ctypes.c_ulonglong
    # Function to get the volume label of a drive
    def get_volume_label(drive_letter):
        volume_name_buffer = ctypes.create_unicode_buffer(1024)
        file_system_name_buffer = ctypes.create_unicode_buffer(1024)
        serial_number = wintypes.DWORD()
        max_component_length = wintypes.DWORD()
        file_system_flags = wintypes.DWORD()
        result = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(drive_letter),
            volume_name_buffer,
            ctypes.sizeof(volume_name_buffer),
            ctypes.byref(serial_number),
            ctypes.byref(max_component_length),
            ctypes.byref(file_system_flags),
            file_system_name_buffer,
            ctypes.sizeof(file_system_name_buffer)
        )
        if result:
            return volume_name_buffer.value
        else:
            print(f"Failed to get volume label for {drive_letter}")
            return None
    # Function to determine the disk volume type
    def get_volume_type(drive_letter):
        IOCTL_DISK_GET_DRIVE_LAYOUT_EX = 0x00070050
        drive_letter_with_slash = f"\\\\.\\{drive_letter}"
        h_device = ctypes.windll.kernel32.CreateFileW(
            ctypes.c_wchar_p(drive_letter_with_slash),
            wintypes.DWORD(0),  # No access to the drive
            wintypes.DWORD(0),  # No sharing
            None,  # Default security attributes
            wintypes.DWORD(3),  # Open existing
            wintypes.DWORD(0),  # Normal attributes
            None  # No template file
        )
        if h_device == wintypes.HANDLE(-1).value:
            raise ctypes.WinError()
        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8)
            ]
        class PARTITION_INFORMATION_GPT(ctypes.Structure):
            _fields_ = [
                ("PartitionType", GUID),
                ("PartitionId", GUID),
                ("Attributes", DWORDLONG),
                ("Name", wintypes.WCHAR * 36)
            ]
        class PARTITION_INFORMATION_MBR(ctypes.Structure):
            _fields_ = [
                ("PartitionType", wintypes.BYTE),
                ("BootIndicator", wintypes.BOOL),
                ("RecognizedPartition", wintypes.BOOL),
                ("HiddenSectors", wintypes.DWORD)
            ]
        class PARTITION_INFORMATION_EX(ctypes.Structure):
            class _UNION(ctypes.Union):
                _fields_ = [
                    ("Mbr", PARTITION_INFORMATION_MBR),
                    ("Gpt", PARTITION_INFORMATION_GPT)
                ]
            _fields_ = [
                ("PartitionStyle", wintypes.DWORD),
                ("StartingOffset", wintypes.LARGE_INTEGER),
                ("PartitionLength", wintypes.LARGE_INTEGER),
                ("PartitionNumber", wintypes.DWORD),
                ("RewritePartition", wintypes.BOOL),
                ("Union", _UNION)
            ]
        class DRIVE_LAYOUT_INFORMATION_EX(ctypes.Structure):
            _fields_ = [
                ("PartitionStyle", wintypes.DWORD),
                ("PartitionCount", wintypes.DWORD),
                ("PartitionEntry", PARTITION_INFORMATION_EX * 1)
            ]
        # Start with an initial guess for partition count
        partition_count_guess = 4
        while True:
            class DRIVE_LAYOUT_INFORMATION_EX_DYN(ctypes.Structure):
                _fields_ = [
                    ("PartitionStyle", wintypes.DWORD),
                    ("PartitionCount", wintypes.DWORD),
                    ("PartitionEntry", PARTITION_INFORMATION_EX * partition_count_guess)
                ]
            drive_layout_info = DRIVE_LAYOUT_INFORMATION_EX_DYN()
            bytes_returned = wintypes.DWORD()
            result = ctypes.windll.kernel32.DeviceIoControl(
                h_device,
                IOCTL_DISK_GET_DRIVE_LAYOUT_EX,
                None,
                0,
                ctypes.byref(drive_layout_info),
                ctypes.sizeof(drive_layout_info),
                ctypes.byref(bytes_returned),
                None
            )
            if not result:
                error_code = ctypes.GetLastError()
                if error_code == 122:  # ERROR_INSUFFICIENT_BUFFER
                    partition_count_guess *= 2
                    continue
                else:
                    ctypes.windll.kernel32.CloseHandle(h_device)
                    raise ctypes.WinError(error_code)
            ctypes.windll.kernel32.CloseHandle(h_device)
            if drive_layout_info.PartitionStyle == 0:
                return "MBR"
            elif drive_layout_info.PartitionStyle == 1:
                return "GPT"
            elif drive_layout_info.PartitionStyle == 2:
                for i in range(drive_layout_info.PartitionCount):
                    partition_info = drive_layout_info.PartitionEntry[i]
                    if partition_info.PartitionStyle == 1 and \
                            partition_info.Union.Gpt.PartitionType == GUID(0xAF9B60A0, 0x1431, 0x4F62, (0xBC, 0x68, 0x33, 0x11, 0x71, 0x4A, 0x69, 0xAD)):
                        return "Dynamic Disk"
            return "Unknown"
    # debug: Iterate through all disk partitions listing all found
    #print(f"DEBUG: start finding psutil.disk_partitions() drive letter, using for partition in psutil.disk_partitions():")
    disk_partitions_drive_letters = []
    for partition in psutil.disk_partitions():
        drive_letter = partition.device.rstrip("\\")
        disk_partitions_drive_letters.append(drive_letter)
    #print(f"DEBUG: end finding psutil.disk_partitions() drive letter, result is {len(disk_partitions_drive_letters)} in {disk_partitions_drive_letters}")
    # Iterate through all disk partitions looking for a specified root folder
    for partition in psutil.disk_partitions():
        drive_letter = partition.device.rstrip("\\")
        #print(f"DEBUG: ******************** START NEW ITERATION in psutil.disk_partitions(): drive_letter='{drive_letter}' partition.device='{partition.device}'")
        try:
            # List all top-level directories in the drive
            #print(f"DEBUG:")
            #print(f"DEBUG: A drive_letter='{drive_letter}' os.listdir(drive_letter)=\n{objPrettyPrint.pformat(os.listdir(drive_letter))}")
            #print(f"DEBUG: A drive_letter='{drive_letter}' os.listdir(drive_letter+'\\')=\n{objPrettyPrint.pformat(os.listdir(drive_letter+'\\'))}")
            #print(f"DEBUG:")
            #print(f"DEBUG: B drive_letter='{drive_letter}' [d for d in os.listdir(drive_letter)]=\n{objPrettyPrint.pformat([d for d in os.listdir(drive_letter)])}")
            #print(f"DEBUG: B drive_letter='{drive_letter}' [d for d in os.listdir(drive_letter+'\\')]=\n{objPrettyPrint.pformat([d for d in os.listdir(drive_letter+'\\')])}")
            #print(f"DEBUG:")
            #top_level_dirs = [d for d in os.listdir(drive_letter)      if os.path.isdir(os.path.join(drive_letter, d))]
            #print(f"DEBUG: C drive_letter='{drive_letter}' [d for d in os.listdir(drive_letter)       if os.path.isdir(os.path.join(drive_letter, d))]=\n{objPrettyPrint.pformat(top_level_dirs)}")
            #print(f"DEBUG:")
            top_level_dirs = [d for d in os.listdir(drive_letter+'\\') if os.path.isdir(os.path.join(drive_letter+'\\', d))]
            #print(f"DEBUG: D drive_letter='{drive_letter}' [d for d in os.listdir(drive_letter+'\\') if os.path.isdir(os.path.join(drive_letter+'\\', d))]=\n{objPrettyPrint.pformat(top_level_dirs)}")
            #print(f"DEBUG:")
            #print(f"DEBUG: E drive_letter='{drive_letter}' top_level_dirs=\n{objPrettyPrint.pformat(top_level_dirs)}")
            #print(f"DEBUG:")
            #print(f"DEBUG: F about to check if 'root_folder in root_folder_names' is in {root_folder_names}")
            #print(f"DEBUG:")
            for root_folder in root_folder_names:
                if root_folder.lower() in (d.lower() for d in top_level_dirs):
                    #print(f"DEBUG: G root_folder.lower()='{root_folder.lower()}' in (d.lower() for d in top_level_dirs) returns '{root_folder.lower() in (d.lower() for d in top_level_dirs)}' ")
                    #print(f"DEBUG:")
                    # Get the volume label of the drive
                    label = get_volume_label(drive_letter + "\\")
                    #print(f"Volume label for {drive_letter}: {label}")
                    # Determine the volume type
                    volume_type = get_volume_type(drive_letter[0] + ":")
                    #print(f"Volume type for {drive_letter}: {volume_type}")
                    free_disk_space = psutil.disk_usage(drive_letter).free
                    if label and volume_type:
                        #print(f"DEBUG: H drive_letter='{drive_letter}' label and volume_type={label and volume_type} so BEFORE add, disks_and_root_folders={disks_and_root_folders}")
                        # Add to the disks_and_root_folders and disks_info dictionaries
                        disks_and_root_folders[drive_letter] = rf"\{root_folder}"
                        disks_info[drive_letter] = {
                            'Root': rf"\{root_folder}",
                            'VolumeLabel': label,
                            'VolumeType': volume_type,
                            'FreeDiskSpace': free_disk_space
                        }
                        #print(f"DEBUG: H drive_letter='{drive_letter}' label and volume_type={label and volume_type} so AFTER  add, disks_and_root_folders={disks_and_root_folders}")
                        #print(f"DEBUG: H drive_letter='{drive_letter}' label and volume_type={label and volume_type} so AFTER  add, disks_info={disks_info}")
                        #print(f"Added drive {drive_letter} with root folder {root_folder}")
                    else:
                        #print(f"Failed to retrieve information for {drive_letter}")
                        continue
                else:
                    continue
        except PermissionError:
            # Skip drives that can't be accessed
            #print(f"PermissionError accessing {drive_letter}")
            #traceback.print_exc()
            continue
        except Exception as e:
            #print(f"Error accessing {drive_letter}: {e}")
            #traceback.print_exc()
            continue
    # Sort the dictionaries by case-insensitive root folder name
    sorted_disks_and_root_folders = dict(sorted(disks_and_root_folders.items(), key=lambda item: item[1].lower()))
    sorted_disks_info = {k: disks_info[k] for k in sorted_disks_and_root_folders.keys()}
    return sorted_disks_and_root_folders, sorted_disks_info

def run_dos_command(command):
    import subprocess
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=True  # Use shell=True to execute the command through the shell
    )
    return result.stdout

def remove_duplicate_dashes_dots_from_i4670_filename(source_string):
    new_source_string = source_string
    new_source_string = case_insensitive_replace(new_source_string, "..", ".")
    new_source_string = case_insensitive_replace(new_source_string, "..", ".")
    new_source_string = case_insensitive_replace(new_source_string, "..", ".")
    new_source_string = case_insensitive_replace(new_source_string, "--", "-")
    new_source_string = case_insensitive_replace(new_source_string, "--", "-")
    new_source_string = case_insensitive_replace(new_source_string, "--", "-")
    return new_source_string

def remove_special_characters(source_string):
    # remove special characters in a filename by Matching them with a regex match in Python
    # Regex for removing special characters
    regex = re.compile(r'[^a-zA-Z0-9\-_. ]+')
    new_source_string = regex.sub('.', source_string)
    return new_source_string

def recognize_and_move_date_string_to_end(source_string):
    # eg source_string test cases
    #    "2024- 3- 2-this is a test",
    #    "abd def-2024- 3- 2",
    #    "abd def-2024- 3- 2-this is a test",
    #    "def2024- 3- 2",
    #    "2024- 3- 2ghi",
    #    "def2024- 3- 2ghi",
    #    "d_ef2024- 3- 2gh_i",
    #    "-2024- 3- 2",
    #    "2024- 3- 2-",
    #    "-2024- 3- 2-",
    #    "_2024- 3- 2.",
    #    "jkl-2024- 3- 2",
    #    "2024- 3- 2-mno",
    #    "2024- 3- 2",
    #    "2024-03-02"
    date_pattern = r'(\d{4})-\s?(\d{1,2})-\s?(\d{1,2})'
    preceding_trailing_characters = ['-', '_', '.', ' ']
    common_characters = '[' + ''.join(preceding_trailing_characters) + ']'
    new_intra_date_separator = "-"
    final_date_format = "{:04d}{sep}{:02d}{sep}{:02d}"
    #
    match = re.search(date_pattern, source_string)
    if match:
        year, month, day = match.groups()
        date_str = match.group(0)    # the recognised date string as-is
        # Check for preceding and trailing characters
        preceding_char = None
        trailing_char = None
        has_preceding_char = False
        has_trailing_char = False
        # Test for preceding character
        preceding_match = re.search(f'({common_characters})?' + re.escape(date_str), source_string)
        if preceding_match:
            preceding_char = preceding_match.group(1)
            if preceding_char in preceding_trailing_characters:
                has_preceding_char = True
        # Test for trailing character
        trailing_match = re.search(re.escape(date_str) + f'({common_characters})?', source_string)
        if trailing_match:
            trailing_char = trailing_match.group(1)
            if trailing_char in preceding_trailing_characters:
                has_trailing_char = True
        # Test for BOTH preceding and trailing as optional on either end and find the fully matched string
        optional_full_match = re.search(f'{common_characters}?' + re.escape(date_str) + f'{common_characters}?', source_string)
        optional_full_match_string = optional_full_match.group(0)    # the recognised date string in-full with optional preceding and trailing characters as-is
        # Format date string with new separator
        formatted_date = final_date_format.format(int(year), int(month), int(day), sep=new_intra_date_separator)
        # Remove optional_full_match_string from source_string and append formatted_date to the end
        if (not source_string.startswith(optional_full_match_string)) and (not source_string.endswith(optional_full_match_string)):
             replace_separator = '-'
        else:
             replace_separator = ''
        updated_source_string = source_string.replace(optional_full_match_string, replace_separator) + f'.{formatted_date}'
    else:
        updated_source_string = source_string
    return updated_source_string

def case_insensitive_replace(source_string, search_string, replacement_string):
    # Compile a regular expression pattern with case insensitivity
    pattern = re.compile(re.escape(search_string), re.IGNORECASE)
    # Perform the replacement
    result = pattern.sub(replacement_string, source_string)
    return result

def case_insensitive_replace_at_start_of_string(source_string, search_string, replacement_string):
    # Compile a regular expression pattern with case insensitivity
    pattern = re.compile(r'^' + re.escape(search_string), re.IGNORECASE)
    # Perform the replacement only if search_string occurs at the start of source_string
    result = pattern.sub(replacement_string, source_string)
    return result

def case_insensitive_replace_at_end_of_string(source_string, search_string, replacement_string):
    # Compile a regular expression pattern with case insensitivity
    pattern = re.compile(re.escape(search_string) + r'$', re.IGNORECASE)
    # Perform the replacement only if search_string occurs at the end of source_string
    result = pattern.sub(replacement_string, source_string)
    return result

def change_filename_layout(new_basename):
    # THESE ARE ALL IN A SPECIAL ORDER !
    new_basename = case_insensitive_replace(new_basename, ".h264", "")
    new_basename = case_insensitive_replace(new_basename, ".h265", "")
    new_basename = case_insensitive_replace(new_basename, ".aac", "")

    new_basename = case_insensitive_replace(new_basename, "_2013-", ".2013-")
    new_basename = case_insensitive_replace(new_basename, "_2014-", ".2014-")
    new_basename = case_insensitive_replace(new_basename, "_2015-", ".2015-")
    new_basename = case_insensitive_replace(new_basename, "_2016-", ".2016-")
    new_basename = case_insensitive_replace(new_basename, "_2017-", ".2017-")
    new_basename = case_insensitive_replace(new_basename, "_2018-", ".2018-")
    new_basename = case_insensitive_replace(new_basename, "_2019-", ".2019-")
    new_basename = case_insensitive_replace(new_basename, "_2020-", ".2020-")
    new_basename = case_insensitive_replace(new_basename, "_2021-", ".2021-")
    new_basename = case_insensitive_replace(new_basename, "_2022-", ".2022-")
    new_basename = case_insensitive_replace(new_basename, "_2023-", ".2023-")
    new_basename = case_insensitive_replace(new_basename, "_2024-", ".2024-")
    new_basename = case_insensitive_replace(new_basename, "_2025-", ".2025-")
    new_basename = case_insensitive_replace(new_basename, "_2026-", ".2026-")
    new_basename = case_insensitive_replace(new_basename, "_2027-", ".2027-")
    new_basename = case_insensitive_replace(new_basename, "_2028-", ".2028-")
    new_basename = case_insensitive_replace(new_basename, "_2029-", ".2029-")
    new_basename = case_insensitive_replace(new_basename, "_2030-", ".2030-")
    new_basename = case_insensitive_replace(new_basename, "_2031-", ".2031-")
    new_basename = case_insensitive_replace(new_basename, "_2032-", ".2032-")
    new_basename = case_insensitive_replace(new_basename, "_2033-", ".2033-")
    new_basename = case_insensitive_replace(new_basename, "_2034-", ".2034-")
    new_basename = case_insensitive_replace(new_basename, "_2035-", ".2035-")
    new_basename = case_insensitive_replace(new_basename, "_2036-", ".2036-")
    new_basename = case_insensitive_replace(new_basename, "_2037-", ".2037-")
    new_basename = case_insensitive_replace(new_basename, "_2038-", ".2038-")
    new_basename = case_insensitive_replace(new_basename, "_2039-", ".2039-")
    new_basename = case_insensitive_replace(new_basename, "_2040-", ".2040-")
    new_basename = case_insensitive_replace(new_basename, "_2041-", ".2041-")
    new_basename = case_insensitive_replace(new_basename, "_2042-", ".2042-")
    new_basename = case_insensitive_replace(new_basename, "_2043-", ".2043-")
    new_basename = case_insensitive_replace(new_basename, "_2044-", ".2044-")
    new_basename = case_insensitive_replace(new_basename, "_2045-", ".2045-")
    new_basename = case_insensitive_replace(new_basename, "_2046-", ".2046-")
    new_basename = case_insensitive_replace(new_basename, "_2047-", ".2047-")
    new_basename = case_insensitive_replace(new_basename, "_2048-", ".2048-")
    new_basename = case_insensitive_replace(new_basename, "_2049-", ".2049-")
    new_basename = case_insensitive_replace(new_basename, "_2050-", ".2050-")

    new_basename = case_insensitive_replace(new_basename, "_-_", "-")
    new_basename = case_insensitive_replace(new_basename, " - ", "-")
    new_basename = case_insensitive_replace(new_basename, "  ", " ")
    new_basename = case_insensitive_replace(new_basename, "  ", " ")
    new_basename = case_insensitive_replace(new_basename, "  ", " ")
    new_basename = case_insensitive_replace(new_basename, "- ", "-")
    new_basename = case_insensitive_replace(new_basename, " -", "-")
    new_basename = case_insensitive_replace(new_basename, "..", ".")
    new_basename = case_insensitive_replace(new_basename, "..", ".")
    new_basename = case_insensitive_replace(new_basename, "..", ".")
    new_basename = case_insensitive_replace(new_basename, "--", "-")
    new_basename = case_insensitive_replace(new_basename, "--", "-")
    new_basename = case_insensitive_replace(new_basename, "--", "-")

    new_basename = case_insensitive_replace(new_basename, " ", "_")
    new_basename = case_insensitive_replace(new_basename, "[", "_")
    new_basename = case_insensitive_replace(new_basename, "]", "_")
    new_basename = case_insensitive_replace(new_basename, "(", "_")
    new_basename = case_insensitive_replace(new_basename, ")", "_")

    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "AFL-Sport-AFL-Championship_Season.", "AFL-")
    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "AFL-Sport-AFL-Championship_Season-", "AFL-")
    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "AFL-Sport-AFL-Championship_Season_", "AFL-")
    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "AFL-Sport-AFL-Championship_Season ", "AFL-")

    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "AFL-Sport_AFL-Championship_Season.", "AFL-")
    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "AFL-Sport_AFL-Championship_Season-", "AFL-")
    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "AFL-Sport_AFL-Championship_Season_", "AFL-")
    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "AFL-Sport_AFL-Championship_Season ", "AFL-")

    new_basename = case_insensitive_replace(new_basename, "Drama-Mystery-Sci-Fi-The X-Files ", "Drama-Mystery-Sci-Fi-The X-Files-")
    new_basename = case_insensitive_replace(new_basename, "Movie Movie ", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie ", "Movie-")
    new_basename = case_insensitive_replace(new_basename, " Movie", "-Movie")
    new_basename = case_insensitive_replace(new_basename, "Action-Adventure-Comedy ", "Action-Adventure-Comedy-")
    new_basename = case_insensitive_replace(new_basename, "Action-Adventure-Crime-Movie ", "Action-Adventure-Crime-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Action-Adventure-Fantasy-Movie ", "Action-Adventure-Fantasy-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Documentary-Travel ", "Adventure-Documentary-Travel-")
    new_basename = case_insensitive_replace(new_basename, "Action-Adventure-Movie-Sci-Fi ", "Action-Adventure-Movie-Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Action-Drama-Movie-Thriller ", "Action-Drama-Movie-Thriller-")
    new_basename = case_insensitive_replace(new_basename, "Action-Drama-Movie-Thriller ", "Action-Drama-Movie-Thriller-")
    new_basename = case_insensitive_replace(new_basename, "Action-Fantasy-Movie ", "Action-Fantasy-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Action-Fantasy-Movie-Sci-Fi ", "Action-Fantasy-Movie-Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Action-Movie-Thriller ", "Action-Movie-Thriller-")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Family-Fantasy-Movie ", "Adventure-Family-Fantasy-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Movie ", "Adventure-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Animation-Comedy-Family-Movie ", "Animation-Comedy-Family-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Biography-Drama-Historical-Movie-Romance ", "Arts-Culture-Biography-Drama-Historical-Movie-Romance-")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Documentary-Historical-Nature-Society-Culture-Travel ", "Arts-Culture-Documentary-Historical-Nature-Society-Culture-Travel-")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Documentary-Historical-Society-Culture ", "Arts-Culture-Documentary-Historical-Society-Culture-")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Drama-Movie ", "Arts-Culture-Drama-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Biography-Comedy-Drama-Movie ", "Biography-Comedy-Drama-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Biography-Documentary-Historical ", "Biography-Documentary-Historical-")
    new_basename = case_insensitive_replace(new_basename, "Biography-Documentary-Historical-Mystery ", "Biography-Documentary-Historical-Mystery-")
    new_basename = case_insensitive_replace(new_basename, "Biography-Documentary-Historical-Society-Culture ", "Biography-Documentary-Historical-Society-Culture-")
    new_basename = case_insensitive_replace(new_basename, "Biography-Documentary-Music ", "Biography-Documentary-Music-")
    new_basename = case_insensitive_replace(new_basename, "Biography-Drama-Historical ", "Biography-Drama-Historical-")
    new_basename = case_insensitive_replace(new_basename, "Biography-Drama-Movie ", "Biography-Drama-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Biography-Drama-Movie-Romance ", "Biography-Drama-Movie-Romance-")
    new_basename = case_insensitive_replace(new_basename, "Children ", "Children-")
    new_basename = case_insensitive_replace(new_basename, "Comedy ", "Comedy-")
    new_basename = case_insensitive_replace(new_basename, "Comedy-Dance-Movie-Romance ", "Comedy-Dance-Movie-Romance-")
    new_basename = case_insensitive_replace(new_basename, "Comedy-Drama-Fantasy-Movie-Romance ", "Comedy-Drama-Fantasy-Movie-Romance-")
    new_basename = case_insensitive_replace(new_basename, "Comedy-Drama-Movie ", "Comedy-Drama-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Comedy-Drama-Music ", "Comedy-Drama-Music-")
    new_basename = case_insensitive_replace(new_basename, "Comedy-Family-Movie ", "Comedy-Family-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Comedy-Family-Movie-Romance ", "Comedy-Family-Movie-Romance-")
    new_basename = case_insensitive_replace(new_basename, "Comedy-Horror-Movie ", "Comedy-Horror-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Comedy-Movie ", "Comedy-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Comedy-Movie-Romance ", "Comedy-Movie-Romance-")
    new_basename = case_insensitive_replace(new_basename, "Crime-Drama ", "Crime-Drama-")
    new_basename = case_insensitive_replace(new_basename, "Crime-Drama-Murder-Mystery ", "Crime-Drama-Murder-Mystery-")
    new_basename = case_insensitive_replace(new_basename, "Crime-Drama-Mystery ", "Crime-Drama-Mystery-")
    new_basename = case_insensitive_replace(new_basename, "Current ", "Current-")
    new_basename = case_insensitive_replace(new_basename, "Documentary ", "Documentary-")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Entertainment-Historical-Travel ", "Documentary-Entertainment-Historical-Travel-")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Historical ", "Documentary-Historical-")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Historical-Mini ", "Documentary-Historical-Mini-")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Historical-Mystery ", "Documentary-Historical-Mystery-")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Historical-War ", "Documentary-Historical-War-")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Medical-Science-Tech ", "Documentary-Medical-Science-Tech-")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Nature ", "Documentary-Nature-")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Science-Tech-Society-Culture ", "Documentary-Science-Tech-Society-Culture-")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Science-Tech-Travel ", "Documentary-Science-Tech-Travel-")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Society-Culture ", "Documentary-Society-Culture-")
    new_basename = case_insensitive_replace(new_basename, "Drama ", "Drama-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Family-Movie ", "Drama-Family-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Fantasy-Mystery ", "Drama-Fantasy-Mystery-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Historical ", "Drama-Historical-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Historical-Movie-Romance ", "Drama-Historical-Movie-Romance-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Horror-Movie-Mystery ", "Drama-Horror-Movie-Mystery-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Movie ", "Drama-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Movie-Music-Romance ", "Drama-Movie-Music-Romance-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Movie-Mystery-Romance ", "Drama-Movie-Mystery-Romance-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Movie-Mystery-Sci-Fi ", "Drama-Movie-Mystery-Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Movie-Romance ", "Drama-Movie-Romance-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Movie-Sci-Fi-Thriller ", "Drama-Movie-Sci-Fi-Thriller-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Movie-Thriller ", "Drama-Movie-Thriller-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Movie-Violence ", "Drama-Movie-Violence-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Murder-Mystery ", "Drama-Murder-Mystery-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Mystery ", "Drama-Mystery-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Mystery-Sci-Fi ", "Drama-Mystery-Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Mystery-Violence ", "Drama-Mystery-Violence-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Romance-Sci-Fi ", "Drama-Romance-Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Drama-Thriller ", "Drama-Thriller-")
    new_basename = case_insensitive_replace(new_basename, "Education-Science ", "Education-Science-")
    new_basename = case_insensitive_replace(new_basename, "Education-Science-Tech ", "Education-Science-Tech-")
    new_basename = case_insensitive_replace(new_basename, "Entertainment ", "Entertainment-")
    new_basename = case_insensitive_replace(new_basename, "Entertainment-Real ", "Entertainment-Real-")
    new_basename = case_insensitive_replace(new_basename, "Horror-Movie ", "Horror-Movie-")
    new_basename = case_insensitive_replace(new_basename, "Infotainment-Real ", "Infotainment-Real-")
    new_basename = case_insensitive_replace(new_basename, "Lifestyle-Medical-Science-Tech ", "Lifestyle-Medical-Science-Tech-")
    new_basename = case_insensitive_replace(new_basename, "Movie ", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Mystery ", "Movie-Mystery-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Sci-Fi ", "Movie-Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Sci-Fi-Thriller ", "Movie-Sci-Fi-Thriller-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Sci-Fi-Western ", "Movie-Sci-Fi-Western-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Thriller ", "Movie-Thriller-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Western ", "Movie-Western-")
    new_basename = case_insensitive_replace(new_basename, "Sci-Fi ", "Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Travel ", "Travel-")

    new_basename = case_insensitive_replace(new_basename, "-44_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_44_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "-SBS_ONE_HD", "")
    new_basename = case_insensitive_replace(new_basename, "_SBS_ONE_HD", "")
    new_basename = case_insensitive_replace(new_basename, "-SBS_VICELAND_HD", "")
    new_basename = case_insensitive_replace(new_basename, "_SBS_VICELAND_HD", "")
    new_basename = case_insensitive_replace(new_basename, "-SBS_World_Movies", "")
    new_basename = case_insensitive_replace(new_basename, "_SBS_World_Movies", "")
    new_basename = case_insensitive_replace(new_basename, "-ABC_HD", "")
    new_basename = case_insensitive_replace(new_basename, "_ABC_HD", "")
    new_basename = case_insensitive_replace(new_basename, "-ABC_ME", "")
    new_basename = case_insensitive_replace(new_basename, "_ABC_ME", "")
    new_basename = case_insensitive_replace(new_basename, "-ABCKids-Kids", "")
    new_basename = case_insensitive_replace(new_basename, "_ABCKids-Kids", "")
    new_basename = case_insensitive_replace(new_basename, "-ABC-Kids", "")
    new_basename = case_insensitive_replace(new_basename, "_ABC-Kids", "")
    new_basename = case_insensitive_replace(new_basename, "-ABCKids", "")
    new_basename = case_insensitive_replace(new_basename, "_ABCKids", "")
    new_basename = case_insensitive_replace(new_basename, "-ABCComedy-Kids", "")
    new_basename = case_insensitive_replace(new_basename, "_ABCComedy-Kids", "")
    new_basename = case_insensitive_replace(new_basename, "-ABC_COMEDY", "")
    new_basename = case_insensitive_replace(new_basename, "_ABC_COMEDY", "")
    new_basename = case_insensitive_replace(new_basename, "-ABC_NEWS", "")
    new_basename = case_insensitive_replace(new_basename, "_ABC_NEWS", "")
    new_basename = case_insensitive_replace(new_basename, "-9Gem_HD_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_9Gem_HD_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "-9Gem", "")
    new_basename = case_insensitive_replace(new_basename, "_9Gem", "")
    new_basename = case_insensitive_replace(new_basename, "-9HD_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_9HD_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "-9HD", "")
    new_basename = case_insensitive_replace(new_basename, "_9HD", "")
    new_basename = case_insensitive_replace(new_basename, "-9Go-", "")
    new_basename = case_insensitive_replace(new_basename, "_9Go-", "")
    new_basename = case_insensitive_replace(new_basename, "-9Life", "")
    new_basename = case_insensitive_replace(new_basename, "_9Life", "")
    new_basename = case_insensitive_replace(new_basename, "-9Rush Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_9Rush Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "-9Rush", "")
    new_basename = case_insensitive_replace(new_basename, "_9Rush", "")
    new_basename = case_insensitive_replace(new_basename, "-10_HD_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_10_HD_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "-10_HD", "")
    new_basename = case_insensitive_replace(new_basename, "_10_HD", "")
    new_basename = case_insensitive_replace(new_basename, "-10_BOLD", "")
    new_basename = case_insensitive_replace(new_basename, "_10_BOLD", "")
    new_basename = case_insensitive_replace(new_basename, "-10_Peach", "")
    new_basename = case_insensitive_replace(new_basename, "_10_Peach", "")
    new_basename = case_insensitive_replace(new_basename, "-TEN_HD", "")
    new_basename = case_insensitive_replace(new_basename, "_TEN_HD", "")
    new_basename = case_insensitive_replace(new_basename, "-7TWO_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_7TWO_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "-7flix_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_7flix_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "-7HD_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_7HD_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "-7HD", "")
    new_basename = case_insensitive_replace(new_basename, "_7HD", "")
    new_basename = case_insensitive_replace(new_basename, "-7mate_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_7mate_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "-7mateHD", "")
    new_basename = case_insensitive_replace(new_basename, "_7mateHD", "")
    new_basename = case_insensitive_replace(new_basename, "-NITV", "")
    new_basename = case_insensitive_replace(new_basename, "_NITV", "")
    new_basename = case_insensitive_replace(new_basename, "-HD_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_HD_Adelaide", "")
    new_basename = case_insensitive_replace(new_basename, "_Adelaide.", ".")

    new_basename = case_insensitive_replace(new_basename, "Movie-Movie", "Movie")
    new_basename = case_insensitive_replace(new_basename, "Sci-Fi Movie", "Sci-Fi-Movie")
    new_basename = case_insensitive_replace(new_basename, "Movie-Sci-Fi-Movie", "Movie-Sci-Fi")
    new_basename = case_insensitive_replace(new_basename, "Movie-Thriller-Movie", "Movie-Thriller")
    new_basename = case_insensitive_replace(new_basename, "Western-Movie", "Western")
    new_basename = case_insensitive_replace(new_basename, "Western Movie", "Western")
    new_basename = case_insensitive_replace(new_basename, "Romance-Movie", "Romance")
    new_basename = case_insensitive_replace(new_basename, "Romance Movie", "Romance")
    new_basename = case_insensitive_replace(new_basename, "Thriller-Movie", "Thriller")
    new_basename = case_insensitive_replace(new_basename, "Thriller Movie", "Thriller")

    new_basename = case_insensitive_replace(new_basename, "-Movie Movie-", "-Movie-")
    new_basename = case_insensitive_replace(new_basename, "-Movie_Movie-", "-Movie-")
    new_basename = case_insensitive_replace(new_basename, "-Movie-Movie-", "-Movie-")
    new_basename = case_insensitive_replace(new_basename, "-Movie- ", "-Movie-")

    new_basename = case_insensitive_replace(new_basename, "Agatha_Christie-s_Poirot_", "Agatha_Christie-s_Poirot-")
    new_basename = case_insensitive_replace(new_basename, "Murder-Mystery_Agatha_Christie-s_Poirot_", "Agatha_Christie-s_Poirot-")
    new_basename = case_insensitive_replace(new_basename, "Murder-Mystery_Agatha_Christie-s_Poirot-", "Agatha_Christie-s_Poirot-")
    new_basename = case_insensitive_replace(new_basename, "Back_Roads_", "Back_Roads-")
    new_basename = case_insensitive_replace(new_basename, "Catalyst_", "Catalyst-")
    new_basename = case_insensitive_replace(new_basename, "Tech_Catalyst_", "Catalyst-")
    new_basename = case_insensitive_replace(new_basename, "Tech_Catalyst-", "Catalyst-")
    new_basename = case_insensitive_replace(new_basename, "Berlin_Station_", "Berlin_Station-")
    new_basename = case_insensitive_replace(new_basename, "Foyle-s_War_", "Foyle-s_War-")
    new_basename = case_insensitive_replace(new_basename, "Killing_Eve_", "Killing_Eve-")
    new_basename = case_insensitive_replace(new_basename, "Medici-Masters_Of_Florence_", "Medici-Masters_Of_Florence-")
    new_basename = case_insensitive_replace(new_basename, "Mistresses_", "Mistresses-")
    new_basename = case_insensitive_replace(new_basename, "Orphan_Black_", "Orphan_Black-")
    new_basename = case_insensitive_replace(new_basename, "Plebs_", "Plebs-")
    new_basename = case_insensitive_replace(new_basename, "Pope-The_Most_Powerful_Man_In_History_", "Pope-The_Most_Powerful_Man_In_History-")
    new_basename = case_insensitive_replace(new_basename, "Scandal_", "Scandal-")
    new_basename = case_insensitive_replace(new_basename, "Star_Trek_", "Star_Trek-")
    new_basename = case_insensitive_replace(new_basename, "The.Expanse_", "The.Expanse-")
    new_basename = case_insensitive_replace(new_basename, "The_Expanse_", "The_Expanse-")
    new_basename = case_insensitive_replace(new_basename, "The_Girlfriend_Experience_", "The_Girlfriend_Experience-")
    new_basename = case_insensitive_replace(new_basename, "The_Inspector_Lynley_Mysteries_", "The_Inspector_Lynley_Mysteries-")
    new_basename = case_insensitive_replace(new_basename, "The_IT_Crowd_", "The_IT_Crowd-")
    new_basename = case_insensitive_replace(new_basename, "the.it.crowd.", "The_IT_Crowd-")
    new_basename = case_insensitive_replace(new_basename, "The_Young_Pope_", "The_Young_Pope-")
    new_basename = case_insensitive_replace(new_basename, "The_Two_Ronnies_", "The_Two_Ronnies-")
    new_basename = case_insensitive_replace(new_basename, "The_Games_", "The_Games-")
    new_basename = case_insensitive_replace(new_basename, "Utopia_", "Utopia-")
    new_basename = case_insensitive_replace(new_basename, "The_X-Files_", "The_X-Files-")

    if "-Movie-".lower() in new_basename.lower():
        new_basename = "Movie-" + case_insensitive_replace(new_basename, "-Movie-", "-") # Move "Movie" to the front of the string

    new_basename = case_insensitive_replace(new_basename, "Adventure-Nature_", "")
    new_basename = case_insensitive_replace(new_basename, "Action-Adventure-Comedy-", "")
    new_basename = case_insensitive_replace(new_basename, "Action-Adventure-Drama_", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Documentary-Travel_", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Documentary-Travel-", "")
    new_basename = case_insensitive_replace(new_basename, "Action-Drama-Sci-Fi_", "")
    new_basename = case_insensitive_replace(new_basename, "Action-Drama_", "")
    new_basename = case_insensitive_replace(new_basename, "Adult-Crime-Drama-Society-Culture-", "")
    new_basename = case_insensitive_replace(new_basename, "Adult-Documentary-Real_Life-Society-Culture-", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Cult-Sci-Fi_", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Documentary-Drama-Sci-Fi-Science-", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Entertainment-Travel-", "")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Documentary-Historical-Nature-Society-Culture-Travel-", "")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Documentary-Historical-Society-Culture-", "")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Entertainment-", "")
    new_basename = case_insensitive_replace(new_basename, "Biography-Documentary-Historical-", "")
    new_basename = case_insensitive_replace(new_basename, "Children-", "")
    new_basename = case_insensitive_replace(new_basename, "Comedy-", "")
    new_basename = case_insensitive_replace(new_basename, "Comedy_", "")
    new_basename = case_insensitive_replace(new_basename, "Cooking-", "")
    new_basename = case_insensitive_replace(new_basename, "Crime-Documentary-Historical-Mini_Series-Religion-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Crime-Documentary-Historical-Mini_Series-Religion-Society-Culture-", "")
    new_basename = case_insensitive_replace(new_basename, "Crime-Drama-Murder-Mystery-", "")
    new_basename = case_insensitive_replace(new_basename, "Crime-Drama-Mystery-", "")
    new_basename = case_insensitive_replace(new_basename, "Crime-Drama-Thriller_", "")
    new_basename = case_insensitive_replace(new_basename, "Crime-Drama-", "")
    new_basename = case_insensitive_replace(new_basename, "Crime-Drama_", "")
    new_basename = case_insensitive_replace(new_basename, "Crime-Mystery_", "")
    new_basename = case_insensitive_replace(new_basename, "Crime_", "")
    new_basename = case_insensitive_replace(new_basename, "Current-Affairs-Documentary_", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Entertainment-Historical-Travel-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Entertainment-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Historical-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Historical-Mystery-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Historical-Religion-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Historical-Science-Tech-Society-Culture-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Historical-Travel_", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Historical-War-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Infotainment-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Medical-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Nature-Society-Culture-Travel-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Nature-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Real_Life-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Science-Tech-Society-Culture-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Science-Tech-Travel-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Science-Tech_", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Science-", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-Travel_", "")
    new_basename = case_insensitive_replace(new_basename, "Documentary-", "")
    new_basename = case_insensitive_replace(new_basename, "Drama-Murder-Mystery-", "")
    new_basename = case_insensitive_replace(new_basename, "Drama-Historical-Mystery-Sci-Fi-Thriller_", "")
    new_basename = case_insensitive_replace(new_basename, "Drama-Historical-", "")
    new_basename = case_insensitive_replace(new_basename, "Drama-Mystery-Sci-Fi-", "")
    new_basename = case_insensitive_replace(new_basename, "Drama-Mystery-", "")
    new_basename = case_insensitive_replace(new_basename, "Drama-Romance-Sci-Fi-", "")
    new_basename = case_insensitive_replace(new_basename, "Drama-Romance_", "")
    new_basename = case_insensitive_replace(new_basename, "Drama-Sci-Fi-Thriller_", "")
    new_basename = case_insensitive_replace(new_basename, "Drama-Thriller-", "")
    new_basename = case_insensitive_replace(new_basename, "Drama-", "")
    new_basename = case_insensitive_replace(new_basename, "Drama_", "")
    new_basename = case_insensitive_replace(new_basename, "Education-Science-Tech-", "")
    new_basename = case_insensitive_replace(new_basename, "Education-Science-", "")
    new_basename = case_insensitive_replace(new_basename, "Education-Science_", "")
    new_basename = case_insensitive_replace(new_basename, "Entertainment-", "")
    new_basename = case_insensitive_replace(new_basename, "Family_Movie-", "")
    new_basename = case_insensitive_replace(new_basename, "Historical-Travel-", "")
    new_basename = case_insensitive_replace(new_basename, "Historical-Travel_", "")
    new_basename = case_insensitive_replace(new_basename, "Historical-Infotainment-Lifestyle-Real_Life-Society-Culture-", "")
    new_basename = case_insensitive_replace(new_basename, "Historical-Infotainment-Lifestyle-Real_Life-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Lifestyle-Medical-Science-Tech-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Animation-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Comedy-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Comedy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Crime-Drama-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Crime-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Drama-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Drama-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Family-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Fantasy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Historical-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Mystery-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Adventure-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Comedy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Crime-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Drama-Historical-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Drama-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Drama-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Drama-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Drama-Western-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Fantasy-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Fantasy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Horror-Sci-Fi-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Sci-Fi-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Action-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Animation-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Biography-Drama-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Children-Family-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Comedy-Drama-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Comedy-Drama-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Drama-Fantasy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Drama-Historical-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Drama-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Family-Fantasy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Fantasy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Adventure-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Animation-Children-Comedy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Animation-Comedy-Family-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Animation-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Arts-Culture-Biography-Drama-Historical-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Arts-Culture-Drama-War_Movie-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Arts-Culture-Drama-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Biography-Comedy-Drama-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Biography-Documentary-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Biography-Drama-Historical-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Biography-Drama-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Biography-Drama-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Biography-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Children-Family-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Crime-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Dance-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-Family-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-Fantasy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-Fantasy-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-Fantasy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-Historical-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-Music-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-Musical-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-Music_Movie-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Drama-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Family-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Family-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Fantasy-Musical-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Fantasy-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Historical-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Horror-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Horror-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Music_Movie-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-War_Movie-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-War-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Comedy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Crime-Drama-Fantasy-Horror-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Crime-Drama-Mystery_Movie-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Crime-Drama-Mystery-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Crime-Mystery-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Crime-Mystery_Movie-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Crime-Romance-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Crime-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Historical-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Horror-Mystery-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Horror-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Music-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Mystery-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Mystery-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Mystery-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Sci-Fi-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-Violence-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-War_Movie-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Drama-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Family-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Family-Fantasy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Family-Musical-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Fantasy-Horror-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Fantasy-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Fantasy-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Horror-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Horror-Mystery-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Horror-Mystery-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Horror-Sci-Fi-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Horror-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Horror-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Horror-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Musical-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Musical-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Music_Movie-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Mystery-Sci-Fi-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Mystery-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Romance-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Romance-Western-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Sci-Fi-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Sci-Fi-Western-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Sci-Fi-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Thriller-", "Movie-")
    new_basename = case_insensitive_replace(new_basename, "Movie-Western-", "Movie-")

    new_basename = case_insensitive_replace(new_basename, "Extreme_Railways_Journeys_", "Extreme_Railways_Journeys-")
    new_basename = case_insensitive_replace(new_basename, "Great_British_Railway_Journeys_", "Great_British_Railway_Journeys-")
    new_basename = case_insensitive_replace(new_basename, "Great_American_Railroad_Journeys_", "Great_American_Railroad_Journeys-")
    new_basename = case_insensitive_replace(new_basename, "Great_Continental_Railway_Journeys_", "Great_Continental_Railway_Journeys-")
    new_basename = case_insensitive_replace(new_basename, "Great_Indian_Railway_Journeys_", "Great_Indian_Railway_Journeys-")
    new_basename = case_insensitive_replace(new_basename, "Tony_Robinson-s_World_By_Rail_", "Tony_Robinson-s_World_By_Rail-")
    new_basename = case_insensitive_replace(new_basename, "Railways_That_Built_Britain_", "Railways_That_Built_Britain-")

    # On second thought, replace Movie at the start with nothing ...
    new_basename = case_insensitive_replace(new_basename, "Movie-", "")

    new_basename = case_insensitive_replace(new_basename, "Action-Drama-Mini_Series-Sci-Fi-", "Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Action-Drama-Mini_Series-Sci-Fi_", "Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Sci-Fi-", "Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Sci-Fi_", "Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Sci-Fi_", "Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Adult-Documentary-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Adult-Documentary-Society-Culture-", "")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Biography-Historical_", "")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Documentary_", "")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Entertainment_", "")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-Biography-Romance-", "")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-War_", "")
    new_basename = case_insensitive_replace(new_basename, "Arts-Culture-", "")
    new_basename = case_insensitive_replace(new_basename, "Biography-Cult-Religion-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Biography-Documentary_", "")
    new_basename = case_insensitive_replace(new_basename, "Biography-Historical_", "")
    new_basename = case_insensitive_replace(new_basename, "Biography-Mini_Series_", "")
    new_basename = case_insensitive_replace(new_basename, "Biography-Tech_", "")
    new_basename = case_insensitive_replace(new_basename, "Biography-", "")
    new_basename = case_insensitive_replace(new_basename, "Entertainment_", "")
    new_basename = case_insensitive_replace(new_basename, "Family-Fantasy_", "")
    new_basename = case_insensitive_replace(new_basename, "Family-Fantasy-", "")
    new_basename = case_insensitive_replace(new_basename, "Food-Wine-Lifestyle-Science_", "")
    new_basename = case_insensitive_replace(new_basename, "Food-Wine-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Historical-", "")
    new_basename = case_insensitive_replace(new_basename, "Historical_", "")
    new_basename = case_insensitive_replace(new_basename, "Historical-Mini_Series-Science-Tech_", "")
    new_basename = case_insensitive_replace(new_basename, "Horror-Mystery-Thriller_", "")
    new_basename = case_insensitive_replace(new_basename, "Infotainment-Real-Life_", "")
    new_basename = case_insensitive_replace(new_basename, "Infotainment-", "")
    new_basename = case_insensitive_replace(new_basename, "Infotainment_", "")
    new_basename = case_insensitive_replace(new_basename, "Lifestyle-", "")
    new_basename = case_insensitive_replace(new_basename, "Lifestyle_", "")
    new_basename = case_insensitive_replace(new_basename, "Lifestyle-Science-Tech_", "")
    new_basename = case_insensitive_replace(new_basename, "Lifestyle-Travel_", "")
    new_basename = case_insensitive_replace(new_basename, "Medical_", "")
    new_basename = case_insensitive_replace(new_basename, "Mini_Series-Thriller_", "")
    new_basename = case_insensitive_replace(new_basename, "Mini_Series-War", "")
    new_basename = case_insensitive_replace(new_basename, "Mini-Series-Science-Tech-Society-Culture-Travel_", "")
    new_basename = case_insensitive_replace(new_basename, "Mini-Series-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Murder-Mystery-", "")
    new_basename = case_insensitive_replace(new_basename, "Murder-Mystery_", "")
    new_basename = case_insensitive_replace(new_basename, "Music-Romance_Movie-", "")
    new_basename = case_insensitive_replace(new_basename, "Music-Romance_Movie_", "")
    new_basename = case_insensitive_replace(new_basename, "Mystery-", "")
    new_basename = case_insensitive_replace(new_basename, "Mystery_", "")
    new_basename = case_insensitive_replace(new_basename, "Nature-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Nature_", "")
    new_basename = case_insensitive_replace(new_basename, "News-Science-Tech-", "")
    new_basename = case_insensitive_replace(new_basename, "News-Science-Tech_", "")
    new_basename = case_insensitive_replace(new_basename, "News_", "")
    new_basename = case_insensitive_replace(new_basename, "Real_Life-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Real_Life-Travel_", "")
    new_basename = case_insensitive_replace(new_basename, "Real_Life_", "")
    new_basename = case_insensitive_replace(new_basename, "Religion-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Religion-Thriller-", "")
    new_basename = case_insensitive_replace(new_basename, "Religion_", "")
    new_basename = case_insensitive_replace(new_basename, "Romance-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Romance_", "")
    new_basename = case_insensitive_replace(new_basename, "Romance-", "")
    new_basename = case_insensitive_replace(new_basename, "Science-Tech_", "")
    new_basename = case_insensitive_replace(new_basename, "Science-Tech-", "")
    new_basename = case_insensitive_replace(new_basename, "Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Society-Culture-", "")
    new_basename = case_insensitive_replace(new_basename, "Science-Tech-Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Science-Tech-Special_", "")
    new_basename = case_insensitive_replace(new_basename, "Science-Tech_", "")
    new_basename = case_insensitive_replace(new_basename, "Science_", "")
    new_basename = case_insensitive_replace(new_basename, "Sci-Fi-Thriller_", "Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Action-Sci-Fi_", "Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Sci-Fi-", "Sci-Fi-")
    new_basename = case_insensitive_replace(new_basename, "Sci-Fi-", "")
    new_basename = case_insensitive_replace(new_basename, "Sci-Fi_", "")
    new_basename = case_insensitive_replace(new_basename, "Society-Culture_", "")
    new_basename = case_insensitive_replace(new_basename, "Thriller-", "")
    new_basename = case_insensitive_replace(new_basename, "Thriller_", "")
    new_basename = case_insensitive_replace(new_basename, "Tech-Travel_", "")
    new_basename = case_insensitive_replace(new_basename, "Tech-Travel-", "")
    new_basename = case_insensitive_replace(new_basename, "Travel_", "")
    new_basename = case_insensitive_replace(new_basename, "Travel-", "")
    new_basename = case_insensitive_replace(new_basename, "Agatha_Christie_", "Agatha_Christie_")
    new_basename = case_insensitive_replace(new_basename, "Agatha_Christie-", "Agatha_Christie_")
    new_basename = case_insensitive_replace(new_basename, "Agatha-Christie_", "Agatha_Christie_")
    new_basename = case_insensitive_replace(new_basename, "Agatha-Christie-", "Agatha_Christie_")
    new_basename = case_insensitive_replace(new_basename, "Agatha_Christie_s_", "")
    new_basename = case_insensitive_replace(new_basename, "Agatha_Christie_s-", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure_Documentary_Nature_", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure_Documentary-Nature_", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Documentary_Nature_", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Documentary_Nature_", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure_Documentary_Nature-", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure_Documentary-Nature-", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Documentary_Nature-", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Documentary_Nature-", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure_Lifestyle_", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure_Lifestyle-", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Lifestyle_", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-Lifestyle-", "")
    new_basename = case_insensitive_replace(new_basename, "Adventure-", "")
    
    new_basename = case_insensitive_replace(new_basename, "Crime_Mystery_", "")
    new_basename = case_insensitive_replace(new_basename, "Crime_Mystery-", "")
    new_basename = case_insensitive_replace(new_basename, "Crime-Mystery_", "")
    new_basename = case_insensitive_replace(new_basename, "Crime-Mystery-", "")


    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "Crime_", "")
    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "Crime-", "")

    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "Chris_Tarrant-s_", "")
    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "Chris_Tarrant-s-", "")

    new_basename = case_insensitive_replace(new_basename, "Chris_Tarrant-", "")
    new_basename = case_insensitive_replace(new_basename, "Chris_Tarrant_", "")
    new_basename = case_insensitive_replace(new_basename, "Chris-Tarrant_", "")
    new_basename = case_insensitive_replace(new_basename, "Chris-Tarrant-", "")

    new_basename = case_insensitive_replace(new_basename, ".h264.", ".")
    new_basename = case_insensitive_replace(new_basename, ".h265.", ".")
    new_basename = case_insensitive_replace(new_basename, ".aac.", ".")
    
    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "-", "")
    new_basename = case_insensitive_replace_at_start_of_string(new_basename, "_", "")
    
    # FINALLY replace some stuff in filenames with underscores
    new_basename = case_insensitive_replace(new_basename, " ", "_")
    new_basename = case_insensitive_replace(new_basename, "[", "_")
    new_basename = case_insensitive_replace(new_basename, "]", "_")
    new_basename = case_insensitive_replace(new_basename, "(", "_")
    new_basename = case_insensitive_replace(new_basename, ")", "_")
    new_basename = case_insensitive_replace(new_basename, "'", "_")
    new_basename = case_insensitive_replace(new_basename, "$", "_")
    return new_basename

def fix_xml_document_content_inside_bprj(file_path, old_basename, new_basename):
    print(f"Error occurred while fixing XML document content in '{file_path}': Error number: {e.errno}, Error message: {e}")
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        # Locate the desired node using XPath
        filename_node = root.find(".//Filename")
        if filename_node is None:
            print("Aborted. Could not find XML node //Filename in file", file_path)
            return False
        txtbefore = filename_node.text
        # Replace the old basename with the new basename
        txtafter = txtbefore.replace(old_basename, new_basename)
        # Update the text of the Filename node
        filename_node.text = txtafter
        print("Update xml node before:", txtbefore)
        print("                after:", filename_node.text)
        # Save the updated XML back to the file
        tree.write(file_path)
        return True
    except Exception as e:
        print(f"Error occurred while fixing XML document content in '{file_path}': Error number: {e.errno}, Error message: {e}")
        return False
    return True

def rename_to_adjusted_filename(old_full_filename, old_filename_without_extension, new_filename_without_extension, new_filename_with_extension, new_full_filename, old_file_extension):
    base_new_filename_without_extension = new_filename_without_extension
    error_number = -1
    rename_retry_count = 0
    while (error_number != 0) and (rename_retry_count < 90):
        try:
            if rename_retry_count > 0:
                print(f"Rename retry #{rename_retry_count}: Renaming: '{old_full_filename}' to '{new_full_filename}")
            os.rename(old_full_filename, new_full_filename)
        except Exception as e:
            error_number = e.errno
            if error_number is None:
                error_number = 17   # Error number for "File exists"
            #print(f"Error occurred while renaming the file: Error number: {e.errno}, Error message: {e}")
            rename_retry_count = rename_retry_count + 1
            new_filename_without_extension = base_new_filename_without_extension + "_" + str(rename_retry_count).zfill(2)
            new_filename_with_extension = new_filename_without_extension + old_file_extension
            new_full_filename = os.path.join(os.path.dirname(old_full_filename), new_filename_with_extension)
        else:
            error_number = 0
            #print("File renamed successfully.")
    if error_number != 0:
        print(f"GAVE UP ATTEMPTING RENAME after {rename_retry_count} retries, leaving '{old_full_filename}' alone.")
        return None, None, None
    #
    # After the rename, process the .bprj xml document so it's content likely matches the matching media file's new filename ... 
    #
    if old_file_extension.lower() == ".bprj".lower():
        result = fix_xml_document_content_inside_bprj(new_filename_with_extension)
        if result:
            print(f"Fixed .bprj XML document content in '{new_filename_with_extension}'")
        else:
            print(f"WARNING: continuing after failed to fix .bprj XML document content in '{new_filename_with_extension}'")
    return new_filename_without_extension, new_filename_with_extension, new_full_filename

if __name__ == "__main__":
    TERMINAL_WIDTH = 250
    objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)    # facilitates formatting 

    root_folder_names = [
        'ROOTFOLDER1',
        'ROOTFOLDER2',
        'ROOTFOLDER3',
        'ROOTFOLDER4',
        'ROOTFOLDER5',
        'ROOTFOLDER6',
        'ROOTFOLDER7',
        'ROOTFOLDER8',
    ]
    disks, disks_info = get_disks_with_root_folders_and_labels(root_folder_names)

    print(f"Disks: \n{objPrettyPrint.pformat(disks)}")
    print(f"Disks Info:\n{objPrettyPrint.pformat(disks_info)}")

    # Define the list of media folders, exclude those where we do not want to reformat the filenames (ie .jpg files et al)
    media_folders = [
        #"2015.11.29-Jess-21st-birthday-party",
        "BigIdeas", 
        "CharlieWalsh",
        "ClassicDocumentaries", 
        "ClassicMovies",
        "Documentaries",
        #"Family_Photos",
        "Footy",
        #"HomePics",
        "Movies",
        "Movies_unsorted", 
        "Music",
        "MusicVideos",
        "OldMovies",
        "SciFi",
        "Series"
    ]
    recurse = True
    file_suffixes = ('.ts', '.mp4', '.mpeg4', '.mpg', '.mpeg', '.vob')

    print(f"\n\nSTARTED Rename Fix Filenames by removing special characters and adjusting titles and moving date in every {file_suffixes} in {disks}")

    #perform_action = False
    perform_action = True

    for d, r in disks.items():
        folder = d + r
        print(f"Starting Folder='{folder}' Recurse={recurse} Valid suffixes='{file_suffixes}'")
        file_list = []
        if recurse:
            print(f"***** Gathering filenames with RECURSE for '{folder}'")
            for root, dirs, files in os.walk(folder):
                # check if root.lower() starts with folder.lower() joined with any of media_folders.lower()
                if any(root.lower().startswith(os.path.join(folder, mf).lower()) for mf in media_folders):
                    print(f"Recurse walk valid Folder='{root}'")
                    for file in files:
                        if any(file.lower().endswith(suffix.lower()) for suffix in file_suffixes):
                            file_list.append(os.path.join(root, file))
                else:
                    print(f"IGNORED folder '{root}' since it did not start with '{folder}' plus any subfolder in {media_folders}")
        else:
            # check if root.lower() contains one of the items in the list media_folders.lower() and only process if it does
            if any(mf.lower() in folder.lower() for mf in media_folders):
                print(f"***** Gathering filenames WITHOUT RECURSE for valid Folder '{folder}'")
                for file in os.listdir(folder):
                    if os.path.isfile(os.path.join(folder, file)) and any(file.lower().endswith(suffix.lower()) for suffix in file_suffixes):
                        file_list.append(os.path.join(folder, file))
        for old_full_filename in file_list:
            old_filename_without_extension = Path(old_full_filename).stem
            old_file_extension = Path(old_full_filename).suffix
            new_filename_without_extension = old_filename_without_extension
            #
            new_filename_without_extension = remove_duplicate_dashes_dots_from_i4670_filename(new_filename_without_extension)
            new_filename_without_extension = remove_special_characters(new_filename_without_extension)
            new_filename_without_extension = recognize_and_move_date_string_to_end(new_filename_without_extension)
            new_filename_without_extension = change_filename_layout(new_filename_without_extension)
            #
            new_filename_with_extension = new_filename_without_extension + old_file_extension
            new_full_filename = os.path.join(os.path.dirname(old_full_filename), new_filename_with_extension)
            if old_filename_without_extension != new_filename_without_extension:
                if perform_action:
                    print(f"Renaming: '{old_full_filename}' to '{new_full_filename}'")
                    new_filename_without_extension, new_filename_with_extension, new_full_filename = rename_to_adjusted_filename(old_full_filename, old_filename_without_extension, new_filename_without_extension, new_filename_with_extension, new_full_filename, old_file_extension)
                    pass
                else:
                    print(f"(perform_action={perform_action}) WOULD HAVE Renamed: '{old_full_filename}' to '{new_full_filename}'")
                    pass
            else:
                print(f"Left alone: '{old_full_filename}'")
                pass
        print(f"Finished Rename Fix Filenames by removing special characters and adjusting titles and moving date in every {file_suffixes} {folder}\n\n")
    print(f"Finished Rename Fix Filenames entirely.")
