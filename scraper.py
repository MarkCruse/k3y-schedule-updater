import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date, timezone
import random
import time

#last_times = ("0:00", "0:00") 


# ---- Config variables ----
start_dt = date.today()
dt = datetime(2026, 1, start_dt.day)
end_year = 2027
end_date = date(2026, 1, 31)   # last day to process
cleaned_lines = []


# ---- Function definitions ----
def build_url(dt, end_year):
    ymd = dt.strftime("%Y%m%d")
    return (
        f"https://skccgroup.com/cgi-bin/calendar.pl?"
        f"end_year={end_year}&"
        f"datestring={ymd}&"
        f"start_month={dt.month}&"
        f"end_date={dt.day}&"
        f"end_month={dt.month}&"
        f"start_year={dt.year}&"
        f"view=Day&fromTemplate=&"
        f"start_date={dt.day}&style=List&"
        f"selected_datestring={ymd}&style=List"
    )

# ---- Main logic ----
current = start_dt

# DEBUG: Show starting info
print("Scraper starting...")
print(f"Today: {start_dt}, End date: {end_date}")
 
# ---- Loop through each day ----
while current <= end_date:
    URL = build_url(current, end_year)
    #print(URL)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
        lines = response.text.splitlines()
    except Exception as e:
        print(f"Error: {e}")

    # Parse the returned HTML
    soup = BeautifulSoup(response.text, "html.parser")

    first_span = soup.find("span", class_="text")

    if first_span:
        extracted = str(first_span)   # includes full <span class="text">...</span>
    else:
        extracted = ""

    ########## CLEAN UP ROUTINES  ########

    # --- 1. REMOVE TABS ---
    cleaned = extracted.replace("\t", "")

    # --- 2. REMOVE BLANK LINES ---
    lines = [line for line in cleaned.splitlines() if line.strip() != ""]

    # Find the first <dt> index that has a time or K3Y pattern
    start_index = None
    for i, line in enumerate(lines):
        line = line.strip()
        if "<dt>" in line:
            # look ahead a few lines to check for time or K3Y call
            for j in range(1, 6):
                if i+j < len(lines):
                    check_line = lines[i+j].strip()
                    if re.match(r"\d{1,2}:\d{2}", check_line) or "K3Y/" in check_line:
                        start_index = i + 1  # start after this <dt>
                        break
            if start_index is not None:
                break

    if start_index is not None:
        lines = lines[start_index:]
    else:
        # fallback if nothing found
        print("Warning: No session <dt> found, keeping all lines")

    # --- 4. REMOVE LAST TWO LINES (closing tags and </span>) ---
    if len(lines) >= 2:
        lines = lines[:-2]  # drop the last two lines

    # --- 5. CLEAN LINES ---
#    cleaned_lines = []
    for line in lines:
        line = line.lstrip()           # remove leading whitespace

        # remove leading dash only
        if line.startswith("-"):
            line = line[1:].lstrip()

        # skip unwanted lines
        if "•" in line:
            continue
        if ": " in line:
            continue
        if line == "<dd>" or line == "<dt>":
            continue

        cleaned_lines.append(line)

    # --- 6. EXTRACT DATE AND REPLACE ALL LINES CONTAINING 'datestring=' ---
    date_match = re.search(r'datestring=(\d{8})', extracted)
    if date_match:
        datestring = date_match.group(1)              # e.g., '20260117'
        date_obj = datetime.strptime(datestring, "%Y%m%d")
        formatted_date = date_obj.strftime("%m/%d/%y")  # e.g., '01/17/26'

        # Replace all lines containing 'datestring='
        cleaned_lines = [
            formatted_date if 'datestring=' in line else line
            for line in cleaned_lines
        ]

    # --- 7. SPLIT LINES CONTAINING 2 OR 3 DASHES ---
    split_lines = []

    for line in cleaned_lines:
        if '--' in line:
            line = line.replace('--', '-')
        line = line.strip()

        dash_count = line.count('-')

        # Only split if line has 2 or 3 dashes
        if (dash_count >2):
            # split on dash, strip spaces, but keep empty strings
            parts = [part.strip() for part in line.split('-')]
            # If more than 4 parts → merge everything after the 3rd part
            if len(parts) > 4:
                parts = parts[:3] + ['-'.join(parts[3:])]
            # Clean the last element (assumed SKCC number)
            if parts:
                skcc_nr = parts[-1]
                skcc_match = re.match(r'(\d+[CTS]?)', skcc_nr)
                parts[-1] = skcc_match.group(1) if skcc_match else skcc_nr.strip()

            split_lines.extend(parts)
            #print(parts)  # to debug
        else:
            # Keep lines with 0 or 1 dash intact
            split_lines.append(line)


    # --- FINAL CLEANED CONTENT ---
    cleaned = "\n".join(split_lines)

#    with open("output_soup.txt", "w", encoding="utf-8") as f:
#        f.write(cleaned)

    cleaned_lines = [line.strip() for line in cleaned.splitlines() if line.strip()]

    # ---------- Stealth Delay ----------
    time.sleep(random.uniform(2.0, 5.0))  # random delay
    
    current += timedelta(days=1)  # increment day

keys = [
    "utc_start",
    "utc_end",
    "k3y_area",
    "session_date",
    "callsign",
    "name",
    "state",
    "skcc_nr",
]

records = []
# Only iterate over full 8-item blocks
for i in range(0, len(cleaned_lines) - len(cleaned_lines) % 8, 8):
    block = cleaned_lines[i:i+8]
    record = dict(zip(keys, block))
    records.append(record)
# Print a single line or entire file to screen
from pprint import pprint
#pprint(records[0])
#pprint(records)

print(f"Number of records found: {len(records)}")
if records:
    print("Sample record:", records[0])
else:
    print("No records found. Check if page was fetched correctly.")

# ---- Write records to JSON file ----
import os
import json

os.makedirs("data", exist_ok=True)

if records:
    payload = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "records": records
    }
    
    with open("data/schedule-cache.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote {len(records)} records to schedule-cache.json")
else:
    print("No records to write — scraper may have failed or found no data")
