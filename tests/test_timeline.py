from showai.core.orchestrator import ShowAI
from showai.core.timeline import Timeline, VoiceEvent, WaitEvent
import os

def test_timeline_additions():
    timeline = Timeline()
    assert len(timeline.events) == 0
    
    timeline.add_voice("Test")
    timeline.add_wait(1.5)
    
    assert len(timeline.events) == 2
    assert isinstance(timeline.events[0], VoiceEvent)
    assert isinstance(timeline.events[1], WaitEvent)
    assert timeline.events[1].seconds == 1.5

def test_orchestrator_cache_generation(mock_tts, tmp_path):
    os.chdir(tmp_path)
    app = ShowAI(tts=mock_tts, output_video="test.mp4")
    
    app.add_voice("Test 1")
    app.add_voice("Test 2")
    
    assert len(app.timeline.events) == 2
    assert app.timeline.events[0].text == "Test 1"
