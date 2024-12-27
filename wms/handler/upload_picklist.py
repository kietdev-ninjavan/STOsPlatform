import logging
from typing import List
from opv2.base.wms import WMSAction
from opv2.services import WMSService
from requests.exceptions import HTTPError, RequestException

logger = logging.getLogger(__name__)

def wms_upload_picklist(orders: List[str]) -> List[dict]:
    """
        ***Only use for BULK RESHIP processs
        Process: 
            Upload picklist to WMS : Status change IN_WAREHOUSE -> PICK_REQUESTED
            Download picklist : Status change PICK_REQUESTED -> PENDING_PICK
        
        Args: 
            orders : list of orders from Metabase Bulk Reship daily
    """
    wms = WMSService()
    pick_action = WMSAction.reship
    try: 
        code, response = wms.upload_picklist(orders, pick_action)
        if code != 200:
            logger.error(f"Error when upload picklist to WMS Service: {response}")
            return []
        logger.info(f"Successfully upload picklist {len(orders)} orders to WMS Service")
        return response
    except (HTTPError, RequestException) as request_error:
        logger.error(f"Request error when upload picklist to WMS Service : {request_error}")
        raise request_error
    except Exception as e:
        logger.error(f"Error when upload picklist to WMS Service: {e}")
        raise e
