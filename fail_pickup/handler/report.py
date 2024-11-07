import logging

from django.db.models import Q
from django.utils import timezone

from google_wrapper.services import GoogleChatService
from google_wrapper.utils.card_builder import CardBuilder
from google_wrapper.utils.card_builder import widgets as W
from google_wrapper.utils.card_builder.elements import (
    CardHeader,
    Section,
)
from opv2.base.pickup import PickupJobStatusChoices
from stos.utils import configs
from .collect_data import collect_job_info
from ..models import PickupJob, Route, PickupJobOrder

logger = logging.getLogger(__name__)


def _build_report_card(total, fail_success, ops_overwrite, not_ready, total_package, fail_package):
    """
    Builds the Google Chat notification card with task failure details.
    """
    card_builder = CardBuilder()

    # Card Header with current timestamp
    card_header = CardHeader()
    card_header.title = "Fail Pickup Job"
    card_header.subtitle = timezone.now().strftime('%d/%m/%Y %H:%M:%S')
    card_builder.set_header(card_header)

    # Card Section
    section = Section()
    section.header = '<font color=\"#156311\">Report</font>'

    # Widgets with task details
    section.add_widget(W.TextParagraph(f'<b>Failed Jobs:</b> {fail_success}/{total}'))
    section.add_widget(W.TextParagraph(f'<b>Failed Packages:</b> {fail_package}/{total_package}'))
    section.add_widget(W.TextParagraph(f'<b>Ops Overwrite:</b> {ops_overwrite}'))
    section.add_widget(W.TextParagraph(f'<b>Not Ready:</b> {not_ready}'))

    card_builder.add_section(section)

    return card_builder.card


def report_fail_job():
    collect_job_info()
    route = Route.objects.filter(
        Q(created_date__date=timezone.now().date()) &
        Q(archived=False)
    ).first()

    if route is None:
        return

    pickup_jobs = PickupJob.objects.filter(
        Q(created_date__date=timezone.now().date())
    )

    total = pickup_jobs.count()
    fail_success = pickup_jobs.filter(
        Q(driver_id=1682343) &
        Q(status=PickupJobStatusChoices.FAILED)
    ).count()

    ops_overwrite = pickup_jobs.filter(
        Q(route_id=route.route_id) &
        ~Q(driver_id=1682343)
    ).count()

    not_ready = pickup_jobs.filter(
        Q(route__isnull=True)
    ).count()

    total_package = PickupJobOrder.objects.filter(
        Q(job_id__in=pickup_jobs)
    ).count()

    fail_package = PickupJobOrder.objects.filter(
        Q(job_id__in=pickup_jobs) &
        Q(job_id__status=PickupJobStatusChoices.FAILED) &
        Q(job_id__driver_id=1682343)
    ).count()

    logger.info(
        f"Fail: {fail_success}/{total}, Ops Overwrite: {ops_overwrite}, Not Ready: {not_ready}, Fail Package: {fail_package}/{total_package}")

    hook_url = configs.get('ROOT_NOTIFICATION_WEBHOOK')
    if hook_url:
        try:
            card = _build_report_card(total, fail_success, ops_overwrite, not_ready, total_package, fail_package)

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
