#!/usr/bin/env python3
"""Generate TikTok slideshow videos using Pollinations.ai + ffmpeg"""

import os
import subprocess
import urllib.parse
import time
import json

FFMPEG = "/home/linuxbrew/.linuxbrew/bin/ffmpeg"
BASE_DIR = os.path.expanduser("~/projects/tiktok-agent")
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")

# Font - use a system font
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
if not os.path.exists(FONT):
    # find any bold font
    result = subprocess.run(["find", "/usr/share/fonts", "-name", "*Bold*", "-name", "*.ttf"], 
                           capture_output=True, text=True)
    fonts = result.stdout.strip().split("\n")
    if fonts and fonts[0]:
        FONT = fonts[0]
    else:
        FONT = ""

print(f"Using font: {FONT}")

def escape_drawtext(text):
    """Escape text for ffmpeg drawtext filter"""
    text = text.replace("\\", "\\\\")
    text = text.replace("'", "\\'")
    text = text.replace(":", "\\:")
    text = text.replace(",", "\\,")
    text = text.replace("[", "\\[")
    text = text.replace("]", "\\]")
    return text

def download_image(prompt, output_path, max_retries=3):
    """Download image from Pollinations.ai"""
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&model=flux"
    
    for attempt in range(max_retries):
        print(f"  Downloading image (attempt {attempt+1}): {output_path}")
        result = subprocess.run([
            "curl", "-L", "-s", "-o", output_path,
            "--max-time", "120",
            "--retry", "2",
            url
        ], capture_output=True)
        
        if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
            print(f"  ✓ Downloaded {os.path.getsize(output_path)//1024}KB")
            return True
        else:
            print(f"  ✗ Failed (code {result.returncode}, size {os.path.getsize(output_path) if os.path.exists(output_path) else 0})")
            if attempt < max_retries - 1:
                time.sleep(5)
    return False

