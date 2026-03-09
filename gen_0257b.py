#!/usr/bin/env python3
"""Generate TikTok videos for 0257 batch — fixed ffmpeg pipeline."""

import os
import subprocess
import time
import urllib.parse
import urllib.request
import tempfile
from pathlib import Path

FFMPEG = "/home/linuxbrew/.linuxbrew/bin/ffmpeg"
VIDEOS_DIR = Path.home() / "projects/tiktok-agent/videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

SERIES = [
    {
        "out": "series-20260309-0325-1.mp4",
        "slides": [
            "Photorealistic 9:16 vertical. A confident young Mexican woman in her late 20s sitting across from a suited manager at a corporate desk, arms crossed, looking calm and powerful. The manager looks slightly nervous. Modern Mexico City office, floor-to-ceiling windows, city skyline at golden hour. Cinematic, high contrast.",
            "Photorealistic 9:16 vertical. Close-up of a phone screen showing a ChatGPT conversation in Spanish with prompt asking to help negotiate a 40 percent salary raise. Hands holding phone, blurred office background. Documentary style, warm office lighting.",
            "Photorealistic 9:16 vertical. Phone screen showing a numbered list of salary negotiation talking points in Spanish. Professional, clean UI. Person hands visible, manicured nails. Shallow depth of field, bokeh background.",
            "Photorealistic 9:16 vertical. Young Mexican woman at a conference table, confident posture, subtle smile, eye contact with the camera. She is mid-conversation. Natural corporate lighting, notepad visible on table. Candid editorial style.",
            "Photorealistic 9:16 vertical. Woman on phone outside office building, celebrating quietly, fist pump, big smile. CDMX street background with iconic Reforma trees. Afternoon golden light. Natural, joyful, candid.",
            "Photorealistic 9:16 vertical. Same woman looking directly into camera, inviting smile, holding phone toward viewer. Modern CDMX apartment background, plants, warm light.",
        ],
    },
    {
        "out": "series-20260309-0325-2.mp4",
        "slides": [
            "Futuristic photorealistic 9:16 vertical. Mexico City Metro Line 1 in 2050. Sleek maglev trains in metallic silver-gold with aztec geometric patterns, levitating above the tracks. Passengers in futuristic casual wear. Bright clean station with biopunk vegetation on walls. Cinematic sci-fi realism.",
            "Futuristic photorealistic 9:16 vertical. The Zocalo of Mexico City in 2050. The Cathedral and National Palace preserved but surrounded by gleaming eco-towers with vertical gardens. Flying taxis in sky. Aztec-inspired architecture fused with ultra-modern glass and steel. Golden hour.",
            "Futuristic photorealistic 9:16 vertical. Polanco neighborhood 2050. Tree-covered pedestrian megabridge over Presidente Masaryk, luxury shops below, automated delivery drones flying between buildings. Lush, clean, vibrant. Late afternoon light.",
            "Futuristic photorealistic 9:16 vertical. Tepito market in 2050. Vibrant and alive with drone delivery hubs mixed with traditional market stalls, holographic price displays. Street art murals covering solar panel facades. Real culture, futuristic.",
            "Futuristic photorealistic 9:16 vertical. Xochimilco canals in 2050. Trajineras now solar-powered but keeping traditional flower decorations. Crystal clear restored water. Floating gardens thriving. Biopunk utopian vision, warm sunset colors.",
            "Futuristic photorealistic 9:16 vertical. Aerial view of Mexico City 2050 at twilight — green corridors, glowing city grid, massive central park where Periferico used to be. Stunning, aspirational cityscape.",
        ],
    },
]


def download_image(prompt, out_path, retries=4):
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&model=flux"
    for attempt in range(retries):
        try:
            if attempt > 0:
                wait = 10 * attempt
                print(f"  Waiting {wait}s before retry...")
                time.sleep(wait)
            print(f"  Downloading (attempt {attempt+1})...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            if len(data) < 5000:
                print(f"  Too small ({len(data)} bytes), retrying...")
                continue
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"  OK ({len(data)} bytes)")
            return True
        except Exception as e:
            print(f"  Error: {e}")
    return False


def make_fallback_slide(out_path):
    """Create a solid black 1080x1920 JPEG as fallback."""
    cmd = [FFMPEG, "-y", "-f", "lavfi", "-i", "color=c=0x1a1a2e:s=1080x1920",
           "-frames:v", "1", "-q:v", "2", out_path]
    subprocess.run(cmd, capture_output=True)
    print(f"  Fallback slide created")


def make_video(slide_paths, out_file):
    """Combine slides into video using simple concat (no xfade — more compatible)."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        list_file = f.name
        for p in slide_paths:
            f.write(f"file '{p}'\n")
            f.write("duration 3\n")
        # repeat last frame
        f.write(f"file '{slide_paths[-1]}'\n")

    cmd = [
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-movflags", "+faststart",
        str(out_file)
    ]
    print(f"  Running ffmpeg concat...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(list_file)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-800:]}")
        return False
    size = os.path.getsize(out_file)
    print(f"  Video saved: {out_file} ({size//1024}KB)")
    return True


for series in SERIES:
    out = VIDEOS_DIR / series["out"]
    if out.exists():
        print(f"Skipping {series['out']} (already exists)")
        continue
    print(f"\n=== Generating {series['out']} ===")
    with tempfile.TemporaryDirectory() as tmp:
        slide_paths = []
        for i, prompt in enumerate(series["slides"]):
            path = os.path.join(tmp, f"slide{i+1}.jpg")
            print(f"  Slide {i+1}/6...")
            ok = download_image(prompt, path)
            if not ok:
                print(f"  Using fallback for slide {i+1}")
                make_fallback_slide(path)
            slide_paths.append(path)
        ok = make_video(slide_paths, out)
        if not ok:
            print(f"FAILED: {series['out']}")

print("\nAll done!")
