# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations
from typing import Any


class TextWizardError(Exception):
    """
    Base class for all errors in the TextWizard library.
    """

    def __init__(self, message: str, param_name: str = None, value: Any = None):
        self.param_name = param_name
        self.value = value
        super().__init__(message)

    def __str__(self):
        base_message = super().__str__()
        if self.param_name and self.value is not None:
            return f"{base_message} (Parameter: {self.param_name}, Value: {self.value})"
        return base_message


class InvalidInputError(TextWizardError):
    """
    Raised when an input parameter is invalid.
    """

    def __init__(self, param_name: str, expected: str, received: Any):
        message = (
            f"Invalid input for '{param_name}': expected {expected}, got {type(received).__name__} "
            f"(value={received})."
        )
        super().__init__(message, param_name, received)


class MissingExtensionError(TextWizardError):
    """
    Raised when the file extension is missing for byte input.
    """

    def __init__(self):
        super().__init__("The 'extension' parameter must be specified for byte input.")


class UnsupportedFileTypeError(TextWizardError):
    """
    Raised when an unsupported file type is used.
    """

    def __init__(self, file_type: str):
        super().__init__(f"Unsupported file type: {file_type}.")


class ValidationError(TextWizardError):
    """
    Raised for generic validation errors.
    """

    def __init__(self, param_name: str, issue: str, value: Any = None):
        message = f"Validation error for '{param_name}': {issue}."
        super().__init__(message, param_name, value)


class InternalError(TextWizardError):
    """
    Raised for unexpected internal errors.
    """

    def __init__(self, original_exception: Exception):
        message = f"{str(original_exception)}"
        super().__init__(message)
        self.original_exception = original_exception


class DocFileAsBytesError(Exception):
    """
    Raised when a .doc file is passed as bytes instead of a path.
    """

    def __init__(self, message=".doc files must be passed as paths, not as bytes."):
        super().__init__(message)


class UnsupportedExtensionError(TextWizardError):
    """
    Raised when an unsupported file extension is encountered.
    """

    def __init__(self, extension):
        self.extension = extension
        self.supported_extensions = [
            "pdf",
            "doc",
            "docx",
            "xlsx",
            "xls",
            "txt",
            "csv",
            "html",
            "htm",
            "json",
            "tif",
            "tiff",
            "jpg",
            "jpeg",
            "png",
            "gif",
        ]
        super().__init__(
            f"The file extension '{self.extension}' is not supported. "
            f"Supported extensions are: {', '.join(self.supported_extensions)}."
        )
class UnsupportedExtensionAzureError(TextWizardError):
    """
    Raised when an unsupported file extension is encountered.
    """

    def __init__(self, extension):
        self.extension = extension
        self.supported_extensions = [
            "pdf",
            "docx",
            "tif",
            "tiff",
            "jpg",
            "jpeg",
            "png",
            "BMP"
        ]
        super().__init__(
            f"The file extension '{self.extension}' is not supported. "
            f"Supported extensions are: {', '.join(self.supported_extensions)}."
        )


class FileNotFoundCustomError(TextWizardError):
    """
    Raised when a file cannot be found or opened.
    """

    def __init__(self, file_path):
        super().__init__(f"File '{file_path}' does not exist.")


class AntiwordNotFoundError(Exception):
    """
    Raised when the Antiword executable is not found or not installed.
    """

    def __init__(self, message="Antiword is not installed or not in PATH."):
        super().__init__(message)


class ExtractionError(Exception):
    """
    Raised for errors during text extraction from files.
    """

    def __init__(self, message):
        super().__init__(message)


class DocxFileError(Exception):
    """
    Raised when there is an issue with the .docx file.
    """

    def __init__(self, message="Error processing the .docx file."):
        super().__init__(message)


class ImageProcessingError(Exception):
    """
    Raised when there is an issue processing an image file.
    """

    def __init__(self, message="Error processing the image file."):
        super().__init__(message)


class HtmlFileError(Exception):
    """
    Raised when there is an issue with the HTML content or file.
    """

    def __init__(self, message="Invalid HTML content or file."):
        super().__init__(message)


class JsonFileError(Exception):
    """
    Raised when there is an issue with the JSON content or file.
    """

    def __init__(self, message="Invalid JSON content or file."):
        super().__init__(message)


class TxtFileError(Exception):
    """
    Raised when a text file cannot be decoded using standard encodings.
    """

    def __init__(self, message="Failed to decode the text file."):
        super().__init__(message)


class OCRNotConfiguredError(Exception):
    """
    Raised when Tesseract OCR is not properly configured or installed.
    """

    def __init__(
        self, message="Tesseract OCR is not properly configured or installed."
    ):
        super().__init__(message)


class FileFormatError(Exception):
    """
    Raised when the file format is not supported or invalid.
    """

    def __init__(self, message="The file format is not supported or invalid."):
        super().__init__(message)


class FileProcessingError(Exception):
    """
    Raised when an error occurs during the processing of a file.
    """

    def __init__(self, message="An error occurred while processing the file."):
        super().__init__(message)



class CSVValidationError(Exception):
    """
    Raised when a validation error occurs in CSV operations.

    Attributes:
        message (str): Description of the validation error.
    """

    def __init__(self, message="CSV validation error occurred"):
        super().__init__(message)
        self.message = message



class InvalidPagesError(TextWizardError):
    """
    Raised when the `pages` argument is not an int or a list of ints.
    """
    def __init__(self, pages):
        super().__init__(
            "Parameter `pages` must be an int or a list of ints ≥ 1.",
            "pages",
            pages,
        )
 
class AzureCredentialsError(TextWizardError):
    """
    Raised when Azure OCR backend is selected but endpoint or key are missing.
    """
    def __init__(self):
        msg = "Azure OCR requires both 'azure_endpoint' and 'azure_key'."
        super().__init__(msg, param_name="ocr_backend", value="azure")

