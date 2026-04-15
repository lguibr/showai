from typing import Callable, Any, Dict, List

class Timeline:
    """Manages the deterministic timeline sequence of ShowAI automation."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def add_action(self, func: Callable[[Any], None]):
        """Append a Playwright page interaction."""
        self.events.append({
            "type": "action",
            "func": func
        })

    def add_voice(self, text: str, wait=True):
        """Append an AI voice narration generation chunk."""
        self.events.append({
            "type": "voice",
            "text": text,
            "wait": wait
        })

    def add_wait(self, seconds: float):
        """Explicitly hold the browser state without actions."""
        self.events.append({
            "type": "wait",
            "seconds": seconds
        })

    def clear(self):
        """Wipes the timeline."""
        self.events = []
