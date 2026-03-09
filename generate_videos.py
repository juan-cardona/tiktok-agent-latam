#!/usr/bin/env python3
"""Generate TikTok videos from scripts using Pollinations FLUX API + ffmpeg."""

import os
import subprocess
import urllib.parse
import urllib.request
import time
import tempfile
import shutil
from datetime import datetime

FFMPEG = "/home/linuxbrew/.linuxbrew/bin/ffmpeg"
VIDEOS_DIR = os.path.expanduser("~/projects/tiktok-agent/videos")
TMP_BASE = os.path.expanduser("~/projects/tiktok-agent/tmp")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(TMP_BASE, exist_ok=True)

TIMESTAMP = datetime.now().strftime("%Y%m%d-%H%M")

# ---------------------------------------------------------------------------
# Video definitions
# ---------------------------------------------------------------------------

videos = [
    {
        "n": 9,
        "hook": "La IA negoció mi aumento mejor que yo... y consiguió el doble.",
        "slides": [
            ("hook", "Photorealistic 9:16 vertical. A confident young Mexican woman in her late 20s sitting across from a suited manager at a corporate desk, arms crossed, looking calm and powerful. The manager looks slightly nervous. Modern Mexico City office, floor-to-ceiling windows, city skyline at golden hour. Cinematic, high contrast."),
            ("setup", "Photorealistic 9:16 vertical. Close-up of a phone screen showing a ChatGPT conversation in Spanish with prompt: Ayúdame a negociar un aumento de sueldo del 40%. Hands holding phone, blurred office background. Documentary style, warm office lighting."),
            ("script", "Photorealistic 9:16 vertical. Phone screen showing a numbered list of salary negotiation talking points in Spanish. Professional, clean UI. Person's hands visible, manicured nails. Shallow depth of field, bokeh background."),
            ("room", "Photorealistic 9:16 vertical. Same young woman at a conference table, confident posture, subtle smile, eye contact with the camera. She's mid-conversation. Natural corporate lighting, notepad visible on table. Candid editorial style."),
            ("result", "Photorealistic 9:16 vertical. Woman on phone outside office building, celebrating quietly, fist pump, big smile. CDMX street background with iconic Reforma trees. Afternoon golden light. Natural, joyful, candid."),
            ("cta", "Photorealistic 9:16 vertical. Same woman looking directly into camera, inviting smile, holding phone toward viewer. Modern CDMX apartment background, plants, warm light. Space left at bottom third for text overlay."),
        ],
        "captions": [
            None,  # slide 1: hook text used
            "Pedí ayuda a ChatGPT para negociar",
            "Me dio exactamente qué decir",
            "Entré a la reunión con todo preparado",
            "Resultado: 22% de aumento conseguido",
            "Guarda esto para tu próxima revisión 👇",
        ],
    },
    {
        "n": 10,
        "hook": "Así se va a ver el Metro CDMX en 2050 según la IA 🤯",
        "slides": [
            ("hook", "Futuristic photorealistic 9:16 vertical. A stunning reimagination of Mexico City Metro Line 1 in 2050. Sleek maglev trains in metallic silver-gold with aztec geometric patterns, levitating above the tracks. Passengers in futuristic casual wear. Bright clean station with biopunk vegetation on walls. Cinematic sci-fi realism."),
            ("zocalo", "Futuristic photorealistic 9:16 vertical. The Zocalo of Mexico City in 2050. The Cathedral and National Palace are perfectly preserved but surrounded by gleaming eco-towers with vertical gardens. Flying taxis visible in sky. Aztec-inspired architecture fused with ultra-modern glass and steel. Golden hour lighting."),
            ("polanco", "Futuristic photorealistic 9:16 vertical. Polanco neighborhood 2050. Tree-covered pedestrian megabridge over Presidente Masaryk, luxury shops below, automated delivery drones flying between buildings. Mexican fashion brands on sleek storefronts. Lush, clean, vibrant. Late afternoon light."),
            ("tepito", "Futuristic photorealistic 9:16 vertical. Tepito market in 2050. Vibrant and alive — drone delivery hubs mixed with traditional market stalls, holographic price displays, same authentic CDMX energy but elevated. Street art murals covering solar panel facades. Real people, real culture, just futuristic."),
            ("xochimilco", "Futuristic photorealistic 9:16 vertical. Xochimilco canals in 2050. The trajineras are now solar-powered but keep their traditional flower decorations. Crystal clear restored water. Floating gardens chinampas thriving. Biopunk utopian vision, warm sunset colors."),
            ("cta", "Futuristic photorealistic 9:16 vertical. Aerial view of Mexico City 2050 at twilight — green corridors, glowing city grid, massive central park where Periferico used to be. Stunning, aspirational. Space at bottom for text overlay."),
        ],
        "captions": [
            None,
            "El Zócalo en 2050: eco-torres y taxis voladores",
            "Polanco con megapuente peatonal arbolado",
            "Tepito: misma energía, tecnología del futuro",
            "Xochimilco: chinampas con agua cristalina",
            "Comenta tu colonia y la visualizo 👇",
        ],
    },
    {
        "n": 11,
        "hook": "Hice en 8 minutos lo que mi colega tardó 3 días... con IA.",
        "slides": [
            ("hook", "Photorealistic 9:16 vertical. Split screen: left side shows stressed Mexican office worker surrounded by stacks of printed spreadsheets and reports, fluorescent lighting, tired expression. Right side shows same person relaxed at clean desk with single laptop, coffee, plant, smiling. Stark lifestyle contrast, editorial style."),
            ("task", "Photorealistic 9:16 vertical. Close-up of a laptop screen showing a complex Excel spreadsheet with hundreds of rows of data, formulas, pivot tables. Hands typing in low office lighting. Overwhelming, chaotic, lots of numbers. Authentic Mexican corporate office vibe."),
            ("ai_move", "Photorealistic 9:16 vertical. Same laptop but now showing a clean ChatGPT conversation in Spanish. The prompt asks for analysis of a dataset. The response is a clean, structured executive summary in bullet points. Screen glow on face, look of relief and surprise."),
            ("output", "Photorealistic 9:16 vertical. Phone screen showing a beautifully formatted report with charts and insights, generated by AI. Professional, polished, ready to send to the boss. Person's thumb scrolling through it. Clean desk, natural light."),
            ("reaction", "Photorealistic 9:16 vertical. Young Mexican professional in casual business clothes walking confidently into a glass-walled meeting room, laptop under arm, slight smirk. CDMX office building interior. Other colleagues visible through glass. Confident, winning."),
            ("cta", "Photorealistic 9:16 vertical. Person at desk looking directly at camera with a knowing smile, laptop open. Modern home office setup. Direct eye contact, inviting. Warm lighting. Space at bottom third for text overlay."),
        ],
        "captions": [
            None,
            "El reporte trimestral: cientos de filas de datos",
            "ChatGPT lo analizó y resumió en segundos",
            "Reporte listo, profesional, listo para el jefe",
            "Entré a la junta con todo resuelto 😏",
            "¿Cuánto tiempo te ahorra la IA? 👇",
        ],
    },
]


