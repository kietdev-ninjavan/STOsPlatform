from .card import CardV2, Card
from .elements import CardHeader, Section


class CardBuilder:
    def __init__(self):
        self.__card = Card()
        self.card = CardV2(self.__card)

    def set_header(self, header: CardHeader):
        self.__card.header = header

    def add_section(self, section: Section):
        self.__card.add_section(section)
