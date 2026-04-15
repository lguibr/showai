import subprocess
import os
import contextlib
import wave
import time
import requests
import atexit
from rich.console import Console

from .base import TTSEngine

console = Console()

class FishEngine(TTSEngine):
    """SOTA Engine using Fish Speech API Server for <14GB VRAM Zero-Shot Voice Cloning."""
    
    def __init__(self, ref_audio: str, ref_text: str, checkpoint="checkpoints/fish-speech-1.5"):
        self.ref_audio = ref_audio
        self.ref_text = ref_text
        self.checkpoint = checkpoint
        self.api_url = "http://127.0.0.1:8080/v1/tts"
        self.health_url = "http://127.0.0.1:8080/v1/health"
        self._server_process = None
        
        self._ensure_server_running()

    def _ensure_server_running(self):
        try:
            res = requests.get(self.health_url)
            if res.status_code == 200:
                console.print("[green]Fish Speech API Server detected running on :8080[/green]")
                return
        except requests.exceptions.ConnectionError:
            pass

        console.print("[yellow]Starting Fish Speech API Server (--half) to maintain <14GB VRAM...[/yellow]")
        abs_cwd = os.path.abspath("fish-speech")
        
        # We start the backend asynchronously and register an atexit to clean it up
        cmd = [
            "uv", "run", "python", "tools/api_server.py",
            "--llama-checkpoint-path", os.path.abspath(f"fish-speech/{self.checkpoint}"),
            "--decoder-checkpoint-path", os.path.abspath(f"fish-speech/{self.checkpoint}/firefly-gan-vq-fsq-8x1024-21hz-generator.pth"),
            "--decoder-config-name", "firefly_gan_vq",
            "--listen", "127.0.0.1:8080",
            "--half" # Critical for RTX 3080Ti VRAM
        ]
        
        self._server_process = subprocess.Popen(
            cmd,
            cwd=abs_cwd,
            stdout=subprocess.DEVNULL,
            stderr=None
        )
        
        atexit.register(self.shutdown_server)
        
        console.print("[yellow]Waiting up to 300s for Fish Speech Web Server to allocate...[/yellow]")
        console.print("[dim](On first run, this may trigger a multi-gigabyte dependency sync inside the background uv orchestrator)[/dim]")
        
        # Wait up to 300 seconds (5 mins) for dependencies to install and weights to map
        for i in range(300):
            time.sleep(1)
            try:
                if requests.get(self.health_url).status_code == 200:
                    console.print("[green]Fish Speech Web Server mapped locally![/green]")
                    return
            except requests.exceptions.ConnectionError:
                pass
                
        raise RuntimeError("Failed to allocate FishSpeech API Server in VRAM (Timed out after 5 minutes).")

    def shutdown_server(self):
        if self._server_process:
            self._server_process.terminate()

    def generate_audio(self, text: str, output_path: str) -> float:
        console.print(f"[cyan]Fish API Synthesizing:[/cyan] '{text[:40]}...'")
        
        abs_cwd = os.path.abspath("fish-speech")
        abs_ref_audio = os.path.abspath(self.ref_audio)
        
        # 'api_client.py' automatically injects the payload to output.wav
        # So we cleanly strip ".wav" if given
        base_out = os.path.abspath(output_path).replace(".wav", "")
        
        cmd = [
            "uv", "run", "python", "tools/api_client.py",
            "--url", self.api_url,
            "--text", text,
            "--reference_audio", abs_ref_audio,
            "--reference_text", self.ref_text,
            "--output", base_out,
            "--no-play",
            "--format", "wav"
        ]
        
        try:
            subprocess.run(
                cmd, 
                cwd=abs_cwd, 
                check=True, 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL
            )
            
            final_artifact = f"{base_out}.wav"
            if os.path.exists(final_artifact):
                with contextlib.closing(wave.open(final_artifact, 'r')) as f:
                    frames = f.getnframes()
                    rate = f.getframerate()
                    duration = frames / float(rate)
                    return duration
            return 2.0
                
        except Exception as e:
            console.print(f"[red]Fish API Transfer Failed: {str(e)}[/red]")
            return 2.0
