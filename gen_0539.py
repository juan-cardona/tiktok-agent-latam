#!/usr/bin/env python3
"""Generate TikTok videos for 0539 batch."""

import os, subprocess, time, urllib.parse, urllib.request, tempfile
from pathlib import Path

FFMPEG = "/home/linuxbrew/.linuxbrew/bin/ffmpeg"
VIDEOS_DIR = Path.home() / "projects/tiktok-agent/videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

SERIES = [
    {
        "out": "series-20260309-0539-1.mp4",
        "slides": [
            "Young Mexican entrepreneur in his late 20s, sitting at a coffee shop in Condesa CDMX, laptop open, expression of nervous anticipation, warm afternoon light through window, shallow depth of field, cinematic 9:16 vertical photorealistic",
            "Close-up of laptop screen showing a business plan document, hand typing into a ChatGPT prompt asking for honest feedback, dark espresso cup beside keyboard, dramatic side lighting, 9:16 vertical photorealistic",
            "Phone screen showing a structured AI response with sections Lo que funciona and Lo que no funciona, bullet points visible, honest critical tone, hand holding phone against blurred cafe background, 9:16 vertical",
            "Close-up of man face reading screen, expression shifting from confident to thoughtful to quietly humbled, window light catching his eyes, candid emotional moment, 9:16 vertical photorealistic",
            "Same man at whiteboard in small home office, rewriting the business model, sticky notes everywhere, energized body language, late night lamp light, 9:16 vertical photorealistic",
            "Man looking directly at camera, calm confident smile, CDMX skyline visible through apartment window at dusk, direct intimate eye contact, 9:16 vertical photorealistic",
        ],
    },
    {
        "out": "series-20260309-0539-2.mp4",
        "slides": [
            "Aerial view of Tepito neighborhood in Mexico City, dense urban grid, colorful tarps over market stalls, street life below, golden hour drone shot, ultra-photorealistic 9:16 vertical",
            "AI-generated redesign of Tepito as thriving cultural creative district, murals covering every building, outdoor galleries, street art museums integrated into existing architecture, crowds of tourists and locals mixing, vibrant daytime, 9:16 vertical photorealistic",
            "AI-imagined Tepito as neon-lit night market destination, lantern-strung alleys, artisan food stalls, live music stages built into repurposed market structures, Tokyo-meets-CDMX aesthetic, 9:16 vertical photorealistic",
            "AI concept of Tepito with vertical gardens climbing building facades, rooftop community gardens, solar-powered street lighting, wide tree-lined pedestrian avenues replacing car traffic, photorealistic dusk, 9:16 vertical",
            "Street-level photo of Tepito market, authentic gritty beauty, vendors, movement, real life, warm imperfect documentary style, 9:16 vertical photorealistic",
            "Wide shot of Mexico City skyline at night from rooftop, city lights stretching to horizon, sense of potential and scale, 9:16 vertical cinematic",
        ],
    },
    {
        "out": "series-20260309-0539-3.mp4",
        "slides": [
            "Young Mexican man late 20s lying on couch scrolling phone at 2am, apartment lights dim, expression of mild restlessness, blue phone light on face, relatable everyday scene, photorealistic 9:16 vertical",
            "Close-up of phone screen showing a ChatGPT conversation, prompt reads asking the AI what habit is holding me back the most, dramatic tight framing, 9:16 vertical photorealistic",
            "AI response on phone screen: El habito de planear sin ejecutar. Consumes informacion, disenas sistemas, pero el primer paso real lo pospones indefinidamente, hand holding phone, dramatic reading moment, 9:16 vertical",
            "Continuation of AI response: No es falta de motivacion. Es que tu identidad esta mas comoda siendo alguien que esta preparandose que alguien que esta haciendo, close-up text, 9:16 vertical photorealistic",
            "Man sitting up on couch, phone lowered, staring into middle distance, processing expression, apartment behind him slightly out of focus, quiet introspective moment, natural light from window, 9:16 vertical",
            "Same man at desk the next morning, laptop open, coffee in hand, looking at camera with a knowing half-smile, productive morning energy, warm light, 9:16 vertical photorealistic",
        ],
    },
]


def download_image(prompt, out_path, retries=4):
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&model=flux"
    for attempt in range(retries):
        try:
            if attempt > 0:
                wait = 12 * attempt
                print(f"  Waiting {wait}s before retry...")
                time.sleep(wait)
            print(f"  Downloading (attempt {attempt+1})...")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            if len(data) < 5000:
                print(f"  Too small ({len(data)}b), retrying...")
                continue
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"  OK ({len(data)//1024}KB)")
            return True
        except Exception as e:
            print(f"  Error: {e}")
    return False


def make_fallback(out_path):
    cmd = [FFMPEG, "-y", "-f", "lavfi", "-i", "color=c=0x111122:s=1080x1920",
           "-frames:v", "1", "-q:v", "2", out_path]
    subprocess.run(cmd, capture_output=True)


def make_video(slide_paths, out_file):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        list_file = f.name
        for p in slide_paths:
            f.write(f"file '{p}'\nduration 3\n")
        f.write(f"file '{slide_paths[-1]}'\n")

    cmd = [
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
        "-movflags", "+faststart", str(out_file)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(list_file)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-500:]}")
        return False
    print(f"  Saved: {out_file} ({os.path.getsize(out_file)//1024}KB)")
    return True


for series in SERIES:
    out = VIDEOS_DIR / series["out"]
    if out.exists() and out.stat().st_size > 10000:
        print(f"Skipping {series['out']} (exists)")
        continue
    print(f"\n=== {series['out']} ===")
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i, prompt in enumerate(series["slides"]):
            p = os.path.join(tmp, f"slide{i+1}.jpg")
            print(f"  Slide {i+1}/6...")
            if not download_image(prompt, p):
                print(f"  Fallback slide {i+1}")
                make_fallback(p)
            paths.append(p)
        make_video(paths, out)

print("\nAll done!")
