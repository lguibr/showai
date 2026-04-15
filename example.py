import os
from dotenv import load_dotenv
load_dotenv()

os.environ["PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS"] = "true"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

from showai import ShowAI, F5TTSEngine

# Use F5-TTS for voice cloning
engine = F5TTSEngine(ref_audio="lgvoice.wav")

app = ShowAI(tts=engine, output_video="demo1.mp4")


app.add_action(lambda page: page.goto("https://aethermaps.luisguilher.me"))
app.add_wait(2.0)

# Add a voice intro
app.add_voice("Welcome Community is my pleasure to share the Aether Maps a deterministic, 2D layered infinite grid of customaziable and explorable world")

# Speak while moving
# add action tahjt scrol out a little the application 
app.add_action(lambda page: page.mouse.wheel(0, 1000))
app.add_wait(1.0)

app.add_voice("Terrains are configurable so can adjust scale, raise the sea level, make it rough or smooth")
app.add_voice("Biomes and Climate could be changed from desets to tropical florests")
app.add_voice("Civilkizations and Strucures could be bigger and sparsed or dense and spread all over the map")
app.add_voice("We have FOG, Explored Map, Path Finder, ray casting, a tile inspector and much more! ")

# (Removed the hacker news hover selector because it will crash on the Tonai website since that class doesn't exist there!)
app.add_wait(1.0)

if __name__ == "__main__":
    app.execute()
