from abc import ABC, abstractmethod
from pathlib import Path


class OCRBackend(ABC):
    @abstractmethod
    def extract_text(self, image_path: Path, language: str = "eng") -> str:
        ...

    @abstractmethod
    def extract_data(self, image_path: Path, language: str = "eng") -> list[dict]:
        """Return word-level data with bounding boxes.

        Each dict should contain:
            - text: the recognized word
            - x: left position in pixels
            - y: top position in pixels
            - width: word width in pixels
            - height: word height in pixels
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        ...

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        ...
