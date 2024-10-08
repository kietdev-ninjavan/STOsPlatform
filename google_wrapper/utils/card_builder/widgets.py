from abc import ABC, abstractmethod


class Widget(ABC):
    @abstractmethod
    def to_dict(self):
        pass


class TextParagraph(Widget):
    def __init__(self, text: str, max_lines: int = None):
        self.__horizontal_alignment = 'START'
        self.text = text
        self.max_lines = max_lines

    def to_dict(self):
        return {
            'horizontalAlignment': self.__horizontal_alignment,
            'textParagraph': {
                'text': self.text,
                'maxLines': self.max_lines
            }
        }
