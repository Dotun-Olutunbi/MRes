import re
from jiwer import wer
from difflib import SequenceMatcher

def tokenize(s):
    # Tokenizer for word-level comparison
    return re.findall(r"\w+", s)


def levenshtein_distance(ref, hyp):
    """Computes word-level Levenshtein distance between two token lists."""
    # Use dynamic programming for word-level
    r, h = tokenize(ref), tokenize(hyp)
    n, m = len(r), len(h)
    dp = [[0]*(m+1) for _ in range(n+1)]
    for i in range(n+1):
        dp[i][0] = i
    for j in range(m+1):
        dp[0][j] = j
    for i in range(1, n+1):
        for j in range(1, m+1):
            cost = 0 if r[i-1] == h[j-1] else 1
            dp[i][j] = min(
                dp[i-1][j] + 1,      # deletion
                dp[i][j-1] + 1,      # insertion
                dp[i-1][j-1] + cost  # substitution
            )
    return dp[n][m]

def extract_blocks(filepath):
    # Extracts per-stage blocks from the formatted comparison file.
    blocks = []
    with open(filepath, 'r', encoding='utf8') as f:
        lines = [line.rstrip() for line in f]
    block = {}
    for line in lines:
        if not line.strip():
            if block:
                blocks.append(block)
                block = {}
        elif re.match(r'^(PICTURE \d+|STAGE B)', line):
            block['stage'] = line.strip()
        elif line.startswith("CHILD [CLEANED]:"):
            block['cleaned'] = line[len("CHILD [CLEANED]:"):].strip()
        elif line.startswith("CHILD-TRANSCRIPT [Whisper]:"):
            block['whisper'] = line[len("CHILD-TRANSCRIPT [Whisper]:"):].strip()
    if block:
        blocks.append(block)
    return blocks

def compute_metrics_for_file(filepath):
    blocks = extract_blocks(filepath)
    result = []
    for blk in blocks:
        stage = blk.get('stage', 'UNKNOWN')
        cleaned = blk.get('cleaned', '')
        whisper = blk.get('whisper', '')
        lev = levenshtein_distance(cleaned, whisper)
        # word error rate (jiwer) expects normal sentences
        error_rate = wer(cleaned, whisper)
        result.append({
            'stage': stage,
            'levenshtein': lev,
            'wer': error_rate,
            'cleaned': cleaned,
            'whisper': whisper
        })
    return result

if __name__ == "__main__":
    filename = "FRIAM02_Comparison2.txt"
    metrics = compute_metrics_for_file(filename)
    for item in metrics:
        print(f"{item['stage']}: Levenshtein={item['levenshtein']}, WER={item['wer']:.2f}")
    
    print("\nSession Summary:")
    lev_distances = [item['levenshtein'] for item in metrics]
    session_total = sum(lev_distances)
    session_average = sum(lev_distances) / len(lev_distances)
    session_median = sorted(lev_distances)[len(lev_distances)//2]
    # For standard deviation (optional, needs math import)
    import math
    session_stddev = math.sqrt(sum((x - session_average)**2 for x in lev_distances) / len(lev_distances))

    print(f"Total session Levenshtein errors: {session_total}")
    print(f"Average errors for this session: {session_average:.2f}")
    print(f"Median errors per event: {session_median}")
    print(f"Std deviation: {session_stddev:.2f}")
        
    
