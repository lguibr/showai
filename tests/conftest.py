import pytest
from showai.tts.base import TTSEngine

class MockTTSEngine(TTSEngine):
    def generate_audio(self, text: str, output_path: str, **kwargs) -> float:
        with open(output_path, "wb") as f:
            f.write(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")
        return 1.0

@pytest.fixture
def mock_tts():
    return MockTTSEngine()
