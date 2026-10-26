# 🤖 Agentic AI: Google LLM + Hugging Face Text-to-Image

An intelligent multi-model image generation agent that uses:
1. **Google Gemini LLM** as the **Prompt Director**: Takes any short, abstract, or simple user text and engineers a high-detail, visually striking prompt with artistic styling, composition, and lighting.
2. **Hugging Face Inference API** (FLUX.1-schnell / SDXL) as the **Image Synthesis Engine**: Renders the enhanced prompt into a high-resolution image.
3. **Google Imagen Fallback**: If Hugging Face is busy or rate-limited, it automatically falls back to Google's Imagen model.

## 📁 Project Structure

- [`text_to_image_agent.py`](file:///d:/work/olama%20resm/AntigravityLab/Agentic%20AI/text_to_image_agent.py) - Main Agent pipeline.
- [`main.py`](file:///d:/work/olama%20resm/AntigravityLab/Agentic%20AI/main.py) - CLI entry point.
- [`.env`](file:///d:/work/olama%20resm/AntigravityLab/Agentic%20AI/.env) - API configuration (`GEMINI_API_KEY`, optional `HF_TOKEN`).
- `outputs/` - Generated images (`.png`) and prompt metadata (`.json`).

## 🚀 How to Run

### Interactive Mode:
```bash
cd "Agentic AI"
python text_to_image_agent.py
```

### Direct CLI Mode:
```bash
python text_to_image_agent.py --prompt "A cyberpunk samurai in neon rain"
```
