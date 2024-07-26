import os
import sys
import shutil
import pprint
import datetime

def get_disks_with_root_folders_and_labels(root_folder_names):
    import os
    import psutil
    import ctypes
    from ctypes import wintypes
    import traceback
    import time
    # Initialize empty dictionaries to store the disk information
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
    disks_and_root_folders = {}
    disks_info = {}
    disk_partitions_drive_letters = [partition.device.rstrip("\\") for partition in psutil.disk_partitions()]

    #print(f"DEBUG: start finding psutil.disk_partitions() drive letter, using for partition in psutil.disk_partitions():")
    for partition in psutil.disk_partitions():
        drive_letter = partition.device.rstrip("\\")
        ####disk_partitions_drive_letters.append(drive_letter) #### removed by changes
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
            top_level_dirs = [d for d in os.listdir(drive_letter + '\\') if os.path.isdir(os.path.join(drive_letter + '\\', d))]
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

# Function to count files and calculate their total size in a given folder
def count_files_size_and_latest_modification(folder_path):
    file_count = 0
    total_size = 0
    latest_modification = None
    for root, dirs, files in os.walk(folder_path):
        file_count += len(files)
        total_size += sum(os.path.getsize(os.path.join(root, file)) for file in files)
        for file in files:
            file_path = os.path.join(root, file)
            mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
            if latest_modification is None or mod_time > latest_modification:
                latest_modification = mod_time
    return file_count, total_size / (1024 * 1024 * 1024), latest_modification    # Convert size to Gigabytes

