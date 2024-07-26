import os
import csv
import difflib
import re
import pprint
from collections import defaultdict
import subprocess
from datetime import datetime

def run_dos_command(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        shell=True  # Use shell=True to execute the command through the shell
    )
    return result.stdout

def preprocess_filename(filename):
    # Remove date-like patterns (yyyy-mm-dd) from the filename
    # This regex pattern matches dates in the format yyyy-mm-dd
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    # Replace dates with an empty string
    return re.sub(date_pattern, '', filename).strip()

def get_all_files_in_folder_tree(directory):
    file_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            relative_path = os.path.relpath(os.path.join(root, file), directory)
            file_paths.append(relative_path)
    return file_paths

def get_all_files_in_folder(directory):
    file_paths = []
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            file_paths.append(file)
    return file_paths

def group_files_by_folder(file_paths):
    grouped_files = {}
    original_to_preprocessed = defaultdict(set)
    for path in file_paths:
        folder = os.path.dirname(path)
        filename = os.path.basename(path)
        preprocessed_filename = preprocess_filename(filename)
        if folder not in grouped_files:
            grouped_files[folder] = []
        grouped_files[folder].append(preprocessed_filename)
        original_to_preprocessed[folder].add((preprocessed_filename, filename))

    return grouped_files, original_to_preprocessed

def find_fuzzy_matches(grouped_files_a, grouped_files_b, original_to_preprocessed_a, original_to_preprocessed_b):
    matches = []
    unmatched_a = {}
    unmatched_b = {}

    for folder in grouped_files_a:
        files_a = grouped_files_a[folder]
        files_b = grouped_files_b.get(folder, [])

        folder_matches, folder_unmatched_a, folder_unmatched_b = match_files_in_folder(files_a, files_b, original_to_preprocessed_a[folder], original_to_preprocessed_b.get(folder, set()))
        matches.extend([(a, b) for a, b in folder_matches])

        if folder_unmatched_a:
            unmatched_a[folder] = folder_unmatched_a
        if folder_unmatched_b:
            unmatched_b[folder] = folder_unmatched_b

    for folder in grouped_files_b:
        if folder not in grouped_files_a:
            unmatched_b[folder] = grouped_files_b[folder]

    return matches, unmatched_a, unmatched_b

def match_files_in_folder(files_a, files_b, original_to_preprocessed_a, original_to_preprocessed_b):
    matches = []
    unmatched_a = set(files_a)
    unmatched_b = set(files_b)

    # Build a reverse lookup for preprocessed to original filenames
    preprocessed_to_original_a = defaultdict(set)
    preprocessed_to_original_b = defaultdict(set)

    for preprocessed, original in original_to_preprocessed_a:
        preprocessed_to_original_a[preprocessed].add(original)
    for preprocessed, original in original_to_preprocessed_b:
        preprocessed_to_original_b[preprocessed].add(original)

    for file_a in files_a:
        close_matches = difflib.get_close_matches(file_a, files_b, n=1, cutoff=0.60)
        #close_matches = difflib.get_close_matches(file_a, files_b, n=1, cutoff=0.65)
        #close_matches = difflib.get_close_matches(file_a, files_b, n=1, cutoff=0.7)
        #close_matches = difflib.get_close_matches(file_a, files_b, n=1, cutoff=0.75)
        if close_matches:
            file_b = close_matches[0]
            # Select the first match from the set of original filenames
            original_a = next(iter(preprocessed_to_original_a[file_a]), None)
            original_b = next(iter(preprocessed_to_original_b[file_b]), None)
            if original_a and original_b:
                matches.append((original_a, original_b))
                unmatched_a.discard(file_a)
                unmatched_b.discard(file_b)

    return matches, unmatched_a, unmatched_b

def generate_unique_filename(base_path, prefix, extension):
    # Generate a unique filename with a timestamp including microseconds
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    counter = 1
    while True:
        filename = f"{prefix}_{timestamp}_{counter}{extension}"
        full_path = os.path.join(base_path, filename)
        if not os.path.exists(full_path):
            return full_path
        counter += 1