def add_text_overlay(input_path, output_path, text, font_size=48, is_hook=False):
    """Add text overlay to image using ffmpeg drawtext"""
    escaped = escape_drawtext(text)
    
    if is_hook:
        font_size = 72
    
    # Build drawtext filter - white text with dark shadow/box
    # Use text wrapping by splitting long lines manually
    words = text.split()
    lines = []
    current = ""
    max_chars = 30 if is_hook else 38
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    
    # Build multiple drawtext filters for each line
    filters = []
    line_height = font_size + 10
    total_height = len(lines) * line_height
    start_y = f"(h-{total_height})/2"
    
    for i, line in enumerate(lines):
        esc_line = escape_drawtext(line)
        y_pos = f"(h-{total_height})/2+{i * line_height}"
        font_arg = f"fontfile={FONT}:" if FONT else ""
        dt = (f"drawtext={font_arg}"
              f"fontsize={font_size}:"
              f"fontcolor=white:"
              f"shadowcolor=black@0.8:"
              f"shadowx=3:"
              f"shadowy=3:"
              f"box=1:"
              f"boxcolor=black@0.5:"
              f"boxborderw=8:"
              f"x=(w-text_w)/2:"
              f"y={y_pos}:"
              f"text='{esc_line}'")
        filters.append(dt)
    
    if not filters:
        filters = [f"drawtext=fontsize={font_size}:fontcolor=white:text='.'"]
    
    vf = ",".join(filters)
    
    cmd = [
        FFMPEG, "-y", "-i", input_path,
        "-vf", vf,
        "-q:v", "2",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ⚠ Text overlay failed: {result.stderr[-300:]}")
        # Fallback: just copy the image
        subprocess.run(["cp", input_path, output_path])
    else:
        print(f"  ✓ Text overlay added")

def create_slideshow(frame_paths, output_path):
    """Create slideshow video with xfade transitions"""
    print(f"  Creating slideshow: {output_path}")
    
    n = len(frame_paths)
    
    # Build the filter complex with xfade
    # Each slide is 3 seconds, transition is 0.5s
    slide_duration = 3.0
    transition_duration = 0.5
    
    # Input args
    input_args = []
    for p in frame_paths:
        input_args += ["-loop", "1", "-t", str(slide_duration + transition_duration), "-i", p]
    
    # Build xfade chain
    # [0][1]xfade=transition=fade:duration=0.5:offset=2.5[v01]
    # [v01][2]xfade=...
    
    if n == 1:
        # Single image
        cmd = [
            FFMPEG, "-y",
            "-loop", "1", "-t", "3", "-i", frame_paths[0],
            "-vf", f"scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
            output_path
        ]
        subprocess.run(cmd, capture_output=True)
        return
    
    # Build complex filter
    filter_parts = []
    
    # Scale all inputs first
    for i in range(n):
        filter_parts.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=25[v{i}]")
    
    # Chain xfades
    prev_out = "v0"
    for i in range(1, n):
        offset = (i) * slide_duration - transition_duration
        if i < n - 1:
            out_label = f"xf{i}"
        else:
            out_label = "vout"
        filter_parts.append(
            f"[{prev_out}][v{i}]xfade=transition=fade:duration={transition_duration}:offset={offset:.2f}[{out_label}]"
        )
        prev_out = out_label
    
    filter_complex = ";".join(filter_parts)
    
    cmd = [FFMPEG, "-y"]
    cmd += input_args
    cmd += [
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        "-preset", "fast",
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"  ⚠ Slideshow failed: {result.stderr[-500:]}")
        print("  Trying concat method...")
        create_slideshow_concat(frame_paths, output_path)
    else:
        size = os.path.getsize(output_path) // 1024 // 1024
        print(f"  ✓ Slideshow created: {size}MB")

def create_slideshow_concat(frame_paths, output_path):
    """Fallback: concat method without transitions"""
    concat_file = output_path + ".concat.txt"
    with open(concat_file, "w") as f:
        for p in frame_paths:
            f.write(f"file '{p}'\n")
            f.write(f"duration 3\n")
        # Last image needs duration too
        f.write(f"file '{frame_paths[-1]}'\n")
        f.write(f"duration 1\n")
    
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0", "-i", concat_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=25",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", "-preset", "fast",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        print(f"  ✗ Concat also failed: {result.stderr[-300:]}")
    else:
        size = os.path.getsize(output_path) // 1024 // 1024
        print(f"  ✓ Slideshow (concat) created: {size}MB")
    
    os.unlink(concat_file)


# ============================================================
# SERIES DATA
# ============================================================

SERIES = {
    1: {
        "title": "DEPA CON IA",
        "slides": [
            {
                "prompt": "Photorealistic 9:16 vertical cinematic photo of a small Mexico City apartment interior in Roma Norte neighborhood. Cramped living room with worn beige walls, mismatched IKEA furniture, cheap laminate floors, single dirty window with thin curtains, dim afternoon light, cluttered bookshelf, pizza box on coffee table. Moody realistic slightly sad lighting. No people. 35mm film grain.",
                "text": "Mi casera me llamo FURIOSA despues de ver esto",
                "is_hook": True
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a laptop screen in a dimly lit apartment showing a ChatGPT interface. Prompt text in Spanish: Redisena este departamento estilo japandi moderno sin remover paredes maximo 8000 pesos. Hands of a young Mexican man typing. Cinematic moody blue screen glow. Shot on Sony A7.",
                "text": "Le pedi a la IA: redisena mi depa japandi con $8,000 pesos",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical AI architectural visualization of transformed small Mexico City apartment. Japandi minimalist style, warm oak tones, white walls, low platform sofa in cream linen, woven rattan pendant lamp, indoor snake plant and pothos, concrete-look floors, soft warm lighting. Same window with linen sheer curtains golden afternoon light. Magazine-quality cozy. No people.",
                "text": "El resultado: estilo japandi completo y hermoso",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a Mexican smartphone screen showing WhatsApp conversation. Chat name: Edificio Alvaro Obregon. Message from Senora Carmen: Buenos dias. Vi fotos de su departamento en Instagram. Los cambios estructurales NO estan permitidos en el contrato. Three blue checkmarks. Cinematic dramatic low-key lighting.",
                "text": "Mi casera: Los cambios estructurales NO estan permitidos",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical photo of a young Mexican man in his mid-20s casual hoodie sitting at small desk in renovated-looking apartment with laptop open. Confidently showing laptop screen. Expression calm slightly smug smile. Walls freshly painted white, removable wallpaper visible, plants on windowsill. Warm natural light. Documentary-style 35mm film.",
                "text": "Twist: todo era temporal y reversible. Sin romper nada",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical magazine-quality interior photo of small apartment in Mexico City completely transformed on a budget. Japandi minimalist, white walls, low-profile beige sofa with rust throw pillow, bamboo side table, large monstera plant, string lights, organized bookshelf. Golden hour light. No people.",
                "text": "Sigueme y te mando el prompt exacto por DM",
                "is_hook": False
            }
        ]
    },
    2: {
        "title": "NEGOCIO EN UN DIA",
        "slides": [
            {
                "prompt": "Photorealistic 9:16 vertical cinematic photo of a young Mexican man in his mid-20s lying in bed in a small Mexico City apartment, laptop open on his stomach, phone beside him, Saturday morning light filtering through blinds. He looks slightly bored but focused. Hoodie and sweatpants. Empty coffee mug on nightstand. Laptop screen glows with ChatGPT. 35mm film grain warm morning light.",
                "text": "$3,000 pesos. Dia 1. Sin inversion.",
                "is_hook": True
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a laptop screen showing a detailed ChatGPT response in Spanish structured like a business plan: Servicio Diseno de menus digitales para restaurantes Precio 500-800 pesos por menu Herramientas Canva ChatGPT Clientes objetivo taquerias y cafeterias. Clean UI readable text hands visible on keyboard coffee cup in background. Cinematic.",
                "text": "ChatGPT me dio el plan: menus digitales para taquerias $500-800 por menu",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical split-view photo showing dual-screen setup: on the left a Canva template being edited on a laptop with beautiful restaurant menu design in Spanish. On the right a phone showing ChatGPT conversation generating menu copy. Desk setup with snacks a plant cozy apartment background. Warm productive afternoon light. Documentary-style.",
                "text": "En 2 horas: 3 menus de ejemplo listos con IA",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a phone screen showing a WhatsApp Business conversation. Sent message: Hola vi que su taqueria no tiene menu digital en WhatsApp le puedo hacer uno profesional hoy mismo por 500 pesos. Below: blue checkmarks and a reply bubble appearing. Screen lit in the dark dramatic.",
                "text": "Mande mensajes a 20 negocios de mi colonia",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a Mexican smartphone showing a Mercado Pago app notification. The notification reads: Recibiste $600.00 de Taqueria El Guero. Time stamp 2:47 PM. Hand holding the phone casual sleeve visible. Background blurred apartment. Cinematic real.",
                "text": "La primera transferencia llego: $600 pesos de Taqueria El Guero",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical flat-lay photo on a wooden desk surface showing: a notebook with handwritten tally marks and totals in pesos totaling 3000, a phone displaying Mercado Pago balance, a laptop with Canva open in background, empty snack wrappers, and a pen. Overhead shot warm golden light through window. Authentic not staged.",
                "text": "Guarda este video. El proximo sabado lo intentas tu",
                "is_hook": False
            }
        ]
    },
    3: {
        "title": "IA EN EL TRABAJO",
        "slides": [
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a phone screen showing a WhatsApp or Teams conversation. Message from Lic. Ramirez: Buenas tardes. Necesito el analisis de ventas Q1 completo para el lunes 8AM. Minimo 40 paginas con graficas y conclusiones ejecutivas. Time stamp 5:02 PM Friday. Hand holding phone shows tense fingers. Office parking lot background blurred. Cinematic relatable dread.",
                "text": "Reporte de 40 paginas. 4 minutos. Mi jefe no sabe nada.",
                "is_hook": True
            },
            {
                "prompt": "Photorealistic 9:16 vertical candid photo of a young Mexican professional late 20s sitting in a car in an office parking lot at dusk. Suit jacket slightly loosened tie undone phone in hand. Expression shifts from shocked to a slow knowing smirk. The car interior is lit by phone screen glow. Through windshield a gray Mexico City office building fading orange sky. Documentary raw. Sony A7 50mm shallow depth of field.",
                "text": "Viernes 5PM. Plan de fin de semana: cancelado... o eso pense",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a laptop screen in a home office or kitchen table setup. The ChatGPT interface shows a long detailed Spanish prompt: Actua como analista de negocios senior. Necesito un reporte ejecutivo de ventas Q1 de 40 paginas con resumen ejecutivo analisis por region comparativo conclusiones estrategicas. Tono formal corporativo mexicano. Hands on keyboard coffee mug nearby casual home clothes. Warm kitchen light.",
                "text": "El prompt que lo resolvio todo en menos de 5 minutos",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a laptop screen showing a Word document rapidly filling with professional Spanish text headers formatted tables. The document title reads ANALISIS DE VENTAS Q1 2026 INFORME EJECUTIVO. Page count visible in bottom toolbar shows 40 plus pages. The room around the laptop is dark except for screen glow. Cinematic almost surreal speed.",
                "text": "40+ paginas generadas. Listo para editar con datos reales",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical photo of a young Mexican professional at a kitchen table relaxed in a t-shirt and jeans editing a printed document with a red pen. Coffee cup phone and laptop nearby. The printed pages look professional with real graphs headers executive formatting. He circles one paragraph and adds a handwritten note. Late evening warm lamp light. 35mm film aesthetic.",
                "text": "Lo revise el viernes en la noche. Sabado libre.",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical photo inside a modern Mexico City corporate meeting room. A projector displays the first slide of a professional presentation titled ANALISIS EJECUTIVO Q1 2026. Around the conference table three or four blurred business professionals. In the foreground the young professional sits confidently back to camera. One exec at the head of the table nods approvingly pointing at the screen. Cinematic wide angle subtle lens flare.",
                "text": "El prompt exacto te lo enseno en el siguiente video",
                "is_hook": False
            }
        ]
    },
    4: {
        "title": "IA REDISENA MEXICO",
        "slides": [
            {
                "prompt": "Photorealistic 9:16 vertical cinematic photo of the Zocalo Plaza de la Constitucion in Mexico City taken from street level at midday. Mexican flag waves in center Catedral Metropolitana in background gray stone paving vendor stalls tent encampments visible on edges smoggy gray-blue sky. People walking vendors protest banner partially visible. Documentary photography 35mm film grain slight haze.",
                "text": "Le pedi a la IA que arreglara el Zocalo de CDMX",
                "is_hook": True
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a laptop screen showing an image generation prompt: The Zocalo of Mexico City redesigned as a modern pedestrian plaza inspired by Medellin and Copenhagen. Green parks replace parking outdoor cafes restored colonial facades with warm lighting wide bike lanes sunset golden hour. The interface shows Midjourney or Adobe Firefly. Dimly lit room hands on keyboard Mexican flag desk ornament visible.",
                "text": "El prompt: conserva la historia moderniza para la gente",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical AI architectural visualization of a redesigned Zocalo in Mexico City. Historic center transformed: lush green park areas with native Mexican plants nopal jacaranda bugambilia, wide pedestrian promenades, outdoor seating areas with cafes, bike lanes with cyclists, Cathedral and Palacio Nacional remain intact with restored warm-lit facades. Golden sunset light birds in flight families walking. Magazine-quality render.",
                "text": "Version 1: parques ciclovias y cafes al aire libre",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical AI architectural visualization of the Zocalo in Mexico City with bold futuristic redesign. Glass-paneled buildings integrated behind colonial facades elevated walkways connecting Cathedral to Palacio Nacional holographic public art installations solar panel canopies. Night scene dramatic lighting neon blues and warm ambers. Controversial visually striking AI-imagined. Cinematic high-detail render.",
                "text": "Version 2: futurista. El INAH ya esta temblando",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical phone screen mockup showing a TikTok comments section in dark mode. Various comments with different like counts: Ya chole con modernizar 4.2K likes, Pero si queda bonito 2.1K likes, La IA no tarda 10 anos en obras como el Metro 8.7K likes, El INAH ya esta temblando 3.3K likes. Authentic TikTok UI. Cinematic mock screenshot.",
                "text": "La gente: La IA no tarda 10 anos como el Metro",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical stunning AI architectural visualization of a harmoniously redesigned Zocalo in Mexico City. Perfect balance of historic preservation and modern livability: restored colonial buildings warm facade lighting, large central green park with native trees ahuehuete jacaranda, pedestrian-only zone, outdoor market with Mexican crafts, children playing near low fountain, Cathedral and Palacio Nacional perfectly framed. Magic hour golden light. Most beautiful version imaginable.",
                "text": "Dime que otro lugar de Mexico quieres que redisene con IA",
                "is_hook": False
            }
        ]
    },
    5: {
        "title": "INGRESOS CON IA",
        "slides": [
            {
                "prompt": "Photorealistic 9:16 vertical cinematic photo of a small Mexico City bedroom doubling as a workspace. A single desk with a mid-range laptop phone external monitor and a ring light. IKEA desk mismatched chair. Empty Electrolit and Sabritas bag on the floor. Unmade bed in background. Posters on the wall. Looks like a real 25-year-old room not an influencer studio. Warm late-night lamp light. 35mm film grain.",
                "text": "$15,000 pesos. Este mes. Sin salir de mi cuarto.",
                "is_hook": True
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a Mexican smartphone screen showing a Mercado Pago app dashboard. The balance shows 15340 MXN in the available balance area. Below a transaction history showing multiple deposits ranging from 800 to 2500 pesos labeled with blurred client names. Date range last 30 days. Screen partially in shadow held by a casual hand. Authentic not overly staged.",
                "text": "$15,340 pesos en 30 dias. 9 clientes. Sin oficina.",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a laptop screen showing a clean well-designed Notion dashboard in Spanish titled Ingresos Marzo Stack de IA. Three rows: Copy para redes ChatGPT Canva 5800 pesos 4 clientes, Automatizaciones WhatsApp Make.com 6200 pesos 2 clientes, Presentaciones ejecutivas Gamma.app 3340 pesos 3 clientes. Total row highlighted in green 15340 pesos. Clean minimal design dark mode. Cinematic overhead laptop shot.",
                "text": "3 fuentes: copy redes, automatizaciones WhatsApp, presentaciones",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical flat-lay photo on a clean dark desk surface. A phone and laptop display various app icons arranged aesthetically: ChatGPT Canva Make.com Gamma.app Notion WhatsApp Business Mercado Pago. Each app logo clearly visible. A handwritten sticky note reads Todo esto es $15K al mes. Overhead cinematic lighting warm desk lamp glow. Slight lens distortion professional editorial look.",
                "text": "ChatGPT + Canva + Make.com + Gamma.app = tu stack",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a phone screen showing a Facebook Marketplace listing: Automatizo el WhatsApp de tu negocio con IA. Respuestas automaticas 24/7 catalogo digital seguimiento de clientes. 1500 pesos una sola vez. The listing has 47 messages and 23 saved. Nearby chat notifications piling up. Background the same bedroom. Real gritty unglamorous sales hustle. Cinematic phone close-up.",
                "text": "Primer cliente: Facebook Marketplace. $1,500 por automatizar WhatsApp",
                "is_hook": False
            },
            {
                "prompt": "Photorealistic 9:16 vertical split composition photo. Left half: a crowded Mexico City Metro at rush hour exhausted commuters packed tightly fluorescent lighting tired faces 7AM. Right half: a young person in pajamas holding a coffee mug laptop open on the bed sunlight through the window at 10AM. The contrast is striking and intentional. Text overlay in minimal white font: Mismo pais. Diferente decision. Cinematic punchy aspirational but grounded.",
                "text": "La siguiente semana: tutorial completo gratis. Sigueme",
                "is_hook": False
            }
        ]
    }
}


