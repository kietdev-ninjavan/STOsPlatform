import logging

from celery_once import QueueOnce
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


class STOsTask(QueueOnce):
    # Set the unique key for the task
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        exc – The exception raised by the task.
        task_id – Unique id of the failed task.
        args – Original arguments for the task that failed.
        kwargs – Original keyword arguments for the task that failed.
        einfo – Exception info including the traceback.
        """
        # Check if the notification webhook URL is set in settings
        hook_url = configs.get('ROOT_NOTIFICATION_WEBHOOK')
        if hook_url:
            try:
                # Build and send the Google Chat notification
                card = self._build_failure_card(exc, task_id, args, kwargs, einfo)
                chat_service = GoogleChatService()
                chat_service.webhook_send(
                    webhook_url=hook_url,
                    card=card,
                )
                logger.info(f"Task failure notification sent for task {task_id}")
            except Exception as notification_exc:
                # Log any errors that occur during notification to avoid masking the actual task failure
                logger.error(
                    f"Failed to send task failure notification for task {task_id}. Error: {notification_exc}"
                )
        else:
            logger.warning("No webhook URL configured, task failure notification skipped.")

        # Call the parent class's on_failure to maintain default behavior
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def _build_failure_card(self, exc, task_id, args, kwargs, einfo):
        """
        Builds the Google Chat notification card with task failure details.
        """
        card_builder = CardBuilder()

        # Card Header with current timestamp
        card_header = CardHeader()
        card_header.title = "Task Failure Report"
        card_header.subtitle = timezone.now().strftime('%d/%m/%Y %H:%M:%S')
        card_builder.set_header(card_header)

        # Card Section
        section = Section()
        section.header = f'<font color=\"#de1304\">Task {self.name} failed</font>'
        section.collapsible = True
        section.uncollapsible_widgets_count = 2

        # Widgets with task details
        section.add_widget(W.TextParagraph(f'<b>Worker:</b> {self.request.hostname}'))
        section.add_widget(W.TextParagraph(f'<b>Task ID:</b> {task_id}'))
        section.add_widget(W.TextParagraph(f'<b>Exception:</b> {exc}'))
        section.add_widget(W.TextParagraph(f'<b>Arguments:</b> {args}'))
        section.add_widget(W.TextParagraph(f'<b>Keyword Arguments:</b> {kwargs}'))

        # Truncate long tracebacks to avoid overwhelming the notification
        max_traceback_length = 1000  # You can adjust the max length as needed
        einfo_str = str(einfo)[:max_traceback_length] + ('...' if len(str(einfo)) > max_traceback_length else '')
        section.add_widget(W.TextParagraph(f'<b>Traceback:</b> {einfo_str}'))

        card_builder.add_section(section)

        return card_builder.card
