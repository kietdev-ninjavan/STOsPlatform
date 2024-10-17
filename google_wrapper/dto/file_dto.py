from typing import List, Optional


# DTO Class for File Metadata with MimeType and Extension Mapping
class FileDTO:
    MIME_TYPE_EXTENSION_MAP = {
        'application/vnd.google-apps.spreadsheet': 'gs',  # Google Sheet
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',  # Excel file
        'application/zip': 'zip',  # Zip file
        'application/pdf': 'pdf',  # PDF file
        'image/jpeg': 'jpg',  # JPEG image
        'image/png': 'png',  # PNG image
        'text/plain': 'txt',  # Text file
        # Add more MIME types as needed
    }

    def __init__(self, file_id: str, name: str, mime_type: str, parents: Optional[List[str]] = None):
        self.file_id = file_id
        self.name = name
        self.mime_type = mime_type
        self.parents = parents or []

    @property
    def extension(self) -> str:
        """Return the file extension based on the MIME type."""
        return self.MIME_TYPE_EXTENSION_MAP.get(self.mime_type, '')  # Default to empty string if MIME type is unknown

    def __repr__(self):
        return f"FileDTO(file_id='{self.file_id}', name='{self.name}', mime_type='{self.mime_type}', parents={self.parents}, extension='{self.extension}')"

    @classmethod
    def from_dict(cls, file_dict: dict):
        """Create a FileDTO instance from a dictionary."""
        return cls(
            file_id=file_dict.get('id'),
            name=file_dict.get('name'),
            mime_type=file_dict.get('mimeType'),
            parents=file_dict.get('parents', [])
        )
