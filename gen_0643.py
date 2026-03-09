#!/usr/bin/env python3
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
        "n": 1,
        "slides": [
            {"text": "Tu trabajo ya no existe... y no te lo dijeron", "visual": "Empty office with robots working on computers, cinematic dramatic lighting, dystopian"},
            {"text": "La IA reemplazó el 40% de tareas de contadores en Fortune 500", "visual": "Red graph showing accounting jobs declining sharply, dark background data visualization"},
            {"text": "Traductores: -32% empleos en 3 años. ChatGPT lo hace en segundos", "visual": "Languages flowing into a glowing AI chip, colorful streams of text converging"},
            {"text": "1 IA atiende 10,000 clientes simultáneamente. Sin café ni descanso", "visual": "Multiple chat bubbles emanating from a single glowing server, digital art blue tones"},
            {"text": "Midjourney generó 15 millones de imágenes HOY. Diseñadores: preocúpense", "visual": "Tsunami of AI generated images overwhelming a lone designer at desk, dramatic illustration"},
            {"text": "Tu trabajo está en esta lista? Comenta abajo. Parte 2 mañana", "visual": "List of jobs with some crossed out in red some highlighted green safe dramatic lighting"},
        ]
    },
    {
        "n": 2,
        "slides": [
            {"text": "La IA predijo cómo será México en 2050... y da miedo", "visual": "Futuristic Mexico City with glass towers and drones flying cinematic sci-fi skyline"},
            {"text": "CDMX tendrá 32M habitantes. Tráfico resuelto con IA autónoma", "visual": "Smart highways with autonomous self-driving cars flowing aerial view futuristic city"},
            {"text": "El español mexicano: el idioma más hablado de internet", "visual": "World map with Mexico glowing brightly at center data streams radiating outward"},
            {"text": "Monterrey = Silicon Valley de Latinoamérica. 500 unicornios 2050", "visual": "Monterrey skyline with holographic tech company logos floating above futuristic night"},
            {"text": "Tacos de canasta entregados por drones en menos de 5 minutos", "visual": "Drone carrying tacos flying over colorful Mexico City neighborhood streets illustration"},
            {"text": "Cuál predicción te asusta más? Comenta. Sigue para más", "visual": "Collage Mexico 2050 predictions with Mexico flag green white red colors dramatic"},
        ]
    },
    {
        "n": 3,
        "slides": [
            {"text": "La IA sabe esto de ti con solo ver tu foto de perfil", "visual": "Profile photo being scanned with floating data points and blue scanning lines dark tech aesthetic"},
            {"text": "Facial recognition detecta tu nivel de estrés con 87% precisión", "visual": "Face with facial mapping dots and stress meter gauge beside it blue tech overlay"},
            {"text": "Tu WhatsApp revela tu edad, nivel educativo y estado emocional", "visual": "WhatsApp chat with analysis labels and data visualization overlay appearing"},
            {"text": "TikTok sabe si eres introvertido ANTES de que tú lo admitas", "visual": "TikTok feed with psychological profile overlay superimposed dramatic neon colors"},
            {"text": "Amazon predice tu próxima compra 3 días antes de que la decidas", "visual": "Shopping cart filling itself while user sleeps in background surreal digital art"},
            {"text": "Qué tanto te conoce la IA? Pon tu % en comentarios", "visual": "Progress bar showing AI knowledge percentage minimal dark design futuristic"},
        ]
    },
]

def download_image(prompt, out_path, retries=5):
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=1080&height=1920&nologo=true&model=flux"
    for attempt in range(retries):
        try:
            print(f"  [{attempt+1}] Fetching image: {prompt[:50]}...")
            r = requests.get(url, timeout=120)
            if r.status_code == 429:
                wait = 15 * (attempt + 1)
                print(f"  429 rate limit — waiting {wait}s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(r.content)
            size = len(r.content)
            if size < 5000:
                print(f"  Response too small ({size}B), retrying...")
                time.sleep(5)
                continue
            print(f"  Saved {out_path} ({size//1024}KB)")
            return True
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(5)
    return False

def add_text_overlay(img_path, text, out_path):
    """Use Pillow to add text overlay to image."""
    img = Image.open(img_path).convert("RGB")
    # Ensure 1080x1920
    if img.size != (1080, 1920):
        img = img.resize((1080, 1920), Image.LANCZOS)
    
    draw = ImageDraw.Draw(img)
    
    # Try to load a bold font
    font_size = 58
    font = None
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, font_size)
                break
            except:
                pass
    if font is None:
        font = ImageFont.load_default()

    # Wrap text
    wrapped = textwrap.wrap(text, width=32)
    
    line_h = font_size + 12
    total_h = len(wrapped) * line_h
    start_y = 1920 - 350
    
    # Semi-transparent dark background box
    pad = 20
    box_top = start_y - pad
    box_bottom = start_y + total_h + pad
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rectangle([(0, box_top), (1080, box_bottom)], fill=(0, 0, 0, 160))
    img = img.convert("RGBA")
    img = Image.alpha_composite(img, overlay)
    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    for i, line in enumerate(wrapped):
        # Get text width
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (1080 - tw) // 2
        y = start_y + i * line_h
        # Black outline
        for dx, dy in [(-3,0),(3,0),(0,-3),(0,3),(-2,-2),(2,-2),(-2,2),(2,2)]:
            draw.text((x+dx, y+dy), line, font=font, fill=(0, 0, 0))
        # White text
        draw.text((x, y), line, font=font, fill=(255, 255, 255))

    img.save(out_path, "JPEG", quality=92)
    return out_path

