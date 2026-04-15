import os
from typing import Callable, Any
from showai.core.timeline import Timeline
from showai.tts.base import TTSEngine
from showai.automation.browser import BrowserAutomation
from showai.media.video_mixer import stitch_video

class ShowAI:
    """The central Orchestrator that binds the architecture."""

    def __init__(self, tts: TTSEngine, output_video: str = "output.mp4", headless: bool = False, play_audio: bool = False):
        self.tts = tts
        self.output_video = output_video
        self.headless = headless
        self.play_audio = play_audio
        self.timeline = Timeline()
        self.audio_tracks = [] # list of (audio_filepath, start_offset_seconds)

    def add_action(self, func: Callable[[Any], None]):
        self.timeline.add_action(func)
        return self

    def add_voice(self, text: str, wait=True, **kwargs):
        self.timeline.add_voice(text, wait, **kwargs)
        return self

    def add_wait(self, seconds: float):
        self.timeline.add_wait(seconds)
        return self

    def _generate_srt(self):
        """Builds a .srt string based on mapped voice events and bounds."""
        def format_srt_time(seconds):
            h = int(seconds / 3600)
            m = int((seconds % 3600) / 60)
            s = int(seconds % 60)
            ms = int((seconds - int(seconds)) * 1000)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            
        srt_content = ""
        counter = 1
        for (audio_path, start_offset), text, duration in zip(self.audio_tracks, self._voice_texts, self._voice_durations):
            end_offset = start_offset + duration
            start_str = format_srt_time(start_offset)
            end_str = format_srt_time(end_offset)
            srt_content += f"{counter}\n{start_str} --> {end_str}\n{text}\n\n"
            counter += 1
            
        with open("captions.srt", "w", encoding="utf-8") as f:
            f.write(srt_content)
        return "captions.srt"

    def execute(self):
        """Bakes audio, runs the browser timeline, and stitches output."""
        from showai.progress import broker
        broker.log("Pre-generating audio cache...")
        os.makedirs("audio_cache", exist_ok=True)
        
        voice_events = [item for item in self.timeline.events if item["type"] == "voice"]
        total_voice = len(voice_events)
        processed = 0
        
        self._voice_texts = []
        self._voice_durations = []
        
        for idx, item in enumerate(self.timeline.events):
            if item["type"] == "voice":
                broker.log(f"Compiling Engine Audio {processed+1}/{total_voice}")
                broker.audio_tasks.append(f"Generating voice node {processed+1}")
                broker.audio_progress = ((processed) / total_voice) * 100
                
                filename = f"audio_cache/step_{idx}.wav"
                kwargs = item.copy()
                kwargs.pop("type", None)
                kwargs.pop("text", None)
                kwargs.pop("wait", None)
                kwargs.pop("audio_file", None)
                kwargs.pop("duration", None)
                
                duration = self.tts.generate_audio(item["text"], filename, **kwargs)
                item["audio_file"] = filename
                item["duration"] = duration
                
                self._voice_texts.append(item["text"])
                self._voice_durations.append(duration)
                
                processed += 1
                broker.audio_progress = ((processed) / total_voice) * 100
                
        broker.log("Injecting Timeline to BrowserAutomation...")
        browser = BrowserAutomation()
        raw_video = browser.execute_timeline(self.timeline.events, self.audio_tracks, headless=self.headless, play_audio=self.play_audio)
        
        srt_path = ""
        if hasattr(self, "_voice_texts"):
            broker.log("Baking SRT Captions...")
            srt_path = self._generate_srt()
        
        broker.log("Stitching Video Output...")
        stitch_video(raw_video, self.output_video, self.audio_tracks, srt_path=srt_path)
        broker.log("ShowAI Video Compilation Completed!")
