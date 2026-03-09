#!/usr/bin/env python3
"""Generate videos 2 and 3 for batch 0643 (video 1 already done)."""
import os
import time
import requests
import subprocess
import tempfile
import shutil
import textwrap
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFont

FFMPEG = "/home/linuxbrew/.linuxbrew/bin/ffmpeg"
VIDEOS_DIR = os.path.expanduser("~/projects/tiktok-agent/videos")

scripts = [
    {
        "n": 2,
        "slides": [
            {"text": "La IA predijo como sera Mexico en 2050... y da miedo", "visual": "Futuristic Mexico City with glass towers and drones flying cinematic sci-fi skyline night"},
            {"text": "CDMX tendra 32M habitantes. Trafico resuelto con IA autonoma", "visual": "Smart highways with autonomous self-driving cars flowing aerial view futuristic city lights"},
            {"text": "El espanol mexicano: el idioma mas hablado de internet", "visual": "World map with Mexico glowing brightly at center golden data streams radiating outward"},
            {"text": "Monterrey igual Silicon Valley de Latam. 500 unicornios 2050", "visual": "Monterrey skyline futuristic night with holographic tech logos floating above buildings"},
            {"text": "Tacos de canasta entregados por drones en menos de 5 minutos", "visual": "Drone carrying tacos flying over colorful Mexico City neighborhood streets vibrant illustration"},
            {"text": "Cual prediccion te asusta mas? Comenta. Sigue para mas", "visual": "Collage Mexico 2050 future predictions green white red colors dramatic composition"},
        ]
    },
    {
        "n": 3,
        "slides": [
            {"text": "La IA sabe esto de ti con solo ver tu foto de perfil", "visual": "Profile photo being scanned with floating data points blue scanning lines dark tech aesthetic"},
            {"text": "Facial recognition detecta tu estres con 87 porciento precision", "visual": "Face with facial mapping dots and stress meter gauge blue tech overlay analysis"},
            {"text": "Tu WhatsApp revela tu edad nivel educativo y estado emocional", "visual": "WhatsApp chat with data analysis labels appearing over messages visualization"},
            {"text": "TikTok sabe si eres introvertido ANTES de que lo admitas", "visual": "TikTok feed with psychological profile overlay superimposed dramatic neon colors"},
            {"text": "Amazon predice tu proxima compra 3 dias antes de que la decidas", "visual": "Shopping cart filling itself while user sleeps in background surreal digital art"},
            {"text": "Que tanto te conoce la IA? Pon tu porcentaje en comentarios", "visual": "Progress bar showing AI knowledge percentage minimal dark design futuristic interface"},
        ]
    },
]

def download_image(prompt, out_path, retries=6):
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1080&height=1920&nologo=true&model=flux"
    for attempt in range(retries):
        try:
            print(f"  [{attempt+1}] {prompt[:55]}...")
            r = requests.get(url, timeout=120)
            if r.status_code == 429:
                wait = 20 + 15 * attempt
                print(f"  429 rate limit — waiting {wait}s")
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.content
            if len(data) < 5000:
                print(f"  Too small ({len(data)}B), waiting 10s...")
                time.sleep(10)
                continue
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"  OK ({len(data)//1024}KB)")
            time.sleep(3)  # polite delay between requests
            return True
        except Exception as e:
            print(f"  Error: {e}")
            time.sleep(8)
    return False

def add_text_overlay(img_path, text, out_path):
    img = Image.open(img_path).convert("RGB")
    if img.size != (1080, 1920):
        img = img.resize((1080, 1920), Image.LANCZOS)
    
    draw = ImageDraw.Draw(img)
    font_size = 58
    font = None
    for fp in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    ]:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except: pass
    if font is None:
        font = ImageFont.load_default()

    wrapped = textwrap.wrap(text, width=32)
    line_h = font_size + 14
    total_h = len(wrapped) * line_h
    start_y = 1920 - 350
    pad = 22

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([(0, start_y - pad), (1080, start_y + total_h + pad)], fill=(0, 0, 0, 160))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    for i, line in enumerate(wrapped):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (1080 - tw) // 2
        y = start_y + i * line_h
        for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,-2),(-2,2),(2,2)]:
            draw.text((x+dx, y+dy), line, font=font, fill=(0, 0, 0))
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    img.save(out_path, "JPEG", quality=92)

def make_video(script):
    n = script["n"]
    slides = script["slides"]
    tmpdir = tempfile.mkdtemp(prefix=f"tiktok_0643_{n}_")
    print(f"\n=== Video {n} | {tmpdir} ===")

    slide_vids = []
    for i, slide in enumerate(slides, 1):
        raw_img = os.path.join(tmpdir, f"s{i}_raw.jpg")
        txt_img = os.path.join(tmpdir, f"s{i}_text.jpg")
        out_vid = os.path.join(tmpdir, f"s{i}.mp4")

        ok = download_image(slide["visual"], raw_img)
        if not ok:
            img = Image.new("RGB", (1080, 1920), (10, 10, 30))
            img.save(raw_img, "JPEG")

        add_text_overlay(raw_img, slide["text"], txt_img)

        cmd = [
            FFMPEG, "-y", "-loop", "1", "-i", txt_img,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-t", "3", "-r", "30", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
            out_vid
        ]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            print(f"  Slide {i}: video OK")
            slide_vids.append(out_vid)
        else:
            print(f"  Slide {i}: video FAILED")

    output_path = os.path.join(VIDEOS_DIR, f"series-20260309-0643-{n}.mp4")
    if not slide_vids:
        print("  No slides!")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return

    # xfade combine
    inputs = []
    for v in slide_vids: inputs += ["-i", v]
    fade_dur, slide_dur = 0.5, 3.0
    nv = len(slide_vids)
    parts = []
    prev = "[0:v]"
    for idx in range(1, nv):
        offset = slide_dur * idx - fade_dur * idx
        curr = f"[{idx}:v]"
        out_l = f"[v{idx}]" if idx < nv-1 else "[vout]"
        parts.append(f"{prev}{curr}xfade=transition=fade:duration={fade_dur}:offset={offset}{out_l}")
        prev = f"[v{idx}]"
    
    cmd = [FFMPEG, "-y"] + inputs + [
        "-filter_complex", ";".join(parts),
        "-map", "[vout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "fast",
        output_path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  xfade failed, using concat: {r.stderr[-200:]}")
        clist = os.path.join(tmpdir, "c.txt")
        with open(clist, "w") as f:
            for v in slide_vids: f.write(f"file '{v}'\n")
        subprocess.run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", clist,
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path],
                       capture_output=True)

    size = os.path.getsize(output_path)//1024 if os.path.exists(output_path) else 0
    print(f"  => {output_path} ({size}KB)")
    shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    for script in scripts:
        make_video(script)
    print("\nDone!")
    for n in [1, 2, 3]:
        p = os.path.join(VIDEOS_DIR, f"series-20260309-0643-{n}.mp4")
        size = os.path.getsize(p)//1024 if os.path.exists(p) else 0
        print(f"  Video {n}: {size}KB")
