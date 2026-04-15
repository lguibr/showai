from mutagen import File

def get_audio_duration(audio_path: str) -> float:
    """Safely calculates the duration of an audio file using Mutagen abstraction."""
    try:
        audio = File(audio_path)
        return audio.info.length if audio else 0.0
    except Exception:
        return 0.0
