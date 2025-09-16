import os
import re
import math
from jiwer import wer

def tokenize(s):
    return re.findall(r"\w+", s)

def levenshtein_distance(ref, hyp):
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
                dp[i-1][j] + 1,
                dp[i][j-1] + 1,
                dp[i-1][j-1] + cost
            )
    return dp[n][m]

def extract_blocks(filepath):
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

def compute_session_metrics(comparison_filepath):
    blocks = extract_blocks(comparison_filepath)
    lev_distances = []
    wer_vals = []
    for blk in blocks:
        cleaned = blk.get('cleaned', '')
        whisper = blk.get('whisper', '')
        lev = levenshtein_distance(cleaned, whisper)
        error_rate = wer(cleaned, whisper)
        lev_distances.append(lev)
        wer_vals.append(error_rate)
    if not lev_distances:
        return None  # skip empty sessions
    session_total = sum(lev_distances)
    session_average = sum(lev_distances) / len(lev_distances)
    session_median = sorted(lev_distances)[len(lev_distances)//2]
    session_stddev = math.sqrt(sum((x - session_average)**2 for x in lev_distances) / len(lev_distances))
    wer_average = sum(wer_vals)/len(wer_vals)
    return {
        "total_levenshtein": session_total,
        "average_levenshtein": session_average,
        "median_levenshtein": session_median,
        "stddev_levenshtein": session_stddev,
        "average_wer": wer_average,
        "event_count": len(lev_distances)
    }
