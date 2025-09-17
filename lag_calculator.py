import re
import statistics
from datetime import timedelta

def parse_timecode(tc):
    # Accepts MM:SS or HH:MM:SS and returns total seconds
    parts = tc.split(":")
    if len(parts) == 2:
        return timedelta(minutes=int(parts[0]), seconds=int(parts[1]))
    elif len(parts) == 3:
        return timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))
    else:
        return timedelta(0)

def extract_lag_times(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        transcript = f.read()

    # Only keeps text before the RECALL AND FEEDBACK
    split_marker = "RECALL AND FEEDBACK"
    transcript = transcript.split(split_marker)[0]

    entry_pattern = re.compile(r'([A-Za-z_]+) \[(\d{2}:\d{2})-(\d{2}:\d{2})\]: ([^\n]*)', re.IGNORECASE)

    entries = []
    for match in entry_pattern.finditer(transcript):
        speaker, start, end, text = match.groups()
        speaker_norm = speaker.strip().upper()
        if speaker_norm in ['PEPPER', 'CHILD']:
            entries.append({
                'speaker': speaker_norm,
                'start': parse_timecode(start),
                'end': parse_timecode(end),
                'text': text.strip()
            })

# Usage:
# lag_results = extract_lag_times("/mnt/c/Users/olutu/Downloads/cleaned_transcriptions/FRIAM07.txt")
# for lag in lag_results:
#     print(lag)

# Separate lag times
pepper_to_child_lags = [entry['lag_seconds'] for entry in lag_results if entry['type'] == 'Pepper to Child']
child_to_pepper_lags = [entry['lag_seconds'] for entry in lag_results if entry['type'] == 'Child to Pepper']

def print_stats(label, lag_list):
    if lag_list:
        print(f"{label} Statistics:")
        print(f"  Count: {len(lag_list)}")
        print(f"  Mean: {statistics.mean(lag_list):.2f} s")
        print(f"  Median: {statistics.median(lag_list):.2f} s")
        print(f"  Standard Deviation: {statistics.stdev(lag_list):.2f} s" if len(lag_list) > 1 else "  Standard Deviation: N/A")
        print(f"  Min: {min(lag_list):.2f} s")
        print(f"  Max: {max(lag_list):.2f} s\n")
    else:
        print(f"{label}: No entries\n")

print_stats("Pepper to Child", pepper_to_child_lags)
print_stats("Child to Pepper", child_to_pepper_lags)
