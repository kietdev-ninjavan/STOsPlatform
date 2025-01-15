import logging
from datetime import datetime

from simple_history.utils import bulk_create_with_history

from metabase.client import MetabaseClient
from opv2.base.wms import WMSAction
from opv2.services import WMSService
from stos.utils import configs
from .upload_picklist import wms_upload_picklist
from ..models import ReshipOrders, OrigOrders

logger = logging.getLogger(__name__)


def wms_bulk_reship():
    """
        Process :

                1. Get orders from Metabase Bulk Reship daily
                2. Upload picklist : Status change "IN_WAREHOUSE" to "PICK_REQUESTED"
                3. Download picklist : Status change "PICK_REQUESTED" to "PENDING_PICK"
                4. Pick orders
                5. Pack orders
                6. Update to DB
    """

    # Get orders from Metabase Bulk Reship daily
    source = metabase_bulk_reship()
    if not source:
        logger.warning("No order found to bulk reship")
        return

    # Upload & Download picklist
    tracking_ids = [value["tracking_id"] for value in source]
    picklist = wms_upload_picklist(orders=tracking_ids)
    if not picklist:
        logger.warning("No order uploaded to picklist")
        return

    success_uploaded = [
        order["tracking_id"]
        for order in picklist
        if order["upload_picklist_status"] == "Success"
    ]

    logger.info(f"Successfully upload picklist {len(success_uploaded)} orders")

    # Pick orders
    wms = WMSService()
    code_pick, response_pick = wms.pick_orders(tracking_ids=success_uploaded)
    if code_pick != 200:
        logger.error(f"Unable to pick RESHIP orders : {response_pick}")
        logger.warning("STOP AT PICK PROCESS!")
        return

    success_picked = response_pick.get("success")
    failed_picked = response_pick.get("failed")
    logger.info(f"Pick : Success {len(success_picked)} orders, Failed {len(failed_picked)} orders")

    # Create reship session
    code_session, reship_session = wms.create_session(action=WMSAction.reship)
    logger.info(f"Reship's Session created : {reship_session}")

    # Create reship bag
    code_bag, reship_bag = wms.create_bag()
    logger.info(f"Reship's Bag created : {reship_bag}")

    # Pack orders
    code_pack, response_pack = wms.pack_orders(
        tracking_ids=success_picked,
        action=WMSAction.reship,
        session=reship_session,
        bag=reship_bag
    )
    if code_pack != 200:
        logger.error(f"Unable to pick RESHIP orders : {response_pack}")
        logger.warning("STOP AT PACK PROCESS!")
        return

    success_packed = response_pack.get("success")
    failed_packed = response_pack.get("failed")
    logger.info(f"Pack : Success {len(success_packed)} orders, Failed {len(failed_packed)} orders")

    # Update to DB
    if success_packed:
        new_record = []
        retrieve_orders = OrigOrders.objects.filter(tracking_id__in=success_picked)
        weights = [
            {value.tracking_id: value.weight}
            for value in retrieve_orders
        ]
        for index, tracking_id in success_packed:
            code_info, wms_info = wms.load_order_by_tracking_id(tracking_id)
            try:
                new_record.append(
                    ReshipOrders(
                        date_input=datetime.today().strftime("%Y-%m-%d"),
                        tracking_id=tracking_id,
                        bag_name=wms_info.get("bag_name"),
                        bag_id=wms_info.get("bag_id"),
                        session_id=wms_info.get("session_id"),
                        weight=weights[tracking_id]
                    )
                )
            except Exception as e:
                logger.error(f"Error when creating new record: Row {index + 1} {e}")
        if new_record:
            creator = bulk_create_with_history(new_record, ReshipOrders)
            logger.info(f"Created {len(creator)} new records")
        else:
            logger.info("No new records to add to the database")

    # Close session
    code_close, response_close = wms.close_session(reship_session.get("id"))
    if code_close == 200:
        logger.info(f'Closed session {reship_session.get("id")}')
    else:
        logger.error(f'Fail to close session {reship_session.get("id")}')


def metabase_bulk_reship():
    """
        Get orders from Metabase Bulk Reship daily

    Returns:
        List[dict] : A list of dict response content.
    """

    shein_vn_bulk_reship_question_id = configs.get("SHEIN_VN_BULK_RESHIP_QUESTION_ID")
    mtb = MetabaseClient()
    return mtb.execute_question(shein_vn_bulk_reship_question_id)
