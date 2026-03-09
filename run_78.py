#!/usr/bin/env python3
"""Run series 7 and 8 only with updated timestamp."""
import sys
sys.path.insert(0, '/home/clawd/projects/tiktok-agent')

# Patch the timestamp for series 7 and 8
from gen_batch import SERIES, process_series, VIDEOS_DIR

# Update timestamps and run only 7 and 8
results = []
for series in SERIES:
    if series["number"] not in (7, 8):
        continue
    series = dict(series, timestamp="20260309-0213")
    try:
        path = process_series(series)
        results.append((series["number"], path, True))
    except Exception as e:
        print(f"  ❌ Series {series['number']} failed: {e}")
        results.append((series["number"], None, False))

print("\nSUMMARY")
for num, path, ok in results:
    status = "✅" if ok else "❌"
    print(f"  Series {num}: {status} {path or 'FAILED'}")