def write_to_csv(SourceFolder_proposed_to_move_files_to_TargetFolder, TargetFolder_proposed_to_remove_files_before_Source_moves, matches, unmatched_a, unmatched_b, output_file_csv):
    with open(output_file_csv, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)

        Instruction_msg = 'REM Inspect by eye: if NOT a valid match REMOVE the DEL command. Copy remaining commands and run them.'
        csvwriter.writerow([f'SOURCE Matched File {SourceFolder_proposed_to_move_files_to_TargetFolder}', f'TARGET Matched File {TargetFolder_proposed_to_remove_files_before_Source_moves}', Instruction_msg])

        # Sort matches case-insensitively by match[0]
        matches.sort(key=lambda x: x[0].lower())
        # Write matched files
        for match in matches:
		    # match [match[0]
            # code to just write the files:
            #csvwriter.writerow([match[0], match[1]])
            # 
            # code to write the files AND .bat commands to del/copy
            # NOTE: delete FIRST in case the filenames were identical, since we
            #       do not want to move then delete the file we just copied ...
            del_cmd  = f'DEL  "{TargetFolder_proposed_to_remove_files_before_Source_moves}\\{match[1]}"'
            move_cmd = f'MOVE /Y "{SourceFolder_proposed_to_move_files_to_TargetFolder}\\{match[0]}" "{TargetFolder_proposed_to_remove_files_before_Source_moves}\\"'
            csvwriter.writerow([match[0], match[1], del_cmd])
            csvwriter.writerow(['','', move_cmd])

        # Write unmatched files
        unmatched_source_folder = SourceFolder_proposed_to_move_files_to_TargetFolder
        unmatched_target_folder = TargetFolder_proposed_to_remove_files_before_Source_moves
        csvwriter.writerow([])
        csvwriter.writerow([f'Unmatched Files {unmatched_source_folder}', f'Unmatched Files {unmatched_target_folder}', 'REM UNmatched Commands'])

        # Create a list of unmatched files in A and B with original filenames
        unmatched_files_a = []   # the source
        unmatched_files_b = []   # already in the target

        for folder in unmatched_a:
            for preprocessed_file in unmatched_a[folder]:
                # Retrieve the original filename
                original_file = next(
                    (orig for preproc, orig in original_to_preprocessed_a[folder] if preproc == preprocessed_file), 
                    ''
                )
                unmatched_files_a.append(os.path.join(folder, original_file))
        
        for folder in unmatched_b:
            for preprocessed_file in unmatched_b[folder]:
                # Retrieve the original filename
                original_file = next(
                    (orig for preproc, orig in original_to_preprocessed_b[folder] if preproc == preprocessed_file), 
                    ''
                )
                unmatched_files_b.append(os.path.join(folder, original_file))

        # Sort unmatched files case-insensitively
        unmatched_files_a.sort(key=lambda x: x.lower())
        unmatched_files_b.sort(key=lambda x: x.lower())
        # Find the maximum length of unmatched files in A or B
        max_length = max(len(unmatched_files_a), len(unmatched_files_b))

        for i in range(max_length):
            file_a = unmatched_files_a[i] if i < len(unmatched_files_a) else ''
            file_b = unmatched_files_b[i] if i < len(unmatched_files_b) else ''
            move_cmd = f'MOVE /Y "{SourceFolder_proposed_to_move_files_to_TargetFolder}\\{file_a}" "{TargetFolder_proposed_to_remove_files_before_Source_moves}\\"' if i < len(unmatched_files_a) else ''
            csvwriter.writerow([file_a, file_b, move_cmd])

