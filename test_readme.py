import sys, os
COSY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CosyVoice")
sys.path.append(COSY_DIR); sys.path.append(os.path.join(COSY_DIR, "third_party", "Matcha-TTS"))
from cosyvoice.cli.cosyvoice import AutoModel

print("Loading model")
cosyvoice = AutoModel(model_dir="pretrained_models/Fun-CosyVoice3-0.5B")
# NOT casting to float() this time. We will just let it be bf16!
print("Model loaded. Testing README EN Zero Shot")

tts_text = 'CosyVoice is undergoing a comprehensive upgrade, providing more accurate, stable, faster, and better voice generation capabilities.'
prompt_text = 'You are a helpful assistant.<|endofprompt|>希望你以后能够做的比我还好呦。'
prompt_wav = 'CosyVoice/asset/zero_shot_prompt.wav'

outputs = list(cosyvoice.inference_zero_shot(tts_text, prompt_text, prompt_wav, stream=False))
print(f"Generated {len(outputs)} chunks. First chunk speech length: {outputs[0]['tts_speech'].shape}")
