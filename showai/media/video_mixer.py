import os
import subprocess
from typing import List, Tuple

def stitch_video(raw_video_path: str, output_video: str, audio_tracks: List[Tuple[str, float]], srt_path: str = ""):
    """
    Overlays a series of audio tracks onto a base video using FFmpeg.
    audio_tracks: List of (audio_filepath, start_offset_seconds)
    srt_path: Path to SRT subtitles file to hard-sub onto video.
    """
    print("[ShowAI] Stitching video and audio tracks with FFmpeg...")

    if not audio_tracks:
        if os.path.exists(raw_video_path):
            os.rename(raw_video_path, output_video)
        return

    cmd = ["ffmpeg", "-y", "-i", raw_video_path]
    for audio, _ in audio_tracks:
        cmd.extend(["-i", audio])

    filter_parts = []
    mix_inputs = []
    for i, (audio, offset_sec) in enumerate(audio_tracks):
        input_idx = i + 1
        ms_delay = int(offset_sec * 1000)
        filter_parts.append(f"[{input_idx}:a]adelay={ms_delay}|{ms_delay}[a{input_idx}]")
        mix_inputs.append(f"[a{input_idx}]")

    if len(mix_inputs) > 1:
        amix_str = "".join(mix_inputs) + f"amix=inputs={len(mix_inputs)}[aout]"
        filter_parts.append(amix_str)
        map_audio = "[aout]"
    elif len(mix_inputs) == 1:
        map_audio = mix_inputs[0]
    else:
        map_audio = "0:a"

    filter_complex = "; ".join(filter_parts)

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", map_audio
    ])
    
    if srt_path and os.path.exists(srt_path):
        cmd.extend(["-vf", f"subtitles={srt_path}:force_style='Fontname=Roboto,Fontsize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,BackColour=&H80000000,Alignment=2,MarginV=25'"])
        
    cmd.extend([
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "192k",
        output_video
    ])

    print("Running FFmpeg command:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print(f"[ShowAI] Successfully produced {output_video}!")
