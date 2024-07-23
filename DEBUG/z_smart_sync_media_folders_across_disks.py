import os
import shutil
import pprint
import os

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

def get_free_space(disk):
    """Returns the free space of the given disk in bytes."""
    return shutil.disk_usage(disk).free

def copy_tree(src, dst):
    """Recursively copy the directory tree from src to dst, skipping existing files."""
    print(f"   --- Attempting to sync copy_tree from '{src}' to '{dst}' ...", flush=True)
    for root, dirs, files in os.walk(src):
        rel_path = os.path.relpath(root, src)
        dst_path = os.path.join(dst, rel_path)
        os.makedirs(dst_path, exist_ok=True)
        for file in files:
            src_file = os.path.join(root, file)
            dst_file = os.path.join(dst_path, file)
            if not os.path.exists(dst_file):
                print(f"      copying file src,dst: shutil.copy2('{src_file}', '{dst_file}'", flush=True)
                shutil.copy2(src_file, dst_file)
                pass

def sync_folders_and_files(disks, media_folders):
    for media_folder in media_folders:
        print(f"*** Start checking media folder {media_folder} across disks ...", flush=True)
        disk_with_files = []
        root_folder_with_files = []
        for disk, root_folder in disks.items():
            media_folder_path = os.path.join(disk, root_folder, media_folder)
            if os.path.exists(media_folder_path):
                has_files = False
                for _, _, files in os.walk(media_folder_path):
                    if files:
                        disk_with_files.append(disk)
                        root_folder_with_files.append(root_folder)
                        has_files = True
                        break
                if not has_files:
                    print(f"Media folder {media_folder} exists on {disk} ({root_folder}) but is empty.", flush=True)
                else:
                    print(f"Media folder {media_folder} exists on {disk} ({root_folder}) and contains files.", flush=True)
        
        if len(disk_with_files) > 1:
            # Multiple disks contain the media folder with files
            print(f"Multiple disks contain the media folder {media_folder} with files", flush=True)
            for disk in disk_with_files:
                for other_disk in disk_with_files:
                    if disk != other_disk:
                        src_path = os.path.join(disk, disks[disk], media_folder)
                        dst_path = os.path.join(other_disk, disks[other_disk], media_folder)
                        copy_tree(src_path, dst_path)
        
        elif len(disk_with_files) == 1:
            # Only one disk contains the media folder with files
            print(f"Only one disk {disk_with_files[0]} ({root_folder_with_files[0]}) contains the media folder {media_folder} with files", flush=True)
            src_disk = disk_with_files[0]
            src_path = os.path.join(src_disk, disks[src_disk], media_folder)
            # Print free space for each disk
            print("Free disk space on each disk:", flush=True)
            for disk in disks.keys():
                free_space = get_free_space(disk)
                print(f"Disk {disk}: {free_space / (1024**3):.2f} GB", flush=True)
            # Select the target disk with the maximum free space, excluding the source disk
            remaining_disks = {disk: root for disk, root in disks.items() if disk != src_disk}
            target_disk = max(remaining_disks.keys(), key=get_free_space)
            print(f"Target disk with max free disk space is '{target_disk}' (excluding source disk '{src_disk}')", flush=True)
            dst_path = os.path.join(target_disk, disks[target_disk], media_folder)    # disks[target_disk] is the rootfolder since the key into disks[] is the target_disk 
            copy_tree(src_path, dst_path)
        
        else:
            # No disks contain the media folder with files or only empty media folders found
            print(f"Media folder {media_folder} does not contain any files on any disk.", flush=True)

if __name__ == "__main__":
    TERMINAL_WIDTH = 132
    objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)  # facilitates formatting

    print(f"\nchatgpt python program version: 2.2\n")

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

    # Define the list of media folders
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
    print(f"media_folders: \n{objPrettyPrint.pformat(media_folders)}")

    # Run the synchronization
    #sync_folders_and_files(disks, media_folders)
