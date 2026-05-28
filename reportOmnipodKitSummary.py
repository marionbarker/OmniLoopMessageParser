# reportOmnipodKitSummary.py
#
# Generate a PDF summary report from omnipodkit_pod_list.csv.
# Prints to the terminal and writes to omnipodkit_summary.pdf in the Output folder.

import os
import markdown
import pandas as pd
from weasyprint import HTML, CSS

outputPath = os.path.expanduser('~/dev/OPK_Private_Beta/Output')
podListFile = os.path.join(outputPath, 'omnipodkit_pod_list.csv')
reportFile  = os.path.join(outputPath, 'omnipodkit_summary.pdf')


# ── load ──────────────────────────────────────────────────────────────────────

df = pd.read_csv(podListFile, dtype=str)
df.columns = df.columns.str.strip()
df['lastMsgDate'] = pd.to_datetime(df['lastMsgDate'], errors='coerce')


# ── helpers ───────────────────────────────────────────────────────────────────

def pod_type_section(label, subset):
    lines = []
    total = len(subset)
    if total == 0:
        lines.append(f'## {label} Pods\n')
        lines.append('No pods found.\n')
        return lines

    faults = subset[subset['Finish2'].str.strip() == 'Fault']
    n_faults = len(faults)
    pct_success = 100 * (total - n_faults) / total

    lines.append(f'## {label} Pods\n')
    lines.append(f'**Total pods:** {total}  ')
    lines.append(f'**Pods with faults:** {n_faults} ({pct_success:.1f}% success)\n')

    if n_faults > 0:
        lines.append('### Fault types\n')
        lines.append('| Fault code | Count |')
        lines.append('|---|---|')
        fault_counts = subset['Finish1'].where(
            subset['Finish2'].str.strip() == 'Fault'
        ).dropna().value_counts()
        for fault_code, count in fault_counts.items():
            lines.append(f'| {fault_code} | {count} |')
        lines.append('')

    return lines


# ── build report ──────────────────────────────────────────────────────────────

lines = []
lines.append('# OmnipodKit Private Beta — Pod Summary\n')

# Date range and tester count
valid_dates = df['lastMsgDate'].dropna()
earliest = valid_dates.min()
latest   = valid_dates.max()
testers  = df['Who'].nunique()
tester_list = sorted(df['Who'].str.replace('_', ' ').unique())

lines.append('## Overview\n')
lines.append(f'**Testers:** {testers}  ')
lines.append(f'**Date range:** {earliest.strftime("%Y-%m-%d")} to {latest.strftime("%Y-%m-%d")}\n')

# Unknown pod type note
unknown = df[df['PodType'].isna() | (df['PodType'].str.strip() == '')]
if len(unknown) > 0:
    lines.append(f'> **Note:** {len(unknown)} pod(s) have no PodType '
                 f'(pairing data not captured in these files).\n')

# Per-type sections
dash_pods = df[df['PodType'].str.strip() == 'DASH']
o5_pods   = df[df['PodType'].str.strip() == 'O5']

lines.extend(pod_type_section('O5', o5_pods))
lines.extend(pod_type_section('DASH', dash_pods))

lines.append('## Tester List\n')
for t in tester_list:
    lines.append(f'- {t}')
lines.append('')

report_md = '\n'.join(lines)

# ── print markdown to terminal ────────────────────────────────────────────────

print(report_md)

# ── convert to PDF ────────────────────────────────────────────────────────────

html_body = markdown.markdown(report_md, extensions=['tables'])

html = f'''<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
{html_body}
</body>
</html>'''

css = CSS(string='''
    @page { margin: 2cm; }
    body { font-family: Helvetica, Arial, sans-serif; font-size: 11pt; color: #111; }
    h1 { font-size: 18pt; border-bottom: 2px solid #333; padding-bottom: 4px; }
    h2 { font-size: 14pt; margin-top: 18pt; }
    h3 { font-size: 12pt; margin-top: 12pt; }
    table { border-collapse: collapse; margin: 8pt 0; }
    th, td { border: 1px solid #bbb; padding: 4pt 8pt; }
    th { background: #eee; }
    blockquote { border-left: 3px solid #999; margin-left: 0; padding-left: 12pt; color: #555; }
    ul { margin: 4pt 0; padding-left: 18pt; }
''')

HTML(string=html).write_pdf(reportFile, stylesheets=[css])
print(f'\nReport written to {reportFile}')
