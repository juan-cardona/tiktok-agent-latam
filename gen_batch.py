#!/usr/bin/env python3
"""Generate TikTok slideshow videos from series scripts using Pollinations FLUX API."""

import os
import subprocess
import time
import urllib.parse
import urllib.request
import shutil
import tempfile
from pathlib import Path

FFMPEG = "/home/linuxbrew/.linuxbrew/bin/ffmpeg"
VIDEOS_DIR = Path.home() / "projects/tiktok-agent/videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

SERIES = [
    {
        "number": 6,
        "timestamp": "20260309-0200",
        "hook_text": "3 entrevistas",
        "slides": [
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a laptop screen showing a messy, outdated resume in Word format. The document has inconsistent fonts, Comic Sans-like headings, a small passport photo in the corner, and generic phrases like 'soy una persona responsable y puntual'. The inbox sidebar shows 47 sent job applications, 0 replies. Dim blue laptop glow in a dark bedroom. Relatable, slightly painful to look at. Cinematic 35mm style.",
                "text": "3 entrevistas",
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a MacBook or laptop screen in a coffee shop showing a ChatGPT conversation in Spanish. The user's prompt reads: 'Actua como un reclutador senior en LATAM. Tengo 3 anos de experiencia en marketing digital. Reescribe mi CV para una vacante de Marketing Manager en una startup de tecnologia en CDMX. Hazlo pasar filtros ATS. Usa metricas reales y lenguaje de alto impacto.' Warm cafe ambient light, hands on keyboard. Cinematic depth of field.",
                "text": "El prompt que cambia todo",
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a sleek, modern resume on a laptop screen. Clean minimal design: white background, professional typography, strong action verbs, bullet points with metrics ('Aumenté conversión en 47%', 'Gestioné presupuesto de $200K MXN', 'Lideré equipo de 5 personas'). The header shows a professional LinkedIn-style name. No photo. ATS-friendly layout. The screen glows warmly in a dim room. Editorial quality shot.",
                "text": "CV nuevo con métricas",
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a Mexican smartphone lock screen showing multiple LinkedIn and email notifications: 'Startup MX vio tu perfil', 'Nueva solicitud de conexion: Reclutadora — Clip', 'Te han invitado a una entrevista — Konfio', 'Tu aplicacion fue seleccionada — Kavak'. Timestamp shows 48 hours after submission. The phone is held with slightly shaking hands. Dramatic side lighting. Cinematic, high contrast.",
                "text": "Notificaciones en 48h",
            },
            {
                "prompt": "Photorealistic 9:16 vertical overhead shot of a clean desk with a notebook open, handwritten in Spanish in neat bullet format: '1. Dale el JD de la vacante a ChatGPT', '2. Pidele que adapte TU CV para ese puesto especifico', '3. Usa Jobscan.co para verificar el score ATS antes de enviar'. A laptop, phone, and cup of coffee also on the desk. Warm morning light. Organized, aspirational, achievable. Flat lay editorial style.",
                "text": "3 pasos del método",
            },
            {
                "prompt": "Photorealistic 9:16 vertical photo of a young Mexican professional in their mid-20s, business casual outfit, sitting confidently in a modern office lobby or co-working space (think WeWork CDMX style). They're smiling at their phone, which shows a calendar app with three interview slots booked this week. Light and airy, professional but approachable. Success energy without being cringe. Shot on Sony A7, 50mm, natural window light.",
                "text": "Sígueme para más 👇",
            },
        ],
    },
    {
        "number": 7,
        "timestamp": "20260309-0200",
        "hook_text": "La IA",
        "slides": [
            {
                "prompt": "Photorealistic 9:16 vertical cinematic photo of a small artisan food business setup in Mexico City — a clean home kitchen with packaged products lined up: jars of salsa, labeled bags, small boxes. Instagram-worthy aesthetic, warm lighting, a phone showing 2,400 followers. Everything looks good on the surface. Cozy, small business energy. But subtle signs of chaos: post-its everywhere, overflowing inbox on laptop in background. Honest, not glamorous.",
                "text": "La IA vio",
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a laptop screen showing a Google Sheets spreadsheet in Spanish, messy and color-coded inconsistently. Columns: Ingresos, Costos, Ganancia. Numbers visible: monthly revenue $18,500 MXN, costs $16,800 MXN, margin 9.7%. A red cell screams 'COSTO DELIVERY: $4,200/mes'. The spreadsheet is partially hidden under browser tabs — Netflix, Instagram, Shopify. Dim home office lighting. Documentary realism.",
                "text": "Números que no cuadran",
            },
            {
                "prompt": "Photorealistic 9:16 vertical laptop screen showing a detailed ChatGPT conversation in Spanish. The AI response is analytical, formatted like a business consultant's report: Warning Analisis de viabilidad: Tu margen operativo actual (9.7%) esta por debajo del minimo sostenible para un negocio de alimentos perecederos (15-20%). Los costos de entrega representan el 22% de tus ingresos — esto es critico. Proyeccion: con el ritmo actual de crecimiento de costos vs ingresos, tendras flujo negativo en aproximadamente 11-14 semanas. Dramatic. Cinematic blue screen glow.",
                "text": "Diagnóstico brutal de IA",
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a phone screen showing a clean WhatsApp message or notes app with a bulleted action plan in Spanish: '1. Eliminar rutas de entrega de baja densidad (ahorro: $1,800/mes)', '2. Subir precio kit familiar 18% (prueba A/B esta semana)', '3. Cambiar proveedor de empaques (cotizacion adjunta)', '4. Lanzar suscripcion mensual para garantizar flujo fijo', '5. Meta: margen 22% en 60 dias'. Clean, actionable, urgent. Warm phone screen glow in dark room.",
                "text": "Plan de rescate 5 pasos",
            },
            {
                "prompt": "Photorealistic 9:16 vertical flat-lay photo of a small business workspace — a desk with a laptop showing updated Google Sheets with green cells, a notebook with checkmarks next to action items, product samples, and a phone showing Mercado Pago with a positive balance. Post-its with 'MARGEN 23%' and 'SUSCRIPTORES: 34' visible. Warm afternoon light. Progress energy. Organized chaos becoming organized success.",
                "text": "2 meses de cambios",
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a smartphone screen showing a clean business dashboard — maybe a Shopify or Notion metrics page in Spanish. Key metrics visible: 'Margen actual: 23.4%', 'Suscriptores activos: 34', 'Ingresos MRR: $22,100 MXN', 'Costo delivery: $1,900 MXN (55% menos)'. A hand with painted nails holds the phone — the business owner. Bright confident lighting. Minimal, factual, satisfying.",
                "text": "Sígueme para más 👇",
            },
        ],
    },
    {
        "number": 8,
        "timestamp": "20260309-0200",
        "hook_text": "De 'I",
        "slides": [
            {
                "prompt": "Photorealistic 9:16 vertical cinematic photo of a young Mexican professional in their mid-20s sitting in a modern CDMX office, visibly anxious. Everyone around them in a meeting room is speaking — an international video call is on the screen showing foreign faces. The protagonist has their notepad in front of them but hasn't written anything, eyes slightly wide, jaw tight. The scene captures professional anxiety perfectly. Documentary style, 35mm grain, natural fluorescent office lighting.",
                "text": "De 'I no speak'",
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a phone screen in a Mexico City metro or cafe showing a ChatGPT conversation in Spanish and English. The user has written: 'Actua como mi tutor de ingles de negocios. Hoy quiero practicar como presentarme en una junta con clientes de EE.UU. Corrigeme con contexto cultural, no solo gramatica.' The AI response starts with a warm, structured lesson. Cramped metro seat visible in background. Everyday learning energy. Cinematic mobile photography.",
                "text": "ChatGPT como tutor",
            },
            {
                "prompt": "Photorealistic 9:16 vertical flat-lay editorial photo on a clean desk: a phone showing ChatGPT, another tab with Claude.ai, earbuds, a small notebook with handwritten English phrases, and a sticky note that reads '20 MIN/DIA = FLUENT'. Clean minimal setup. Warm morning coffee light. Labels visible: 'Conversacion IA', 'Shadowing podcast', 'Vocab con contexto'. Organized learning aesthetic. Shot from above, editorial quality.",
                "text": "Stack de 20 min diarios",
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a Notion or Google Docs page in Spanish showing a 90-day learning tracker. A table with columns: Semana, Habilidad practicada, Nivel autopercibido (1-10), Notas. Weeks 1-4: scores of 3-4. Weeks 5-8: scores of 5-7. Weeks 9-13: scores of 7-9. Key entry highlighted: 'Semana 12: Primera reunion real con cliente de Austin. Me entendieron. Los entendi.' Color-coded green progression. Real, humble, honest.",
                "text": "Progreso en 90 días",
            },
            {
                "prompt": "Photorealistic 9:16 vertical photo of a young Mexican professional confidently speaking in a video call on a laptop. The Zoom screen shows two American-looking professionals listening attentively. The protagonist has notes beside them, speaks with clear body language — leaning slightly forward, one hand gesturing. Modern CDMX apartment background, clean and professional. Warm natural light from a window. Candid success moment. Shot on Sony A7.",
                "text": "Primera junta en inglés",
            },
            {
                "prompt": "Photorealistic 9:16 vertical close-up of a phone showing a LinkedIn message thread in English: 'Great meeting you today! Your presentation was very clear and professional. We'd love to move forward.' The reply from the protagonist: 'Thank you so much! Looking forward to working together'. The phone is held by a hand with a subtle smile partially visible. Background: a Mexico City window with city view. Pride, quiet achievement, authentic.",
                "text": "Sígueme para más 👇",
            },
        ],
    },
]


