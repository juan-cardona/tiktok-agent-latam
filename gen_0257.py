#!/usr/bin/env python3
"""Generate TikTok videos for 0257 batch (scripts 1-3)."""

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
            "Photorealistic 9:16 vertical. Close-up of a phone screen showing a ChatGPT conversation in Spanish with prompt: Ayudame a negociar un aumento de sueldo del 40%. Hands holding phone, blurred office background. Documentary style, warm office lighting.",
            "Photorealistic 9:16 vertical. Phone screen showing a numbered list of salary negotiation talking points in Spanish. Professional, clean UI. Person's hands visible, manicured nails. Shallow depth of field, bokeh background.",
            "Photorealistic 9:16 vertical. Same young woman at a conference table, confident posture, subtle smile, eye contact with the camera. She's mid-conversation. Natural corporate lighting, notepad visible on table. Candid editorial style.",
            "Photorealistic 9:16 vertical. Woman on phone outside office building, celebrating quietly, fist pump, big smile. CDMX street background with iconic Reforma trees. Afternoon golden light. Natural, joyful, candid.",
            "Photorealistic 9:16 vertical. Same woman looking directly into camera, inviting smile, holding phone toward viewer. Modern CDMX apartment background, plants, warm light. Space left at bottom third for text overlay.",
        ],
    },
    {
        "out": "series-20260309-0325-2.mp4",
        "slides": [
            "Futuristic photorealistic 9:16 vertical. A stunning reimagination of Mexico City Metro Line 1 in 2050. Sleek maglev trains in metallic silver-gold with aztec geometric patterns, levitating above the tracks. Passengers in futuristic casual wear. Bright clean station with biopunk vegetation on walls. Cinematic sci-fi realism.",
            "Futuristic photorealistic 9:16 vertical. The Zocalo of Mexico City in 2050. The Cathedral and National Palace are perfectly preserved but surrounded by gleaming eco-towers with vertical gardens. Flying taxis visible in sky. Aztec-inspired architecture fused with ultra-modern glass and steel. Golden hour lighting.",
            "Futuristic photorealistic 9:16 vertical. Polanco neighborhood 2050. Tree-covered pedestrian megabridge over Presidente Masaryk, luxury shops below, automated delivery drones flying between buildings. Mexican fashion brands on sleek storefronts. Lush, clean, vibrant. Late afternoon light.",
            "Futuristic photorealistic 9:16 vertical. Tepito market in 2050. Vibrant and alive — drone delivery hubs mixed with traditional market stalls, holographic price displays, same authentic CDMX energy but elevated. Street art murals covering solar panel facades. Real people, real culture, just futuristic.",
            "Futuristic photorealistic 9:16 vertical. Xochimilco canals in 2050. The trajineras are now solar-powered but keep their traditional flower decorations. Crystal clear restored water. Floating gardens chinampas thriving. Biopunk utopian vision, warm sunset colors.",
            "Futuristic photorealistic 9:16 vertical. Aerial view of Mexico City 2050 at twilight — green corridors, glowing city grid, massive central park where Periferico used to be. Stunning, aspirational. Space at bottom for text overlay.",
        ],
    },
    {
        "out": "series-20260309-0325-3.mp4",
        "slides": [
            "Photorealistic 9:16 vertical. Split screen: left side shows stressed Mexican office worker surrounded by stacks of printed spreadsheets and reports, fluorescent lighting, tired expression. Right side shows same person relaxed at clean desk with single laptop, coffee, plant, smiling. Stark lifestyle contrast, editorial style.",
            "Photorealistic 9:16 vertical. Close-up of a laptop screen showing a complex Excel spreadsheet with hundreds of rows of data, formulas, pivot tables. Hands typing in low office lighting. Overwhelming, chaotic, lots of numbers. Authentic Mexican corporate office vibe.",
            "Photorealistic 9:16 vertical. Same laptop but now showing a clean ChatGPT conversation in Spanish. The prompt asks for analysis of a dataset. The response is a clean, structured executive summary in bullet points. Screen glow on face, look of relief and surprise.",
            "Photorealistic 9:16 vertical. Phone screen showing a beautifully formatted report with charts and insights, generated by AI. Professional, polished, ready to send to the boss. Person's thumb scrolling through it. Clean desk, natural light.",
            "Photorealistic 9:16 vertical. Young Mexican professional in casual business clothes walking confidently into a glass-walled meeting room, laptop under arm, slight smirk. CDMX office building interior. Other colleagues visible through glass. Confident, winning.",
            "Photorealistic 9:16 vertical. Person at desk looking directly at camera with a knowing smile, laptop open. Modern home office setup. Direct eye contact, inviting. Warm lighting. Space at bottom third for text overlay.",
        ],
    },
]


