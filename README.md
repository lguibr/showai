<p align="center">
  <img src="assets/logo.png" alt="ShowAI Logo" width="250" />
</p>

<h1 align="center">ShowAI</h1>

> **A blazing fast, programmatic browser voiceover & timeline generator.**

**ShowAI** is a Python framework that completely automates the creation of narrated browser recordings. It allows you to programmatically define a "timeline" consisting of browser actions, wait periods, and AI-generated voiceovers. The engine runs Playwright under the hood, plays the generated voice in sync with the actions, captures the raw video, and seamlessly stitches everything together using FFmpeg.

---

## 🚀 Features

- **Programmatic Timeline**: Chain `add_action(lambda page: ...)`, `add_wait(sec)`, and `add_voice("Text")` to script your perfect demo.
- **Zero-Shot Voice Cloning Architecture**:
  - 🎙️ **FunAudioLLM / CosyVoice 3.0**: High-quality, zero-shot voice cloning directly from a short reference audio file. The engine robustly maps instructions to speech directly inside a `Qwen2` LLM architecture.
- **Cinematic Execution**: Features a built-in boot-up sequence, terminal ASCII art banner, and a professional video splash screen using your `logo.png`.
- **Auto-Stitching**: Transparently delegates video + audio track alignment to FFmpeg, guaranteeing perfectly synced `.mp4` outputs.
---

## 🛠️ Installation

ShowAI's client logic is blazing fast and lightweight. It delegates the heavy PyTorch Voice Cloning inference to an external `docker-compose` backend!

```bash
# 1. Start the Voice Cloning Backend (Requires CUDA/NVIDIA Toolkit)
# This spins up the CosyVoice FastAPI Engine on port :50000
docker-compose up -d

# 2. Setup your local Environment 
uv venv --python 3.12 .venv
source .venv/bin/activate

# 3. Install the ShowAI Lightweight Client API
uv pip install -e .

# 4. Ensure browser drivers are present
playwright install chromium
```

---

## 💻 Quickstart

Because `ShowAI` dynamically queries the `localhost:50000` Docker backend, you can execute your timelines entirely completely free of PyTorch overhead:

```python
import os
from dotenv import load_dotenv
from showai import ShowAI, CosyVoiceEngine

load_dotenv()

# 1. Initialize CosyVoice 3.0 (Requires a sample reference audio and its transcription)
engine = CosyVoiceEngine(
    default_prompt_audio="assets/my_voice.wav",
    default_prompt_text="Community is my pleasure to share the Aether maps a deterministic 2D layered infinite grid of customizable and explorable world."
)

app = ShowAI(tts=engine, output_video="showcase.mp4", headless=False, play_audio=True)

# 2. Introduce the video
app.add_voice("Welcome to my ShowAI project.")

# 3. Add visual interactions via Playwright
app.add_action(lambda page: page.goto("https://aethermaps.luisguilher.me"))
app.add_wait(1.5)

# 4. Speak while navigating
app.add_voice("The timeline engine perfectly syncs my voice to these exact moments.")
app.add_wait(2.0)

if __name__ == "__main__":
    app.execute()
```

Run your timeline from your terminal (the ASCII banner will welcome you!):

```bash
python aethermap.py
```

---

## 🧠 Architecture Setup

### Timeline Orchestrator (`ShowAI`)

The Orchestrator caches the entire timeline before spinning up the browser. All heavy TTS generation and LLM token decoding happens *before* the browser window opens to ensure perfectly buttery-smooth Playwright recordings.

### Browser Automation (`BrowserAutomation`)

Runs in `headless=False` so you visually confirm the script is working. It automatically renders a cinematic center-framed black HTML screen containing the logo for 0.5s before kicking off your `goto` and `click` logic. It automatically routes the generated voice cloning audio track sequentially through background threads to match the execution.

### Missing FFmpeg?

If the script crashes at the final video stitching step or `CosyVoice` fails to resample internal references, ensure your system has FFmpeg installed:

- Ubuntu/Debian: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`

<p align="center">
  <i>Built to automate the un-automatable.</i>
</p>
