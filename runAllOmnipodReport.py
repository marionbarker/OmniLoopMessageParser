# runAllOmnipodReport.py
#
# Process every Loop (.md) and Trio (.txt) report found in the OPK Private
# Beta Input folder, oldest first (by file modification time).
#
# Designed to be re-run as new files arrive: just drop new files into the
# Input folder and run this script.  Delete omnipodkit_raw_pod_list.csv in the
# Output folder first if you want a fresh summary.

import os
import re
from main import main

inputPath = os.path.expanduser('~/dev/OPK_Private_Beta/Input')
outputPath = os.path.expanduser('~/dev/OPK_Private_Beta/Output')
vFlag = 5   # verbose csv output + stats row

# ── collect all .md and .txt files, sorted oldest first ──────────────────────
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

files.sort(key=lambda x: x[1])   # oldest first

print(f'\n{len(files)} file(s) to process:\n')
for fname, _ in files:
    print(f'  {fname}')
print()

# ── process each file in turn ─────────────────────────────────────────────────
for filename, _ in files:
    fullFilePath = os.path.join(inputPath, filename)

    # determine app type from extension
    if filename.endswith('.md'):
        loopType = 'Loop'
    else:
        loopType = 'FX'

    # extract Google user name from "... - Name.ext"
    stem = filename.rsplit('.', 1)[0]
    if ' - ' in stem:
        person_raw = stem.rsplit(' - ', 1)[1]
    else:
        person_raw = 'Unknown'
    person = person_raw.replace(' ', '_')

    # extract date from filename
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
        thisDate = 'WillReadFromFileAndUpdate'

    fileDict = {
        'filename':   fullFilePath,
        'path':       inputPath,
        'personFile': filename,
        'file':       filename,
        'loopType':   loopType,
        'recordType': 'unknown',
        'date':       thisDate,
        'person':     person,
        'statsFile':  os.path.join(outputPath, 'omnipodkit_raw_pod_list.csv'),
    }

    print(f'========================================')
    print(f' Processing: {filename}')
    print(f'   Person:   {person_raw}')
    print(f'   Type:     {loopType}')
    print(f'   Date:     {thisDate}')

    main(fileDict, outputPath, vFlag)
