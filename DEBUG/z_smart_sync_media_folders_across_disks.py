import os
import shutil

# Define the disks and their root folders
disks = {
    "X:": r"\ROOTFOLDER1",
    "V:": r"\ROOTFOLDER2",
    "F:": r"\ROOTFOLDER3",
    "H:": r"\ROOTFOLDER4",
    "K:": r"\ROOTFOLDER5"
}

# Define the list of media folders
media_folders = [
    "2015.11.29-Jess-21st-birthday-party",
    "BigIdeas", "CharlieWalsh",
    "ClassicDocumentaries", 
    "ClassicMovies",
    "Documentaries",
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
        for disk, root_folder in disks.items():
            media_folder_path = os.path.join(disk, root_folder, media_folder)
            if os.path.exists(media_folder_path):
                has_files = False
                for _, _, files in os.walk(media_folder_path):
                    if files:
                        disk_with_files.append(disk)
                        has_files = True
                        break
                if not has_files:
                    print(f"Media folder {media_folder} exists on {disk} but is empty.", flush=True)
                else:
                    print(f"Media folder {media_folder} exists on {disk} and contains files.", flush=True)
        
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
            print(f"Only one disk {disk_with_files[0]} contains the media folder {media_folder} with files", flush=True)
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
            dst_path = os.path.join(target_disk, disks[target_disk], media_folder)
            copy_tree(src_path, dst_path)
        
        else:
            # No disks contain the media folder with files or only empty media folders found
            print(f"Media folder {media_folder} does not contain any files on any disk.", flush=True)

if __name__ == "__main__":
    # Run the synchronization
    sync_folders_and_files(disks, media_folders)
