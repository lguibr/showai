import os
import sys
import httpx
import wave
from typing import Optional

from .base import TTSEngine
from showai.core.timeline import VoiceMode

class CosyVoiceEngine(TTSEngine):
    """
    Lightweight HTTP API Client for CosyVoice Docker Endpoint.
    Requires CosyVoice FastAPI server to be running on localhost:50000.
    """
    
    def __init__(self, default_prompt_audio: Optional[str] = None, default_prompt_text: Optional[str] = None, api_endpoint: str = "http://localhost:50000"):
        self.default_prompt_audio = default_prompt_audio
        self.default_prompt_text = default_prompt_text
        self.api_endpoint = api_endpoint.rstrip("/")
        self.sample_rate = 22050 # Standard CosyVoice sample rate
        
    def _initialize_model(self):
        # We perform a quick heartbeat check to ensure the Docker container is alive
        try:
            with httpx.Client(timeout=3.0) as client:
                client.get(self.api_endpoint)
        except httpx.RequestError as e:
            print(f"[CosyVoice API] WARNING: Cannot connect to {self.api_endpoint}. Is the Docker container running?")

    def generate_audio(self, text: str, output_path: str, **kwargs) -> float:
        self._initialize_model()
        
        mode = kwargs.get("mode", VoiceMode.CROSS_LINGUAL)
        speed = kwargs.get("speed", 1.0) # Note: API might not support speed natively, ignored for simplicity
        
        print(f"[CosyVoice API] Synthesizing ({mode.value}): {text[:50]}...")

        # Prepare HTTP multipart/form-data payload
        data = {"tts_text": text}
        files = None
        
        # We manually chunk like the original if needed, but CosyVoice FastAPI natively handles normalization 
        # inside its own pipeline so we just send the raw text!

        if mode == VoiceMode.ZERO_SHOT:
            prompt_audio = kwargs.get("prompt_audio") or self.default_prompt_audio
            prompt_text = kwargs.get("prompt_text") or self.default_prompt_text
            if not prompt_audio or not prompt_text:
                raise ValueError("ZERO_SHOT requires both prompt_audio and prompt_text.")
            
            # API expects prompt_text properly formatted 
            if "<|endofprompt|>" not in prompt_text:
                prompt_text = f"You are a helpful assistant.<|endofprompt|>{prompt_text}"
            
            data["prompt_text"] = prompt_text
            files = {"prompt_wav": open(prompt_audio, "rb")}
            endpoint_url = f"{self.api_endpoint}/inference_zero_shot"

        elif mode == VoiceMode.CROSS_LINGUAL:
            prompt_audio = kwargs.get("prompt_audio") or self.default_prompt_audio
            if not prompt_audio:
                raise ValueError("CROSS_LINGUAL requires prompt_audio.")
                
            instruct_text = kwargs.get("prompt_text", "You are a helpful assistant.<|endofprompt|>")
            if "<|endofprompt|>" not in instruct_text:
                instruct_text = f"You are a helpful assistant.<|endofprompt|>{instruct_text}"
            
            data["tts_text"] = f"{instruct_text}{text}"
            files = {"prompt_wav": open(prompt_audio, "rb")}
            endpoint_url = f"{self.api_endpoint}/inference_cross_lingual"

        elif mode == VoiceMode.SFT:
            data["spk_id"] = kwargs.get("spk_id", "中文女")
            endpoint_url = f"{self.api_endpoint}/inference_sft"

        elif mode == VoiceMode.INSTRUCT:
            data["spk_id"] = kwargs.get("spk_id", "中文女")
            instruct_text = kwargs.get("instruct_text")
            if not instruct_text:
                raise ValueError("INSTRUCT mode requires instruct_text.")
            data["instruct_text"] = instruct_text
            endpoint_url = f"{self.api_endpoint}/inference_instruct"
        else:
            raise ValueError(f"Unknown mode: {mode}")

        # Send request
        try:
            with httpx.Client(timeout=120.0) as client: # Long timeout for TTS generation
                response = client.post(endpoint_url, data=data, files=files)
                response.raise_for_status()
                pcm_bytes = response.content
        finally:
            if files:
                files["prompt_wav"].close()

        if not pcm_bytes:
            raise RuntimeError("Received empty audio response from CosyVoice API.")

        # API returns raw 16-bit PCM bytes. Transform them into a valid physical .wav file.
        with wave.open(output_path, 'wb') as f:
            f.setnchannels(1)       # Mono
            f.setsampwidth(2)       # 16-bit (2 bytes)
            f.setframerate(self.sample_rate)
            f.writeframes(pcm_bytes)
            
        # Calculate precise duration
        num_frames = len(pcm_bytes) / 2 # 2 bytes per frame
        duration_sec = num_frames / self.sample_rate
        return duration_sec
