import os
from datetime import datetime
from typing import List, Any, Dict, Optional
from unicodedata import normalize


def chunk_list(input_list: List[Any], chunk_size: int = 1000) -> List[List[Any]]:
    """
    Splits a list into smaller lists (chunks) of a specified size.

    Args:
        input_list (List[Any]): The list to be chunked.
        chunk_size (int): The size of each chunk. Defaults to 1000.

    Returns:
        List[List[Any]]: A list of lists, where each inner list is a chunk of the original list.

    Raises:
        ValueError: If chunk_size is less than 1.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be greater than 0")

    return [input_list[i:i + chunk_size] for i in range(0, len(input_list), chunk_size)]


def chunk_dict(input_dict: Dict[Any, Any], chunk_size: int = 1000) -> List[Dict[Any, Any]]:
    """
    Splits a dictionary into smaller dictionaries (chunks) of a specified size.

    Args:
        input_dict (dict): The dictionary to be chunked.
        chunk_size (int): The size of each chunk. Defaults to 1000.

    Returns:
        List[dict]: A list of dictionaries, where each dictionary is a chunk of the original dictionary.

    Raises:
        ValueError: If chunk_size is less than 1.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be greater than 0")

    return [{k: input_dict[k] for k in list(input_dict.keys())[i:i + chunk_size]}
            for i in range(0, len(input_dict), chunk_size)]


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
        "%d-%m-%Y %H:%M:%S"  # Date and time
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
