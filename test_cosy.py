import sys
import os

COSY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CosyVoice")
sys.path.append(COSY_DIR)
sys.path.append(os.path.join(COSY_DIR, "third_party", "Matcha-TTS"))

from cosyvoice.cli.cosyvoice import AutoModel
import torchaudio

print("Loading model")
model_dir = "pretrained_models/Fun-CosyVoice3-0.5B"
cosyvoice = AutoModel(model_dir=model_dir)
cosyvoice.model.llm.float()
cosyvoice.model.flow.float()
cosyvoice.model.hift.float()

ref_audio = "CosyVoice/asset/zero_shot_prompt.wav"
ref_text = "<|endofprompt|>希望你以后能够做的比我还好呦。"

text = "Biomes and climate can be drastically changed ... ranging from scorching deserts, to lush tropical forests...."

print(f"Synthesizing: {text}")

for n, chunk in enumerate(cosyvoice.frontend.text_normalize(text, split=True)):
    print(f"Synthesizing Chunk {n}: '{chunk}'")
    chunk_with_lang = f"<|en|>{chunk}"
    outputs = list(cosyvoice.inference_zero_shot(chunk_with_lang, ref_text, ref_audio, stream=False))
    print(f"Chunk {n} generated {len(outputs)} frames!")

