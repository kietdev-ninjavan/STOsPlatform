import logging

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..models import ServiceAccount


class GoogleDriveService:
    def __init__(self, service_account: ServiceAccount, logger: logging.Logger = logging.getLogger(__name__)):
        self.__logger = logger
        """Initialize the GoogleDriveService using a GoogleServiceAccount model instance."""
        try:
            # Load credentials and create the Drive API client (v3)
            scopes = ['https://www.googleapis.com/auth/drive']
            credentials = Credentials.from_service_account_info(service_account.to_dict(), scopes=scopes)
            self.drive_service = build('drive', 'v3', credentials=credentials)
        except HttpError as e:
            raise Exception(f"Failed to authenticate Google Drive API: {e}")

    def get_file_info(self, file_id: str):
        """Fetch file information, including folder ID (parents)."""
        try:
            # Use Drive API v3 to get the file metadata
            file_metadata = self.drive_service.files().get(fileId=file_id, fields='id, parents').execute()
            return file_metadata
        except HttpError as e:
            self.__logger.error(f"Failed to fetch file info: {e}")
            raise Exception(f"Failed to fetch file info: {e}")

    def convert_file_to_google_sheet(self, file_id: str):
        """Converts an existing .xlsx file in Google Drive to Google Sheets and keeps it in the same folder."""
        try:
            # Get file metadata to determine its parent folder
            file_metadata = self.get_file_info(file_id)
            parent_folders = file_metadata.get('parents', [])

            # Define the metadata for the new Google Sheets file
            file_metadata_for_conversion = {
                'mimeType': 'application/vnd.google-apps.spreadsheet',
                'parents': parent_folders
            }

            # Use Drive API v3 to copy and convert the file
            converted_file = self.drive_service.files().copy(
                fileId=file_id,
                body=file_metadata_for_conversion
            ).execute()

            self.__logger.info(f"File '{file_id}' successfully converted to Google Sheets and kept in the same folder.")
            return converted_file['id']  # Return the new Google Sheets ID
        except HttpError as e:
            self.__logger.error(f"Failed to convert file to Google Sheets: {e}")
            raise Exception(f"Failed to convert file to Google Sheets: {e}")
