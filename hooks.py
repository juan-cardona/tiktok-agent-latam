"""
hooks.py — Hook research & generation for TikTok content pipeline
Uses Claude via Databricks proxy or Anthropic API directly.
Formula: person + conflict/doubt + AI solves it
"""

import os
import json
import random
import anthropic

# Databricks proxy base URL
DATABRICKS_BASE_URL = "https://adb-4687815777645220.0.azuredatabricks.net/serving-endpoints/anthropic"

# Trending topics pool (updated periodically)
TRENDING_TOPICS = [
    "programar sin saber nada",
    "pasar de junior a senior más rápido",
    "no tener tiempo para aprender a programar",
    "errores de código que nadie entiende",
    "entrevistas técnicas de trabajo",
    "aprender inglés técnico para programar",
    "crear una startup sin equipo",
    "automatizar tareas aburridas del trabajo",
    "ganar dinero con código siendo principiante",
    "hacer landing pages sin diseñador",
    "usar IA para hacer freelance",
    "sustituir a un diseñador UX con IA",
    "ChatGPT vs Claude: cuál usar",
    "código legacy que nadie quiere tocar",
    "hacer un proyecto de portfolio impresionante",
]

HOOK_FORMULA = """
Fórmula de hook viral: PERSONA + CONFLICTO/DUDA + IA LO RESUELVE

Ejemplos:
- "Esta dev llevaba 3 meses atascada con un bug... Claude lo resolvió en 40 segundos"
- "No sabía nada de programación. Usó IA y consiguió su primer cliente freelance en 2 semanas"
- "Su jefe le pidió una feature 'imposible'. Con OpenAI Codex la entregó en 1 hora"
"""


def get_client():
    """Return Anthropic client — Databricks proxy if key available, else direct."""
    api_key = os.environ.get("DATABRICKS_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "No API key found. Set DATABRICKS_API_KEY or ANTHROPIC_API_KEY env var."
        )

    # Prefer Databricks proxy
    if os.environ.get("DATABRICKS_API_KEY"):
        return anthropic.Anthropic(
            api_key=api_key,
            base_url=DATABRICKS_BASE_URL,
        )
    else:
        return anthropic.Anthropic(api_key=api_key)


def research_hooks(n=5, topic=None):
    """Generate n hook ideas for the given topic (random if None)."""
    if topic is None:
        topic = random.choice(TRENDING_TOPICS)

    client = get_client()

    system = (
        "Eres un experto en contenido viral de TikTok para audiencia LATAM (México, Argentina, Colombia). "
        "Tu especialidad es contenido de IA, programación y tecnología en español. "
        "Conoces las tendencias actuales de TikTok y sabes qué formatos generan engagement."
    )

    prompt = f"""
Genera {n} hooks virales para TikTok sobre el tema: "{topic}"

{HOOK_FORMULA}

Para cada hook, devuelve un JSON con:
- hook: el texto del hook (max 15 palabras, impactante, primera persona o narrativa)
- topic: el tema específico
- conflict: el conflicto o duda de la persona
- resolution: cómo la IA lo resuelve (menciona Claude, OpenAI, o "IA" genérica)
- score: tu estimación de viralidad del 1-10
- format: "slideshow" (6 imágenes) o "talking_head"

Responde SOLO con un array JSON válido, sin markdown, sin explicaciones.
"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        system=system,
    )

    raw = message.content[0].text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    hooks = json.loads(raw)
    return hooks


def pick_best_hook(hooks):
    """Pick the highest-scoring hook from the list."""
    return max(hooks, key=lambda h: h.get("score", 0))


def generate_image_prompts(hook, n=6):
    """Generate n image prompts for a slideshow based on the hook."""
    client = get_client()

    prompt = f"""
Dado este hook de TikTok en español:
"{hook['hook']}"

Conflicto: {hook['conflict']}
Resolución con IA: {hook['resolution']}

Genera {n} prompts en INGLÉS para Stable Diffusion SDXL que cuenten esta historia visualmente.
Estilo: fotorrealista, cinematográfico, iluminación dramática, colores vibrantes.
Las imágenes deben fluir como una historia de 6 slides:
1. Establecer la persona/personaje
2-3. Mostrar el conflicto o problema
4. El momento "a-ha" con la IA
5-6. La resolución exitosa

Responde SOLO con un array JSON de {n} strings (los prompts en inglés). Sin markdown.
"""

    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    prompts = json.loads(raw)
    return prompts


if __name__ == "__main__":
    print("Testing hook generation...")
    hooks = research_hooks(n=3)
    print(json.dumps(hooks, indent=2, ensure_ascii=False))
    best = pick_best_hook(hooks)
    print("\nBest hook:", best["hook"])
    prompts = generate_image_prompts(best)
    print("\nImage prompts:")
    for i, p in enumerate(prompts, 1):
        print(f"  {i}. {p}")
