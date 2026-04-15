import os
from dotenv import load_dotenv

load_dotenv()

os.environ["PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS"] = "true"
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

from showai import ShowAI, CosyVoiceEngine

# Use CosyVoice 3 for reliable voice cloning
engine = CosyVoiceEngine(
    default_prompt_audio="data/assets/my_voice.wav",
    default_prompt_text="some call me nature, others call me mother nature"
)

app = ShowAI(tts=engine, output_video="data/output/videos/aethermap_showcase.mp4", headless=False, play_audio=True)

# Helper function to inject into actions for reliable slider updates
def update_slider(page, label_text, value):
    page.evaluate(f'''() => {{
        const labels = Array.from(document.querySelectorAll('label'));
        const label = labels.find(l => l.innerText.includes('{label_text}'));
        if (label) {{
            const input = label.nextElementSibling;
            if (input && input.tagName === 'INPUT') {{
                input.value = '{value}';
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }}
    }}''')
    
def click_accordion(page, text):
    try:
        page.evaluate(f'''() => {{
            const btns = Array.from(document.querySelectorAll('button'));
            const b = btns.find(b => b.innerText.includes('{text}') && b.innerText.includes('+'));
            if (b) b.click();
        }}''')
    except Exception:
        pass

# --- Canvas Map Interactions ---
def scroll_map(page, start_x=800, start_y=500, end_x=400, end_y=500):
    page.mouse.move(start_x, start_y)
    page.mouse.down()
    page.mouse.move(end_x, end_y, steps=20) # 'steps' makes it drag smoothly like a human
    page.mouse.up()

def click_map(page, x, y):
    page.locator("canvas").click(position={"x": x, "y": y})

def walk_to(page, x, y):
    page.locator("canvas").dblclick(position={"x": x, "y": y})

def find_and_walk_sequence(page):
    # Extremely reliable tracker by scanning canvas for the PINK stairs dot
    coords = page.evaluate(f'''() => {{
        const canvas = document.querySelector('canvas');
        if (!canvas) return null;
        const ctx = canvas.getContext('2d');
        const w = canvas.width;
        const h = canvas.height;
        const data = ctx.getImageData(0, 0, w, h).data;
        
        // Scan for Pink tile (R>200, G<50, B>200)
        for (let y = 100; y < h; y += 2) {{ 
            for (let x = 320; x < w; x += 2) {{ 
                const i = (y * w + x) * 4;
                if (data[i] > 200 && data[i+1] < 100 && data[i+2] > 200) {{
                    return {{x, y, w, h}};
                }}
            }}
        }}
        return null;
    }}''')
    
    if coords:
        px, py = coords['x'], coords['y']
        # 1. Single click bottom cell of tower (roughly slightly down from pink dot)
        page.locator("canvas").click(position={"x": px, "y": py + 40})
        page.wait_for_timeout(1000)
        
        # 2. Double click the pink point to go to Z -1
        page.locator("canvas").dblclick(position={"x": px, "y": py})
        page.wait_for_timeout(2000) # Wait for animation down
        
        # 3. Double click center point of viewport to go back up Z 0
        cx = coords['w'] / 2 + 160
        cy = coords['h'] / 2
        page.locator("canvas").dblclick(position={"x": cx, "y": cy})
        page.wait_for_timeout(2000)

def pan_left_sequence(page):
    for _ in range(5):
        # Dragging mouse to the right pulls the canvas view to the LEFT
        scroll_map(page, start_x=400, start_y=500, end_x=1000, end_y=500)
        page.wait_for_timeout(500)

app.add_action(lambda page: page.goto("https://aethermaps.luisguilher.me"))
app.add_wait(3.0)

# 1. Intro
app.add_voice("Welcome, Community ...  It is my absolute pleasure to share Aether Maps, a deterministic, two-D layered infinite grid ...A fully customizable, and explorable world...")

# 2. Fog, Tile Inspector, Movement (Do this first while the map is pristine!)
app.add_voice("We also have interactive fog, explored map memory, a path finder... Ray casting, a tile inspector, and much more.")
app.add_action(lambda page: scroll_map(page, start_x=800, start_y=500, end_x=600, end_y=400))
# Execute reliable color tracker sequence 
app.add_action(find_and_walk_sequence)
app.add_voice("Just double click, to travel to that chunk or use stairs to go deep underground... Try tweaking gameplay rules, expanding the fog radius...")
app.add_action(pan_left_sequence)

app.add_action(lambda page: click_accordion(page, "GAMEPLAY"))
app.add_action(lambda page: update_slider(page, "Fog Radius", "32"))

# 3. Terrains are configurable
app.add_voice("Terrains are highly configurable; you can adjust the scale, raise the sea level, and make it rough or smooth...")
app.add_action(lambda page: update_slider(page, "Sea Level", "0.2"))
app.add_action(lambda page: update_slider(page, "Roughness", "0.8"))
app.add_action(lambda page: page.locator("button:has-text('REGENERATE WORLD')").click())
app.add_wait(1.5)
# Zoom out to see the larger terrain structure
app.add_action(lambda page: page.get_by_role("button", name="-", exact=True).click())

# 4. Biomes and Climate
app.add_action(lambda page: click_accordion(page, "BIOMES & CLIMATE"))
app.add_voice("Biomes and climate can be drastically changed ... ranging from scorching deserts, to lush tropical forests....")
# Increase moisture to create forests
app.add_action(lambda page: update_slider(page, "Moisture Offset", "0.4"))
# Decrease temp
app.add_action(lambda page: update_slider(page, "Temp. Offset", "-0.2"))
app.add_wait(0.5)
app.add_action(lambda page: page.locator("button:has-text('REGENERATE WORLD')").click())
app.add_wait(1.5)
app.add_action(lambda page: page.get_by_role("button", name="-", exact=True).click())
app.add_wait(0.5)

# 5. Civilizations
app.add_action(lambda page: click_accordion(page, "CIVILIZATION"))
app.add_voice("Civilizations and structures can be sparse and tiny ... or heavily dense, and spread all over the map...")
app.add_action(lambda page: update_slider(page, "Structure Chance", "0.9"))
app.add_action(lambda page: update_slider(page, "Avg Size", "100"))
app.add_action(lambda page: page.locator("button:has-text('REGENERATE WORLD')").click())
app.add_wait(1.5)

app.add_voice("And explore the infinite procedural universe yourself ... Enjoy creating your worlds with Aether Maps...")
app.add_wait(0.5)
app.add_voice("Thank you for watching, please let me know if you have any questions..  and happy mapping")

if __name__ == "__main__":
    app.execute()

