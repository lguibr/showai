import os
import sys
import torch
import torchaudio
from typing import Optional

from .base import TTSEngine
from showai.core.timeline import VoiceMode

class CosyVoiceEngine(TTSEngine):
    """
    Strict, production-ready integration of FunAudioLLM/CosyVoice 3.0.
    Fully embraces the official API signatures and Matcha-TTS dependencies.
    """
    
    def __init__(self, default_prompt_audio: Optional[str] = None, default_prompt_text: Optional[str] = None, model_dir: str = "pretrained_models/Fun-CosyVoice3-1.5B"):
        self.default_prompt_audio = default_prompt_audio
        self.default_prompt_text = default_prompt_text
        self.model_dir = model_dir
        self.cosyvoice = None

    def _initialize_model(self):
        if self.cosyvoice is not None:
            return

        # 1. Strictly enforce the Matcha-TTS path injection required by CosyVoice
        COSY_DIR = os.path.abspath("CosyVoice")
        MATCHA_DIR = os.path.join(COSY_DIR, "third_party", "Matcha-TTS")
        
        if COSY_DIR not in sys.path:
            sys.path.append(COSY_DIR)
        if MATCHA_DIR not in sys.path:
            sys.path.append(MATCHA_DIR)

        from huggingface_hub import snapshot_download
        from cosyvoice.cli.cosyvoice import AutoModel
        
        # 2. Download Fun-CosyVoice3-1.5B if missing
        if not os.path.exists(self.model_dir):
            print(f"[CosyVoice 3.0] Downloading model to {self.model_dir}...")
            self.model_dir = snapshot_download(
                'FunAudioLLM/Fun-CosyVoice3-1.5B-2512', 
                local_dir=self.model_dir
            )
            
        print("[CosyVoice 3.0] Loading AutoModel into memory...")
        self.cosyvoice = AutoModel(model_dir=self.model_dir)

        # 3. Prevent mixed precision crashes (bfloat16 vs float32)
        self.cosyvoice.model.llm.float()
        self.cosyvoice.model.flow.float()
        self.cosyvoice.model.hift.float()

    def generate_audio(self, text: str, output_path: str, **kwargs) -> float:
        self._initialize_model()
        
        mode = kwargs.get("mode", VoiceMode.CROSS_LINGUAL)
        speed = kwargs.get("speed", 1.0)
        
        print(f"[CosyVoice 3.0] Synthesizing ({mode.value} | speed={speed}): {text[:50]}...")

        audio_tensors =[]
        
        # CosyVoice 3.0 text normalization
        chunks = self.cosyvoice.frontend.text_normalize(text, split=True, text_frontend=True)
        if isinstance(chunks, str):
            chunks = [chunks]
            
        for chunk in chunks:
            if mode == VoiceMode.ZERO_SHOT:
                prompt_audio = kwargs.get("prompt_audio") or self.default_prompt_audio
                prompt_text = kwargs.get("prompt_text") or self.default_prompt_text
                if not prompt_audio or not prompt_text:
                    raise ValueError("ZERO_SHOT requires both prompt_audio and prompt_text.")
                
                # In CosyVoice 3.0, the LLM treats the prompt_text sequence strictly as:
                # [Instruct Text] + <|endofprompt|> + [Reference Text]
                # We must append the instruction boundary correctly to avoid the Vocoder/LLM
                # context drifting and misinterpreting commas as boundaries.
                if "<|endofprompt|>" not in prompt_text:
                    prompt_text = f"You are a helpful assistant.<|endofprompt|>{prompt_text}"
                
                # API: inference_zero_shot(tts_text, prompt_text, prompt_speech_16k, ...)
                outputs = list(self.cosyvoice.inference_zero_shot(
                    chunk, prompt_text, prompt_audio, stream=False, speed=speed
                ))
                
            elif mode == VoiceMode.CROSS_LINGUAL:
                prompt_audio = kwargs.get("prompt_audio") or self.default_prompt_audio
                if not prompt_audio:
                    raise ValueError("CROSS_LINGUAL requires prompt_audio.")
                
                # Check if the user passed an instruction (prompt_text variable is functionally the instruction prefixed here)
                instruct_text = kwargs.get("prompt_text", "You are a helpful assistant.<|endofprompt|>")
                if "<|endofprompt|>" not in instruct_text:
                    instruct_text = f"You are a helpful assistant.<|endofprompt|>{instruct_text}"
                
                # We inject the instruct text before the TTS chunk for the LLM
                formatted_chunk = f"{instruct_text}{chunk}"
                
                # API: inference_cross_lingual(tts_text, prompt_speech_16k, stream=False, speed=1.0)
                outputs = list(self.cosyvoice.inference_cross_lingual(
                    formatted_chunk, prompt_audio, stream=False, speed=speed
                ))
                
            elif mode == VoiceMode.SFT:
                spk_id = kwargs.get("spk_id", "中文女")
                # API: inference_sft(tts_text, spk_id, stream=False, speed=1.0)
                outputs = list(self.cosyvoice.inference_sft(
                    chunk, spk_id, stream=False, speed=speed
                ))
                
            elif mode == VoiceMode.INSTRUCT:
                spk_id = kwargs.get("spk_id", "中文女")
                instruct_text = kwargs.get("instruct_text")
                if not instruct_text:
                    raise ValueError("INSTRUCT mode requires instruct_text.")
                
                # API: inference_instruct(tts_text, spk_id, instruct_text, stream=False, speed=1.0)
                outputs = list(self.cosyvoice.inference_instruct(
                    chunk, spk_id, instruct_text, stream=False, speed=speed
                ))
            else:
                raise ValueError(f"Unknown mode: {mode}")

            audio_tensors.extend([out['tts_speech'] for out in outputs])
        
        if len(audio_tensors) > 1:
            final_audio = torch.cat(audio_tensors, dim=1)
        else:
            final_audio = audio_tensors[0]

        torchaudio.save(output_path, final_audio, self.cosyvoice.sample_rate)
        
        return final_audio.shape[1] / float(self.cosyvoice.sample_rate)
