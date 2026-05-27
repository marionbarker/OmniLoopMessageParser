# runLastOmnipodReport.py
#
# Process the most recent Loop (.md) or Trio (.txt) report from the OPK
# Private Beta shared folder.
#
# Files are downloaded from Google Drive with the uploader's name appended:
#   Loop files:  "Loop Report YYYY-MM-DD HH_MM_SS<tz> ... - Google Name.md"
#   Trio files:  "YYYY-MM-DD - Google Name.txt"
#
# Output goes to ~/dev/OPK_Private_Beta/Output:
#   omnipodkit_stats.csv        one row per pod (appended, header on first run)
#   podState_Name_YYYYMMDD_HHMM_#.csv  per-pod state detail

import os
import re
from main import main

inputPath = os.path.expanduser('~/dev/OPK_Private_Beta/Input')
outputPath = os.path.expanduser('~/dev/OPK_Private_Beta/Output')
vFlag = 5   # verbose csv output + stats row

# ── find the most recent .md or .txt file ────────────────────────────────────
files = []
for fname in os.listdir(inputPath):
    if fname == '.DS_Store':
        continue
    if fname.endswith('.md') or fname.endswith('.txt'):
        fullPath = os.path.join(inputPath, fname)
        mtime = os.path.getmtime(fullPath)
        files.append((fname, mtime))

if not files:
    print('No .md or .txt files found in', inputPath)
    raise SystemExit(1)

files.sort(key=lambda x: x[1])
filename = files[-1][0]          # most recently modified
fullFilePath = os.path.join(inputPath, filename)

# ── determine app type from extension ────────────────────────────────────────
if filename.endswith('.md'):
    loopType = 'Loop'
else:
    loopType = 'FX'

# ── extract Google user name from "... - Name.ext" ───────────────────────────
stem = filename.rsplit('.', 1)[0]       # strip extension
if ' - ' in stem:
    person_raw = stem.rsplit(' - ', 1)[1]   # text after the last " - "
else:
    person_raw = 'Unknown'
# replace spaces with underscores so the name is safe in filenames
person = person_raw.replace(' ', '_')

# ── extract date from filename ────────────────────────────────────────────────
# Loop files: "Loop Report YYYY-MM-DD HH_MM_SS<tz> ..."
# Trio files: date is read from inside the file by loop_read_file
if loopType == 'Loop':
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})\s+(\d{2})_(\d{2})', stem)
    if match:
        thisDate = (match.group(1) + match.group(2) + match.group(3) +
                    '_' + match.group(4) + match.group(5))
    else:
        thisDate = 'unknown'
else:
    thisDate = 'WillReadFromFileAndUpdate'   # set by loop_read_file for FX

# ── build fileDict ────────────────────────────────────────────────────────────
# Built directly here rather than via getFileDict because these files live
# flat in the Input folder (no person-subfolder structure) and the person
# name comes from the filename, not the folder hierarchy.
fileDict = {
    'filename':   fullFilePath,
    'path':       inputPath,
    'personFile': filename,
    'file':       filename,
    'loopType':   loopType,
    'recordType': 'unknown',
    'date':       thisDate,
    'person':     person,
    # statsFile overrides the default dash_stats.csv in analyzePodMessages
    'statsFile':  os.path.join(outputPath, 'omnipodkit_raw_pod_list.csv'),
}

print(f'\n Processing: {filename}')
print(f'   Person:   {person_raw}')
print(f'   Type:     {loopType}')
print(f'   Date:     {thisDate}')

main(fileDict, outputPath, vFlag)
