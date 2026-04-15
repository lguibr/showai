import time
import subprocess
import base64
import os
from typing import List, Tuple
from playwright.sync_api import sync_playwright
from showai.core.timeline import TimelineEvent, ActionEvent, WaitEvent, VoiceEvent

class BrowserAutomation:
    """Encapsulates Playwright execution context strictly."""
    
    def __init__(self, output_video_dir: str = "raw_video"):
        self.output_video_dir = output_video_dir
        
    def execute_timeline(self, events: List[TimelineEvent], audio_tracks: List[Tuple[str, float]], headless: bool = False, play_audio: bool = False) -> str:
        """
        Runs the exact series of timeline events visually.
        Returns the raw video path.
        """
        from showai.progress import broker
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 720},
                record_video_dir=self.output_video_dir
            )
            page = context.new_page()
            
            # --- START STRAP SPLASH ---
            try:
                logo_path = "data/assets/logo.png" if os.path.exists("data/assets/logo.png") else "assets/logo.png"
                with open(logo_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                img_src = f"data:image/png;base64,{b64}"
            except Exception:
                img_src = ""

            html_splash = f"""
            <html style="background: black; margin: 0; padding: 0; display: flex; align-items: center; justify-content: center; height: 100vh; overflow: hidden;">
                <body>
                    <img src="{img_src}" style="max-height: 50vh; max-width: 50vw; object-fit: contain;">
                </body>
            </html>
            """
            page.set_content(html_splash)
            time.sleep(0.5) 
            # --- END STRAP SPLASH ---
            
            time.sleep(1) # Record buffer
            
            start_time = time.time()
            total_events = len(events)
            
            for idx, item in enumerate(events):
                broker.timeline_progress = (idx / total_events) * 100
                broker.timeline_tasks.append(f"Timeline Step {idx+1}/{total_events} [{item.type}]")
                elapsed_offset = time.time() - start_time
                
                if isinstance(item, ActionEvent):
                    item.func(page)
                
                elif isinstance(item, VoiceEvent):
                    audio_file = item.audio_file
                    duration = item.duration
                    audio_tracks.append((audio_file, elapsed_offset))
                    
                    if play_audio and audio_file:
                        subprocess.Popen(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", audio_file])
                        
                    if item.wait and duration:
                        time.sleep(duration)
                
                elif isinstance(item, WaitEvent):
                    time.sleep(item.seconds)
                    
            broker.timeline_progress = 100
            broker.timeline_tasks.append("Finalizing Render...")
                    
            time.sleep(1) # Final buffer
            
            page.close()
            context.close()
            raw_path = page.video.path()
            browser.close()
            
            return raw_path
