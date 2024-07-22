import os
import shutil

# Define the disks and their root folders
disks = {
    "X:": r"\ROOTFOLDER1",
    "V:": r"\ROOTFOLDER2",
    "F:": r"\ROOTFOLDER3",
    "H:": r"\ROOTFOLDER4",
    "K:": r"\ROOTFOLDER5",
    "W:": r"\ROOTFOLDER6"
}

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

# Function to count files and calculate their total size in a given folder
def count_files_and_size(folder_path):
    file_count = 0
    total_size = 0
    for root, dirs, files in os.walk(folder_path):
        file_count += len(files)
        total_size += sum(os.path.getsize(os.path.join(root, file)) for file in files)
    return file_count, total_size / (1024 * 1024 * 1024)  # Convert size to Gigabytes

# Initialize the result dictionary
result = {folder: {disk: (0, 0) for disk in disks} for folder in media_folders}
free_space = {}

# Iterate over each disk and media folder to count files and calculate size
for disk, root_folder in disks.items():
    for media_folder in media_folders:
        folder_path = os.path.join(disk, root_folder, media_folder)
        if os.path.exists(folder_path):
            result[media_folder][disk] = count_files_and_size(folder_path)
    # Get the free space for each disk
    total, used, free = shutil.disk_usage(disk)
    free_space[disk] = free / (1024 * 1024 * 1024)  # Convert size to Gigabytes

# Calculate the fixed column width based on the longest header and data values
disk_headers = [f"{disk} ({root_folder})" for disk, root_folder in disks.items()]
max_count_length = max(len(f"{count}") for folder in media_folders for disk in disks for count, _ in [result[folder][disk]])
max_size_length = max(len(f"{size:.2f} GB") for folder in media_folders for disk in disks for _, size in [result[folder][disk]])
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
        file_count, total_size = result[media_folder][disk]
        row += f"{file_count:>{max_count_length}} / {total_size:>{max_size_length}.2f} GB".rjust(column_width)
    print(row)

# Print the dashed line before the free disk space row
print("-" * len(header))

# Add the free disk space row
free_space_row = "{:<45}".format("Free Disk Space")
for disk in disks:
    free_space_row += f"{free_space[disk]:>{max_size_length}.2f} GB".rjust(column_width)
print(free_space_row)
