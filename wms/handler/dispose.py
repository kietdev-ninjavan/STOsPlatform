import logging
from opv2.base.wms import WMSBin, WMSOrderStatus,WMSAction
from opv2.services import WMSService

logger = logging.getLogger(__name__)

def wms_dispose():
    wms = WMSService()
    code_pp, response_pp = wms.load_orders_by_status(status=[WMSOrderStatus.pending_pick.value])
    pending_pick_orders = response_pp.get("parcels")
    
    current_bin_ids = [
        bin[0] for bin in WMSBin.choices
    ]
    
    shein_orders = [
        order["tracking_id"]
        for order in pending_pick_orders
        if order["global_shipper_id"] == 7512979 
        and order["pick-action"] == "DISPOSE"
        and order["bin_id"] in current_bin_ids
    ]
    
    if not shein_orders: 
        logger.info("No SHEIN orders to dispose")
        logger.warning("STOP AT COLLECT PENDING PICK PROCESS!")
        return
    
    logger.info(f"Found SHEIN {len(shein_orders)} orders to dispose")
    code_pick, response_pick = wms.pick_orders(tracking_ids=shein_orders)
    if code_pick != 200: 
        logger.error(f"Unable to pick DISPOSE orders : {response_pick}")
        logger.warning("STOP AT PICK PROCESS!")
        return
    
    success_picked = response_pick.get("success")
    failed_picked = response_pick.get("failed")
    logger.info(f"Successfully DISPOSE picked {len(success_picked)} orders")
    logger.info(f"Failed to DISPOSE pick {len(failed_picked)} orders")
    
    code_session , dispose_session = wms.create_session(action=WMSAction.dispose.value)
    logger.info(f"Dispose's Session created : {dispose_session}")
    
    code_pack , response_pack = wms.pack_orders(
        tracking_ids= success_picked,
        action= WMSAction.dispose.value,
        session= dispose_session
    )
    if code_pack != 200: 
        logger.error(f"Unable to pick DISPOSE orders : {response_pack}")
        logger.warning("STOP AT PACK PROCESS!")
        return
    
    success_packed = response_pack.get("success")
    failed_packed = response_pack.get("failed")
    logger.info(f"Successfully DISPOSE packed {len(success_packed)} orders")
    logger.info(f"Failed to DISPOSE pack {len(failed_packed)} orders")
    
    
    code_close, response_close = wms.close_session(dispose_session.get("id"))
    if code_close == 200:
        logger.info(f"Closed session {dispose_session.get("id")}")
    else:
        logger.error(f"Fail to close session {dispose_session.get("id")}")
    