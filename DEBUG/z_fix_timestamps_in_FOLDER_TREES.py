import os
import re
import ctypes
from ctypes import wintypes
from datetime import datetime
import pytz
from typing import List

def set_file_timestamps(folder: str, suffixes: List[str], recurse: bool = True, perform_action: bool = True):
    TERMINAL_WIDTH = 250
    print(f"\n\nSTARTED Set file date-time timestamps")
    print(f"Incoming Folder='{folder}'")
    print(f"Recurse: {recurse}")
    print(f"Valid suffixes: {suffixes}")
    
    file_list = []
    folder = folder.rstrip("\\").rstrip(" ")
    
    if "*" in suffixes:
        suffixes = [""]  # Match all files if "*" is in suffixes

    if recurse:
        print(f"Gathering filenames with RECURSE for '{folder}'")
        for root, _, files in os.walk(folder):
            for file in files:
                if any(file.lower().endswith(suffix.lower()) for suffix in suffixes):
                    file_list.append(os.path.join(root, file))
    else:
        print(f"Gathering filenames without RECURSE for '{folder}'")
        for file in os.listdir(folder):
            if os.path.isfile(os.path.join(folder, file)) and any(file.lower().endswith(suffix.lower()) for suffix in suffixes):
                file_list.append(os.path.join(folder, file))
    
    print(f"STARTING Set file date-time timestamps in every {suffixes} filename by Matching them with a regex match in Python ...")
    # Regex pattern for extracting date string from filename
    date_pattern = r'\b\d{4}-\d{2}-\d{2}\b'
    # Get the local timezone
    local_tz = pytz.timezone('Australia/Adelaide')  # Set your local timezone    # Note: local_tz = get_localzone()  # Get the local timezone dynamically fails later
    for old_full_filename in file_list:
        filename = os.path.basename(old_full_filename)
        # Look for a properly formatted date string in the filename
        match = re.search(date_pattern, filename)
        if match:
            date_string = match.group()
            date_from_file = datetime.strptime(date_string, "%Y-%m-%d")   # Convert to datetime object
            date_from_file = local_tz.localize(date_from_file).replace(hour=0, minute=0, second=0, microsecond=0)   # Replace time portion with 00:00:00.00 in local timezone
            fs = "date from filename"
            #print(f"DEBUG: +++ date pattern match found in filename: {date_from_file} {old_full_filename}")
        else:
            creation_time = os.path.getctime(old_full_filename)
            date_from_file = datetime.fromtimestamp(creation_time)
            date_from_file = local_tz.localize(date_from_file).replace(hour=0, minute=0, second=0, microsecond=0)   # Replace time portion with 00:00:00.00 in local timezone
            fs = "creation date of file"
            #print(f"DEBUG: --- date pattern match NOT found in filename, using creation date of the file instead: {date_from_file} {old_full_filename}")
        if perform_action:
            # Python cannot set creation time using os.utime, so use Windows API to set both creation and modification times
            datetime_1601 = datetime(1601, 1, 1, tzinfo=pytz.utc)
            time_difference = (date_from_file - datetime_1601).total_seconds()   # Calculate time difference in seconds
            time_windows = int(time_difference * 10**7)   # Convert time difference to FILETIME format
            handle = ctypes.windll.kernel32.CreateFileW(old_full_filename, wintypes.DWORD(256), 0, None, wintypes.DWORD(3), 0, None)
            # Change BOTH creation and modification times
            ctypes.windll.kernel32.SetFileTime(handle, ctypes.byref(ctypes.c_ulonglong(time_windows)), None, ctypes.byref(ctypes.c_ulonglong(time_windows)))
            ctypes.windll.kernel32.CloseHandle(handle)
            print(f"Set {fs} '{date_from_file}' into creation-date and modification-date on '{old_full_filename}'")
        else:
            print(f"Would set {fs} '{date_from_file}' into creation-date and modification-date on '{old_full_filename}'")

    print(f"FINISHED Set file date-time timestamps in every {suffixes} filename by Matching them with a regex match in Python ...\n\n")

if __name__ == "__main__":
    disks = {
        "X:": r"\ROOTFOLDER1",
        "V:": r"\ROOTFOLDER2",
        "F:": r"\ROOTFOLDER3",
        "H:": r"\ROOTFOLDER4",
        "K:": r"\ROOTFOLDER5",
        "W:": r"\ROOTFOLDER6"
    }

    #file_suffixes = ['.ts', '.mp4', '.mpeg4', '.mpg', '.mpeg', '.vob', 'jpg', '.jpeg', '.avi', '.bprj']  # Add '*' if you want to match all files
    file_suffixes = ['*']

    for d, r in disks.items():
        root = d + r
        set_file_timestamps(root, file_suffixes, recurse=True, perform_action=True)
