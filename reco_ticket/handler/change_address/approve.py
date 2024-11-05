import logging
import unicodedata

from django.db.models import Q
from django.utils import timezone
from simple_history.utils import bulk_update_with_history

from opv2.dto import TicketResolveDTO
from opv2.services import TicketService, OrderService
from ...models import TicketChangeAddress

logger = logging.getLogger(__name__)


def __normalize_text(text):
    return unicodedata.normalize('NFC', text).lower()


def __check_vietnamese_substring(a, b):
    if not a or not b:
        return False
    try:
        a = __normalize_text(a)
        b = __normalize_text(b)
    except Exception as e:
        logger.error(f"Error normalizing text: {e}")
        return False

    is_a_in_b = a in b
    is_b_in_a = b in a

    return is_a_in_b != is_b_in_a


def __resolve_tickets(tickets, new_instruction, action, action_reason):
    # Prepare DTOs for resolving tickets
    data_resolve = [
        TicketResolveDTO(
            tracking_id=ticket.tracking_id,
            ticket_id=ticket.ticket_id,
            order_outcome='RESUME DELIVERY',
            custom_fields=[],
            new_instruction=new_instruction
        ) for ticket in tickets
    ]

    # Initialize the ticket service and attempt to resolve tickets
    ticket_svc = TicketService(logger=logger)
    stt_code, result = ticket_svc.resolve_tickets(data_resolve)

    if stt_code != 200:
        logger.error(f"Failed to resolve tickets with status code {stt_code}")
        return

    success_ticket_ids = result.get('success', [])
    if not success_ticket_ids:
        logger.warning("No tickets were successfully resolved")
        return

    # Prepare tickets for bulk update
    map_ticket_id = {f'{ticket.ticket_id}': ticket for ticket in tickets}
    tickets_to_update = []
    for ticket_id in success_ticket_ids:
        ticket = map_ticket_id.get(f'{ticket_id}')
        if ticket is None:
            continue

        ticket.action = action
        ticket.action_reason = action_reason
        ticket.updated_date = timezone.now()
        tickets_to_update.append(ticket)

    # Attempt bulk update with history
    try:
        success = bulk_update_with_history(
            tickets_to_update,
            TicketChangeAddress,
            batch_size=1000,
            fields=['action', 'action_reason', 'updated_date']
        )
        logger.info(f"Updated {success}/{len(tickets_to_update)} tickets' statuses")
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        raise e


def __change_address(tickets):
    order_svc = OrderService(logger=logger)
    success = 0
    for ticket in tickets:
        stt_code, result = order_svc.change_to_address(
            order_id=ticket.order_id,
            address1=ticket.detect.address,
            address2='',
            city='',
        )

        if stt_code != 200:
            logger.error(f"Failed to change address for order {ticket.order_id}: {result}")
            continue

        logger.info(f"Changed address for order {ticket.order_id}")
        success += 1

    logger.info(f"Changed address for {success}/{len(tickets)} orders")


def approve_hcm_dn_hn():
    main_provinces = ['Hồ Chí Minh', 'Đà Nẵng', 'Hà Nội']
    abbreviations = ['HCM', 'ĐN', 'HN']

    province_filters = Q()
    for province in main_provinces + abbreviations:
        province_filters |= Q(province__icontains=province) | Q(old_province__icontains=province)

    address_filters = Q()
    for term in main_provinces + abbreviations:
        address_filters |= Q(old_address__icontains=term)

    detect_filters = Q()
    for term in main_provinces + abbreviations:
        detect_filters |= Q(detect__province__icontains=term)

    tickets = TicketChangeAddress.objects.filter(
        (province_filters | address_filters) & detect_filters & Q(action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No tickets to approve")
        return

    logger.info(f"Found {tickets.count()} tickets to approve")

    __resolve_tickets(
        tickets,
        'Change',
        'Approve',
        'In province HCM, DN, HN')

    __change_address(tickets)


def approve_map_2_level():
    tickets = TicketChangeAddress.objects.filter(
        Q(action__isnull=True) &
        Q(detect__isnull=False)
    )

    if not tickets.exists():
        logger.info("No ticket to approve")
        return

    logger.info(f"Found {tickets.count()} ticket(s) to handler")

    approve = []
    reject = []
    for ticket in tickets:
        try:
            if ((
                    __check_vietnamese_substring(ticket.detect.province, ticket.old_address) or
                    __check_vietnamese_substring(ticket.detect.province, ticket.old_province)
            ) and
                    (
                            __check_vietnamese_substring(ticket.detect.district, ticket.old_address) or
                            __check_vietnamese_substring(ticket.detect.district, ticket.old_district) or
                            __check_vietnamese_substring(ticket.detect.district, ticket.zone_name)
                    )
            ):
                approve.append(ticket)

            else:
                reject.append(ticket)
        except Exception as e:
            logger.error(f"Error check map 2 level: {e}")
            continue

    if approve:
        logger.info(f"Approving {len(approve)} tickets")
        __resolve_tickets(approve, 'Change', 'Approve', 'Map 2 level')
        __change_address(approve)

    if reject:
        logger.info(f"Rejecting {len(reject)} tickets")
        __resolve_tickets(reject, 'Only Ward/Commune can be changed', 'Resolved (Resume Delivery)', 'Not map 2 level')
