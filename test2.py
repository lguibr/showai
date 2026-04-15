import sys
import os

try:
    print("Testing CosyVoice initialization...")
    from showai.tts.cosy_engine import CosyVoiceEngine
    # The models are already downloaded, we just want to init it
    engine = CosyVoiceEngine(ref_audio="lgvoice.wav")
    engine.generate_audio("test", "test.wav")
    print("SUCCESS: Instantiated AutoModel successfully.")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
