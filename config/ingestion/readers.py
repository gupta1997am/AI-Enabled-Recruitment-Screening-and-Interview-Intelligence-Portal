from pathlib import Path

import pandas as pd

from .exceptions import (
    EmptyFileError,
    FileReadError,
    UnsupportedFileTypeError,
)


SUPPORTED_EXTENSIONS = {".csv", ".xls", ".xlsx"}


def read_candidate_file(file_source):
    """
    Read a CSV or Excel file and return a pandas DataFrame.

    file_source can be a file path or a Django uploaded file.
    """

    filename = getattr(file_source, "name", str(file_source))
    extension = Path(filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type: {extension or 'unknown'}. "
            "Upload a CSV, XLS, or XLSX file."
        )

    try:
        if hasattr(file_source, "seek"):
            file_source.seek(0)

        if extension == ".csv":
            dataframe = pd.read_csv(file_source)
        else:
            dataframe = pd.read_excel(file_source)

    except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
        raise FileReadError(
            "The CSV file is empty or has an invalid format."
        ) from exc

    except Exception as exc:
        raise FileReadError(
            f"Could not read '{Path(filename).name}'. "
            "Check that the file is valid and not corrupted."
        ) from exc

    if dataframe.empty:
        raise EmptyFileError(
            "The uploaded file contains no candidate records."
        )

    # Normalize column headings for consistent processing.
    dataframe.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in dataframe.columns
    ]

    return dataframe