def download_image(prompt, out_path, retries=3):
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&model=flux"
    for attempt in range(retries):
        try:
            print(f"  Downloading (attempt {attempt+1})...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if len(data) < 5000:
                print(f"  Too small ({len(data)} bytes), retrying...")
                time.sleep(5)
                continue
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"  OK ({len(data)} bytes)")
            return True
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(5)
    return False


def make_fallback_slide(out_path):
    cmd = [FFMPEG, "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=1",
           "-frames:v", "1", out_path]
    subprocess.run(cmd, capture_output=True)


def make_video(slides, out_file):
    with tempfile.TemporaryDirectory() as tmp:
        # Download slides
        slide_paths = []
        for i, prompt in enumerate(slides):
            path = os.path.join(tmp, f"slide{i+1}.jpg")
            print(f"  Slide {i+1}/6...")
            ok = download_image(prompt, path)
            if not ok:
                print(f"  Using fallback for slide {i+1}")
                make_fallback_slide(path)
            slide_paths.append(path)

        # Build video with xfade transitions
        # Each slide: 3s display + 0.5s fade. Total = 6*3 - 5*0.5 = 15.5s
        duration = 3.0
        fade = 0.5

        # Create input args and filter
        inputs = []
        for p in slide_paths:
            inputs += ["-loop", "1", "-t", str(duration + fade), "-i", p]

        # Build xfade filter chain
        filter_parts = []
        prev = "[0:v]"
        for i in range(1, len(slide_paths)):
            offset = i * duration - (i - 1) * fade  # approx offset
            # Actually use cumulative: offset = i * duration - i * 0 for simpler approach
            offset = i * (duration - fade) + (i - 1) * fade
            # Simpler: just use i * duration - i * fade * 0.5
            # offset for xfade: when transition starts = sum of previous slide durations
            offset = duration * i - fade * i + fade * (i - 1)
            # Clean formula: slide i starts playing at time = (i-1)*(duration-fade)+something
            # Let's use: offset = (i) * duration - (i) * fade
            offset = round(i * duration - i * fade + (i - 1) * fade, 3)
            # Simplest: offset = i * (duration - fade)
            offset = round(i * (duration - fade), 3)
            curr = f"[{i}:v]"
            out_label = f"[v{i}]" if i < len(slide_paths) - 1 else "[vout]"
            filter_parts.append(f"{prev}{curr}xfade=transition=fade:duration={fade}:offset={offset}{out_label}")
            prev = f"[v{i}]"

        filter_str = ";".join(filter_parts)

        cmd = [FFMPEG, "-y"] + inputs + [
            "-filter_complex", filter_str,
            "-map", "[vout]",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-r", "30", "-movflags", "+faststart",
            str(out_file)
        ]
        print(f"  Running ffmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ffmpeg error: {result.stderr[-500:]}")
            return False
        print(f"  Video saved: {out_file}")
        return True


for series in SERIES:
    out = VIDEOS_DIR / series["out"]
    if out.exists():
        print(f"Skipping {series['out']} (already exists)")
        continue
    print(f"\n=== Generating {series['out']} ===")
    ok = make_video(series["slides"], out)
    if not ok:
        print(f"FAILED: {series['out']}")

print("\nDone!")
