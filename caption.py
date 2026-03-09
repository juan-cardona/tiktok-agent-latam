"""
caption.py — Generate Spanish TikTok caption with hook + CTA
"""

import os
import json
import requests

DATABRICKS_BASE_URL = "https://adb-4687815777645220.0.azuredatabricks.net/serving-endpoints"
DATABRICKS_MODEL = "databricks-claude-sonnet-4-5"

HASHTAG_POOLS = {
    "ai": ["#IA", "#InteligenciaArtificial", "#AITools", "#ChatGPT", "#Claude", "#OpenAI"],
    "coding": ["#Programacion", "#Programador", "#Dev", "#Codigo", "#SoftwareDeveloper", "#CodeWithAI"],
    "latam": ["#TikTokMexico", "#TikTokLatam", "#TechEnEspanol", "#ProgramadoresMX"],
    "growth": ["#AprendeConTikTok", "#TipsDeCarrera", "#FreelanceTips", "#DesarrolloPersonal"],
    "viral": ["#Viral", "#ParaTi", "#FYP", "#Trending"],
}

MAX_CAPTION_LENGTH = 2200  # TikTok's limit


def call_llm(prompt: str, max_tokens: int = 1024) -> str:
    """Call Databricks-hosted Claude via OpenAI-compatible API."""
    api_key = os.environ.get("DATABRICKS_API_KEY") or os.environ.get("DATABRICKS_TOKEN")
    if not api_key:
        raise ValueError("Set DATABRICKS_API_KEY env var.")
    url = f"{DATABRICKS_BASE_URL}/{DATABRICKS_MODEL}/invocations"
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"anthropic_version": "2023-06-01", "max_tokens": max_tokens,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def generate_caption(hook: dict, image_prompts: list[str]) -> dict:
    """
    Generate full TikTok caption including hook text, body, CTA, and hashtags.
    Returns dict with 'caption', 'hashtags', 'full_text'.
    """
    prompt = f"""
Crea una caption completa para TikTok en español para este contenido:

Hook: {hook['hook']}
Tema: {hook.get('topic', '')}
Conflicto: {hook.get('conflict', '')}
Resolución con IA: {hook.get('resolution', '')}
Formato: slideshow de 6 imágenes

La caption debe:
1. Empezar con el hook exacto (para capturar atención en los primeros 3 segundos)
2. Tener 2-3 líneas de cuerpo que generen curiosidad (no spoilear la solución)
3. Terminar con CTA claro: "Guarda este video 👇", "Sígueme para más tips de IA", etc.
4. Usar emojis con moderación (2-4 máximo)
5. Máximo 200 caracteres para el texto visible (antes de "ver más")

También sugiere 12-15 hashtags relevantes mezclando: nicho (IA/programación), audiencia LATAM, y virales.

Responde en JSON con:
{{
  "caption_text": "...",  // el texto principal sin hashtags
  "hook_line": "...",     // primera línea (el hook)
  "cta": "...",           // call to action
  "hashtags": ["#tag1", "#tag2", ...],
  "tone": "...",          // tono del video: motivacional/informativo/sorpresa/etc
  "best_posting_time": "..." // mejor hora para publicar en LATAM
}}
"""

    raw = call_llm(prompt)
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    result = json.loads(raw)

    # Assemble full caption
    full_text = f"{result['caption_text']}\n\n{' '.join(result['hashtags'])}"
    if len(full_text) > MAX_CAPTION_LENGTH:
        # Trim hashtags to fit
        hashtags = result["hashtags"]
        while len(full_text) > MAX_CAPTION_LENGTH and hashtags:
            hashtags.pop()
            full_text = f"{result['caption_text']}\n\n{' '.join(hashtags)}"
        result["hashtags"] = hashtags

    result["full_text"] = full_text
    return result


def format_for_display(caption_data: dict) -> str:
    """Pretty-print caption data for terminal/Discord display."""
    lines = [
        "📝 CAPTION GENERADA",
        "=" * 50,
        f"🎣 Hook: {caption_data.get('hook_line', '')}",
        "",
        caption_data.get("caption_text", ""),
        "",
        f"📣 CTA: {caption_data.get('cta', '')}",
        f"🎭 Tono: {caption_data.get('tone', '')}",
        f"⏰ Mejor hora: {caption_data.get('best_posting_time', '')}",
        "",
        "🏷️ Hashtags:",
        " ".join(caption_data.get("hashtags", [])),
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    test_hook = {
        "hook": "Esta dev llevaba 3 meses atascada con un bug... Claude lo resolvió en 40 segundos",
        "topic": "debugging con IA",
        "conflict": "bug imposible de resolver que bloquea el proyecto",
        "resolution": "Claude analiza el stack trace y encuentra el problema en segundos",
        "score": 9,
    }
    caption = generate_caption(test_hook, [])
    print(format_for_display(caption))
    print("\nFull caption preview:")
    print(caption["full_text"][:300], "...")
