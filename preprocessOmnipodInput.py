# preprocessOmnipodInput.py
#
# Preprocess the OPK Private Beta Input folder before running analysis.
#
# Handles two zip formats:
#
# 1. Per-person zips: "{any name} - Google Name.zip"
#    - Extract .md and .txt files, appending " - Google Name" before extension.
#    - Move zip to Processed.
#
# 2. Drive-download zips: "drive-download*.zip" (Google Drive bulk download)
#    - Contains files already named with " - Google Name" convention.
#    - Valid files (.md, date-prefixed .txt) are extracted to Input as-is.
#    - Gzip-compressed Trio logs ("log_prev.txt - Name(N).gz"):
#        decompress, extract date from first line, rename to
#        "YYYY-MM-DD - Name(N).txt" and place in Input.
#    - Nested per-person .zip files are handled like case 1 above.
#    - Unrecognised files (log, watch_log, etc.) are moved to Processed.
#    - Move the outer zip to Processed.
#
# Called by runAllOmnipodReport.py and can also be run standalone.

import gzip
import os
import re
import shutil
import zipfile

inputPath     = os.path.expanduser('~/dev/OPK_Private_Beta/Input')
processedPath = os.path.expanduser('~/dev/OPK_Private_Beta/Processed')


def _is_valid_report(basename):
    """Return True if the file looks like a Loop or Trio report we want to process."""
    if basename.endswith('.md'):
        return True
    if basename.endswith('.txt') and re.match(r'\d{4}-\d{2}-\d{2}', basename):
        return True
    return False


def _handle_person_zip(zip_path, person_raw, dest_dir):
    """
    Extract .md/.txt files from a per-person zip, appending " - person_raw"
    before the extension, into dest_dir. Returns list of extracted filenames.
    """
    suffix = ' - ' + person_raw
    extracted = []
    extract_dir = zip_path + '_extracted'
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.namelist():
            if member.startswith('__MACOSX') or os.path.basename(member).startswith('._'):
                continue
            base = os.path.basename(member)
            if not (base.endswith('.md') or base.endswith('.txt')):
                continue
            root, ext = os.path.splitext(base)
            new_name = root + suffix + ext
            zf.extract(member, extract_dir)
            shutil.move(os.path.join(extract_dir, member),
                        os.path.join(dest_dir, new_name))
            print(f'  Extracted: {new_name}')
            extracted.append(new_name)

    shutil.rmtree(extract_dir, ignore_errors=True)
    return extracted


def _handle_gz_trio(fpath, fname, dest_dir):
    """
    Decompress a gzip-compressed Trio log file named like
    "log_prev.txt - Person Name(N).gz".

    Extracts the date from the first line of the file content and writes
    the decompressed file as "YYYY-MM-DD - Person Name(N).txt" into dest_dir.
    Returns the output filename, or None if the file could not be handled.
    """
    # fname example: "log_prev.txt - Joseph Moran(1).gz"
    inner = fname[:-3]  # strip .gz → "log_prev.txt - Joseph Moran(1)"

    if ' - ' not in inner:
        return None

    person_part = inner.rsplit(' - ', 1)[1]   # "Joseph Moran(1)"

    # Strip trailing (N) — it's an artifact of Google Drive deduplication
    # when multiple log_prev.txt files land in the same folder.
    # The date in the filename is sufficient to distinguish files.
    person_name = re.sub(r'\s*\(\d+\)$', '', person_part).strip()  # "Joseph Moran"

    try:
        with gzip.open(fpath, 'rt', encoding='utf-8', errors='replace') as gz_f:
            content = gz_f.read()
    except Exception as e:
        print(f'  Warning: could not decompress {fname}: {e}')
        return None

    # Extract date from the first timestamp in the file (local time)
    first_line = content.lstrip().split('\n')[0]
    date_match = re.match(r'(\d{4}-\d{2}-\d{2})', first_line)
    if not date_match:
        print(f'  Warning: no date found in {fname}, skipping')
        return None

    date_str = date_match.group(1)   # "YYYY-MM-DD"
    out_name = f'{date_str} - {person_name}.txt'
    out_path = os.path.join(dest_dir, out_name)

    with open(out_path, 'w', encoding='utf-8') as out_f:
        out_f.write(content)

    return out_name


def preprocess_input_folder():
    os.makedirs(processedPath, exist_ok=True)

    zip_files = [f for f in os.listdir(inputPath) if f.endswith('.zip')]

    if not zip_files:
        return

    for zip_name in zip_files:
        zip_path = os.path.join(inputPath, zip_name)
        stem = zip_name[:-4]

        # ── Case 1: per-person zip ("{name} - Google Name.zip") ──────────────
        if ' - ' in stem and not stem.lower().startswith('drive-download'):
            person_raw = stem.rsplit(' - ', 1)[1]
            print(f'\nUnzipping (per-person): {zip_name}')
            print(f'  Person: {person_raw}')
            _handle_person_zip(zip_path, person_raw, inputPath)
            shutil.move(zip_path, os.path.join(processedPath, zip_name))
            print(f'  Moved zip to Processed/')
            continue

        # ── Case 2: Google Drive bulk download ("drive-download*.zip") ───────
        if stem.lower().startswith('drive-download'):
            print(f'\nUnzipping (drive-download): {zip_name}')
            extract_dir = os.path.join(inputPath, stem + '_extracted')
            os.makedirs(extract_dir, exist_ok=True)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(extract_dir)

            # Walk the extracted contents
            for dirpath, _, filenames in os.walk(extract_dir):
                for fname in filenames:
                    if fname.startswith('__MACOSX') or fname.startswith('._'):
                        continue
                    fpath = os.path.join(dirpath, fname)

                    # Nested per-person zip
                    if fname.endswith('.zip') and ' - ' in fname:
                        nested_stem = fname[:-4]
                        person_raw = nested_stem.rsplit(' - ', 1)[1]
                        print(f'  Nested zip: {fname}  (person: {person_raw})')
                        _handle_person_zip(fpath, person_raw, inputPath)
                        shutil.move(fpath, os.path.join(processedPath, fname))
                        continue

                    # Gzip-compressed Trio log
                    if fname.endswith('.gz') and ' - ' in fname:
                        out_name = _handle_gz_trio(fpath, fname, inputPath)
                        if out_name:
                            print(f'  Decompressed: {fname} → {out_name}')
                        else:
                            shutil.move(fpath, os.path.join(processedPath, fname))
                        continue

                    # Valid Loop/Trio report — move to Input as-is
                    if _is_valid_report(fname):
                        dest = os.path.join(inputPath, fname)
                        shutil.move(fpath, dest)
                        print(f'  Extracted: {fname}')
                        continue

                    # Everything else (log, watch_log, etc.) — discard to Processed
                    print(f'  Skipping (not a report): {fname}')
                    shutil.move(fpath, os.path.join(processedPath, fname))

            shutil.rmtree(extract_dir, ignore_errors=True)
            shutil.move(zip_path, os.path.join(processedPath, zip_name))
            print(f'  Moved zip to Processed/')
            continue

        # ── Unrecognised zip (no " - " and not drive-download) ───────────────
        print(f'\nSkipping unrecognised zip: {zip_name}')


if __name__ == '__main__':
    preprocess_input_folder()
    print('\nPreprocessing complete.')
