#!/usr/bin/env python3
"""Run series 8 only with updated timestamp."""
import sys
sys.path.insert(0, '/home/clawd/projects/tiktok-agent')

from gen_batch import SERIES, process_series

for series in SERIES:
    if series["number"] != 8:
        continue
    series = dict(series, timestamp="20260309-0213")
    try:
        path = process_series(series)
        print(f"✅ Series 8 done: {path}")
    except Exception as e:
        print(f"❌ Series 8 failed: {e}")
        import traceback; traceback.print_exc()