def process_series(series_num, series_data):
    print(f"\n{'='*60}")
    print(f"SERIES {series_num}: {series_data['title']}")
    print(f"{'='*60}")
    
    series_dir = os.path.join(VIDEOS_DIR, f"series-{series_num}")
    os.makedirs(series_dir, exist_ok=True)
    
    raw_paths = []
    overlay_paths = []
    
    for i, slide in enumerate(series_data["slides"], 1):
        print(f"\n--- Slide {i} ---")
        
        raw_path = os.path.join(series_dir, f"slide-{i}.jpg")
        overlay_path = os.path.join(series_dir, f"slide-{i}-text.jpg")
        
        # Download image
        if os.path.exists(raw_path) and os.path.getsize(raw_path) > 10000:
            print(f"  ✓ Already exists: {raw_path}")
        else:
            success = download_image(slide["prompt"], raw_path)
            if not success:
                print(f"  ✗ Failed to download slide {i}, using placeholder")
                # Create a placeholder with ffmpeg
                color = ["black", "darkblue", "darkgreen", "darkred", "purple", "darkorange"][i % 6]
                subprocess.run([
                    FFMPEG, "-y",
                    "-f", "lavfi", "-i", f"color={color}:size=1080x1920:rate=1",
                    "-frames:v", "1", raw_path
                ], capture_output=True)
        
        raw_paths.append(raw_path)
        
        # Add text overlay
        add_text_overlay(raw_path, overlay_path, slide["text"], is_hook=slide.get("is_hook", False))
        overlay_paths.append(overlay_path)
        
        # Small delay to avoid overwhelming the API
        if i < len(series_data["slides"]):
            time.sleep(2)
    
    # Create slideshow
    output_path = os.path.join(VIDEOS_DIR, f"series-{series_num}.mp4")
    create_slideshow(overlay_paths, output_path)
    
    if os.path.exists(output_path):
        size = os.path.getsize(output_path)
        print(f"\n✅ Series {series_num} complete: {output_path} ({size//1024//1024}MB)")
        return True, size
    else:
        print(f"\n❌ Series {series_num} failed")
        return False, 0


# Run all series
results = {}
for num in range(1, 6):
    success, size = process_series(num, SERIES[num])
    results[num] = {"success": success, "size": size}

print(f"\n{'='*60}")
print("FINAL RESULTS:")
print(f"{'='*60}")
for num, r in results.items():
    status = "✅" if r["success"] else "❌"
    size_mb = r["size"] // 1024 // 1024 if r["size"] > 0 else 0
    print(f"{status} Series {num}: {size_mb}MB")

# Save results
with open(os.path.join(BASE_DIR, "video_results.json"), "w") as f:
    json.dump(results, f, indent=2)

print("\nDone!")