def download_image(prompt, out_path, retries=3):
    """Download image from Pollinations FLUX API."""
    encoded = urllib.parse.quote(prompt, safe='')
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&model=flux"
    print(f"  Downloading: {url[:80]}...")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = resp.read()
            with open(out_path, "wb") as f:
                f.write(data)
            print(f"  → Saved {out_path} ({len(data)//1024}KB)")
            return True
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(5)
    return False


def escape_drawtext(text):
    """Escape text for ffmpeg drawtext."""
    # Escape special chars: ' : \ [ ]
    text = text.replace('\\', '\\\\')
    text = text.replace("'", "\\'")
    text = text.replace(':', '\\:')
    text = text.replace('[', '\\[')
    text = text.replace(']', '\\]')
    return text


def wrap_text(text, max_chars=35):
    """Simple word wrap."""
    words = text.split()
    lines = []
    current = ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current = (current + " " + w).strip()
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return "\n".join(lines)


def build_video(video_def):
    n = video_def["n"]
    hook = video_def["hook"]
    slides = video_def["slides"]
    captions = video_def["captions"]

    tmp_dir = os.path.join(TMP_BASE, f"video_{n}")
    os.makedirs(tmp_dir, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"Building video {n}: {hook}")
    print(f"{'='*60}")

    # Step 1: Download images
    img_paths = []
    for i, (label, prompt) in enumerate(slides):
        out_path = os.path.join(tmp_dir, f"slide_{i+1}.jpg")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 10000:
            print(f"  Slide {i+1} already exists, skipping download.")
        else:
            ok = download_image(prompt, out_path)
            if not ok:
                print(f"  ERROR: Failed to download slide {i+1}, using fallback black image")
                # Create black fallback
                subprocess.run([
                    FFMPEG, "-y", "-f", "lavfi", "-i", f"color=c=black:size=1080x1920:rate=1",
                    "-vframes", "1", out_path
                ], capture_output=True)
        img_paths.append(out_path)
        time.sleep(1)  # polite delay

    # Step 2: Add text overlays and create per-slide videos
    slide_videos = []
    for i, img_path in enumerate(img_paths):
        slide_out = os.path.join(tmp_dir, f"slide_{i+1}.mp4")
        
        if i == 0:
            overlay_text = hook
        else:
            overlay_text = captions[i] or ""

        # Wrap text
        wrapped = wrap_text(overlay_text, max_chars=30)
        lines = wrapped.split("\n")
        num_lines = len(lines)
        line_h = 75  # approx height per line at fontsize 60
        box_h = num_lines * line_h + 40
        box_y = 1920 - box_h - 60  # bottom third area

        escaped = escape_drawtext(wrapped)

        # Build drawtext filter
        drawtext = (
            f"drawtext=fontfile={FONT}:"
            f"text='{escaped}':"
            f"fontcolor=white:"
            f"fontsize=58:"
            f"x=(w-text_w)/2:"
            f"y={box_y + 20}:"
            f"line_spacing=10:"
            f"box=1:"
            f"boxcolor=black@0.65:"
            f"boxborderw=20"
        )

        cmd = [
            FFMPEG, "-y",
            "-loop", "1",
            "-i", img_path,
            "-vf", drawtext,
            "-t", "3",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            slide_out
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ffmpeg slide error: {result.stderr[-500:]}")
        else:
            print(f"  Slide {i+1} video created: {slide_out}")
        slide_videos.append(slide_out)

    # Step 3: Concatenate with xfade transitions
    output_path = os.path.join(VIDEOS_DIR, f"series-{TIMESTAMP}-{n}.mp4")
    
    # Build complex filter for xfade
    # Each slide is 3s, fade duration 0.5s
    # xfade offsets: 2.5, 5.0, 7.5, 10.0, 12.5
    inputs = []
    for sv in slide_videos:
        inputs += ["-i", sv]
    
    num_slides = len(slide_videos)
    fade_dur = 0.5
    slide_dur = 3.0
    
    # Build xfade chain
    filter_parts = []
    for i in range(num_slides - 1):
        offset = (i + 1) * slide_dur - fade_dur
        if i == 0:
            in_a = f"[0:v]"
            in_b = f"[1:v]"
        else:
            in_a = f"[xf{i-1}]"
            in_b = f"[{i+1}:v]"
        out_label = f"[xf{i}]"
        filter_parts.append(f"{in_a}{in_b}xfade=transition=fade:duration={fade_dur}:offset={offset}{out_label}")
    
    filter_complex = ";".join(filter_parts)
    last_label = f"[xf{num_slides-2}]"

    cmd = (
        [FFMPEG, "-y"] +
        inputs +
        [
            "-filter_complex", filter_complex,
            "-map", last_label,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            output_path
        ]
    )
    
    print(f"\n  Combining slides into: {output_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg combine error:\n{result.stderr[-1000:]}")
    else:
        size = os.path.getsize(output_path) // (1024*1024)
        print(f"  ✅ Video {n} saved: {output_path} ({size}MB)")
    
    return output_path


# Generate all 3 videos
for vdef in videos:
    build_video(vdef)

print("\n\nAll videos generated!")
print("Files in videos dir:")
for f in sorted(os.listdir(VIDEOS_DIR)):
    if f.endswith(".mp4"):
        path = os.path.join(VIDEOS_DIR, f)
        print(f"  {f} ({os.path.getsize(path)//1024}KB)")
