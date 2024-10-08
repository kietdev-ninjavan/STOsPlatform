import uuid

from .elements import CardHeader, Section


class Card:
    def __init__(self):
        self.__header = None
        self.__sections = []

    @property
    def header(self):
        return self.__header

    @header.setter
    def header(self, header: CardHeader):
        self.__header = header

    def add_section(self, section: Section):
        self.__sections.append(section)

    def to_dict(self):
        card = {
            "header": self.__header.to_dict() if self.__header else None,
            "sections": [section.to_dict() for section in self.__sections]
        }
        return card


class CardV2:
    def __init__(self, card: Card):
        self.card_id = uuid.uuid4()
        self.card = card

    def to_dict(self):
        card_v2 = {
            "cardId": str(self.card_id),
            "card": self.card.to_dict()
        }
        return card_v2
