import os
from showai import CosyVoiceEngine
from showai.tts.cosy_engine import VoiceMode

def main():
    print("--- ShowAI Extended Multilingual & Emotional Showcase Generator ---")
    
    output_dir = os.path.join("data", "output", "samples")
    os.makedirs(output_dir, exist_ok=True)
    
    # Define exact textual mapping mapping directly to emotions in English and Spanish. 
    # Proper grammar and sentence flow has been enforced.
    scenarios = {
        "Default": {
            "prompt": "You are a helpful assistant.<|endofprompt|>",
            "English": "Hello world, I am a synthetic voice.",
            "Spanish": "Hola mundo, soy una voz sintética."
        },
        "Sad": {
            "prompt": "You are a helpful assistant. Please speak very sadly.<|endofprompt|>",
            "English": "Why didn't you leave a star on this GitHub project?",
            "Spanish": "¿Por qué no dejaste una estrella en este proyecto de GitHub?"
        },
        "Enthusiastic": {
            "prompt": "You are a helpful assistant. Please speak very enthusiastically.<|endofprompt|>",
            "English": "Welcome to ShowAI, a new way to showcase your projects!",
            "Spanish": "¡Bienvenido a ShowAI, una nueva forma de mostrar tus proyectos!"
        }
    }
    
    voices = {
        "Custom": {
            "wav": "data/assets/my_voice.wav",
            "ref_text": "Community is my pleasure to share the Aether maps a deterministic 2D layered infinite grid of customizable and explorable world."
        },
        "Reference_EN": {
            "wav": "data/assets/basic_ref_en.wav",
            "ref_text": "some call me nature, others call me mother nature"
        }
    }

    engine = CosyVoiceEngine(
        default_prompt_audio="data/assets/my_voice.wav",
        default_prompt_text="Placeholder"
    )

    for voice_name, voice_data in voices.items():
        print(f"\n--- Processing Voice: {voice_name} ---")
        
        for emotion, config in scenarios.items():
            for lang in ["English", "Spanish"]:
                text = config[lang]
                prompt_prefix = config["prompt"]
                
                print(f"Synthesizing [{emotion}] [{lang}]...")
                
                output_name = f"showcase_{voice_name}_{lang}_{emotion}.wav".lower()
                output_path = os.path.join(output_dir, output_name)
                
                # Determine mode based on whether a valid transcript is provided or needed
                # For custom voice, using Cross Lingual provides far more stability when 
                # exact transcription mapping fails, avoiding fallback to base Chinese.
                if voice_name == "Custom":
                    v_mode = VoiceMode.CROSS_LINGUAL
                    dynamic_prompt_text = prompt_prefix  # Instruct only
                else:
                    v_mode = VoiceMode.ZERO_SHOT
                    dynamic_prompt_text = f"{prompt_prefix}{voice_data['ref_text']}"
                
                try:
                    dur = engine.generate_audio(
                        text=text,
                        output_path=output_path,
                        mode=v_mode,
                        prompt_audio=voice_data["wav"],
                        prompt_text=dynamic_prompt_text
                    )
                    print(f"  -> Saved: {output_path} ({dur:.2f}s)")
                except Exception as e:
                    print(f"  -> ERROR processing {output_name}: {e}")

    print("\n[✔] Extended Multilingual & Emotional Showcase completed successfully!")

if __name__ == "__main__":
    main()
