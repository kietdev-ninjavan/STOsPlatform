import json
import logging

import requests

from ..utils.card_builder import CardV2


class GoogleChatService:
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        self.__logger = logger

    def webhook_send(self, webhook_url: str, message: str = None, card: CardV2 = None):
        if not message and not card:
            raise ValueError("Message or card must be provided.")

        headers = {
            'Content-Type': 'application/json; charset=UTF-8'
        }

        data = {
            'text': message,
            'cardsV2': [card.to_dict()] if card else []
        }

        try:
            response = requests.post(
                webhook_url, headers=headers, data=json.dumps(data)
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            if e.response.status_code == 400:
                self.__logger.error(f"Failed to webhook send: {e}")
        except requests.RequestException as e:
            self.__logger.error(f"Failed to webhook send: {e}")
