from .base import TTSEngine

class F5TTSEngine(TTSEngine):
    """High Quality TTS Engine using F5-TTS model for Zero-Shot Voice Cloning."""
    
    def __init__(self, ref_audio: str, ref_text: str = ""):
        """
        Args:
            ref_audio (str): Path to the reference audio used for voice cloning.
            ref_text (str): Optional reference text. If empty, it'll attempt to transcribe.
        """
        self.ref_audio = ref_audio
        self.ref_text = ref_text
        self.f5tts = None

    def generate_audio(self, text: str, output_path: str) -> float:
        if self.f5tts is None:
            from f5_tts.api import F5TTS
            # Initialize engine (weights will load on first inference)
            self.f5tts = F5TTS()

        # F5TTS generates and saves the file directly if file_wave is set
        raw_wav, sr, _ = self.f5tts.infer(
            ref_file=self.ref_audio,
            ref_text=self.ref_text,
            gen_text=text,
            file_wave=output_path
        )
        
        # Calculate generation length in seconds
        return len(raw_wav) / float(sr)
