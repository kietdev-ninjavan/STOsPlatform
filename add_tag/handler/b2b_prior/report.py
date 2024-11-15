import logging

from django.utils import timezone

from google_wrapper.services import GoogleChatService
from google_wrapper.utils.card_builder import CardBuilder
from google_wrapper.utils.card_builder import widgets as W
from google_wrapper.utils.card_builder.elements import (
    CardHeader,
    Section,
)
from stos.utils import configs

logger = logging.getLogger(__name__)


def _build_report_card(total, add_success, add_failed):
    """
    Builds the Google Chat notification card with task failure details.
    """
    card_builder = CardBuilder()

    # Card Header with current timestamp
    card_header = CardHeader()
    card_header.title = "Add Prior Tag B2B"
    card_header.subtitle = timezone.now().strftime('%d/%m/%Y %H:%M:%S')
    card_builder.set_header(card_header)

    # Card Section
    section = Section()
    section.header = '<font color=\"#156311\">Report</font>'

    # Widgets with task details
    section.add_widget(W.TextParagraph(f'<b>Total:</b> {total}'))
    section.add_widget(W.TextParagraph(f'<b>Success:</b> {add_success}'))
    section.add_widget(W.TextParagraph(f'<b>Failed:</b> {add_failed}'))

    card_builder.add_section(section)

    return card_builder.card


def report_add_tag(total, add_success, add_failed):
    hook_url = configs.get('ROOT_NOTIFICATION_WEBHOOK')
    if hook_url:
        try:
            card = _build_report_card(total, add_success, add_failed)

            chat_service = GoogleChatService()
            chat_service.webhook_send(
                webhook_url=hook_url,
                card=card,
            )
        except Exception as notification_exc:
            # Log any errors that occur during notification to avoid masking the actual task failure
            logger.error(
                f"Failed to send notify. Error: {notification_exc}"
            )
    else:
        logger.warning("No webhook URL configured, task failure notification skipped.")
