import logging

from django.utils import timezone

from ..base import BaseService


class UploadService(BaseService):
    def __init__(self, logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initialize the UploadService with a logger and a requests' session.
        """
        super().__init__(logger)
        self.__base_url = 'https://walrus.ninjavan.co/vn'

    def __signed_url(self, route_id: int, waypoint_id: int) -> tuple:
        """
        Get a signed URL for uploading a photo.

        Returns:
            Tuple[int, dict]: A tuple containing the status code and the signed URL.
        """
        payload = {
            "route_id": route_id,
            "waypoint_id": waypoint_id
        }
        url = f"{self.__base_url}/driver/1.0/photos/signed-url/upload"
        return self.make_request(url, method='POST', payload=payload)

    def __google_upload(self, signed_url: str, file_path: str = None, content: bytes = None) -> tuple:
        """
        Upload a photo to Google Cloud Storage.

        Returns:
            Tuple[int, dict]: A tuple containing the status code and the response data.
        """
        if not file_path and not content:
            return 400, {'error': 'No file path or content provided.'}

        if file_path:
            try:
                with open(file_path, 'rb') as file:
                    data = file.read()
            except FileNotFoundError:
                return 404, {'error': 'File not found.'}

        if content:
            data = content

        return self.make_request(signed_url, method='PUT', data=data)

    def upload_photo(self, route_id: int, waypoint_id: int, photo_path: str = None, content: bytes = None) -> tuple:

        if not photo_path and not content:
            return 400, {'error': 'No photo path or content provided.'}

        # Get a signed URL for uploading the photo
        status_code, response = self.__signed_url(route_id, waypoint_id)
        if status_code != 200:
            return status_code, response

        signed_url = response['data'].get('signed_url')
        file_path = response['data'].get('file_path')
        bucket = response['data'].get('bucket')

        # Upload the photo to Google Cloud Storage
        status_code, response = self.__google_upload(signed_url, photo_path, content)
        if status_code != 200:
            return status_code, response

        # Upload to NJV system
        url = f"{self.__base_url}/driver/1.0/photos"
        payload = {
            "bucket": f"{bucket}",
            "commit_date": int(timezone.now().timestamp()) * 1000,
            "file_path": f"{file_path}",
            "route_id": route_id,
            "signed_url": f"{signed_url}",
            "taken_at": int(timezone.now().timestamp()) * 1000,
            "waypoint_id": waypoint_id
        }
        return self.make_request(url, method='POST', payload=payload)
