import os
from typing import Callable, Any, Optional
from showai.core.timeline import Timeline, ActionEvent, WaitEvent, VoiceEvent, VoiceMode
from showai.tts.base import TTSEngine
from showai.automation.browser import BrowserAutomation
from showai.media.video_mixer import stitch_video

class ShowAI:
    """The central Orchestrator that binds the architecture."""

    def __init__(self, tts: TTSEngine, output_video: str = "output.mp4", headless: bool = False, play_audio: bool = False, workspace_dir: str = "data"):
        self.tts = tts
        self.output_video = output_video
        self.headless = headless
        self.play_audio = play_audio
        self.workspace_dir = workspace_dir
        self.timeline = Timeline()
        self.audio_tracks =[] # list of (audio_filepath, start_offset_seconds)

    def add_action(self, func: Callable[[Any], None]):
        self.timeline.add_action(func)
        return self

    def add_voice(self, text: str, **kwargs):
        self.timeline.add_voice(text, **kwargs)
        return self

    def add_wait(self, seconds: float):
        self.timeline.add_wait(seconds)
        return self

    def _generate_srt(self):
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
            
        
        srt_output = os.path.join(self.workspace_dir, "output", "captions", "captions.srt")
        with open(srt_output, "w", encoding="utf-8") as f:
            f.write(srt_content)
        return srt_output

    def execute(self):
        from showai.progress import broker
        broker.log("Pre-generating audio cache with CosyVoice 3.0...")
        
        # Ensure deep directory structure exists
        os.makedirs(os.path.join(self.workspace_dir, "cache", "audio"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_dir, "cache", "video"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_dir, "output", "videos"), exist_ok=True)
        os.makedirs(os.path.join(self.workspace_dir, "output", "captions"), exist_ok=True)
        
        voice_events =[e for e in self.timeline.events if isinstance(e, VoiceEvent)]
        total_voice = len(voice_events)
        processed = 0
        
        self._voice_texts = []
        self._voice_durations =[]
        
        for idx, item in enumerate(self.timeline.events):
            if isinstance(item, VoiceEvent):
                broker.log(f"Compiling Engine Audio {processed+1}/{total_voice}")
                broker.audio_tasks.append(f"Generating voice node {processed+1}")
                broker.audio_progress = ((processed) / total_voice) * 100
                
                filename = os.path.join(self.workspace_dir, "cache", "audio", f"step_{idx}.wav")
                
                # Pass all strict parameters to the engine
                duration = self.tts.generate_audio(
                    text=item.text, 
                    output_path=filename, 
                    mode=item.mode,
                    prompt_audio=item.prompt_audio,
                    prompt_text=item.prompt_text,
                    spk_id=item.spk_id,
                    instruct_text=item.instruct_text,
                    speed=item.speed
                )
                item.audio_file = filename
                item.duration = duration
                
                self._voice_texts.append(item.text)
                self._voice_durations.append(duration)
                
                processed += 1
                broker.audio_progress = ((processed) / total_voice) * 100
                
        broker.log("Injecting Timeline to BrowserAutomation...")
        browser = BrowserAutomation(output_video_dir=os.path.join(self.workspace_dir, "cache", "video"))
        raw_video = browser.execute_timeline(self.timeline.events, self.audio_tracks, headless=self.headless, play_audio=self.play_audio)
        
        srt_path = ""
        if hasattr(self, "_voice_texts") and self._voice_texts:
            broker.log("Baking SRT Captions...")
            srt_path = self._generate_srt()
        
        broker.log("Stitching Video Output...")
        stitch_video(raw_video, self.output_video, self.audio_tracks, srt_path=srt_path)
        broker.log("ShowAI Video Compilation Completed!")
