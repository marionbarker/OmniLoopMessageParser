# preprocessOmnipodInput.py
#
# Preprocess the OPK Private Beta Input folder before running analysis.
#
# For every .zip file matching "{any name} - Google Name.zip":
#   1. Extract the Google user name from the zip filename.
#   2. Unzip the archive.
#   3. For each .md or .txt file inside (skipping __MACOSX metadata):
#      - Append " - Google Name" before the file extension.
#      - Move the renamed file to the Input folder.
#   4. Move the zip file to ~/dev/OPK_Private_Beta/Processed.
#   5. Remove the now-empty extraction directory (if any).
#
# Called by runAllOmnipodReport.py and can also be run standalone.

import os
import re
import shutil
import zipfile

inputPath    = os.path.expanduser('~/dev/OPK_Private_Beta/Input')
processedPath = os.path.expanduser('~/dev/OPK_Private_Beta/Processed')


def preprocess_input_folder():
    os.makedirs(processedPath, exist_ok=True)

    zip_files = [f for f in os.listdir(inputPath)
                 if f.endswith('.zip') and ' - ' in f]

    if not zip_files:
        return

    for zip_name in zip_files:
        zip_path = os.path.join(inputPath, zip_name)

        # Extract Google user name from "... - Google Name.zip"
        stem = zip_name[:-4]                          # strip .zip
        person_raw = stem.rsplit(' - ', 1)[1]         # text after last " - "
        suffix = ' - ' + person_raw                   # e.g. " - Marion Barker"

        print(f'\nUnzipping: {zip_name}')
        print(f'  Person: {person_raw}')

        # Extract to a temp subdirectory inside Input to avoid name collisions
        extract_dir = os.path.join(inputPath, stem + '_extracted')
        os.makedirs(extract_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for member in zf.namelist():
                # Skip macOS metadata entries
                if member.startswith('__MACOSX') or os.path.basename(member).startswith('._'):
                    continue
                # Only process .md and .txt files
                base = os.path.basename(member)
                if not (base.endswith('.md') or base.endswith('.txt')):
                    continue

                # Build new filename: insert " - Person" before extension
                root, ext = os.path.splitext(base)
                new_name = root + suffix + ext

                # Extract to temp dir then move to Input
                zf.extract(member, extract_dir)
                extracted_path = os.path.join(extract_dir, member)
                dest_path = os.path.join(inputPath, new_name)
                shutil.move(extracted_path, dest_path)
                print(f'  Extracted: {new_name}')

        # Remove extraction directory tree (now empty of useful files)
        shutil.rmtree(extract_dir, ignore_errors=True)

        # Move zip to Processed folder
        shutil.move(zip_path, os.path.join(processedPath, zip_name))
        print(f'  Moved zip to Processed/')


if __name__ == '__main__':
    preprocess_input_folder()
    print('\nPreprocessing complete.')
