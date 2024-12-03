import json
import logging
from typing import List

from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_update_with_history

from google_wrapper.services import GenminiAIService
from stos.utils import configs, chunk_list, parse_datetime, swap_day_month_if_different
from ...models import TicketChangeDate

logger = logging.getLogger(__name__)


def gemini_detect(data: List[dict]):
    """
    This function is used to detect the address by Gemini
    """
    gemini = GenminiAIService(configs.get('AI_API_KEY_CHANGE_ADDRESS'), logger=logger)

    history = [
        {
            "role": "user",
            "parts": [
                "Given a list of data containing ticket IDs, a base date called \"today\" in the format `YYYY-MM-DD`, and text with potential date information, identify and calculate dates based on specific days of the week mentioned. \n\n- If the text includes a Vietnamese day of the week (e.g., \"thứ 2\" for Monday), calculate the next occurrence of that day based on \"today\".\n- If the text contains a specific date in Vietnamese, extract and standardize it to `YYYY-MM-DD`.\n- If no date or day of the week is found, set the output to `null`.\n\n**Day Mappings in Vietnamese**:\n- \"thứ 2\" = Monday\n- \"thứ 3\" = Tuesday\n- \"thứ 4\" = Wednesday\n- \"thứ 5\" = Thursday\n- \"thứ 6\" = Friday\n- \"thứ 7\" = Saturday\n- \"chủ nhật\" = Sunday\n\n**Input JSON**:\n[\n  {\n    \"ticket_id\": \"<ticket_id>\",\n    \"today\": \"%Y-%m-%d (%A)\",\n    \"text\": \"<Vietnamese text with possible date or weekday information>\"\n  },\n  ...\n]\n\nFor each entry, do the following::\n1. Format the extracted data into the following JSON structure:\n2. Check if the text includes a Vietnamese day of the week. If so, calculate the next date for that day based on \"today\".\n3. If a specific date is written in the text, standardize it to `YYYY-MM-DD`.\n4. If no recognizable date or day of the week is found, set the `date` to `null`.\n5. Return the output JSON only. Not more text.\n\n**Output JSON**:\n{\n   \"data\": [\n     {\n       \"ticket_id\": \"<ticket_id>\",\n       \"input\": \"<Original Text>\",\n       \"date\": \"<Calculated or Extracted Date in YYYY-MM-DD format or null>\"\n     },\n     ...\n   ]\n}\n\n**Examples**:\n\nInput:\n[\n  {\n    \"ticket_id\": \"001\",\n    \"today\": \"2024-10-31\",\n    \"text\": \"khách hẹn thứ 2\"\n  },\n  {\n    \"ticket_id\": \"002\",\n    \"today\": \"2024-10-31\",\n    \"text\": \"Cuộc họp sẽ diễn ra vào ngày 5 tháng 11 năm 2024.\"\n  },\n  {\n    \"ticket_id\": \"003\",\n    \"today\": \"2024-10-31\",\n    \"text\": \"05/10 giao lại\"\n  },\n  {\n    \"ticket_id\": \"004\",\n    \"today\": \"2024-10-31\",\n    \"text\": \"Không có ngày nào cụ thể trong văn bản này.\"\n  }\n]\n\nExpected Output:\n{\n   \"data\": [\n     {\n       \"ticket_id\": \"001\",\n       \"input\": \"khách hẹn thứ 2\",\n       \"date\": \"2024-11-04\"\n     },\n     {\n       \"ticket_id\": \"002\",\n       \"input\": \"Cuộc họp sẽ diễn ra vào ngày 5 tháng 11 năm 2024.\",\n       \"date\": \"2024-11-05\"\n     },\n     {\n       \"ticket_id\": \"003\",\n       \"input\": \"05/10 giao lại\",\n       \"date\": \"2024-10-05\"\n     },\n     {\n       \"ticket_id\": \"004\",\n       \"input\": \"Không có ngày nào cụ thể trong văn bản này.\",\n       \"date\": null\n     }\n   ]\n}\n\nYou know what I mean? If you understand, answer yes and wait for me to provide the address json list.",
            ],
        },
        {
            "role": "model",
            "parts": [
                "yes\n",
            ],
        },
    ]

    detected = gemini.chat_session(history, f'{data}')

    return detected


def detect_date():
    """
    This function is used to detect the address of the ticket
    """
    tickets = TicketChangeDate.objects.filter(
        Q(detected_date__isnull=True) &
        (
                Q(exception_reason__isnull=False) |
                Q(notes__isnull=False) |
                Q(comments__isnull=False)
        ) &
        Q(action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No tickets to detect address")

    logger.info(f"Found {tickets.count()} tickets to detect address")
    data = []
    for ticket in tickets:
        content = " ".join(filter(None, [ticket.notes, ticket.comments, ticket.exception_reason]))

        data.append({
            "ticket_id": ticket.ticket_id,
            "today": timezone.now().strftime("%Y-%m-%d (%A)"),
            "text": f"{content}",
        })

    detected_data = []
    for chunk in chunk_list(data, 50):
        logger.info(f"Detecting {len(chunk)} tickets")
        detected = gemini_detect(chunk)

        if not detected:
            logger.error("Error getting response from Gemini")
            continue
        logger.debug(f"Detected: {detected}")
        try:
            json_response = json.loads(detected)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing response: {e}")
            continue

        detected_data.extend(json_response.get('data', []))

    logger.info(f"Got {len(detected_data)} responses from Gemini")

    ticket_id_map = {ticket.ticket_id: ticket for ticket in tickets}

    update_data = []
    for item in detected_data:
        ticket = ticket_id_map.get(item.get('ticket_id'))
        if ticket is None:
            continue
        date_str = item.get('date')
        if date_str is None:
            continue
        date = parse_datetime(date_str)

        ticket.detected_date = swap_day_month_if_different(date)
        ticket.updated_date = timezone.now()

        update_data.append(ticket)

    try:
        logger.info("Inserting detected address records")
        success = bulk_update_with_history(update_data, TicketChangeDate, batch_size=1000, fields=['detected_date', 'updated_date'])
    except Exception as e:
        logger.error(f"Error saving detected address: {e}")
        raise e

    logger.info(f"Successfully inserted {success}/{len(detected_data)} detected address records.")
