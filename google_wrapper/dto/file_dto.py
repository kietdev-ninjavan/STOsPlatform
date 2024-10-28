from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class FileDTO:
    file_id: str
    name: str
    mime_type: str
    parents: List[str] = field(default_factory=list)

    MIME_TYPE_EXTENSION_MAP: Dict[str, str] = field(default_factory=lambda: {
        'application/vnd.google-apps.spreadsheet': 'gs',  # Google Sheet
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',  # Excel file
        'application/zip': 'zip',  # Zip file
        'application/pdf': 'pdf',  # PDF file
        'image/jpeg': 'jpg',  # JPEG image
        'image/png': 'png',  # PNG image
        'text/plain': 'txt',  # Text file
        # Add more MIME types as needed
    })

    @property
    def extension(self) -> str:
        """Return the file extension based on the MIME type."""
        return self.MIME_TYPE_EXTENSION_MAP.get(self.mime_type, 'unknown')  # Return 'unknown' for unknown MIME types

    def __repr__(self):
        return (f"FileDTO(file_id='{self.file_id}', name='{self.name}', "
                f"mime_type='{self.mime_type}', parents={self.parents}, extension='{self.extension}')")

    @staticmethod
    def get_extension_from_mime(mime_type: str) -> str:
        """Static method to get the extension from a MIME type."""
        mime_type_extension_map = {
            'application/vnd.google-apps.spreadsheet': 'gs',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
            'application/zip': 'zip',
            'application/pdf': 'pdf',
            'image/jpeg': 'jpg',
            'image/png': 'png',
            'text/plain': 'txt',
            # Add more MIME types as needed
        }
        return mime_type_extension_map.get(mime_type, 'unknown')

    @classmethod
    def from_dict(cls, file_dict: dict):
        """Create a FileDTO instance from a dictionary."""
        return cls(
            file_id=file_dict.get('id'),
            name=file_dict.get('name'),
            mime_type=file_dict.get('mimeType'),
            parents=file_dict.get('parents', [])
        )
