import os
from datetime import datetime
from itertools import islice
from typing import Dict, Optional
from typing import List, Any, Generator, Tuple
from unicodedata import normalize

from django.utils import timezone

from core.base.model import BaseModel


def chunk_list(input_list: List[Any], chunk_size: int = 1000) -> Generator[List[Any], None, None]:
    """
    Splits a list into smaller lists (chunks) of a specified size using a generator.

    Args:
        input_list (List[Any]): The list to be chunked.
        chunk_size (int): The size of each chunk. Defaults to 1000.

    Yields:
        Generator[List[Any], None, None]: A generator of lists, where each list is a chunk of the original list.

    Raises:
        ValueError: If chunk_size is less than 1.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be greater than 0")

    it = iter(input_list)
    while True:
        chunk = list(islice(it, chunk_size))
        if not chunk:
            break
        yield chunk


def chunk_dict(input_dict: Dict[Any, Any], chunk_size: int = 1000) -> Generator[Dict[Any, Any], None, None]:
    """
    Splits a dictionary into smaller dictionaries (chunks) of a specified size using a generator.

    Args:
        input_dict (Dict[Any, Any]): The dictionary to be chunked.
        chunk_size (int): The size of each chunk. Defaults to 1000.

    Yields:
        Generator[Dict[Any, Any], None, None]: A generator of dictionaries, where each dictionary is a chunk of the original dictionary.

    Raises:
        ValueError: If chunk_size is less than 1.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be greater than 0")

    it = iter(input_dict.items())
    while True:
        chunk = dict(islice(it, chunk_size))
        if not chunk:
            break
        yield chunk


def text_in_text(sub_text: str, main_text: str) -> bool:
    """
    Check if one text is found within another text, case-insensitive and normalized.

    Args:
        sub_text (str): The text to search for.
        main_text (str): The text to search within.

    Returns:
        bool: True if sub_text is found within main_text, False otherwise.
    """
    return normalize('NFC', sub_text.lower()) in normalize('NFC', main_text.lower())


def clear_temporary_file(file_path: str) -> None:
    """
    Delete a temporary file from the file system.

    Args:
        file_path (str): The path to the file to be deleted.

    Raises:
        Exception: If an unexpected error occurs during file deletion.
    """
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass  # File is already deleted or doesn't exist.
    except Exception as e:
        raise e


def parse_datetime(date_string: str, custom_formats: Optional[List[str]] = None) -> datetime:
    """
    Parses a date or datetime string into a datetime object using predefined or custom formats.

    Supported formats:
    - Date only: '%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d', '%d/%m/%Y', '%m-%d-%Y', '%d-%m-%Y', '%B %d, %Y'
    - Date and time: '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%Y/%m/%d %H:%M:%S',
                     '%d/%m/%Y %H:%M:%S', '%m-%d-%Y %H:%M:%S', '%d-%m-%Y %H:%M:%S'

    Args:
        date_string (str): The date or datetime string to parse.
        custom_formats (list, optional): A list of additional datetime formats to try.

    Returns:
        datetime: A datetime object parsed from the given string.

    Raises:
        ValueError: If the date string does not match any of the expected or custom formats.
    """
    # Default formats for date and datetime
    default_formats = [
        "%Y-%m-%d",  # Date only
        "%m/%d/%Y",  # Date only
        "%Y/%m/%d",  # Date only
        "%d/%m/%Y",  # Date only
        "%m-%d-%Y",  # Date only
        "%d-%m-%Y",  # Date only
        "%B %d, %Y",  # Date only (e.g., 'September 12, 2024')
        "%Y-%m-%d %H:%M:%S",  # Date and time
        "%m/%d/%Y %H:%M:%S",  # Date and time
        "%Y/%m/%d %H:%M:%S",  # Date and time
        "%d/%m/%Y %H:%M:%S",  # Date and time
        "%m-%d-%Y %H:%M:%S",  # Date and time
        "%d-%m-%Y %H:%M:%S",  # Date and time
        "%B %d, %Y %H:%M:%S",  # Date and time (e.g., 'September 12, 2024 14:30:00')
        "%Y-%m-%d %H:%M",  # Date and time without seconds
        "%m/%d/%Y %H:%M",  # Date and time without seconds
        "%Y/%m/%d %H:%M",  # Date and time without seconds
        "%d/%m/%Y %H:%M",  # Date and time without seconds
        "%m-%d-%Y %H:%M",  # Date and time without seconds
        "%d-%m-%Y %H:%M",  # Date and time without seconds
        "%Y-%m-%dT%H:%M:%SZ",  # Date and time in ISO 8601 format
        "%Y-%m-%dT%H:%M:%S.%fZ",  # Date and time in ISO 8601 format with microseconds
    ]

    # Add custom formats if provided
    if custom_formats:
        default_formats.extend(custom_formats)

    for fmt in default_formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    raise ValueError(f"Date string '{date_string}' does not match any of the expected formats.")


def check_record_change(existing_record: BaseModel, updated_record: BaseModel, excluded_fields=None):
    """
    Compares fields between two model instances, updating fields in the existing_record if
    they differ from the updated_record. Excludes specific fields from comparison and updates
    the 'updated_date' if any changes are made.

    :param existing_record: The current model instance to update.
    :param updated_record: The model instance with new values to compare against.
    :param excluded_fields: Optional list of fields to exclude from comparison.
    :return: Tuple (is_updated: bool, updated_record: ModelInstance, updated_fields: list).
    """
    if not isinstance(existing_record, type(updated_record)):
        raise ValueError("Both instances must be of the same model type.")

    is_updated = False
    updated_fields = []

    # Exclude default fields and the primary key from comparison
    excluded_fields = set(excluded_fields or {})
    excluded_fields.update({'created_date', 'updated_date', 'delete_at', existing_record._meta.pk.name})

    # Get relevant fields (excluding many-to-many, one-to-many, and excluded fields)
    fields = [f.name for f in existing_record._meta.get_fields()
              if not (f.many_to_many or f.one_to_many or f.name in excluded_fields)]

    # Compare field values between the two records
    for field in fields:
        current_value = getattr(existing_record, field, None)
        new_value = getattr(updated_record, field, None)

        if current_value != new_value:
            setattr(existing_record, field, new_value)
            updated_fields.append(field)
            is_updated = True

    # Update the 'updated_date' if any fields were modified
    if is_updated:
        existing_record.updated_date = timezone.now()

    return is_updated, existing_record, updated_fields


def paginate_count(total_count: int, page_size: int) -> List[Tuple[int, int]]:
    """
    Generates pagination information based on a total count and page size.

    Args:
        total_count (int): The total number of items.
        page_size (int): The number of items per page.

    Returns:
        List[Tuple[int, int]]: A list of tuples, where each tuple contains the page number and the size of that page.
    """
    pages = []
    total_pages = (total_count + page_size - 1) // page_size

    for page_num in range(1, total_pages + 1):
        # Calculate size for the current page
        if page_num == total_pages and total_count % page_size != 0:
            page_size_actual = total_count % page_size  # Last page might have fewer items
        else:
            page_size_actual = page_size

        pages.append((page_num, page_size_actual))

    return pages
