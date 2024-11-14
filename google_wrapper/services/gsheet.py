import logging
from random import randint
from typing import Union, Tuple, Optional, List, Dict

import gspread
import pandas as pd
from gspread import utils
from gspread.exceptions import (
    APIError,
    SpreadsheetNotFound,
    WorksheetNotFound
)
from gspread_dataframe import get_as_dataframe, set_with_dataframe
from gspread_formatting import Color, CellFormat, format_cell_range
from oauth2client.service_account import ServiceAccountCredentials
from retry import retry

from ..models import ServiceAccount


class GoogleSheetService:
    """
    A service for interacting with Google Sheets using a provided Google service account.
    Supports operations like updating cells and columns, and formatting.

    Attributes:
        client: A gspread client authorized via Google service account.
        spreadsheet: The opened Google spreadsheet.
        logger: Logger for logging events and errors.
    """

    def __init__(self, service_account: ServiceAccount, spreadsheet_id: str,
                 logger: logging.Logger = logging.getLogger(__name__)):
        """
        Initializes the GoogleSheetService with a Google service account and spreadsheet ID.

        Args:
            service_account (ServiceAccount): The service account credentials.
            spreadsheet_id (str): The ID of the Google Spreadsheet.
            logger (logging.Logger, optional): Logger for logging events. Defaults to a logger for the current module.
        """
        self.__logger = logger
        self.__spreadsheet_id = spreadsheet_id
        try:
            # Load credentials and authorize the client
            scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account.to_dict(), scope)
            self.client = gspread.authorize(credentials)
        except APIError as e:
            raise Exception(f"Failed to authenticate Google Sheets API: {e}")

        try:
            # Open the spreadsheet
            self.__spreadsheet = self.client.open_by_key(spreadsheet_id)
            self.__name = self.__spreadsheet.title
            self.__logger.info(f"Opened spreadsheet '{self.__name}' ({self.__spreadsheet_id}).")
        except SpreadsheetNotFound:
            raise Exception(f"Spreadsheet with ID '{spreadsheet_id}' not found.")

    def __handle_api_error(self, error: APIError) -> None:
        """
        Internal method to handle API errors, specifically quota or permission-related issues.

        Args:
            error (APIError): The error to handle.

        Raises:
            APIError: Reraises the original error after logging.
        """
        self.__logger.error(f"API Error STT code: {error.response.status_code}")
        if error.response.status_code in [403, 429]:
            if error.response.status_code == 403:
                self.__logger.warning("Access forbidden: You do not have permission to access the resource.")
            elif error.response.status_code == 429:
                self.__logger.warning("Quota or rate limit exceeded: Too many requests.")
        raise error

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def __get_worksheet_by_gid(self, gid: int) -> gspread.Worksheet:
        """
        Retrieve a worksheet by its GID.

        Args:
            gid (int): The GID of the worksheet.

        Returns:
            gspread.Worksheet: The worksheet object.

        Raises:
            Exception: If worksheet is not found.
        """
        try:
            worksheet = self.__spreadsheet.get_worksheet_by_id(gid)
            self.__logger.info(f"Retrieved worksheet '{worksheet.title}' from spreadsheet '{self.__name}'.")
            return worksheet
        except WorksheetNotFound:
            raise Exception(f"Worksheet with ID '{gid}' not found.")
        except APIError as error:
            self.__handle_api_error(error)

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def __get_worksheet_by_name(self, name: str) -> gspread.Worksheet:
        """
        Retrieve a worksheet by its name.

        Args:
            name (str): The name of the worksheet.

        Returns:
            gspread.Worksheet: The worksheet object.

        Raises:
            Exception: If worksheet is not found.
        """
        try:
            worksheet = self.__spreadsheet.worksheet(name)
            self.__logger.info(f"Retrieved worksheet '{worksheet.title}' from spreadsheet '{self.__name}'.")
            return worksheet
        except WorksheetNotFound:
            raise Exception(f"Worksheet with name '{name}' not found.")
        except APIError as error:
            self.__handle_api_error(error)

    def __get_worksheet(self, worksheet: Union[int, str, gspread.Worksheet]) -> gspread.Worksheet:
        """
        Retrieve a worksheet based on an identifier (GID, name, or direct worksheet object).

        Args:
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet identifier or object.

        Returns:
            gspread.Worksheet: The worksheet object.

        Raises:
            ValueError: If the input is not of the expected type.
        """
        if isinstance(worksheet, gspread.Worksheet):
            return worksheet
        elif isinstance(worksheet, int):
            return self.__get_worksheet_by_gid(worksheet)
        elif isinstance(worksheet, str):
            return self.__get_worksheet_by_name(worksheet)
        else:
            raise ValueError("Worksheet must be an int (GID), str (name), or gspread.Worksheet.")

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def read_cell(self, cell: Union[str, Tuple[int, int]], worksheet: Union[int, str, gspread.Worksheet]) -> str:
        """
        Read the value of a specific cell in the worksheet.

        Args:
            cell (Union[str, Tuple[int, int]]): The cell to read (as A1 notation or (col, row) tuple).
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet to read from.

        Returns:
            str: The value of the cell.

        Raises:
            ValueError: If the worksheet is not a recognized type.
            APIError: If an API error occurs during the read.
        """
        worksheet = self.__get_worksheet(worksheet)

        # Convert (col, row) tuple to A1 notation if needed
        if isinstance(cell, tuple):
            cell = utils.rowcol_to_a1(cell[1], cell[0])

        try:
            value = worksheet.acell(cell).value
            self.__logger.info(f"Read cell '{cell}' in worksheet '{worksheet.title}'.")
            return value
        except APIError as error:
            self.__handle_api_error(error)

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def search_cell(self, value: str, worksheet: Union[int, str, gspread.Worksheet], in_row: Optional[int] = None,
                    in_column: Optional[int] = None, ) -> Tuple[int, int]:
        """
        Search for a specific value in the worksheet and return the cell coordinates.

        Args:
            value (str): The value to search for.
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet to search in.
            in_row (Optional[int], optional): The row to search in. Defaults to None.
            in_column (Optional[int], optional): The column to search in. Defaults to None.

        Returns:
            Tuple[int, int]: The (row, column) coordinates of the cell.

        Raises:
            ValueError: If the worksheet is not a recognized type.
            APIError: If an API error occurs during the search.
        """
        worksheet = self.__get_worksheet(worksheet)

        try:
            cell = worksheet.find(value, in_row=in_row, in_column=in_column)
            self.__logger.info(f"Found value '{value}' in cell '{cell}' in worksheet '{worksheet.title}'.")
            return cell.row, cell.col
        except APIError as error:
            self.__handle_api_error(error)
        except Exception as error:
            raise error

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def update_cell(self, cell: Union[str, Tuple[int, int]], value: str,
                    worksheet: Union[int, str, gspread.Worksheet]) -> None:
        """
        Update a specific cell in the worksheet.

        Args:
            cell (Union[str, Tuple[int, int]]): The cell to update (as A1 notation or (col, row) tuple).
            value (str): The value to set in the cell.
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet to update.

        Raises:
            ValueError: If the worksheet is not a recognized type.
            APIError: If an API error occurs during the update.
        """
        worksheet = self.__get_worksheet(worksheet)

        # Convert (col, row) tuple to A1 notation if needed
        if isinstance(cell, tuple):
            cell = utils.rowcol_to_a1(cell[1], cell[0])

        try:
            worksheet.update_acell(cell, value)
            self.__logger.info(f"Updated cell '{cell}' in worksheet '{worksheet.title}'.")
        except APIError as error:
            self.__handle_api_error(error)

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def update_column(self, worksheet: Union[int, str, gspread.Worksheet], column: int, values: list,
                      start_row: Optional[int] = None, color: bool = False, random_color: bool = False) -> None:
        """
        Update a specific column in the worksheet.

        Args:
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet to update.
            column (int): The column number to update.
            values (list): The values to set in the column.
            start_row (Optional[int], optional): The row to start updating from. Defaults to the first empty row.
            color (bool, optional): Whether to apply color formatting. Defaults to False.
            random_color (bool, optional): Whether to use random colors. Defaults to False.

        Raises:
            ValueError: If the worksheet type is invalid.
            Exception: If an error occurs during the update.
        """
        worksheet = self.__get_worksheet(worksheet)

        # Set the start row if not provided
        if not start_row:
            start_row = len(worksheet.col_values(column)) + 1

        end_row = start_row + len(values) - 1

        # Prepare the cells
        cell_list = worksheet.range(start_row, column, end_row, column)
        for cell, value in zip(cell_list, values):
            cell.value = value

        try:
            worksheet.update_cells(cell_list)
            self.__logger.info(
                f"Updated column '{column}' in worksheet '{worksheet.title}' from {start_row} to {end_row}.")
        except APIError as error:
            self.__handle_api_error(error)
        except Exception as error:
            raise error

        # Apply color formatting if required
        if color:
            background_color = (Color(randint(60, 194) / 255.0,
                                      randint(60, 194) / 255.0,
                                      randint(60, 194) / 255.0) if random_color else Color(1, 1, 1))
            cell_format = CellFormat(backgroundColor=background_color)
            cell_range = f'{utils.rowcol_to_a1(start_row, column)}:{utils.rowcol_to_a1(end_row, column)}'

            try:
                format_cell_range(worksheet, cell_range, cell_format)
                self.__logger.info(
                    f"Applied color formatting to range '{cell_range}' in worksheet '{worksheet.title}'.")
            except APIError as error:
                self.__handle_api_error(error)
            except Exception as error:
                raise error

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def get_all_records(self, worksheet: Union[int, str, gspread.Worksheet]) -> List[Dict[str, Union[int, float, str]]]:
        """
        Retrieve all records from the worksheet.

        Args:
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet to retrieve records from.

        Returns:
            list[dict]: A list of dictionaries representing the records.

        Raises:
            ValueError: If the worksheet is not a recognized type.
            APIError: If an API error occurs during the read.
        """
        worksheet = self.__get_worksheet(worksheet)

        try:
            records = worksheet.get_all_records()
            records = [{k: (None if v == "" else v) for k, v in d.items()} for d in records]
            self.__logger.info(f"Retrieved all records from worksheet '{worksheet.title}'.")
            return records
        except APIError as error:
            self.__handle_api_error(error)

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def get_all_records_as_dataframe(self, worksheet: Union[int, str, gspread.Worksheet]) -> pd.DataFrame:
        """
        Retrieve all records from the worksheet as a pandas DataFrame using gspread-dataframe.

        Args:
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet to retrieve records from.

        Returns:
            pd.DataFrame: A pandas DataFrame containing the records.

        Raises:
            ValueError: If the worksheet is not a recognized type.
            APIError: If an API error occurs during the read.
        """
        worksheet = self.__get_worksheet(worksheet)

        try:
            # Retrieve the worksheet's content as a DataFrame
            df = get_as_dataframe(worksheet, evaluate_formulas=True, header=1)  # Adjust header row as needed
            self.__logger.info(f"Retrieved all records as DataFrame from worksheet '{worksheet.title}'.")
            return df
        except APIError as error:
            self.__handle_api_error(error)

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def get_column(self, worksheet: Union[int, str, gspread.Worksheet], column: Union[int, str]) -> List[str]:
        """
        Retrieve a specific column from the worksheet as a list using gspread.

        Args:
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet to retrieve the column from.
            column (Union[int, str]): The column identifier, either as a string (column name) or integer (column index).

        Returns:
            list[str]: A list containing the values of the specified column.

        Raises:
            ValueError: If the column is not found or invalid.
            APIError: If an API error occurs during the read.
        """
        worksheet = self.__get_worksheet(worksheet)

        try:
            # If the column is specified as a string (A1 notation or header)
            if isinstance(column, str):
                # Assuming column is an A1 notation column letter (e.g., 'A', 'B')
                col_values = worksheet.col_values(utils.a1_to_rowcol(f"{column}1")[1])
            elif isinstance(column, int):
                # If column is specified as an integer, retrieve by index (1-based index)
                col_values = worksheet.col_values(column)
            else:
                raise ValueError("Column must be specified as an integer (index) or string (column name).")

            # Optionally remove empty values
            col_values_cleaned = [value for value in col_values if value.strip()]

            self.__logger.info(f"Retrieved column '{column}' from worksheet '{worksheet.title}'.")
            return col_values_cleaned
        except APIError as error:
            self.__handle_api_error(error)
        except ValueError as ve:
            self.__logger.error(f"ValueError: {ve}")
            raise

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def add_dataframe(self, dataframe: pd.DataFrame, worksheet: Union[int, str, gspread.Worksheet], append: bool = False) -> None:
        """
        Add a pandas DataFrame to a worksheet with the option to append or replace the data.

        Args:
            dataframe (pd.DataFrame): The DataFrame to add.
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet to update.
            append (bool): Whether to append the data to the existing sheet or replace it. Defaults to False (replace).

        Raises:
            ValueError: If the worksheet type is invalid.
            APIError: If an API error occurs during the update.
        """
        worksheet = self.__get_worksheet(worksheet)

        try:
            if append:
                # Find the next available row
                existing_rows = len(worksheet.get_all_values())
                start_row = existing_rows + 1  # Append after the last row
                set_with_dataframe(worksheet, dataframe, row=start_row, include_column_header=False)
                self.__logger.info(f"Appended DataFrame to worksheet '{worksheet.title}' starting from row {start_row}.")
            else:
                # Replace the entire sheet content with the new DataFrame
                worksheet.clear()  # Clear existing content
                set_with_dataframe(worksheet, dataframe, include_column_header=True)
                self.__logger.info(f"Replaced data in worksheet '{worksheet.title}' with new DataFrame.")
        except APIError as error:
            self.__handle_api_error(error)

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def duplicate_worksheet(self, source_worksheet: Union[int, str, gspread.Worksheet], new_worksheet_name: str) -> gspread.Worksheet:
        """
        Duplicate an existing worksheet to create a new worksheet with the specified name.

        Args:
            source_worksheet (Union[int, str, gspread.Worksheet]): The source worksheet to duplicate.
            new_worksheet_name (str): The name of the new worksheet to create.

        Raises:
            ValueError: If the worksheet type is invalid.
            APIError: If an API error occurs during the duplication.
        """
        source_worksheet = self.__get_worksheet(source_worksheet)
        exist_worksheets = self.__spreadsheet.worksheets()

        # Check if the new worksheet name already exists skip
        worksheet_titles = [worksheet.title for worksheet in exist_worksheets]
        if new_worksheet_name in worksheet_titles:
            self.__logger.warning(f"Worksheet '{new_worksheet_name}' already exists in the spreadsheet.")
            return self.__spreadsheet.worksheet(new_worksheet_name)

        try:
            # Duplicate the source worksheet
            new_worksheet = source_worksheet.duplicate(insert_sheet_index=len(exist_worksheets) + 1,
                                                       new_sheet_name=new_worksheet_name)
            self.__logger.info(f"Duplicated worksheet '{source_worksheet.title}' to '{new_worksheet.title}'.")
            return new_worksheet
        except APIError as error:
            self.__handle_api_error(error)
        except Exception as error:
            raise error

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def clear_column(self, worksheet: Union[int, str, gspread.Worksheet], column: int, start_row: int = 1) -> None:
        """
        Clear a specific column in the worksheet starting from the specified row.

        Args:
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet to clear.
            column (int): The column number to clear.
            start_row (int): The row to start clearing from.

        Raises:
            ValueError: If the worksheet type is invalid.
            APIError: If an API error occurs during the clearing.
        """
        worksheet = self.__get_worksheet(worksheet)

        try:
            # Clear the column starting from the specified row
            cell_list = worksheet.range(start_row, column, worksheet.row_count, column)
            for cell in cell_list:
                cell.value = ""

            worksheet.update_cells(cell_list)
            self.__logger.info(f"Cleared column '{column}' in worksheet '{worksheet.title}' from row {start_row}.")
        except APIError as error:
            self.__handle_api_error(error)
        except Exception as error:
            raise error

    @retry(APIError, tries=6, delay=2, backoff=2, jitter=(1, 3))
    def clear_worksheet(self, worksheet: Union[int, str, gspread.Worksheet]) -> None:
        """
        Clear all content from the worksheet.

        Args:
            worksheet (Union[int, str, gspread.Worksheet]): The worksheet to clear.

        Raises:
            ValueError: If the worksheet type is invalid.
            APIError: If an API error occurs during the clearing.
        """
        worksheet = self.__get_worksheet(worksheet)

        try:
            worksheet.clear()
            self.__logger.info(f"Cleared all content from worksheet '{worksheet.title}'.")
        except APIError as error:
            self.__handle_api_error(error)
        except Exception as error:
            raise error