if __name__ == "__main__":
    TERMINAL_WIDTH = 250
    objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)  # facilitates formatting

    print(f"Patience Please, this will take a while due to looking at the modification dates on all files ...", flush=True)

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

    # List of media folders
    media_folders = [
        "2015.11.29-Jess-21st-birthday-party",
        "BigIdeas",
        "CharlieWalsh",
        "ClassicDocumentaries",
        "ClassicMovies",
        "Documentaries",
        "Family_Photos",
        "Footy",
        "HomePics",
        "Movies",
        "Movies_unsorted",
        "Music",
        "MusicVideos",
        "OldMovies",
        "SciFi",
        "Series"
    ]

    # Initialize the result dictionary
    result = {folder: {disk: (0, 0, None) for disk in disks} for folder in media_folders}
    free_space = {}

    # Iterate over each disk and media folder to count files and calculate size
    for disk, root_folder in disks.items():
        for media_folder in media_folders:
            folder_path = os.path.join(disk, root_folder, media_folder)
            if os.path.exists(folder_path):
                result[media_folder][disk] = count_files_size_and_latest_modification(folder_path)
        # Get the free space for each disk
        total, used, free = shutil.disk_usage(disk)
        free_space[disk] = free / (1024 * 1024 * 1024)  # Convert size to Gigabytes

    #print(f"\n")
    #print(f"\ndisks: \n{objPrettyPrint.pformat(disks)}")
    #print(f"\ndisks_info:\n{objPrettyPrint.pformat(disks_info)}")
    #print(f"\nmedia_folders:\n{objPrettyPrint.pformat(media_folders)}")
    #print(f"\nresult:\n{objPrettyPrint.pformat(result)}")
    #print(f"\n")

    # Calculate the fixed column width based on the longest header and data values
    disk_headers = [f"{disk} ({root_folder})" for disk, root_folder in disks.items()]
    max_count_length = max(len(f"{count}") for folder in media_folders for disk in disks for count, _, _ in [result[folder][disk]])
    max_size_length = max(len(f"{size:.2f} GB") for folder in media_folders for disk in disks for _, size, _ in [result[folder][disk]])
    max_date_length = max(len(f"{date}") for folder in media_folders for disk in disks for _, _, date in [result[folder][disk]] if date)
    max_header_length = max(len(header) for header in disk_headers)
    column_width = max(30, max_count_length + max_size_length + 7, max_header_length + 2)  # Adjust width
    # Generate the cross-tabulation header
    header = "{:<45}".format("Folder_Name") + "".join(f"{disk} ({root_folder})".rjust(column_width) for disk, root_folder in disks.items())
    print(header)
    print("-" * len(header))
    # Generate the data rows
    for media_folder in media_folders:
        row = "{:<45}".format(media_folder)
        for disk in disks:
            file_count, total_size, latest_file_modification_date = result[media_folder][disk]
            row += f"{file_count:>{max_count_length}} / {total_size:>{max_size_length}.2f} GB".rjust(column_width)
        print(row)
        # Print the latest modification date underneath
        date_row = " " * 45
        for disk in disks:
            _, _, latest_file_modification_date = result[media_folder][disk]
            if latest_file_modification_date:
                date_str = latest_file_modification_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                date_str = "   "
            date_row += f"{date_str:>{column_width}}"
        print(date_row)
        # Print the dashed line after each result
        print("-" * len(header))
    # Add the free disk space row
    free_space_row = "{:<45}".format("Free Disk Space")
    for disk in disks:
        free_space_row += f"{free_space[disk]:>{max_size_length}.2f} GB".rjust(column_width)
    print(free_space_row)

    # ChatGPT extensions

    # (b) Create a new variable like 'disks_info' containing a list of media_folders only where a media folder under that root folder on that disk has a non-zero file count
    new_disks_info = {disk: {"root_folder": root_folder, "media_folders": []} for disk, root_folder in disks.items()}
    for media_folder in media_folders:
        for disk in disks:
            file_count, total_size, latest_file_modification_date = result[media_folder][disk]
            if file_count > 0:
                new_disks_info[disk]["media_folders"].append({
                    "media_folder": media_folder,
                    "file_count": file_count,
                    "used_space_gb": total_size,
                    "latest_file_modification_date": latest_file_modification_date
                })

    # (c) Create a new variable like 'media_folders' containing a list of disks only where that disk has the media folder under that root folder on that disk has a non-zero file count
    new_media_folders_info = {media_folder: {"disks": []} for media_folder in media_folders}
    for media_folder in media_folders:
        for disk in disks:
            file_count, total_size, latest_file_modification_date = result[media_folder][disk]
            if file_count > 0:
                new_media_folders_info[media_folder]["disks"].append({
                    "disk": disk,
                    "root_folder": disks[disk],
                    "file_count": file_count,
                    "used_space_gb": total_size,
                    "latest_file_modification_date": latest_file_modification_date
                })

    # (d) Print new variable from (b)
    #print("-" * len(header))
    #print("New Disks Info with Non-Zero Media Folders:", flush=True)
    #for disk, info in new_disks_info.items():
    #    print(f"Disk: {disk}, Root Folder: {info['root_folder']}")
    #    for folder_info in info["media_folders"]:
    #        print(f"  Media Folder: {folder_info['media_folder']}, File Count: {folder_info['file_count']}, Used Space: {folder_info['used_space_gb']:.2f} GB, Latest File Modification Date: {folder_info['latest_file_modification_date']}")
    #    print()
    print(f"\nNew_disks_info:\n{objPrettyPrint.pformat(new_disks_info)}")
    print(f"\n")

    # (e) Print new variable from (c)
    #print("-" * len(header))
    #print("New Media Folders Info with Non-Zero Disks:", flush=True)
    #for media_folder, info in new_media_folders_info.items():
    #    print(f"Media Folder: {media_folder}")
    #    for disk_info in info["disks"]:
    #        print(f"  Disk: {disk_info['disk']}, Root Folder: {disk_info['root_folder']}, File Count: {disk_info['file_count']}, Used Space: {disk_info['used_space_gb']:.2f} GB, Latest File Modification Date: {disk_info['latest_file_modification_date']}")
    #    print()
    print(f"\nNew_media_folders_info:\n{objPrettyPrint.pformat(new_media_folders_info)}")
    print(f"\n")
	
    print("-" * len(header))
    print(f"\n", flush=True)

    # More ChatGPT extensions

    # (f) Ask the user to choose a media folder from the 'new_media_folders_info'
    print("Select a SOURCE media folder to Mirror onto other disks (including deleting unmatched files on targets):")
    for idx, media_folder in enumerate(new_media_folders_info.keys(), start=1):
        print(f"{idx}. {media_folder}")
    print("Enter 'q' to quit immediately.")
    while True:
        user_input = input("Enter the number of your choice or letter q : ").strip().lower()
        if user_input == 'q':
            print("QUIT selected, exiting the program immediately !!")
            sys.exit()
        try:
            media_folder_choice = int(user_input)
            if 1 <= media_folder_choice <= len(new_media_folders_info):
                chosen_media_folder = list(new_media_folders_info.keys())[media_folder_choice - 1]
                break
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
    print(f"\nYou selected media folder: {chosen_media_folder}")

    # (g) Based on the selected media folder, ask the user to choose a disk from 'new_disks_info'
    print(f"Select a SOURCE disk for that media folder to Mirror onto other disks (including deleting unmatched files on targets) '{chosen_media_folder}':")
    print("Enter 'q' to quit.")
    # Determine the disk with the newest modification date
    newest_mod_date = None
    newest_mod_disk_info = None
    for disk_info in new_media_folders_info[chosen_media_folder]["disks"]:
        if newest_mod_date is None or disk_info["latest_file_modification_date"] > newest_mod_date:
            newest_mod_date = disk_info["latest_file_modification_date"]
            newest_mod_disk_info = disk_info
    # Print choices with additional information and highlight the newest modification date
    for idx, disk_info in enumerate(new_media_folders_info[chosen_media_folder]["disks"], start=1):
        highlight = f" *** {idx}. *** Latest Modification Date ***" if disk_info == newest_mod_disk_info else ""
        print(f"{idx}. {disk_info['disk']} (Root Folder: {disk_info['root_folder']})"
              f" File Count: {disk_info['file_count']}    Used Disk Space: {disk_info['used_space_gb']:.2f} GB"
              f"    Latest File Modification Date: {disk_info['latest_file_modification_date']}{highlight}")
    while True:
        user_input = input("Enter the number of your choice or letter q : ").strip().lower()
        if user_input == 'q':
            print("Exiting the program.")
            sys.exit()
        try:
            disk_choice = int(user_input)
            if 1 <= disk_choice <= len(new_media_folders_info[chosen_media_folder]["disks"]):
                chosen_disk = new_media_folders_info[chosen_media_folder]["disks"][disk_choice - 1]['disk']
                chosen_root_folder = new_media_folders_info[chosen_media_folder]["disks"][disk_choice - 1]['root_folder']
                break
            else:
                print("Invalid choice. Please enter a number from the list.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")
    print(f"You selected disk: {chosen_disk} (Root Folder: {chosen_root_folder})")

    # (h) Print the pinpointed result based on the user's choices
    chosen_disk_info = next(info for info in new_disks_info[chosen_disk]["media_folders"] if info["media_folder"] == chosen_media_folder)

    print(f"\n")
    print("Selected SOURCE to Mirror onto other disks (including deleting unmatched files on targets):")
    print(f"\n")
    print(f"Media Folder: {chosen_media_folder}")
    print(f"Disk: {chosen_disk} (Root Folder: {chosen_root_folder})")
    print(f"File Count: {chosen_disk_info['file_count']}")
    print(f"Used Disk Space: {chosen_disk_info['used_space_gb']:.2f} GB")
    print(f"Latest File Modification Date: {chosen_disk_info['latest_file_modification_date']}")
    print(f"\n")

    # More ChatGPT extensions for execute_mirror_and_sync

    # WARNING DESTRUCTION POSSIBLE
    #
    #    You are about to Mirror-synchronize files FROM '$sourcePath' INTO '$destPath'.
    #    This operation WILL OVERWRITE existing files where they have different sizes and
    #    WILL DELETE filenames in the destination which are not present in the source !
    #
    # First Pass: Copy Files from Source to Destination
    def Copy_update_files(source_path, dest_path, perform_action=False):
        print(f"Commenced Copy_update_files('{source_path}', '{dest_path}', perform_action={perform_action})")
        for root, dirs, files in os.walk(source_path):
            for file_name in files:
                source_file = os.path.join(root, file_name)
                dest_file = source_file.replace(source_path, dest_path)
                if os.path.exists(dest_file):
                    # File exists in destination, check size
                    source_size = os.path.getsize(source_file)
                    dest_size = os.path.getsize(dest_file)
                    #print(f"DEBUG: {source_size} vs {dest_size} Gb '{source_file}'")
                    if source_size != dest_size:
                        # Copy file if sizes differ
                        print(f"Copying file '{source_file}' with different sizes perform_action={perform_action} (Source: {source_size}, Destination: {dest_size}): '{dest_file}')")
                        if perform_action:
                            print(f"perform_action={perform_action} shutil.copy2('{source_file}', '{dest_file}')")
                            shutil.copy2(source_file, dest_file)
                            continue
                        else:
                            #print(f"perform_action={perform_action} #shutil.copy2('{source_file}', '{dest_file}')")
                            continue
                    else:
                        #print(f"File exists in destination with same size {dest_size}, ignoring: {dest_file}")
                        continue
                else:
                    # Copy missing files
                    print(f"Copying new file to: '{dest_file}' perform_action={perform_action}")
                    if perform_action:
                        print(f"perform_action={perform_action} shutil.copy2('{source_file}', '{dest_file}')")
                        shutil.copy2(source_file, dest_file)
                        continue
                    else:
                        #print(f"perform_action={perform_action} #shutil.copy2('{source_file}', '{dest_file}')")
                        continue

    # Second Pass: Remove destination files not present in source
    def Remove_destination_files_not_present_in_source(source_path, dest_path, perform_action=False):
        print(f"Commenced Remove_destination_files_not_present_in_source('{source_path}', '{dest_path}', perform_action={perform_action})")
        for root, dirs, files in os.walk(dest_path):
            for file_name in files:
                dest_file = os.path.join(root, file_name)
                source_file = dest_file.replace(dest_path, source_path)
                if not os.path.exists(source_file):
                    # Remove destination file not present in source
                    print(f"Removing destination file not in SOURCE ('{source_path}'): '{dest_file}'")
                    if perform_action:
                       print(f"perform_action={perform_action} os.remove({dest_file})")
                       os.remove(dest_file)
                       continue
                    else:
                       #print(f"perform_action={perform_action} #os.remove('{dest_file}')")
                       continue
                else:
                    #print(f"KEEPING destination since matching file in SOURCE ('{source_path}'): '{dest_file}'")
                    continue
    def execute_mirror_and_sync(source_path, dest_path, perform_action=False):
        # BIG BIG Warning message
        print(f"""
        WARNING:
    
        You are about to Mirror-synchronize files FROM '{source_path}' INTO '{dest_path}'.
        This operation WILL OVERWRITE existing files where they have different sizes and
        WILL DELETE filenames in the destination which are not present in the source!
    
        Final Warning: Do you want to continue with this possibly destructive action? (Y/N)
        """)
        response = input("Enter Y to continue or N to skip: ").strip().upper()
        if response != 'Y':
            print("Operation aborted by user.")
            return
        print(f"Starting file synchronization from '{source_path}' to '{dest_path}' with PerformAction={perform_action}")
        # First Pass: Copy Files from Source to Destination
        Copy_update_files(source_path, dest_path, perform_action)
        # Second Pass: Remove destination files not present in source
        Remove_destination_files_not_present_in_source(source_path, dest_path, perform_action)
        print("Synchronization complete.")

    # Infer the source path based on the user's selection
    source_path = f"{chosen_disk}{chosen_root_folder}\\{chosen_media_folder}"
    
    # Iterate through the destinations excluding the selected source disk
    destinations = [
        f"{disk_info['disk']}{disk_info['root_folder']}\\{chosen_media_folder}"
        for disk_info in new_media_folders_info[chosen_media_folder]["disks"]
        if disk_info['disk'] != chosen_disk
    ]
    
    # Execute the synchronization for each destination
    print(f"\n")
    perform_action = True
    for destination in destinations:
        print(f"\nMirroring from source '{source_path}' to destination '{destination}'...\n")
        execute_mirror_and_sync(source_path, destination, perform_action=perform_action)
    print(f"\n")
    print("All synchronization operations completed.")
    print(f"\n", flush=True)
