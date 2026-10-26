# 🧪 AntigravityLab

A showcase of interactive Python applications, featuring:
1. 🎮 **Snake & Ball Arcade Game** — A fast-paced arcade game built in Tkinter with particle physics, 8-bit sound effects, and an optional bouncing hazard ball obstacle.
2. 🤖 **Agentic AI: Text-to-Image Pipeline** — An intelligent generative AI workflow that pairs Google Gemini LLM as an art director/prompt engineer with Hugging Face & FLUX image synthesis.

---

## 📂 Repository Structure

```text
AntigravityLab/
├── Agentic AI/
│   ├── outputs/               # Generated PNG images & prompt JSON metadata
│   ├── .env.example           # Template for API keys (never commit .env)
│   ├── main.py                # Agent CLI launcher
│   ├── text_to_image_agent.py # Core agentic text-to-image engine
│   ├── requirements.txt       # Dependencies for Agentic AI
│   └── README.md              # Detailed guide for Agentic AI
├── snakeball/
│   ├── main.py                # Game entry point
│   ├── snake_ball_game.py     # Main arcade game implementation
│   ├── requirements.txt       # Standard library notice
│   └── README.md              # Detailed guide & controls for Snakeball
├── .gitignore                 # Enforces security; ignores .env and caches
├── README.md                  # Main repository documentation
└── requirements.txt           # Unified project dependencies
```

---

## ⚡ Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/subbuworkspace/AntigravityLab.git
cd AntigravityLab
```

### 2. Set Up Virtual Environment (Recommended)
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 🎮 Project 1: Snake & Ball Arcade

A modern retro arcade game built with Python's built-in `tkinter` canvas.

```bash
cd snakeball
python snake_ball_game.py
```

### Controls:
- **Move Snake**: Arrow Keys or `W`, `A`, `S`, `D`
- **Start / Pause**: `Space` or `Enter`
- **Restart**: `R`
- **Toggle Bouncing Hazard Ball**: `H` (or click top button)
- **Toggle Sound Effects**: `M` (or click top button)
- **Quit**: `Esc`

---

## 🤖 Project 2: Agentic AI (Google LLM + Hugging Face)

An intelligent multi-stage image generation agent:
1. **Google Gemini LLM** (`gemini-flash-latest`) analyzes your input prompt and transforms it into an artistic visual specification.
2. **Hugging Face / FLUX.1 Engine** renders the enhanced prompt into a crisp image.

### Setup API Keys:
1. Copy the example environment file:
   ```bash
   cp "Agentic AI/.env.example" "Agentic AI/.env"
   ```
2. Open `Agentic AI/.env` and add your keys:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   HF_TOKEN=your_optional_huggingface_token
   ```

### Run Generation:
- **Interactive Mode**:
  ```bash
  cd "Agentic AI"
  python text_to_image_agent.py
  ```
- **Direct CLI Mode**:
  ```bash
  cd "Agentic AI"
  python text_to_image_agent.py --prompt "A cyberpunk samurai fighting under a crimson moon"
  ```

---

## 🔒 Security & Privacy

- **Never commit `.env` or API keys.** The repository includes a strict `.gitignore` to prevent secret leaks.
- Always use `.env.example` as a template for team members or public forks.

---

## 📜 License

MIT License. Feel free to use, modify, and build upon this repository!
