import logging

from django.utils import timezone

from ..base import BaseService


class PickupService(BaseService):
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the UploadService with a logger and a requests' session.
        """
        super().__init__(logger)
        self.__base_url = 'https://walrus.ninjavan.co'

    def pickup_fail(self, route_id: int, waypoint_id: int, contact: str, file_path: str, photo_url: str,
                    failure_reason_id: int, shipper_id: int, job_id: int, physical_items: list) -> tuple:
        url = f"{self.__base_url}/driver/2.2/routes/{route_id}/waypoints/{waypoint_id}/pods"
        current_time = timezone.now()
        payload = {
            "commit_date": int(current_time.timestamp() * 1000),
            "contact": contact,
            "delivered_quantity": 0,
            "images": [
                {
                    "bucket": "nv-prod-services",
                    "file_path": file_path,
                    "image_type": "WAYPOINT_PHOTO",
                    "url": photo_url
                }
            ],
            "imei": self.phone_imei,
            "jobs": [
                {
                    "action": "FAIL",
                    "discount_amount": 0.0,
                    "failure_reason_id": failure_reason_id,
                    "global_shipper_id": shipper_id,
                    "id": job_id,
                    "mode": "PICK_UP",
                    "physical_items": physical_items,
                    "status": "PENDING",
                    "total_collected_amount": 0.0,
                    "type": "PICKUP_APPOINTMENT"
                }
            ],
            "last_sync_at": int((current_time + timezone.timedelta(seconds=5)).timestamp() * 1000),
            "latitude": 14.0583,
            "longitude": 108.2772,
            "num_photos": 1,
            "num_photos_to_upload": 0,
            "pickup_quantity": 0,
            "route_date": int(current_time.timestamp() * 1000),
            "submission_count": 0
        }

        return self.make_request(url, method='PUT', payload=payload)
