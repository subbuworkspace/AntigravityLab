"""
Agentic AI: Google LLM + Hugging Face Text-to-Image Generation Pipeline
======================================================================
1. Agentic Director (Google Gemini LLM): Takes user prompt and enhances it into
   a rich, visually descriptive prompt with lighting, atmosphere, and styling.
2. Image Synthesis Engine:
   - Hugging Face InferenceClient (FLUX.1-schnell / SDXL) via HF_TOKEN.
   - Fallback image generation endpoints.
3. Automatically outputs saved PNG + JSON prompt metadata.
"""

import argparse
import datetime
import io
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if sys.platform.startswith("win"):
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dotenv import load_dotenv
from PIL import Image

CURRENT_DIR = Path(__file__).resolve().parent
load_dotenv(CURRENT_DIR / ".env")
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")

OUTPUT_DIR = CURRENT_DIR / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class AgenticTextToImage:
    def __init__(self, gemini_api_key=None, hf_token=None):
        self.gemini_api_key = gemini_api_key or GEMINI_API_KEY
        self.hf_token = hf_token or HF_TOKEN
        self.gemini_client = None
        self.hf_client = None
        self._init_clients()

    def _init_clients(self):
        # 1. Initialize Google Gemini Client
        if self.gemini_api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                print("[✓] Google Gemini LLM Director: CONNECTED")
            except Exception as e:
                print(f"[!] Warning: Could not initialize Google GenAI: {e}")
        else:
            print("[!] Note: GEMINI_API_KEY not found. LLM prompt enhancement will be skipped.")

        # 2. Initialize Hugging Face Client
        try:
            from huggingface_hub import InferenceClient
            self.hf_client = InferenceClient(token=self.hf_token)
            if self.hf_token:
                print("[✓] Hugging Face API: CONNECTED (Authenticated)")
            else:
                print("[!] Hugging Face: No HF_TOKEN found in .env.")
                print("    (Get a free token at https://huggingface.co/settings/tokens to enable custom HF models)")
        except Exception as e:
            print(f"[!] Note on HF client init: {e}")

    def enhance_prompt_with_gemini(self, user_prompt: str) -> str:
        """Uses Google Gemini LLM to expand and enhance the user's prompt."""
        if not self.gemini_client:
            return user_prompt

        system_instruction = (
            "You are an expert AI visual prompt engineer and art director. "
            "Given a user's text concept, enhance it into a vivid, photorealistic, highly detailed "
            "visual description for a modern text-to-image generator (FLUX / Stable Diffusion). "
            "Detail the subject, lighting, mood, color palette, camera lens/angle, and artistic texture. "
            "Output ONLY the final enhanced prompt text in 1-2 concise sentences. Do not add quotes or intros."
        )

        for model_name in ["gemini-flash-latest", "gemini-3.8-flash", "gemini-flash-lite-latest"]:
            try:
                print(f"[*] [Agent] Google LLM ({model_name}) enhancing prompt: '{user_prompt}'...")
                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=f"User prompt: {user_prompt}",
                    config={"system_instruction": system_instruction, "temperature": 0.7}
                )
                if response and response.text:
                    enhanced = response.text.strip().replace('"', '')
                    print(f"[+] [Agent] Enhanced Prompt:\n    \"{enhanced}\"\n")
                    return enhanced
            except Exception as err:
                print(f"[!] {model_name} notice: {err}")
                continue

        print("[!] Using original prompt without enhancement.")
        return user_prompt

    def generate_image_hf(self, prompt: str, model: str = "black-forest-labs/FLUX.1-schnell") -> Image.Image:
        """Generates an image using Hugging Face InferenceClient."""
        if not self.hf_client:
            raise ValueError("Hugging Face client is not initialized.")
        print(f"[*] [Hugging Face] Generating with model: {model}...")
        return self.hf_client.text_to_image(prompt, model=model)

    def generate_image_fallback(self, prompt: str) -> Image.Image:
        """Fallback generation via free web synthesis endpoint."""
        print("[*] [Engine] Generating image from prompt...")
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=768&nologo=true"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=40) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data))

    def generate(self, user_prompt: str, hf_model: str = "black-forest-labs/FLUX.1-schnell") -> Path:
        print("\n" + "=" * 60)
        print(f"🚀 Starting Generation for: \"{user_prompt}\"")
        print("=" * 60)

        # 1. Google Gemini Prompt Enhancement
        enhanced_prompt = self.enhance_prompt_with_gemini(user_prompt)

        # 2. Image Synthesis
        image = None
        provider_name = ""

        if self.hf_token:
            try:
                image = self.generate_image_hf(enhanced_prompt, model=hf_model)
                provider_name = f"Hugging Face ({hf_model})"
            except Exception as e:
                print(f"[!] Hugging Face provider message: {e}")

        if image is None:
            try:
                image = self.generate_image_fallback(enhanced_prompt)
                provider_name = "Image Synthesis Engine"
            except Exception as e:
                print(f"[!] Fallback error: {e}")
                raise RuntimeError(f"Could not generate image: {e}")

        # 3. Save File
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = "".join(c if c.isalnum() else "_" for c in user_prompt[:25]).strip("_")
        out_image_path = OUTPUT_DIR / f"{timestamp}_{slug}.png"
        image.save(out_image_path, format="PNG")

        # 4. Save Metadata JSON
        meta = {
            "timestamp": timestamp,
            "original_prompt": user_prompt,
            "enhanced_prompt": enhanced_prompt,
            "provider": provider_name,
            "output_file": str(out_image_path),
            "dimensions": f"{image.width}x{image.height}",
        }
        out_meta_path = OUTPUT_DIR / f"{timestamp}_{slug}.json"
        with open(out_meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        print("\n" + "—" * 60)
        print("🎉 Generated Successfully!")
        print(f"🖼️  File:     {out_image_path}")
        print("🤖 Director: Google Gemini LLM")
        print(f"🎨 Renderer: {provider_name}")
        print(f"📐 Size:     {image.width}x{image.height} px")
        print("—" * 60 + "\n")

        return out_image_path


def interactive_loop():
    print("=" * 65)
    print("🤖 AGENTIC AI: Google LLM + Hugging Face Text-to-Image")
    print("=" * 65)
    agent = AgenticTextToImage()
    print("\nType any prompt to generate an image (or type 'exit' to quit).\n")

    while True:
        try:
            prompt = input("Enter prompt > ").strip()
            if not prompt:
                continue
            if prompt.lower() in ("exit", "quit", "q"):
                print("Exiting. Have a great day!")
                break
            agent.generate(prompt)
        except KeyboardInterrupt:
            print("\nExited.")
            break
        except Exception as e:
            print(f"[!] Error: {e}\n")


def main():
    parser = argparse.ArgumentParser(description="Google LLM + Hugging Face Text-to-Image Agent")
    parser.add_argument("--prompt", type=str, help="Text prompt to generate an image for")
    parser.add_argument("--model", type=str, default="black-forest-labs/FLUX.1-schnell", help="Hugging Face model ID")
    args = parser.parse_args()

    if args.prompt:
        agent = AgenticTextToImage()
        agent.generate(args.prompt, hf_model=args.model)
    else:
        interactive_loop()


if __name__ == "__main__":
    main()
