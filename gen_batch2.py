#!/usr/bin/env python3
"""Generate remaining TikTok videos: 0539-2, 0539-3, 0611-1, 0611-2, 0611-3."""

import os, subprocess, time, urllib.parse, urllib.request, tempfile
from pathlib import Path

FFMPEG = "/home/linuxbrew/.linuxbrew/bin/ffmpeg"
VIDEOS_DIR = Path.home() / "projects/tiktok-agent/videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

SERIES = [
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
            "Close-up of phone screen showing a ChatGPT conversation, prompt asks what habit is holding me back the most, dramatic tight framing, 9:16 vertical photorealistic",
            "AI response on phone screen showing the habit of planning without executing, consuming information but postponing real first steps indefinitely, hand holding phone, dramatic reading moment, 9:16 vertical",
            "Continuation of AI response showing not lack of motivation but identity being more comfortable as someone preparing than someone doing, close-up text on phone screen, 9:16 vertical photorealistic",
            "Man sitting up on couch, phone lowered, staring into middle distance, processing expression, apartment behind him slightly out of focus, quiet introspective moment, natural light from window, 9:16 vertical",
            "Same man at desk the next morning, laptop open, coffee in hand, looking at camera with a knowing half-smile, productive morning energy, warm light, 9:16 vertical photorealistic",
        ],
    },
    {
        "out": "series-20260309-0611-1.mp4",
        "slides": [
            "Dramatic close-up of a glowing laptop screen in a dark room, a hooded figure typing rapidly, blue light reflecting on their face, neon digital data streams floating in the air, cinematic lighting, photorealistic, 9:16 vertical",
            "Photorealistic visualization of a person digital footprint, floating social media icons, location pins, credit card symbols, phone numbers, all connected by glowing blue lines forming a web, dark background, 9:16 vertical",
            "Person looking shocked at their phone screen, mouth open, eyes wide, phone showing a data dashboard with personal information, dramatic lighting, Mexican young adult, urban background, photorealistic, 9:16 vertical",
            "Cinematic shot of a smartphone with a glowing AI interface scanning a profile photo, biometric data overlay, face recognition grid lines, high-tech aesthetic, dark moody background, photorealistic, 9:16 vertical",
            "Split screen left side shows a normal person in Mexico City street right side shows a complete digital profile with all their data floating in holographic display, photorealistic, dramatic, 9:16 vertical",
            "Young Mexican person confidently using privacy settings on their phone, clean minimal UI glowing green for protected, hopeful lighting, modern apartment background, photorealistic, 9:16 vertical",
        ],
    },
    {
        "out": "series-20260309-0611-2.mp4",
        "slides": [
            "Young Mexican man at a messy desk on Day 1, overwhelmed by papers and tasks, frustrated expression, warm indoor lighting, laptop open, photorealistic, 9:16 vertical",
            "Same young man on Day 7, slightly more organized desk, experimenting with AI chatbot on screen, curious expression, learning posture, photorealistic, 9:16 vertical",
            "Day 15 the man working confidently, multiple screens with AI tools open, notes everywhere, energized expression, productivity visible, modern Mexican apartment, photorealistic, 9:16 vertical",
            "Day 22 man presenting a polished project on a big screen to colleagues, confident body language, glowing presentation created with AI assistance, professional office setting in Mexico City, photorealistic, 9:16 vertical",
            "Day 30 clean organized desk, man smiling at laptop, calendar showing completed tasks, side-by-side comparison showing before and after productivity charts floating holographically, photorealistic, 9:16 vertical",
            "Man relaxing with coffee, phone showing free time in the evening, peaceful expression, warm sunset through window, modern Mexico City apartment, photorealistic, 9:16 vertical",
        ],
    },
    {
        "out": "series-20260309-0611-3.mp4",
        "slides": [
            "Dramatic split image left side shows busy Mexican office workers at computers right side shows glowing AI robots doing the same tasks, ominous lighting contrast, cinematic, photorealistic, 9:16 vertical",
            "Call center office in Mexico City, rows of agents with headsets, but half the seats are empty, replaced by glowing AI terminals, moody lighting, photorealistic, 9:16 vertical",
            "Accounting office with papers everywhere, a person looking worried at their desk, while a holographic AI interface processes thousands of documents instantly beside them, photorealistic, dramatic, 9:16 vertical",
            "Creative studio a graphic designer looking concerned at their screen while an AI tool generates beautiful designs instantly on the adjacent monitor, photorealistic, modern Mexican creative workspace, 9:16 vertical",
            "Futuristic factory floor in Mexico with robotic arms doing precise work, a few human supervisors watching tablets, clean industrial setting, photorealistic, 9:16 vertical",
            "Confident young Mexican professional smiling, surrounded by glowing AI tools as assistants not replacements, empowered posture, modern tech-forward workspace, hope and opportunity vibe, photorealistic, 9:16 vertical",
        ],
    },
]


def download_image(prompt, out_path, retries=4):
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&model=flux"
    for attempt in range(retries):
        try:
            if attempt > 0:
                wait = 15 * attempt
                print(f"    Waiting {wait}s before retry...")
                time.sleep(wait)
            print(f"    Attempt {attempt+1}...", flush=True)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            if len(data) < 5000:
                print(f"    Too small ({len(data)}b), retrying...")
                continue
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"    OK ({len(data)//1024}KB)", flush=True)
            return True
        except Exception as e:
            print(f"    Error: {e}", flush=True)
    return False


def make_fallback(out_path):
    cmd = [FFMPEG, "-y", "-f", "lavfi", "-i", "color=c=0x111122:s=1080x1920",
           "-frames:v", "1", "-q:v", "2", out_path]
    subprocess.run(cmd, capture_output=True)
    print(f"    Fallback created", flush=True)


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
        print(f"  ffmpeg error: {result.stderr[-500:]}", flush=True)
        return False
    print(f"  Saved {out_file} ({os.path.getsize(out_file)//1024}KB)", flush=True)
    return True


for series in SERIES:
    out = VIDEOS_DIR / series["out"]
    if out.exists() and out.stat().st_size > 10000:
        print(f"Skip {series['out']} (exists)")
        continue
    print(f"\n=== {series['out']} ===", flush=True)
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i, prompt in enumerate(series["slides"]):
            p = os.path.join(tmp, f"slide{i+1}.jpg")
            print(f"  Slide {i+1}/6...", flush=True)
            if not download_image(prompt, p):
                make_fallback(p)
            paths.append(p)
        make_video(paths, out)

print("\nAll done!", flush=True)
