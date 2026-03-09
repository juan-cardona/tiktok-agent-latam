# TikTok Agent Skill Log
_Oliver Henry style — track what works, kill what doesn't_

## Core Formula
**PERSONA + CONFLICTO + IA LO RESUELVE**
Person has a problem → AI solves it → audience thinks "that could be me"

## What Works (update as you test)

### Hooks that perform
- Narrative hooks in third person: "Esta dev llevaba 3 meses..." → high intrigue
- Number-based: "3 meses → 40 segundos" → contrast creates curiosity
- First person vulnerability: "No sabía programar y..." → relatable

### Image style
- Dark background + vibrant accent colors (neon blue, coral red) → thumb-stopping
- Faces showing emotion (frustration → relief) → human connection
- Code on screen in dark mode → instant "developer" signal
- Portrait 9:16 for TikTok slides

### Caption structure
- Line 1: Hook (same as video, drives saves)
- Line 2-3: Tease without spoiling
- Line 4: CTA (save, follow, comment)
- Hashtags: mix niche + LATAM + viral (12-15 total)

### Best posting times (LATAM)
- Mexico: 7-9pm CST (after work)
- Argentina: 8-10pm ART
- Colombia: 7-9pm COT
- Sunday + Tuesday peak engagement

### Topics that resonate in LATAM
- "de 0 a conseguir trabajo con IA" → aspirational
- "automatizé [tarea aburrida] con IA" → practical
- bugs/errores resueltos con IA → relatable pain
- ganar dinero freelance con IA → monetization angle

## What Doesn't Work

### Avoid
- Generic "ChatGPT is amazing" content → oversaturated
- Long explanations in caption → kills engagement
- English hooks for Spanish audience → wrong fit
- More than 4 emojis → looks spammy

## Pipeline Notes

### ComfyUI Setup
- Model: SDXL base 1.0 (sd_xl_base_1.0.safetensors)
- VRAM: RTX 3060 12GB — use fp16, batch_size=1
- Resolution: 768x1344 (TikTok portrait)
- Steps: 25, CFG: 7, sampler: dpmpp_2m karras
- Install: `cd ~/ComfyUI && python main.py --listen 127.0.0.1 --port 8188`

### API
- Databricks proxy: https://adb-4687815777645220.0.azuredatabricks.net/serving-endpoints/anthropic
- Env var: DATABRICKS_API_KEY or ANTHROPIC_API_KEY
- Model: claude-sonnet-4-5 (via proxy)

## TODO
- [ ] Wire Discord notification in agent.py step 7
- [ ] Install ComfyUI and test image generation
- [ ] Test full pipeline end-to-end
- [ ] Add TikTok auto-upload via unofficial API (tiktok-uploader)
- [ ] Track which hooks perform → feed back into TRENDING_TOPICS
- [ ] A/B test hook formulas
