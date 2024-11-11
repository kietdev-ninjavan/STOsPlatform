import copy
import logging

from django.db.models import Q
from django.utils import timezone
from gql import gql
from simple_history.utils import bulk_create_with_history, bulk_update_with_history

from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from opv2.base.order import GranularStatusChoices
from opv2.base.ticket import TicketTypeChoices
from opv2.services import GraphQLService, TicketService
from stos.utils import configs, chunk_list, check_record_change
from ..models import Order

logger = logging.getLogger(__name__)


def collect_vendor_call_data():
    gsheet_service = GoogleSheetService(
        service_account=get_service_account(configs.get('GSA_BI')),
        spreadsheet_id=configs.get('PSS_VENDOR_SPREADSHEET_ID'),
        logger=logger
    )

    records = gsheet_service.get_all_records(configs.get('PSS_VENDOR_WORKSHEET_ID'))

    if not records:
        logger.info("No data found in the Google Sheet")
        return

    for chunk in chunk_list(records, 1000):
        tracking_ids = [record.get('tracking_id') for record in chunk]
        project_calls = [record.get('project_call') for record in chunk]

        # Fetch existing orders only with the fields needed and store in a set for faster lookup
        existing_orders = set(
            Order.objects.filter(
                Q(tracking_id__in=tracking_ids) &
                Q(project_call__in=project_calls)
            ).values_list('tracking_id', 'project_call')
        )

        new_records = []
        for index, row in enumerate(chunk):
            # Check against the set instead of querying the database
            if (row.get('tracking_id'), row.get('project_call')) in existing_orders:
                continue

            if not row.get('tracking_id'):
                logger.warning(f"Row {index + 1} empty tracking_id, skipping")
                continue

            # Process new records as needed
            try:
                new_records.append(Order(
                    tracking_id=row.get('tracking_id'),
                    project_call=row.get('project_call'),
                    time_stamp=row.get('time_stamp'),
                    dest_hub_id=row.get('dest_hub_id'),
                    shipper_group=row.get('shipper_group')
                ))
            except Exception as e:
                logger.error(f'Can not add row {index + 1} to Database: {e}')
                continue

        # Bulk create new records here if needed
        if new_records:
            success = bulk_create_with_history(new_records, Order, batch_size=1000, ignore_conflicts=True)
            logger.info(f"Successfully added {len(success)} new records to the database")
        else:
            logger.info("No new records to add to the database")


def load_order_info():
    graphql_client = GraphQLService(
        url="https://api.ninjavan.co/vn/core/graphql/order",
        logger=logger
    )

    orders = Order.objects.filter(
        Q(created_date__date=timezone.now().date()) &
        (
                Q(granular_status__isnull=True) |
                ~Q(granular_status__in=[GranularStatusChoices.completed, GranularStatusChoices.cancelled])
        )
    )

    if not orders:
        logger.info("No orders need update info in the database")
        return

    tracking_ids = [order.tracking_id for order in orders]
    query = gql("""
        query ($trackingOrStampIds: [String!]!, $offset: Int!) {
            listOrders(tracking_or_stamp_ids: $trackingOrStampIds, offset: $offset) {
                order {
                    trackingId,
                    id,
                    status,
                    granularStatus,
                    isRts,
                    lastDelivery {
                        waypoint {
                            id
                        }
                    }
                }
            }
        }
    """)

    orders_info = []
    for chunk in chunk_list(tracking_ids, 100):
        variables = {
            "trackingOrStampIds": chunk,
            "offset": 0,
        }

        try:
            result = graphql_client.execute_query(query, variables)
        except Exception as e:
            logger.error(f"Error when executing GraphQL query: {e}")
            raise e

        orders_info.extend(result["listOrders"])

    tracking_id_map = {order["order"]["trackingId"]: order["order"] for order in orders_info}

    order_has_changed = []
    for order in orders:
        new_record = copy.deepcopy(order)
        order_info = tracking_id_map[order.tracking_id]
        new_record.granular_status = order_info["granularStatus"]
        new_record.order_id = order_info["id"]
        new_record.rts = order_info["isRts"]
        new_record.waypoint_id = order_info["lastDelivery"]["waypoint"]["id"]

        is_updated, existing_record, _ = check_record_change(
            existing_record=order,
            updated_record=new_record,
            excluded_fields=['tracking_id', 'order_sn']
        )
        if is_updated:
            order_has_changed.append(existing_record)

    if not order_has_changed:
        logger.info("No orders have changed")
        return

    success = bulk_update_with_history(order_has_changed, Order, batch_size=1000,
                                       fields=['granular_status', 'order_id', 'rts', 'waypoint_id', 'updated_date'])

    logger.info(f"Updated {success}/{len(orders)} orders in the database")


def __get_last_instruction(ticket_ids):
    ticket_service = TicketService(logger=logger)

    stt_code, result = ticket_service.get_detail_tickets(ticket_ids)

    if stt_code != 200:
        logger.error('Fail get ticket detail')
        return {}

    if not result:
        logger.info("No ticket detail found for the orders")
        return {}

    last_instructions = {}
    for ticket_id, data in result.items():
        custom_fields = {cf['fieldName']: cf['fieldValue'] for cf in data['customFields']}
        last_instruction = custom_fields.get('TICKET NOTES', '')
        last_instructions[ticket_id] = last_instruction

    return last_instructions


def load_ticket_info_sla():
    orders = Order.objects.filter(
        Q(created_date__date=timezone.now().date()) &
        Q(project_call__icontains='Breach SLA') &
        Q(route__isnull=True) &
        Q(ticket_id__isnull=False)
    )

    if not orders:
        logger.info("No SLA orders available")
        return

    tracking_ids = orders.values_list('tracking_id', flat=True)

    ticket_service = TicketService(logger=logger)
    stt_code, ticket_info = ticket_service.get_ticket_by_tracking_ids(tracking_ids, ticket_types=[TicketTypeChoices.MISSING])

    if stt_code != 200:
        logger.error('Fail get ticket missing')
        return

    if not ticket_info:
        logger.info("No ticket info found for the orders")
        return
    ticket_ids = [item.id for item in ticket_info]
    last_instructions = __get_last_instruction(ticket_ids)
    map_tracking_ticket = {item.tracking_id: item for item in ticket_info}

    update_orders = []
    for order in orders:
        ticket = map_tracking_ticket.get(order.tracking_id, None)
        if ticket:
            order.ticket_id = ticket.id
            order.investigating_hub_id = ticket.investigating_hub_id
            order.last_instruction = last_instructions.get(ticket.id, None)
            update_orders.append(order)

    success = bulk_update_with_history(update_orders, Order, batch_size=1000, fields=['ticket_id', 'investigating_hub_id', 'last_instruction'])
    logger.info(f"Updated {success}/{len(orders)} orders with ticket info")
