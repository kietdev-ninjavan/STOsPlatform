import logging

from django.db.models import Q
from django.utils import timezone
from gql import gql
from simple_history.utils import bulk_create_with_history, bulk_update_with_history

from network.models import Zone
from opv2.services import OrderService, GraphQLService
from redash.client import RedashClient
from stos.utils import configs, chunk_list
from ...models import TicketChangeAddress

logger = logging.getLogger(__name__)


def collect_ticket_change_address():
    redash_client = RedashClient(
        api_key=configs.get('REDASH_API_KEY'),
        logger=logger
    )

    try:
        tickets = redash_client.fresh_query_result(query_id=2014)
    except Exception as e:
        raise e

    total_tickets = len(tickets)
    total_success = 0
    for chunk in chunk_list(tickets, 1000):
        ticket_ids = [ticket['ticket_id'] for ticket in chunk]

        # Get the existing tickets
        existing_tickets = TicketChangeAddress.objects.filter(ticket_id__in=ticket_ids).values_list('ticket_id', flat=True)
        new_tickets = []
        for ticket in chunk:
            if ticket['ticket_id'] in existing_tickets:
                continue

            try:
                ticket = TicketChangeAddress(
                    ticket_id=ticket.get('ticket_id'),
                    tracking_id=ticket.get('tracking_id'),
                    ticket_status=ticket.get('status_id'),
                    ticket_type=ticket.get('type_id'),
                    ticket_sub_type=ticket.get('subtype_id'),
                    hub_id=ticket.get('hub_id'),
                    shipper_id=ticket.get('global_shipper_id'),
                    investigating_hub_id=ticket.get('investigating_hub_id'),
                    created_at=ticket.get('created_at'),
                    comments=ticket.get('comments') if ticket.get('comments') != '' else None,
                    notes=ticket.get('ticket_notes') if ticket.get('ticket_notes') != '' else None,
                    exception_reason=ticket.get('exception_reason') if ticket.get('exception_reason') != '' else None,
                    province=ticket.get('province'),
                    times_change=ticket.get('change_address_times'),
                    first_attempt_date=ticket.get('date_of_1st_delivery_fail'),

                )
                new_tickets.append(ticket)
            except Exception as e:
                logger.error(f"Error creating ticket {ticket['ticket_id']}: {e}")
                continue

        success = bulk_create_with_history(new_tickets, TicketChangeAddress, batch_size=1000, ignore_conflicts=True)

        total_success += len(success)
        logger.info(f"Successfully inserted {len(success)} tickets change address records.")

    logger.info(f'Successfully inserted {total_success}/{total_tickets} tickets change address records.')


def load_zone_info(tracking_ids):
    graphql_client = GraphQLService(
        url="https://api.ninjavan.co/vn/core/graphql/order",
        logger=logger
    )

    query = gql("""
            query ($trackingOrStampIds: [String!]!, $offset: Int!) {
                listOrders(tracking_or_stamp_ids: $trackingOrStampIds, offset: $offset) {
                    order {
                        trackingId,
                        lastDelivery {
                            waypoint {
                                routingZoneId
                            }
                        }
                    }
                }
            }
        """)

    list_orders = []
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

        list_orders.extend(result["listOrders"])

    tracking_zone_id_map = {order["order"]["trackingId"]: order["order"]["lastDelivery"]["waypoint"]["routingZoneId"] for order in list_orders}
    tracking_zone_name_map = {}
    for tracking_id, zone_id in tracking_zone_id_map.items():
        try:
            zone = Zone.objects.get(legacy_zone_id=zone_id)
            tracking_zone_name_map[tracking_id] = zone.name
        except Zone.DoesNotExist:
            logger.warning(f"Zone with ID {zone_id} not found")
            continue

    return tracking_zone_name_map


def load_order_info():
    tickets = TicketChangeAddress.objects.filter(
        Q(action__isnull=True)
    )

    if not tickets.exists():
        logger.info("No ticket to load order info")
        return

    order_svc = OrderService(logger=logger)
    tracking_ids = tickets.values_list('tracking_id', flat=True)
    stt_code, result = order_svc.search_all(tracking_ids)
    tracking_zone_name_map = load_zone_info(tracking_ids)
    if stt_code != 200:
        logger.error(f"Error searching orders: {result}")
        raise Exception("Error searching orders")
    update = []
    for ticket in tickets:
        info = result.get(ticket.tracking_id)
        if not info:
            continue
        ticket.old_address = info.full_address
        ticket.old_province = info.province
        ticket.order_id = info.id
        ticket.old_district = info.district
        ticket.old_ward = info.ward
        ticket.rts_flag = info.is_rts
        ticket.order_status = info.granular_status
        ticket.zone_name = tracking_zone_name_map.get(ticket.tracking_id)
        ticket.updated_date = timezone.now()

        update.append(ticket)

    try:
        success = bulk_update_with_history(
            update,
            TicketChangeAddress, batch_size=1000,
            fields=['old_address', 'order_id', 'old_province', 'old_district', 'old_ward', 'rts_flag', 'order_status', 'zone_name', 'updated_date']
        )

        logger.info(f"Updated {success}/{tickets.count()} tickets' order info")
    except Exception as e:
        logger.error(f"Failed to update orders: {e}")
        raise e
