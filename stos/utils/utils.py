import os
import textwrap
from datetime import datetime
from io import BytesIO
from itertools import islice
from typing import Dict, Optional
from typing import List, Any, Generator, Tuple
from unicodedata import normalize

from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
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


def parse_datetime(date_string: str, custom_formats: Optional[List[str]] = None) -> datetime | None:
    if not date_string:
        return None
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


def swap_day_month_if_different(date: datetime) -> datetime:
    """
    Swaps the day and month in a datetime object if the month is different from the current month.
    :param date:
    :return:
    """
    current_month = datetime.now().month
    # Swap only if the input month is different from the current month
    if date.month < current_month:
        try:
            # Attempt to swap day and month
            return date.replace(day=date.month, month=date.day)
        except ValueError:
            # Return original date if swap results in an invalid date
            return date
    return date


def create_zns_image(data: Dict[str, Any], cell_height: int = 80, header_width: int = 260,
                     cell_width: int = 540, font_size: int = 20,
                     label_color: Tuple[int, int, int, int] = (94, 94, 94, 255),
                     text_color: Tuple[int, int, int, int] = (0, 0, 0, 255),
                     background_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
                     border_color: Tuple[int, int, int, int] = (224, 224, 224, 255)) -> bytes:
    """
    Generates a ZNS image displaying provided field labels and values.

    Args:
        data (Dict[str, Any]): Dictionary of labels and values to display.
        cell_height (int, optional): Height of each cell. Defaults to 80.
        header_width (int, optional): Width of label (header) column. Defaults to 260.
        cell_width (int, optional): Width of value column. Defaults to 540.
        font_size (int, optional): Font size for text. Defaults to 20.
        label_color (Tuple[int, int, int, int], optional): RGBA color for labels. Defaults to gray.
        text_color (Tuple[int, int, int, int], optional): RGBA color for values. Defaults to black.
        background_color (Tuple[int, int, int, int], optional): RGBA background color. Defaults to white.
        border_color (Tuple[int, int, int, int], optional): RGBA color for borders. Defaults to light gray.

    Returns:
        bytes: Binary data of the generated image in JPEG format.

    Raises:
        FileNotFoundError: If font files are not found in the specified directory.
        IOError: If there is an issue creating or saving the image.
    """
    # Paths to font files
    font_label_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Roboto-Medium.ttf')
    font_text_path = os.path.join(settings.BASE_DIR, 'static', 'fonts', 'Roboto-Light.ttf')
    print(font_label_path)
    try:
        font_label = ImageFont.truetype(font_label_path, font_size)
        font_text = ImageFont.truetype(font_text_path, font_size)
    except IOError as e:
        raise FileNotFoundError("Font files not found in the specified directory") from e

    # Calculate image dimensions
    num_rows = len(data)
    image_width = header_width + cell_width
    image_height = cell_height * num_rows

    # Create image and draw object
    image = Image.new('RGBA', (image_width, image_height), background_color)
    draw = ImageDraw.Draw(image)

    # Draw borders
    for i in range(num_rows + 1):
        y = i * cell_height
        draw.line([(0, y), (image_width, y)], fill=border_color, width=2)
    draw.line([(header_width, 0), (header_width, image_height)], fill=border_color, width=2)

    # Draw labels and values
    for row_index, (label, value) in enumerate(data.items()):
        # Label position
        label_x = 10
        label_y = row_index * cell_height + 10
        draw.text((label_x, label_y), label, font=font_label, fill=label_color)

        # Value position (wrapped text)
        value_x = header_width + 10
        value_y = row_index * cell_height + 10
        wrapped_text = textwrap.fill(str(value), width=40)
        draw.text((value_x, value_y), wrapped_text, font=font_text, fill=text_color)

    # Save to binary
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)  # Reset position for reading

    return output.getvalue()
