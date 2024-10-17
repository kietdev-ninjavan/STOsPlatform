import logging
from typing import List, Optional

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from ..dto import FileDTO
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

    def get_file_info(self, file_id: str) -> FileDTO:
        """Fetch file information, including folder ID (parents), and return it as a FileDTO."""
        try:
            # Use Drive API v3 to get the file metadata
            file_metadata = self.drive_service.files().get(fileId=file_id,
                                                           fields='id, parents, name, mimeType').execute()
            return FileDTO.from_dict(file_metadata)
        except HttpError as e:
            self.__logger.error(f"Failed to fetch file info: {e}")
            raise Exception(f"Failed to fetch file info: {e}")

    def convert_file_to_google_sheet(self, file_id: str, parent_folders: Optional[List[str]] = None) -> FileDTO:
        """
        Converts an existing .xlsx file in Google Drive to Google Sheets and returns the new file as a FileDTO.

        :param file_id: The ID of the .xlsx file to convert.
        :param parent_folders: The folders where the file is located.
        :return: FileDTO of the newly converted Google Sheets file.
        """
        try:
            # Define the metadata for the new Google Sheets file
            file_metadata_for_conversion = {
                'mimeType': 'application/vnd.google-apps.spreadsheet',
                'parents': parent_folders or []
            }

            # Use Drive API v3 to copy and convert the file
            converted_file = self.drive_service.files().copy(
                fileId=file_id,
                body=file_metadata_for_conversion
            ).execute()

            # Create a FileDTO for the newly created Google Sheets file
            gs_file_dto = FileDTO.from_dict({
                'id': converted_file['id'],
                'name': converted_file['name'],
                'mimeType': 'application/vnd.google-apps.spreadsheet',
                'parents': parent_folders
            })

            self.__logger.info(f"File '{file_id}' successfully converted to Google Sheets (ID: {gs_file_dto.file_id}).")
            return gs_file_dto

        except HttpError as e:
            self.__logger.error(f"Failed to convert file to Google Sheets: {e}")
            raise Exception(f"Failed to convert file to Google Sheets: {e}")

    def get_file_by_name(self, file_name: str) -> List[FileDTO]:
        """Fetch files' metadata based on a substring match in the name and return them as a list of FileDTOs."""
        try:
            query = f"name contains '{file_name}' and trashed = false"
            results = self.drive_service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, parents, mimeType)',
                pageSize=10
            ).execute()

            files = results.get('files', [])

            if not files:
                self.__logger.info(f"No files found with name containing '{file_name}'.")
                return []

            # Convert raw file data to FileDTO objects
            file_dtos = [FileDTO.from_dict(file) for file in files]

            self.__logger.info(f"Files found with name containing '{file_name}': {file_dtos}")
            return file_dtos

        except HttpError as e:
            self.__logger.error(f"Failed to search for files by name: {e}")
            raise Exception(f"Failed to search for files by name: {e}")

    def get_or_convert_to_google_sheet(self, file_name: str) -> Optional[FileDTO]:
        """
        Fetch a file by name. If it's an .xlsx file, convert it to Google Sheets.
        If it's already a Google Sheets file, return the FileDTO.
        Otherwise, return None if no valid file is found.

        :param file_name: The name of the file to search for.
        :return: FileDTO for the Google Sheets file or None if no valid file is found.
        """
        try:
            # Search for files that match the given name
            files = self.get_file_by_name(file_name)

            if not files:
                self.__logger.info(f"No file found with the name '{file_name}'")
                return None

            # Loop through matching files and handle based on file type
            for file in files:
                if file.extension == 'gs':
                    self.__logger.info(f"Found Google Sheet with name '{file_name}' (ID: {file.file_id})")
                    return file  # Return the FileDTO for the Google Sheets file

                if file.extension == 'xlsx':
                    self.__logger.info(
                        f"Found Excel file '{file_name}' (ID: {file.file_id}), converting to Google Sheets.")
                    gs_file_dto = self.convert_file_to_google_sheet(file.file_id,
                                                                    file.parents)  # Convert to Google Sheets
                    self.__logger.info(f"Successfully converted to Google Sheet (ID: {gs_file_dto.file_id})")
                    return gs_file_dto  # Return the FileDTO for the converted Google Sheets file

            self.__logger.info(f"No valid gs or xlsx file found with the name '{file_name}'")
            return None

        except Exception as e:
            self.__logger.error(f"Error in get_or_convert_to_google_sheet: {e}")
            raise Exception(f"Error in get_or_convert_to_google_sheet: {e}")
