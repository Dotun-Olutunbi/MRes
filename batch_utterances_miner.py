import os
import re
from collections import defaultdict

# WHISPER_TRANSCRIPT_FILE = "/mnt/c/Documents and Settings/olutu/Downloads/whisper_transcriptions/TUEPM30_2025-08-05_16-07-37.txt"
# CLEANED_TRANSCRIPT_FILE = "/mnt/c/Documents and Settings/olutu/Downloads/cleaned_transcriptions/TUEPM30.txt"
# OUTPUT_COMPARISON_FILE = "/mnt/c/Documents and Settings/olutu/Downloads/wer_processing_transcriptions/TUEPM30_Comparison.txt"

WHISPER_FOLDER = "/mnt/c/Documents and Settings/olutu/Downloads/whisper_transcriptions/"
CLEANED_FOLDER = "/mnt/c/Documents and Settings/olutu/Downloads/cleaned_transcriptions/"
OUTPUT_FOLDER = "/mnt/c/Documents and Settings/olutu/Downloads/wer_processing_transcriptions/"


def normalize_event_label(event_label):
    """
    Normalize stage/event labels consistently:
    - Converts 'SHOWING PICTURE X' to 'PICTURE X'
    - Merges 'STAGE 2' and 'STAGE B' as 'STAGE B'
    - Converts to uppercase for consistency
    """
    label = event_label.strip().upper()
    if label in ["STAGE 2", "STAGE B"]:
        return "STAGE B"
    match = re.match(r"SHOWING PICTURE (\d+)", label)
    if match:
        return f"PICTURE {match.group(1)}"
    return label

def extract_whisper_event_utterances(text):
    """
    Extracts the child utterances per event from the Whisper-generated transcription file.
    Returns a dictionary: event -> list of utterances
    """
    event_to_utterances = defaultdict(list)
    current_event = None
    for line in text.splitlines():
        event_header = re.match(r"EXP-EVENT: ([\w\s]+)", line)
        if event_header:
            current_event = normalize_event_label(event_header.group(1))
            continue
        if line.startswith("CHILD-TRANSCRIPT:") and current_event:
            utterance = re.sub(r"CHILD \[[^\]]+\]:\s*", "", line.split(":", 1)[-1]).strip()
            if utterance:
                event_to_utterances[current_event].append(utterance)
    return event_to_utterances

def extract_cleaned_event_utterances(text):
    """
    Extracts child utterances per event from the manually cleaned transcript.
    Returns a dictionary: event -> list of utterances
    """
    event_to_utterances = defaultdict(list)
    current_event = None
    for line in text.splitlines():
        event_header = re.match(r"^(PICTURE \d+|STAGE 2|STAGE B|SHOWING PICTURE \d+)", line, re.IGNORECASE)
        if event_header:
            current_event = normalize_event_label(event_header.group(1))
            continue
        child_speech = re.match(r"^CHILD \[[\d:.-]+\]:\s*(.*)", line)
        if child_speech and current_event:
            utterance = child_speech.group(1).strip()
            if utterance:
                event_to_utterances[current_event].append(utterance)
    return event_to_utterances

def natural_event_sort_key(event_label):
    """
    Sorts events so 'PICTURE 1', 'PICTURE 2' ... appear before 'STAGE B'.
    """
    match = re.match(r"PICTURE (\d+)", event_label)
    if match:
        return (0, int(match.group(1)))
    if event_label.startswith("STAGE"):
        return (1, event_label)
    return (2, event_label)

def batch_process_files():
    count=0
    whisper_files = [f for f in os.listdir(WHISPER_FOLDER) if f.endswith(".txt")]
    for whisper_file in whisper_files:
        # Find the base filename (e.g., "TUEPM30" from "TUEPM30_2025-08-05_16-07-37.txt")
        match = re.match(r"(.+)_\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}\.txt$", whisper_file)
        if not match:
            continue # skip files that don't match expected pattern
        base_name = match.group(1)
        cleaned_file = base_name + ".txt"
        whisper_path = os.path.join(WHISPER_FOLDER, whisper_file)
        cleaned_path = os.path.join(CLEANED_FOLDER, cleaned_file)
        output_file = base_name + "_Comparison.txt"
        output_path = os.path.join(OUTPUT_FOLDER, output_file)
        
         # Skip if output already exists
        if os.path.exists(output_path):
            print(f"Skipping {output_file}, already exists.")
            count+=1
            continue

        # Making sure the cleaned transcript exists
        if not os.path.exists(cleaned_path):
            print(f"Skipped {whisper_file}, no cleaned transcript found ({cleaned_file})")
            continue

        # Read and process as before
        with open(whisper_path, "r", encoding="utf8") as f:
            whisper_text = f.read()
        with open(cleaned_path, "r", encoding="utf8") as f:
            cleaned_text = f.read()
        whisper_utterances_by_event = extract_whisper_event_utterances(whisper_text)
        cleaned_utterances_by_event = extract_cleaned_event_utterances(cleaned_text)
        all_events = sorted(set(whisper_utterances_by_event.keys()) | set(cleaned_utterances_by_event.keys()),
                            key=natural_event_sort_key)
        output_lines = []
        for event in all_events:
            cleaned_utterances = ' '.join(cleaned_utterances_by_event.get(event, []))
            whisper_utterances = ' '.join(whisper_utterances_by_event.get(event, []))
            output_lines.append(f"{event}")
            output_lines.append(f"CHILD [CLEANED]: {cleaned_utterances}")
            output_lines.append(f"CHILD-TRANSCRIPT [Whisper]: {whisper_utterances}")
            output_lines.append("")
        with open(output_path, "w", encoding="utf8") as fout:
            fout.write('\n'.join(output_lines))
        print(f"Comparison file saved as: {output_path}")
    print(f"Total files processed/skipped: {count}")

if __name__ == "__main__":
    batch_process_files()

