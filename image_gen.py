"""
image_gen.py — Generate slideshow images via ComfyUI API (local GPU)
Falls back to placeholder images if ComfyUI is not running.

ComfyUI should be running at http://127.0.0.1:8188
Install: cd ~/ComfyUI && python main.py --listen 127.0.0.1 --port 8188
"""

import json
import time
import uuid
import urllib.request
import urllib.error
from pathlib import Path

COMFYUI_URL = "http://127.0.0.1:8188"

# SDXL workflow template — portrait format for TikTok (768x1344)
SDXL_WORKFLOW = {
    "3": {
        "class_type": "KSampler",
        "inputs": {
            "cfg": 7,
            "denoise": 1,
            "latent_image": ["5", 0],
            "model": ["4", 0],
            "negative": ["7", 0],
            "positive": ["6", 0],
            "sampler_name": "dpmpp_2m",
            "scheduler": "karras",
            "seed": 0,  # will be randomized
            "steps": 25,
        },
    },
    "4": {
        "class_type": "CheckpointLoaderSimple",
        "inputs": {"ckpt_name": "sd_xl_base_1.0.safetensors"},
    },
    "5": {
        "class_type": "EmptyLatentImage",
        "inputs": {"batch_size": 1, "height": 1344, "width": 768},
    },
    "6": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 1],
            "text": "",  # will be filled with positive prompt
        },
    },
    "7": {
        "class_type": "CLIPTextEncode",
        "inputs": {
            "clip": ["4", 1],
            "text": "ugly, blurry, low quality, watermark, text, nsfw, distorted, deformed",
        },
    },
    "8": {
        "class_type": "VAEDecode",
        "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
    },
    "9": {
        "class_type": "SaveImage",
        "inputs": {"filename_prefix": "tiktok", "images": ["8", 0]},
    },
}


def is_comfyui_running():
    """Check if ComfyUI API is up."""
    try:
        urllib.request.urlopen(f"{COMFYUI_URL}/system_stats", timeout=3)
        return True
    except Exception:
        return False


def queue_prompt(workflow: dict) -> str:
    """Submit workflow to ComfyUI and return prompt_id."""
    client_id = str(uuid.uuid4())
    payload = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
    return result["prompt_id"]


def wait_for_completion(prompt_id: str, timeout=300):
    """Poll ComfyUI until the prompt is done, return output filenames."""
    start = time.time()
    while time.time() - start < timeout:
        with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as r:
            history = json.loads(r.read())
        if prompt_id in history:
            outputs = history[prompt_id]["outputs"]
            images = []
            for node_output in outputs.values():
                if "images" in node_output:
                    images.extend(node_output["images"])
            return images
        time.sleep(2)
    raise TimeoutError(f"ComfyUI prompt {prompt_id} timed out after {timeout}s")


def download_image(filename: str, subfolder: str, dest_path: Path):
    """Download generated image from ComfyUI output folder."""
    url = f"{COMFYUI_URL}/view?filename={filename}&subfolder={subfolder}&type=output"
    urllib.request.urlretrieve(url, dest_path)


def generate_placeholder(dest_path: Path, prompt: str, index: int):
    """Create a simple SVG placeholder when ComfyUI is not available."""
    dest_path.with_suffix(".svg").write_text(
        f"""<svg width="768" height="1344" xmlns="http://www.w3.org/2000/svg">
  <rect width="768" height="1344" fill="#1a1a2e"/>
  <rect x="40" y="40" width="688" height="1264" fill="none" stroke="#e94560" stroke-width="4" rx="20"/>
  <text x="384" y="150" font-family="Arial" font-size="80" fill="#e94560" text-anchor="middle">🤖</text>
  <text x="384" y="240" font-family="Arial" font-size="36" fill="#ffffff" text-anchor="middle">Slide {index + 1}</text>
  <text x="384" y="672" font-family="Arial" font-size="22" fill="#aaaaaa" text-anchor="middle" 
        style="word-wrap: break-word">[ComfyUI not running]</text>
  <text x="384" y="720" font-family="Arial" font-size="18" fill="#666666" text-anchor="middle">Install: cd ~/ComfyUI &amp;&amp; python main.py</text>
</svg>""",
        encoding="utf-8",
    )
    # Also write a .txt with the intended prompt
    dest_path.with_suffix(".prompt.txt").write_text(prompt, encoding="utf-8")


def generate_images(prompts: list[str], output_dir: Path) -> list[Path]:
    """
    Generate images for all prompts.
    Uses ComfyUI if running, otherwise creates placeholders.
    Returns list of output paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []

    if not is_comfyui_running():
        print("⚠️  ComfyUI not running — creating placeholder files.")
        print(f"   To install ComfyUI: cd ~/ && git clone https://github.com/comfyanonymous/ComfyUI.git")
        print(f"   Then: cd ~/ComfyUI && pip install -r requirements.txt")
        print(f"   Then: python main.py --listen 127.0.0.1 --port 8188")
        for i, prompt in enumerate(prompts):
            dest = output_dir / f"slide_{i+1:02d}.png"
            generate_placeholder(dest, prompt, i)
            paths.append(dest.with_suffix(".svg"))  # placeholder is SVG
        return paths

    print(f"✅ ComfyUI running — generating {len(prompts)} images...")
    import random

    for i, prompt in enumerate(prompts):
        print(f"   [{i+1}/{len(prompts)}] {prompt[:60]}...")
        workflow = json.loads(json.dumps(SDXL_WORKFLOW))  # deep copy
        workflow["6"]["inputs"]["text"] = (
            f"{prompt}, cinematic lighting, ultra detailed, 8k, tiktok vertical"
        )
        workflow["3"]["inputs"]["seed"] = random.randint(0, 2**32 - 1)

        prompt_id = queue_prompt(workflow)
        images = wait_for_completion(prompt_id)

        if images:
            dest = output_dir / f"slide_{i+1:02d}.png"
            download_image(images[0]["filename"], images[0].get("subfolder", ""), dest)
            paths.append(dest)
        else:
            print(f"   ⚠️  No output for slide {i+1}")

    return paths


if __name__ == "__main__":
    test_prompts = [
        "A tired developer staring at multiple screens with code, dark office, cinematic",
        "Close-up of frustrated face illuminated by blue monitor light",
        "Chat interface showing AI solving a complex bug, dramatic lighting",
        "Developer's face lighting up with realization and joy",
        "Clean code on screen, developer celebrating, warm lighting",
        "Developer presenting successful feature to impressed colleagues",
    ]
    out = Path("/tmp/tiktok_test_images")
    paths = generate_images(test_prompts, out)
    print(f"\nGenerated {len(paths)} files in {out}")
    for p in paths:
        print(f"  {p}")
