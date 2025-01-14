import logging
from datetime import datetime, timedelta

from requests.exceptions import HTTPError, RequestException

from opv2.base.wms import WMSBin
from opv2.services import WMSService

logger = logging.getLogger(__name__)


def wms_putaway():
    """
        Process :

                1. Load orders automatically ASN Uploaded on WMS
                2. Putaway SHEIN orders
    """

    # Load SHEIN ASN Uploaded orders within 2 days ago
    wms = WMSService()
    to_putaway = []
    try:
        code_asn, response_asn = wms.load_asn_orders(
            asn_from=datetime.now() - timedelta(days=2),
            asn_to=datetime.now()
        )
        current_asn_uploaded = response_asn.get("parcels")
        if not current_asn_uploaded:
            logger.info("No ASN Uploaded orders to putaway")
            return
        shein_asn_uploaded = [
            {
                "tracking_id": order["tracking_id"],
                "global_shipper_id": order["global_shipper_id"]
            }
            for order in current_asn_uploaded
            if order["global_shipper_id"] == 7512979
        ]
        if not shein_asn_uploaded:
            logger.info("No SHEIN orders to putaway")
            return
        logger.info(f"Found SHEIN {len(shein_asn_uploaded)} orders to putaway")
        to_putaway.extend(shein_asn_uploaded)
    except (HTTPError, RequestException) as request_error:
        logger.error(f"Request error when load ASN orders from WMS Service : {request_error}")
        raise request_error
    except Exception as e:
        logger.error(f"Error when load ASN orders from WMS Service: {e}")
        raise e

    # Putaway orders
    code_putaway, response_putaway = wms.putaway_orders(
        tracking_ids=[order["tracking_id"] for order in to_putaway],
        bin=WMSBin
    )
    if code_putaway != 200:
        logger.error(f"Error when putaway orders: {response_putaway}")
        return

    logger.info(f"Successfully putaway {len(response_putaway)} orders")
