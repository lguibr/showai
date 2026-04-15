from dataclasses import dataclass
from typing import Callable, Any, List, Optional, Union
from enum import Enum

class VoiceMode(str, Enum):
    ZERO_SHOT = "zero_shot"
    CROSS_LINGUAL = "cross_lingual"
    SFT = "sft"
    INSTRUCT = "instruct"

@dataclass
class ActionEvent:
    func: Callable[[Any], None]
    type: str = "action"

@dataclass
class WaitEvent:
    seconds: float
    type: str = "wait"

@dataclass
class VoiceEvent:
    text: str
    wait: bool = True
    mode: VoiceMode = VoiceMode.CROSS_LINGUAL
    
    # For ZERO_SHOT and CROSS_LINGUAL
    prompt_audio: Optional[str] = None
    prompt_text: Optional[str] = None  # Required ONLY for ZERO_SHOT
    
    # For SFT and INSTRUCT
    spk_id: Optional[str] = None
    instruct_text: Optional[str] = None # Required ONLY for INSTRUCT
    
    # Global generation params
    speed: float = 1.0
    
    # Internal state
    audio_file: Optional[str] = None
    duration: Optional[float] = None
    type: str = "voice"

TimelineEvent = Union[ActionEvent, WaitEvent, VoiceEvent]

class Timeline:
    """Manages the deterministic timeline sequence of ShowAI automation."""

    def __init__(self):
        self.events: List[TimelineEvent] =[]

    def add_action(self, func: Callable[[Any], None]):
        self.events.append(ActionEvent(func=func))

    def add_voice(self, text: str, **kwargs):
        self.events.append(VoiceEvent(text=text, **kwargs))

    def add_wait(self, seconds: float):
        self.events.append(WaitEvent(seconds=seconds))

    def clear(self):
        self.events =[]
