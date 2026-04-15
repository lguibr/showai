import sys, os, torch, torchaudio
COSY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CosyVoice")
sys.path.append(COSY_DIR); sys.path.append(os.path.join(COSY_DIR, "third_party", "Matcha-TTS"))
from cosyvoice.cli.cosyvoice import AutoModel

cosyvoice = AutoModel(model_dir="pretrained_models/Fun-CosyVoice3-0.5B")
cosyvoice.model.llm.float()
cosyvoice.model.flow.float()
cosyvoice.model.hift.float()

ref_audio = "assets/basic_ref_en.wav"
ref_text = "ignored"

text = "You are a helpful assistant.<|endofprompt|>This is a quick test of the English generation system. Let's see if it speaks in English or Chinese."
outputs = list(cosyvoice.inference_cross_lingual(text, ref_audio, stream=False))
torchaudio.save("audio_cache/quick_test.wav", outputs[0]['tts_speech'], cosyvoice.sample_rate)
print("Saved to audio_cache/quick_test.wav! Output was length:", outputs[0]['tts_speech'].shape)