def download_image(prompt: str, output_path: str, retries: int = 3) -> bool:
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1080&height=1920&nologo=true&model=flux"
    for attempt in range(1, retries + 1):
        print(f"    Downloading (attempt {attempt}/{retries})...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as response:
                data = response.read()
            if len(data) < 5000:
                print(f"    Warning: small response ({len(data)} bytes), retrying...")
                time.sleep(5)
                continue
            with open(output_path, "wb") as f:
                f.write(data)
            print(f"    Downloaded {len(data)//1024}KB → {output_path}")
            return True
        except Exception as e:
            print(f"    Error: {e}")
            time.sleep(5)
    return False


def make_fallback_slide(output_path: str, width: int = 1080, height: int = 1920):
    """Create a solid black fallback slide."""
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi",
        "-i", f"color=black:size={width}x{height}:duration=1",
        "-frames:v", "1",
        output_path,
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"    Created fallback slide: {output_path}")


def add_text_overlay(input_path: str, output_path: str, text: str):
    """Add white text with black outline at bottom center."""
    # Escape special ffmpeg drawtext characters
    safe_text = (
        text.replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace(":", "\\:")
            .replace("%", "\\%")
            # Remove emoji that ffmpeg can't render without special font
    )
    # Strip emoji for ffmpeg compatibility
    import re
    safe_text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u00A1-\u00FF]', '', safe_text).strip()
    if not safe_text:
        safe_text = "Sigueme para mas"

    drawtext = (
        f"fontsize=72:fontcolor=white:borderw=4:bordercolor=black:"
        f"x=(w-text_w)/2:y=h-150:"
        f"text='{safe_text}'"
    )
    cmd = [
        FFMPEG, "-y",
        "-i", input_path,
        "-vf", f"drawtext={drawtext}",
        "-q:v", "2",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"    drawtext warning: {result.stderr[-200:]}")
        # fallback: just copy
        shutil.copy(input_path, output_path)
    else:
        print(f"    Text overlay added: '{safe_text}'")


