import abc

class TTSEngine(abc.ABC):
    """Abstract interface for synthetic voice engines."""
    
    @abc.abstractmethod
    def generate_audio(self, text: str, output_path: str, **kwargs) -> float:
        """
        Generates audio for the specified text and saves it to output_path.
        Must return the true length of the generated audio in seconds.
        """
        pass
