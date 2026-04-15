<p align="center">
  <img src="logo.png" alt="ShowAI Logo" width="250" />
</p>

<h1 align="center">ShowAI</h1>

> **A blazing fast, programmatic browser voiceover & timeline generator.**

**ShowAI** is a Python framework that completely automates the creation of narrated browser recordings. It allows you to programmatically define a "timeline" consisting of browser actions, wait periods, and AI-generated voiceovers. The engine runs Playwright under the hood, plays the generated voice in sync with the actions, captures the raw video, and seamlessly stitches everything together using FFmpeg.

---

## 🚀 Features

- **Programmatic Timeline**: Chain `add_action(lambda page: ...)`, `add_wait(sec)`, and `add_voice("Text")` to script your perfect demo.
- **Dual TTS Engine Architecture**: 
  - 🎙️ **F5-TTS**: High-quality, zero-shot voice cloning directly from your `.wav`/`.m4a` files.
- **Cinematic Execution**: Features a built-in boot-up sequence, terminal ASCII art banner, and a professional video splash screen using your `logo.png`.
- **Auto-Stitching**: Transparently delegates video + audio track alignment to FFmpeg, guaranteeing perfectly synced `.mp4` outputs.

---

## 🛠️ Installation

ShowAI is built for modern Python (3.10+). We recommend using `uv` for lightning-fast dependency resolution.

```bash
# 1. Create your isolated environment
uv venv --python 3.12 venv
source venv/bin/activate

# 2. Install ShowAI in editable mode
uv pip install -e .

# 3. Ensure browser drivers are present
playwright install chromium
```

---

## 💻 Quickstart 

A robust `example.py` is included in the project directory. It demonstrates how to rapidly spin up a voice-synced walkthrough using **F5-TTSVoice Cloning**.

```python
import os
from dotenv import load_dotenv

from showai import ShowAI, F5TTSEngine

# Define Voice Engine (Using your own zero-shot profile)
engine = F5TTSEngine(ref_audio="lgvoice.wav")

app = ShowAI(tts=engine, output_video="demo1.mp4")

# 1. Introduce the video
app.add_voice("Welcome to my ShowAI project.")

# 2. Add visual interactions via Playwright
app.add_action(lambda page: page.goto("https://tonai.luisguilher.me"))
app.add_wait(1.5)

# 3. Speak while navigating
app.add_voice("The timeline engine perfectly syncs my voice to these exact moments.")
app.add_wait(2.0)

if __name__ == "__main__":
    app.execute()
```

Run your timeline from your terminal (the ASCII banner will welcome you!):
```bash
python example.py
```

---

## 🧠 Architecture Setup

### Timeline Orchestrator (`ShowAI`)
The Orchestrator caches the entire timeline before spinning up the browser. All heavy TTS generation happens *before* the browser window opens to ensure perfectly buttery-smooth Playwright recordings.

### Browser Automation (`BrowserAutomation`)
Runs in `headless=False` so you visually confirm the script is working. It automatically renders a cinematic center-framed black HTML screen containing the logo for 0.5s before kicking off your `goto` and `click` logic.

### Missing FFmpeg?
If the script crashes at the final video stitching step, please ensure your system has FFmpeg installed:
- Ubuntu/Debian: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`

<p align="center">
  <i>Built to automate the un-automatable.</i>
</p>