def build_video(slide_paths: list, output_path: str):
    """Combine slides into a video with crossfade transitions."""
    duration = 3.0
    fade_duration = 0.5

    # Build a complex filtergraph for xfade transitions
    n = len(slide_paths)

    # Create input args
    inputs = []
    for p in slide_paths:
        inputs += ["-loop", "1", "-t", str(duration), "-i", p]

    # Build filter_complex for xfade
    filter_parts = []
    # Scale all inputs
    for i in range(n):
        filter_parts.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]")

    # Chain xfades
    # First transition: v0 + v1 → xf0
    offset = duration - fade_duration
    filter_parts.append(f"[v0][v1]xfade=transition=fade:duration={fade_duration}:offset={offset}[xf0]")
    for i in range(2, n):
        offset = (i - 1) * duration - (i - 1) * fade_duration + (duration - fade_duration)
        prev = f"xf{i-2}"
        cur = f"v{i}"
        out = f"xf{i-1}"
        filter_parts.append(f"[{prev}][{cur}]xfade=transition=fade:duration={fade_duration}:offset={offset}[{out}]")

    final_out = f"xf{n-2}"
    filter_complex = ";".join(filter_parts)

    cmd = [
        FFMPEG, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", f"[{final_out}]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-r", "30",
        output_path,
    ]
    print(f"  Running ffmpeg to build video...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-500:]}")
        raise RuntimeError("ffmpeg failed")
    print(f"  ✅ Video saved: {output_path}")


def process_series(series: dict):
    num = series["number"]
    ts = series["timestamp"]
    slides_data = series["slides"]
    output_filename = f"series-{ts}-{num}.mp4"
    output_path = VIDEOS_DIR / output_filename

    print(f"\n{'='*60}")
    print(f"Processing Series {num} → {output_filename}")
    print(f"{'='*60}")

    with tempfile.TemporaryDirectory() as tmpdir:
        raw_slides = []
        overlaid_slides = []

        for i, slide in enumerate(slides_data, 1):
            raw_path = os.path.join(tmpdir, f"slide-{i}-raw.jpg")
            overlay_path = os.path.join(tmpdir, f"slide-{i}-overlay.jpg")

            print(f"\n  Slide {i}/6: {slide['text']}")
            success = download_image(slide["prompt"], raw_path)
            if not success:
                print(f"  ⚠️  Download failed, using fallback black slide")
                make_fallback_slide(raw_path)

            add_text_overlay(raw_path, overlay_path, slide["text"])
            overlaid_slides.append(overlay_path)

        print(f"\n  Building video from {len(overlaid_slides)} slides...")
        build_video(overlaid_slides, str(output_path))

    return output_path


def main():
    print("TikTok Video Generator — Series 6, 7, 8")
    print(f"Output directory: {VIDEOS_DIR}")

    results = []
    for series in SERIES:
        try:
            path = process_series(series)
            results.append((series["number"], path, True))
        except Exception as e:
            print(f"  ❌ Series {series['number']} failed: {e}")
            results.append((series["number"], None, False))

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for num, path, ok in results:
        status = "✅" if ok else "❌"
        print(f"  Series {num}: {status} {path or 'FAILED'}")


if __name__ == "__main__":
    main()
