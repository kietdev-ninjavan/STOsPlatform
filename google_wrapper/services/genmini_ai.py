import logging
from enum import Enum

import google.generativeai as gemini

logger = logging.getLogger(__name__)


class ModelEnum(Enum):
    """Enumeration for Gemini model versions."""
    GEMINI_1_0_PRO_LATEST = 'gemini-1.0-pro-latest'
    GEMINI_1_5_FLASH_LATEST = 'gemini-1.5-flash-latest'
    GEMINI_1_5_PRO_LATEST = 'gemini-1.5-pro-latest'
    TEXT_EMBEDDING = 'models/embedding-001'


class GenminiAIService:
    """
    A class to interact with the Gemini API.

    Models and Quotas:
    ========================
    Model: gemini-1.0-pro-latest
    Quota: 15 RPM | 32,000 TPM | 1,500 RPD | 46,080,000 TPD
    Input: Text
    ========================
    Model: gemini-1.5-flash-latest
    Quota: 15 RPM | 1 million TPM | 1,500 RPD | 1,440,000,000 TPD
    Input: Audio, images, video, and text
    ========================
    Model: gemini-1.5-pro-latest
    Quota: 2 RPM | 32,000 TPM | 50 RPD | 46,080,000 TPD
    Input: Text
    """

    def __init__(self, api_key: str, model: ModelEnum = ModelEnum.GEMINI_1_5_FLASH_LATEST, generation_config: dict = None,
                 logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the GoogleGemini instance.

        Args:
            api_key (str): The API key for authentication.
            model (ModelEnum): The model to use for generating content.
            logger (logging.Logger): The logger instance for logging.
        """
        if not api_key:
            logger.error("Google Gemini API key is missing.")
            raise ValueError("Google Gemini API key is missing.")

        if not generation_config:
            generation_config = {
                "temperature": 1,
                "top_p": 0.95,
                "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }

        gemini.configure(api_key=api_key)
        self.model = gemini.GenerativeModel(
            model_name=model.value,
            generation_config=generation_config
        )
        self.__logger = logger

    def count_tokens(self, prompt):
        """
        Count the tokens in the given prompt.

        Args:
            prompt (str): The input text prompt.

        Returns:
            int: The total number of tokens in the prompt.
        """
        response = self.model.count_tokens(prompt)
        return response.total_tokens

    def chat(self, prompt):
        """
        Generate a response based on the given prompt.

        Args:
            prompt (str): The input text prompt.

        Returns:
            str: The generated response text.
        """
        try:
            response = self.model.generate_content(prompt)
            return self.clear_response(response.text)
        except Exception as e:
            self.__logger.error(f"Error gemini chat: {e}")
            return None

    def chat_session(self, history: list, massage: str):
        """
        Generate a response based on the given prompt.

        Args:
            history (list): The list of previous messages in the chat session.
            massage (str): The input text message.

        Returns:
            str: The generated response text.
        """

        try:
            session = self.model.start_chat(history=history)
            response = session.send_message(massage)
            return self.clear_response(response.text)
        except Exception as e:
            self.__logger.error(f"Error gemini chat session: {e}")
            return None

    @staticmethod
    def clear_response(response):
        """
        Clean the response text by removing code blocks and adjusting formatting.

        Args:
            response (str): The response text to be cleaned.

        Returns:
            str: The cleaned response text.
        """
        if '```json' in response:
            cleaned_text = response.replace('```json', '').replace('```', '').strip()
        else:
            cleaned_text = response.strip()
        return cleaned_text
