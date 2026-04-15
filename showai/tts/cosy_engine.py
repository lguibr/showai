import os
import sys
import torch
import torchaudio

# Dynamically inject CosyVoice path so we can import from it
COSY_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "CosyVoice")
sys.path.append(COSY_DIR)
sys.path.append(os.path.join(COSY_DIR, "third_party", "Matcha-TTS"))

from .base import TTSEngine

class CosyVoiceEngine(TTSEngine):
    """High Quality TTS Engine using FunAudioLLM's CosyVoice 3 for Zero-Shot Voice Cloning."""
    
    def __init__(self, ref_audio: str, ref_text: str = ""):
        """
        Args:
            ref_audio (str): Path to the reference audio used for voice cloning.
            ref_text (str): Reference text corresponding to the audio.
        """
        self.ref_audio = ref_audio
        self.ref_text = ref_text
        self.cosyvoice = None

    def generate_audio(self, text: str, output_path: str, **kwargs) -> float:
        if self.cosyvoice is None:
            # Note: We must run inside a properly configured environment for modelscope and torchaudio
            from huggingface_hub import snapshot_download
            from cosyvoice.cli.cosyvoice import AutoModel
            
            # Download locally to pretrained_models
            model_dir = snapshot_download(
                'FunAudioLLM/Fun-CosyVoice3-0.5B-2512', 
                local_dir=os.path.join(os.path.dirname(COSY_DIR), 'pretrained_models', 'Fun-CosyVoice3-0.5B')
            )
            self.cosyvoice = AutoModel(model_dir=model_dir)

            # Convert all models explicitly to float32 to prevent "got Float and BFloat16" mixed dtype crashes
            # since the Qwen2 weights are stored in bfloat16 but inputs are standard float32.
            self.cosyvoice.model.llm.float()
            self.cosyvoice.model.flow.float()
            self.cosyvoice.model.hift.float()

        print(f"[CosyVoice] Synthesizing: {text}")

        # Use cross_lingual inference by default. This bypasses the strict forced-alignment requires of zero-shot 
        # (which often causes severe Chinese hallucination or robot noise if the transcription is slightly off).
        # We inject the standard instruct tag <|endofprompt|> to compel the model to speak exactly what follows.
        instruct_prefix = "You are a helpful assistant.<|endofprompt|>"
            
        audio_tensors = []
        
        # We manually chunk so each sentence independently gets the instruct context,
        # ensuring the LLM doesn't lose context over long paragraphs.
        # We skip text_frontend=True here because we're manually injecting the <|endofprompt|> tag afterwards.
        # Alternatively, we just use text_frontend=True to split into plain sentences first.
        chunks = self.cosyvoice.frontend.text_normalize(text, split=True, text_frontend=True)
        if isinstance(chunks, str):
            chunks = [chunks]
            
        for chunk in chunks:
            chunk_instruct = f"{instruct_prefix}{chunk}"
            # inference_cross_lingual clones the acoustic properties of ref_audio WITHOUT needing its transcript.
            outputs = list(self.cosyvoice.inference_cross_lingual(chunk_instruct, self.ref_audio, stream=False))
            audio_tensors.extend([out['tts_speech'] for out in outputs])
        
        if len(audio_tensors) > 1:
            final_audio = torch.cat(audio_tensors, dim=1)
        else:
            final_audio = audio_tensors[0]

        torchaudio.save(output_path, final_audio, self.cosyvoice.sample_rate)
        
        return final_audio.shape[1] / float(self.cosyvoice.sample_rate)
