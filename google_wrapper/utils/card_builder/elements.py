from abc import ABC, abstractmethod

from .widgets import Widget


class BaseElement(ABC):
    @abstractmethod
    def to_dict(self):
        pass


class CardHeader(BaseElement):
    def __init__(self):
        self.__title = None
        self.__subtitle = None
        self.__image_type = 'CIRCLE'
        self.__image_url = "https://i.ibb.co/gVg41Y4/Logo-Noti2.png"
        self.__image_alt = "STOs Notify"

    @property
    def title(self):
        return self.__title

    @title.setter
    def title(self, title):
        self.__title = title

    @property
    def subtitle(self):
        return self.__subtitle

    @subtitle.setter
    def subtitle(self, subtitle):
        self.__subtitle = subtitle

    @property
    def image_type(self):
        return self.__image_type

    @image_type.setter
    def image_type(self, image_type):
        self.__image_type = image_type

    def to_dict(self):
        card_header = {
            "title": self.__title,
            "subtitle": self.__subtitle,
            "imageType": self.__image_type,
            "imageUrl": self.__image_url,
            "imageAltText": self.__image_alt
        }
        return card_header


class Section(BaseElement):
    def __init__(self):
        self.__header = None
        self.__collapsible = False
        self.__collapsible_widgets_count = 1
        self.__widgets = []

    @property
    def header(self):
        return self.__header

    @header.setter
    def header(self, header: str):
        self.__header = header

    @property
    def collapsible(self):
        return self.__collapsible

    @collapsible.setter
    def collapsible(self, collapsible):
        self.__collapsible = collapsible

    @property
    def collapsible_widgets_count(self):
        return self.__collapsible_widgets_count

    @collapsible_widgets_count.setter
    def collapsible_widgets_count(self, collapsible_widgets_count):
        self.__collapsible_widgets_count = collapsible_widgets_count

    def add_widget(self, widget: Widget):
        self.__widgets.append(widget)

    def to_dict(self):
        section = {
            "header": self.__header,
            "collapsible": self.__collapsible,
            "uncollapsibleWidgetsCount": self.__collapsible_widgets_count,
            "widgets": [widget.to_dict() for widget in self.__widgets]
        }
        return section