def make_slide_video(img_path, duration, out_vid):
    """Convert image to video clip."""
    cmd = [
        FFMPEG, "-y",
        "-loop", "1", "-i", img_path,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-t", str(duration),
        "-r", "30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast",
        out_vid
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Slide video error: {result.stderr[-300:]}")
        return False
    return True

def combine_with_xfade(slide_vids, output_path, slide_dur=3.0, fade_dur=0.5):
    n = len(slide_vids)
    inputs = []
    for v in slide_vids:
        inputs += ["-i", v]
    
    filter_parts = []
    prev = "[0:v]"
    for idx in range(1, n):
        offset = slide_dur * idx - fade_dur * idx
        curr = f"[{idx}:v]"
        out_label = f"[v{idx}]" if idx < n - 1 else "[vout]"
        filter_parts.append(f"{prev}{curr}xfade=transition=fade:duration={fade_dur}:offset={offset}{out_label}")
        prev = f"[v{idx}]"
    
    filtergraph = ";".join(filter_parts)
    cmd = [FFMPEG, "-y"] + inputs + [
        "-filter_complex", filtergraph,
        "-map", "[vout]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", "23",
        "-preset", "fast",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  xfade error: {result.stderr[-400:]}")
        # Fallback: simple concat
        return False
    return True

def concat_fallback(slide_vids, output_path, tmpdir):
    concat_list = os.path.join(tmpdir, "concat.txt")
    with open(concat_list, "w") as f:
        for v in slide_vids:
            f.write(f"file '{v}'\n")
    cmd = [
        FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "fast",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  Concat fallback error: {result.stderr[-300:]}")
        return False
    return True

def make_video(script):
    n = script["n"]
    slides = script["slides"]
    tmpdir = tempfile.mkdtemp(prefix=f"tiktok_0643_{n}_")
    print(f"\n=== Video {n} | tmpdir: {tmpdir} ===")

    slide_vids = []
    for i, slide in enumerate(slides, 1):
        raw_img = os.path.join(tmpdir, f"slide_{i}_raw.jpg")
        txt_img = os.path.join(tmpdir, f"slide_{i}_text.jpg")
        out_vid = os.path.join(tmpdir, f"slide_{i}.mp4")

        # Download image with fallback to black
        ok = download_image(slide["visual"], raw_img)
        if not ok:
            print(f"  Creating black fallback for slide {i}")
            img = Image.new("RGB", (1080, 1920), (20, 20, 40))
            img.save(raw_img, "JPEG")

        # Add text overlay
        add_text_overlay(raw_img, slide["text"], txt_img)
        print(f"  Text overlay added to slide {i}")

        # Convert to video
        if make_slide_video(txt_img, 3, out_vid):
            print(f"  Slide {i} video: OK")
            slide_vids.append(out_vid)
        else:
            print(f"  Slide {i} video: FAILED")

    output_path = os.path.join(VIDEOS_DIR, f"series-20260309-0643-{n}.mp4")

    if len(slide_vids) == 0:
        print(f"  No slide videos produced for video {n}!")
        shutil.rmtree(tmpdir, ignore_errors=True)
        return output_path

    print(f"  Combining {len(slide_vids)} slides...")
    ok = combine_with_xfade(slide_vids, output_path)
    if not ok:
        print(f"  xfade failed, trying concat fallback...")
        ok = concat_fallback(slide_vids, output_path, tmpdir)

    if ok:
        size = os.path.getsize(output_path) // 1024
        print(f"  Video {n} saved: {output_path} ({size}KB)")
    else:
        print(f"  Video {n} FAILED to produce output")

    shutil.rmtree(tmpdir, ignore_errors=True)
    return output_path

if __name__ == "__main__":
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    results = []
    for script in scripts:
        path = make_video(script)
        results.append(path)

    print("\n=== All done ===")
    for r in results:
        size = os.path.getsize(r) // 1024 if os.path.exists(r) else 0
        print(f"  {r} ({size}KB)")
