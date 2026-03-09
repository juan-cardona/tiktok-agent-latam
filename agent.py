#!/usr/bin/env python3
"""
agent.py — Main daily TikTok content agent runner
Run: python agent.py
Or via systemd: tiktok-agent.service (daily at 9am Mexico City)

Pipeline:
  1. Research trending hooks (hooks.py)
  2. Pick best hook
  3. Generate image prompts
  4. Generate slideshow images (image_gen.py via ComfyUI)
  5. Generate Spanish caption (caption.py)
  6. Save draft package to ~/projects/tiktok-agent/drafts/YYYY-MM-DD/
  7. (Optional) Post Discord notification
"""

import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Project root
PROJECT_DIR = Path(__file__).parent
DRAFTS_DIR = PROJECT_DIR / "drafts"

TZ_CDMX = ZoneInfo("America/Mexico_City")


def get_today_dir() -> Path:
    today = datetime.now(TZ_CDMX).strftime("%Y-%m-%d")
    d = DRAFTS_DIR / today
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_draft(draft_dir: Path, data: dict):
    """Save all draft assets to the day's folder."""
    # Main metadata file
    meta_path = draft_dir / "draft.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Caption as plain text for easy copy-paste
    caption_path = draft_dir / "caption.txt"
    caption_path.write_text(
        data.get("caption", {}).get("full_text", ""), encoding="utf-8"
    )

    # Hook summary
    hook_path = draft_dir / "hook.txt"
    hook = data.get("hook", {})
    hook_path.write_text(
        f"HOOK: {hook.get('hook', '')}\n\n"
        f"Conflicto: {hook.get('conflict', '')}\n"
        f"Resolución: {hook.get('resolution', '')}\n"
        f"Score: {hook.get('score', '')}/10\n",
        encoding="utf-8",
    )

    # Image prompts
    prompts_path = draft_dir / "image_prompts.txt"
    prompts = data.get("image_prompts", [])
    prompts_path.write_text(
        "\n\n".join(f"Slide {i+1}:\n{p}" for i, p in enumerate(prompts)),
        encoding="utf-8",
    )

    print(f"✅ Draft saved to: {draft_dir}")


def log(msg: str):
    ts = datetime.now(TZ_CDMX).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def run():
    log("🚀 TikTok Agent starting...")
    draft_dir = get_today_dir()
    log(f"📁 Draft dir: {draft_dir}")

    # Check if already ran today
    meta_path = draft_dir / "draft.json"
    if meta_path.exists():
        log("⏭️  Draft already exists for today. Use --force to regenerate.")
        if "--force" not in sys.argv:
            return

    # ── Step 1: Research hooks ──────────────────────────────────────────────
    log("🔍 Step 1: Researching hooks...")
    from hooks import research_hooks, pick_best_hook, generate_image_prompts

    hooks = research_hooks(n=5)
    log(f"   Generated {len(hooks)} hook candidates")

    # ── Step 2: Pick best hook ──────────────────────────────────────────────
    log("🎯 Step 2: Picking best hook...")
    best_hook = pick_best_hook(hooks)
    log(f"   ✨ Best hook (score {best_hook.get('score')}/10): {best_hook['hook']}")

    # ── Step 3: Generate image prompts ─────────────────────────────────────
    log("🎨 Step 3: Generating image prompts...")
    image_prompts = generate_image_prompts(best_hook, n=6)
    log(f"   Generated {len(image_prompts)} prompts")

    # ── Step 4: Generate images ────────────────────────────────────────────
    log("🖼️  Step 4: Generating slideshow images...")
    from image_gen import generate_images

    images_dir = draft_dir / "images"
    image_paths = generate_images(image_prompts, images_dir)
    log(f"   Generated {len(image_paths)} images in {images_dir}")

    # ── Step 5: Generate caption ───────────────────────────────────────────
    log("✍️  Step 5: Generating Spanish caption...")
    from caption import generate_caption, format_for_display

    caption_data = generate_caption(best_hook, image_prompts)
    log(f"   Caption generated ({len(caption_data.get('full_text', ''))} chars)")
    print()
    print(format_for_display(caption_data))
    print()

    # ── Step 6: Save draft package ─────────────────────────────────────────
    log("💾 Step 6: Saving draft package...")
    draft = {
        "date": datetime.now(TZ_CDMX).isoformat(),
        "hook": best_hook,
        "all_hooks": hooks,
        "image_prompts": image_prompts,
        "image_paths": [str(p) for p in image_paths],
        "caption": caption_data,
    }
    save_draft(draft_dir, draft)

    # ── Step 7: Discord notification ──────────────────────────────────────
    log("📣 Step 7: Discord notification (placeholder — wire separately)")
    # TODO: call openclaw discord send with draft summary

    log("🎉 Agent complete! Review draft at:")
    log(f"   {draft_dir}")
    log(f"   Caption: {draft_dir / 'caption.txt'}")
    log(f"   Hook: {draft_dir / 'hook.txt'}")

    return draft


if __name__ == "__main__":
    try:
        run()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Agent failed: {e}")
        traceback.print_exc()
        sys.exit(1)
