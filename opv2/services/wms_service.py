import logging
from datetime import datetime
from random import choice
from typing import List, Tuple, Dict

from django.utils import timezone
from requests.exceptions import (
    HTTPError,
    ConnectionError,
    RequestException,
    Timeout
)
from retry import retry

from opv2.base.wms import WMSBin, WMSOrderStatus, WMSAction
from ..base import WMSBaseService

logger = logging.getLogger(__name__)


class WMSService(WMSBaseService):
    """
        A class for making API requests to the WMS Service.
    """

    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the WMSService with a logger and a requests" session.
        """
        super().__init__(logger)
        self._logger = logger
        self._base_url = "https://api.ninjavan.co/global/wms"

    def load_asn_orders(self,
                        asn_from: datetime,
                        asn_to: datetime,
                        status: List[WMSOrderStatus] = [WMSOrderStatus.asn_uploaded.value],
                        limit: int = 1000) -> Tuple[int, dict]:

        url = f"{self._base_url}/parcels/filter"
        payload = {
            "system_id": "VN",
            "status": status,
            "limit": limit,
            "asn_upload_from": asn_from.strftime("%Y-%m-%d"),
            "asn_upload_to": asn_to.strftime("%Y-%m-%d"),
            "sort": "asn_uploaded_timestamp DESC"
        }

        return self.make_request(url, method="POST", payload=payload)

    def load_orders_by_status(self,
                              status: List[WMSOrderStatus],
                              limit: int = 1000) -> Tuple[int, dict]:
        """
        Load orders info by statuses from WMS

        Args:
            status (List[WMSOrderStatus]): List of WMS order statuses.
            limit (int, optional): Search limitation. Defaults to 1000.

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """

        url = f"{self._base_url}/parcels/filter"
        payload = {
            "system_id": "VN",
            "status": status,
            "limit": limit,
        }

        return self.make_request(url, method="POST", payload=payload)

    @retry(exceptions=(HTTPError, ConnectionError, Timeout, RequestException), tries=3, delay=2, backoff=2, jitter=(1, 3))
    def load_order_by_tracking_id(self, tracking_id: str) -> Tuple[int, dict]:
        """
        Load order info by tracking id from WMS

        Args:
            tracking_id (str): Tracking id to search

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """
        url = f"{self._base_url}/parcels/filter"
        payload = {
            "system_id": "VN",
            "tracking_id": tracking_id
        }

        return self.make_request(url, method="POST", payload=payload)

    def load_bins(self) -> Tuple[int, dict]:
        """
        Load bins info from WMS

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """

        url = f"{self._base_url}/bins?system_id=VN"
        return self.make_request(url, method="GET")

    @retry(exceptions=(HTTPError, ConnectionError, Timeout, RequestException), tries=3, delay=2, backoff=2, jitter=(1, 3))
    def create_bag(self) -> Tuple[int, dict]:
        """
        Create bag from WMS

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """

        url = f"{self._base_url}/bags"
        return self.make_request(url, method="POST", payload={})

    @retry(exceptions=(HTTPError, ConnectionError, Timeout, RequestException), tries=3, delay=2, backoff=2, jitter=(1, 3))
    def create_session(self, action: str) -> Tuple[int, dict]:
        """
        Create session from WMS

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """

        url = f"{self._base_url}/sessions/create"
        return self.make_request(url, method="POST", payload={"type": action})

    @retry(exceptions=(HTTPError, ConnectionError, Timeout, RequestException), tries=3, delay=2, backoff=2, jitter=(1, 3))
    def close_session(self, session_id: int) -> Tuple[int, dict]:
        """
        Close session from WMS

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """

        url = f"{self._base_url}/sessions/close/{session_id}"
        return self.make_request(url, method="POST")

    @retry(exceptions=(HTTPError, ConnectionError, Timeout, RequestException), tries=3, delay=2, backoff=2, jitter=(1, 3))
    def putaway_orders(self,
                       tracking_ids: List[str],
                       bin: WMSBin) -> Tuple[int, List[Dict]]:
        """
        Putaway orders from WMS

        Args:
            tracking_ids (List[str]): List of tracking ids to putaway
            bin (WMSBin): Bin for storage

        Returns:
            Tuple[int, dict]: A tuple containing status code and list of putaway response.
        """

        if not tracking_ids:
            return 500, {"message": "No order found to putaway"}

        url = f"{self._base_url}/parcels/putawaybulk"
        bin_retrieve = choice(bin.choices)
        logger.info(f'Bin chosen : {bin_retrieve[1]} - id : {bin_retrieve[0]}')
        payload = [
            {
                "system_id": "VN",
                "tracking_id": tracking_id,
                "bin_id": bin_retrieve[0],
                "problematic_reason": ""
            }
            for tracking_id in tracking_ids
        ]

        code, response = self.make_request(url, method="POST", payload=payload)
        response = [{"tracking_id": key, "putaway_status": value} for key, value in response.items()]

        return code, response

    @retry(exceptions=(HTTPError, ConnectionError, Timeout, RequestException), tries=3, delay=2, backoff=2, jitter=(1, 3))
    def upload_picklist(self,
                        tracking_ids: List[str],
                        pick_action: WMSAction) -> Tuple[int, List[Dict]]:
        """
        Upload picklist to WMS
            including Download picklist step ( required to change status to PENDING_PICK )

        Args:
            tracking_ids (List[str]): List of tracking ids to upload picklist
            pick_action (WMSAction): Pick action for upload picklist

        Returns:
            Tuple[int, dict]: A tuple containing status code and response data.
        """

        if not tracking_ids:
            return 500, {"message": "No order found to upload picklist"}

        url = f"{self._base_url}/parcels/upload"
        payload = [
            {
                "system_id": "VN",
                "tracking_id": tracking_id,
                "pick_action": pick_action.value,
                "relabel_tracking_id": "",
                "picklist_upload_timestamp": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%SSZ")
            }
            for tracking_id in tracking_ids
        ]

        code, response = self.make_request(url, method="POST", payload=payload)
        response = [
            {
                "tracking_id": key,
                "upload_picklist_status": value
            }
            for key, value in response.items()
        ]

        """
            Need to download picklist step for changing status from PICK_REQUESTED to PENDING_PICK
            Not use DOWNLOAD response
        """
        url_down = f"{self._base_url}/parcels/downloadcsv/VN"
        code_down, response_down = self.make_request(url_down, method="GET")

        return code, response

    @retry(exceptions=(HTTPError, ConnectionError, Timeout, RequestException), tries=3, delay=2, backoff=2, jitter=(1, 3))
    def pick_orders(self, tracking_ids: List[str]) -> Tuple[int, Dict]:
        """
        Pick orders from WMS

        Args:
            tracking_ids (List[str]): List of tracking ids to pick

        Returns:
            Tuple[int, dict]: A tuple containing status code and dict of pick response.
        """

        if not tracking_ids:
            return 500, {"message": "No order found to pick"}

        url = f"{self._base_url}/parcels/pick"
        success = []
        failed = []
        payload = [
            {
                "system_id": "VN",
                "tracking_id": tracking_id
            }
            for tracking_id in tracking_ids
        ]
        for order in payload:
            code, response = self.make_request(url, method="POST", payload=order)
            if code == 200:
                success.append(order.get("tracking_id"))
            else:
                failed.append(order.get("tracking_id"))

        result = {"sucesss": success, "failed": failed}

        return code, result

    @retry(exceptions=(HTTPError, ConnectionError, Timeout, RequestException), tries=3, delay=2, backoff=2, jitter=(1, 3))
    def pack_orders(self,
                    tracking_ids: List[str],
                    action: WMSAction,
                    session: dict,
                    bag: dict = None
                    ) -> Tuple[int, dict]:
        """
        Pack orders from WMS

        Args:
            tracking_ids (List[str]): List of tracking ids to pack
            action (WMSAction): Action to pack
            session (dict): Session to pack
            bag (dict, optional): Bag to pack - not use for Relabel

        Returns:
            Tuple[int, dict]: A tuple containing status code and dict of pack response.
        """
        if not tracking_ids:
            return 500, {"message": "No order found to pack"}

        if action.action == "RELABEL" and bag:
            return 500, {"message": "Bag must be None for Relabel action"}

        url = f"{self._base_url}{action.path}"
        bag_id = bag.get("id") if bag else None
        session_id = session.get("id")
        success = []
        failed = []

        payload = [
            {"system_id": "VN", "tracking_id": tracking_id, "session_id": session_id, "bag_id": bag_id}
            if bag_id else {"system_id": "VN", "tracking_id": tracking_id, "session_id": session_id}
            for tracking_id in tracking_ids
        ]

        for order in payload:
            code, response = self.make_request(url, method="POST", payload=order)
            if code == 200:
                success.append(order.get("tracking_id"))
            else:
                failed.append(order.get("tracking_id"))

        result = {"sucesss": success, "failed": failed}

        return code, result