if __name__ == "__main__":

    TERMINAL_WIDTH = 250
    objPrettyPrint = pprint.PrettyPrinter(width=TERMINAL_WIDTH, compact=False, sort_dicts=False)    # facilitates formatting 
    #print(f"DEBUG: {objPrettyPrint.pformat(a_list)}")

    triplets = [
        [r"2015.11.29-Jess-21st-birthday-party", r"T:\HDTV\VRDTVSP-Converted\2015.11.29-Jess-21st-birthday-party", r"X:\ROOTFOLDER1\2015.11.29-Jess-21st-birthday-party"],
        [r"BigIdeas", r"T:\HDTV\VRDTVSP-Converted\BigIdeas", r"H:\ROOTFOLDER4\BigIdeas"],
        [r"CharlieWalsh", r"T:\HDTV\VRDTVSP-Converted\CharlieWalsh", r"X:\ROOTFOLDER1\CharlieWalsh"],
        [r"ClassicDocumentaries", r"T:\HDTV\VRDTVSP-Converted\ClassicDocumentaries", r"X:\ROOTFOLDER1\ClassicDocumentaries"],
        [r"ClassicMovies", r"T:\HDTV\VRDTVSP-Converted\ClassicMovies", r"X:\ROOTFOLDER1\ClassicMovies"],
        [r"Documentaries", r"T:\HDTV\VRDTVSP-Converted\Documentaries", r"V:\ROOTFOLDER2\Documentaries"],
        [r"Family_Photos", r"T:\HDTV\VRDTVSP-Converted\Family_Photos", r"X:\ROOTFOLDER1\Family_Photos"],
        [r"Footy", r"T:\HDTV\VRDTVSP-Converted\Footy", r"X:\ROOTFOLDER1\Footy"],
        [r"HomePics", r"T:\HDTV\VRDTVSP-Converted\HomePics", r"F:\ROOTFOLDER3\HomePics"],
        [r"Movies", r"T:\HDTV\VRDTVSP-Converted\Movies", r"H:\ROOTFOLDER4\Movies"],
        [r"Movies_unsorted", r"T:\HDTV\VRDTVSP-Converted\Movies_unsorted", r"X:\ROOTFOLDER1\Movies_unsorted"],
        [r"MusicVideos", r"T:\HDTV\VRDTVSP-Converted\MusicVideos", r"K:\ROOTFOLDER5\MusicVideos"],
        [r"OldMovies", r"T:\HDTV\VRDTVSP-Converted\OldMovies", r"V:\ROOTFOLDER2\OldMovies"],
        [r"SciFi", r"T:\HDTV\VRDTVSP-Converted\SciFi", r"X:\ROOTFOLDER1\SciFi"],
        [r"Series", r"T:\HDTV\VRDTVSP-Converted\Series", r"V:\ROOTFOLDER2\Series"],
    ]

    for triplet in triplets:
        #print(f"{triplet[0]}    {triplet[1]}    {triplet[2]}")
        #
        # Specify directories and output file
        output_dir = r'X:\CONVERT'
        prefix = 'z_fuzzy_match_results_' + triplet[0]
        extension = '.csv'
        output_file_csv = generate_unique_filename(output_dir, prefix, extension)
        SourceFolder_proposed_to_move_files_to_TargetFolder = triplet[0]
        SourceFolder_proposed_to_move_files_to_TargetFolder = triplet[1]
        TargetFolder_proposed_to_remove_files_before_Source_moves = triplet[2]
        #
        files_a = get_all_files_in_folder(SourceFolder_proposed_to_move_files_to_TargetFolder)
        files_b = get_all_files_in_folder(TargetFolder_proposed_to_remove_files_before_Source_moves)
        #
        grouped_files_a, original_to_preprocessed_a = group_files_by_folder(files_a)
        grouped_files_b, original_to_preprocessed_b = group_files_by_folder(files_b)
        #
        matches, unmatched_a, unmatched_b = find_fuzzy_matches(grouped_files_a, grouped_files_b, original_to_preprocessed_a, original_to_preprocessed_b)
        print(f"\nCreating .csv file '{output_file_csv}'\nBased on PC Staging Source: '{SourceFolder_proposed_to_move_files_to_TargetFolder}' and PC drive\folder: '{TargetFolder_proposed_to_remove_files_before_Source_moves}'")
        write_to_csv(SourceFolder_proposed_to_move_files_to_TargetFolder, TargetFolder_proposed_to_remove_files_before_Source_moves, matches, unmatched_a, unmatched_b, output_file_csv)
    print(f"Finished creating .csv files")
