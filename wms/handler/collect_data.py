import logging
import copy
from django.db.models import Q
from gql import gql
from simple_history.utils import bulk_create_with_history, bulk_update_with_history
from google_wrapper.services import GoogleSheetService
from google_wrapper.utils import get_service_account
from stos.utils import configs, chunk_list, check_record_change
from opv2.services import GraphQLService, WMSService
from ..models import OrigOrders

logger = logging.getLogger(__name__)

def warehouse_holding():
    """
        Collect SHEIN holding orders from Warehouse
        Update to database
    """
    holding_spreadsheet_id = '1N_Q5Ntf2-I1Bi0IfPH-9lf9HU8GLTBbAKNzGYTZ8liE' 
    holding_sheet_id = 1167505016
    sheet_authorization = GoogleSheetService(
        service_account=get_service_account(configs.get('GSA_BI')),
        spreadsheet_id=holding_spreadsheet_id,
        logger=logger
    )
    
    holding_data = sheet_authorization.get_all_records(holding_sheet_id)
    if not holding_data:
        logger.info("No SHEIN holding data found in the Google Sheet")
        return
    
    current_orders = OrigOrders.objects.values_list('tracking_id', flat=True)
    new_holding = [ 
        value for value in holding_data
        if value['tracking_id'] not in current_orders
    ]
    
    new_record = []
    for index, value in enumerate(new_holding):
        try : 
            new_record.append(
                OrigOrders(
                    date_input = value['date'],
                    tracking_id = value['tracking_id']
                )
            )
        except Exception as e:
            logger.error(f"Error when creating new record: Row {index + 1}")
    if new_record:
        creator = bulk_create_with_history(new_record,OrigOrders)
        logger.info(f"Created {len(creator)} new records")
    else:
        logger.info("No new records to add to the database")
    
   
def update_opv2_info():     
    """
        Retrieve orders from DB without "Returned to Sender" or None status
        Refresh last status from Opv2
        Update to database
    """
    pending_orders = OrigOrders.objects.filter(
        ~Q(granular_status = 'Returned to Sender') | 
        Q(granular_status__isnull = True)
    )
    
    if not pending_orders:
        logger.info("No orders need update info in the database")
        return

    orders_info = []
    graphql_client = GraphQLService(
        url="https://api.ninjavan.co/vn/core/graphql/order",
        logger=logger
    )
    query = gql("""
        query ($trackingOrStampIds: [String!]!, $offset: Int!) {
            listOrders(tracking_or_stamp_ids: $trackingOrStampIds, offset: $offset) {    
                order {
                    trackingId
                    granularStatus
                }
            }
        }
    """)
    for chunk in chunk_list([value.tracking_id for value in pending_orders], 100):
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
    for order in pending_orders:
        new_record = copy.deepcopy(order)
        order_info = tracking_id_map[order.tracking_id]
        new_record.granular_status = order_info["granularStatus"]
        is_updated, existing_record, _ = check_record_change(
            existing_record=order,
            updated_record=new_record
        )
        if is_updated:
            order_has_changed.append(existing_record)
    if not order_has_changed:
        logger.info("No orders have changed")
        return

    success = bulk_update_with_history(order_has_changed, OrigOrders, batch_size=1000,
                                       fields=['granular_status', 'tracking_id', 'updated_date'])

    logger.info(f"Updated {success}/{len(pending_orders)} orders in the database")
    
def update_wms_info():     
    """
        Retrieve orders from DB with "Returned to Sender" status and not enough WMS info
        Refresh info from WMS
        Update to database
    """    
    pending_orders = OrigOrders.objects.filter(
        (Q(wms_status = "") |
        Q(bin_name = "") |
        Q(putaway_datetime = "") |
        Q(picklist_uploaded_timestamp = "") |
        Q(pending_pick_timestamp = "") |
        Q(pick_timestamp = "") |
        Q(pack_timestamp = "")) &
        Q(granular_status = "Returned to Sender")
    )
    if not pending_orders:
        logger.info("No orders need update WMS info in the database")
        return

    
    wms = WMSService()
    orders_info = []
    
    for order in pending_orders:
        tracking_id = order.tracking_id
        try :
            code_info, wms_info = wms.load_order_by_tracking_id(tracking_id)
        except Exception as e:
            logger.error(f"Error when load order's info from WMS Service: {e}")
            
        orders_info.append(wms_info["parcels"][0])
    
    tracking_id_map = {order["tracking_id"]: order for order in orders_info}

    order_has_changed = []
    for order in pending_orders:
        new_record = copy.deepcopy(order)
        order_info = tracking_id_map[order.tracking_id]
        new_record.wms_status = order_info["status"] if order_info["status"] else ""
        new_record.bin_name = order_info["bin_name"] if order_info["bin_name"] else ""
        new_record.putaway_datetime = order_info["putaway_timestamp"] if order_info["putaway_timestamp"] else ""
        new_record.picklist_uploaded_timestamp = order_info["picklist_uploaded_timestamp"] if order_info["picklist_uploaded_timestamp"] else ""
        new_record.pending_pick_timestamp = order_info["pending_pick_timestamp"] if order_info["pending_pick_timestamp"] else ""
        new_record.pick_timestamp = order_info["pick_timestamp"] if order_info["pick_timestamp"] else ""
        new_record.pack_timestamp = order_info["pack_timestamp"] if order_info["pack_timestamp"] else ""
        new_record.auto_dispose =  1 if order_info["auto_dispose"] == True else 0
        is_updated, existing_record, _ = check_record_change(
            existing_record=order,
            updated_record=new_record,
            excluded_fields= ["granular_status"]
        )
        if is_updated:
            order_has_changed.append(existing_record)
    if not order_has_changed:
        logger.info("No orders have changed")
        return

    success = bulk_update_with_history(order_has_changed, OrigOrders,
                                       fields=["updated_date", "tracking_id", "wms_status", "bin_name", "putaway_datetime",
                                               "picklist_uploaded_timestamp", "pending_pick_timestamp", "pick_timestamp",
                                               "pack_timestamp", "auto_dispose"])

    logger.info(f"Updated {success}/{len(pending_orders)} orders in the database")
    