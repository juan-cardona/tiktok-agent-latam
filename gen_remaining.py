#!/usr/bin/env python3
"""Generate remaining videos: 0742-2 and 0742-3."""
import os, subprocess, time, urllib.parse, urllib.request, tempfile, re
from pathlib import Path

FFMPEG = "/home/linuxbrew/.linuxbrew/bin/ffmpeg"
VIDEOS_DIR = Path.home() / "projects/tiktok-agent/videos"

def extract_prompts(path):
    content = open(path).read()
    # Extract "Image prompt: `...`" pattern
    prompts = re.findall(r'Image prompt:\s*`([^`]+)`', content)
    if len(prompts) == 6:
        return prompts
    # Fallback: numbered photorealistic descriptions
    prompts = re.findall(r'\d+\.\s+\*\*Slide[^*]*\*\*\s*\n\s+(?:Text:[^\n]+\n\s+)?(?:Image prompt:\s*`([^`]+)`|([A-Z][^\n]{20,}))', content)
    return [p[0] or p[1] for p in prompts if p[0] or p[1]][:6]

SERIES = [
    ("script-20260309-0742-2.md", "series-20260309-0742-2.mp4"),
    ("script-20260309-0742-3.md", "series-20260309-0742-3.mp4"),
]

def download_image(prompt, out_path, retries=4):
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&model=flux"
    for attempt in range(retries):
        try:
            if attempt > 0:
                wait = 20 * attempt
                print(f"    Waiting {wait}s...", flush=True)
                time.sleep(wait)
            print(f"    Attempt {attempt+1}...", flush=True)
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as resp:
                data = resp.read()
            if len(data) < 5000:
                print(f"    Too small ({len(data)}b)", flush=True)
                time.sleep(10)
                continue
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"    OK ({len(data)//1024}KB)", flush=True)
            return True
        except Exception as e:
            print(f"    Error: {e}", flush=True)
    return False

def make_fallback(out_path):
    cmd = [FFMPEG, "-y", "-f", "lavfi", "-i", "color=c=0x1a1a2e:s=1080x1920",
           "-frames:v", "1", "-q:v", "2", out_path]
    subprocess.run(cmd, capture_output=True)

def make_video(slide_paths, out_file):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        list_file = f.name
        for p in slide_paths:
            f.write(f"file '{p}'\nduration 3\n")
        f.write(f"file '{slide_paths[-1]}'\n")
    cmd = [FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", list_file,
           "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", str(out_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    os.unlink(list_file)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-300:]}", flush=True)
        return False
    print(f"  Saved {out_file} ({os.path.getsize(out_file)//1024}KB)", flush=True)
    return True

drafts = Path.home() / "projects/tiktok-agent/drafts"
for script_name, out_name in SERIES:
    out = VIDEOS_DIR / out_name
    if out.exists() and out.stat().st_size > 10000:
        print(f"Skip {out_name}")
        continue
    script_path = drafts / script_name
    prompts = extract_prompts(str(script_path))
    print(f"\n=== {out_name} ({len(prompts)} prompts) ===", flush=True)
    if len(prompts) < 6:
        print(f"  Only got {len(prompts)} prompts, padding with fallbacks", flush=True)
        while len(prompts) < 6:
            prompts.append("Photorealistic 9:16 vertical CDMX cityscape at golden hour, modern Mexico City skyline")
    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for i, prompt in enumerate(prompts):
            p = os.path.join(tmp, f"slide{i+1}.jpg")
            print(f"  Slide {i+1}/6: {prompt[:60]}...", flush=True)
            if not download_image(prompt, p):
                make_fallback(p)
            paths.append(p)
        make_video(paths, out)

print("\nDone!", flush=True)
