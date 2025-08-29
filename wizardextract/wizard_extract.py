# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later


from pathlib import Path
from typing import Union, Optional,List
from wizardextract.wizard_extractors.extraction_text import TextExtractor
from wizardextract.utils.errors.errors_handle import handle_errors


class WizardExtract:
    def __init__(self):
        self._text_extractor = TextExtractor()

    
    # ----------------------------------------------------------------------
    # Text extraction
    # ----------------------------------------------------------------------

    @handle_errors
    def extract_text(
            self,
            input_data: Union[str, bytes, Path],
            extension: Optional[str] = None,
            pages: Optional[Union[int, str, List[Union[int, str]]]] = None,
            ocr: bool = False,
            language_ocr: str = "eng",    
    ) -> str:
        """
        Extracts text from the provided input data based on its format and type.

        Args:
            input_data (Union[str, bytes, Path]):
                The input for extraction: a filesystem path, raw bytes, or string content.
            extension (Optional[str]):
                File extension to use when `input_data` is bytes (e.g. 'pdf', 'xlsx').
            pages (Optional[int | str | list[int | str]]):
                • For paged formats (PDF, DOCX, TIFF): one-based page numbers to extract.
                • For Excel formats (XLSX, XLS): sheet index (int), sheet name (str),
                  or a mixed list thereof.
                • If None (default), all pages/sheets are extracted.
            ocr (bool):
                Enables OCR for text extraction using Tesseract OCR. Applicable for formats
                like PDF, DOCX, and image-based files.
            language_ocr (str):
                Tesseract language code (default: 'eng').

        Returns:
            str: The extracted text content.

        Raises:
            InvalidInputError: If the input data is invalid or unsupported.

        Supported formats:
            'pdf', 'doc', 'docx', 'xlsx', 'xls', 'txt', 'csv',
            'html', 'htm', 'json', 'tif', 'tiff', 'jpg', 'jpeg',
            'png', 'gif'
        """
        
        
        return self._text_extractor.data_extractor(
            input_data,
            extension,
            pages,
            ocr,
            language_ocr,
        )

    def extract_text_azure(
            self,
            input_data: Union[str, bytes, Path],
            extension: Optional[str] = None,
            language_ocr: str = "eng",
            pages: Optional[Union[int, str, List[Union[int, str]]]] = None,
            azure_endpoint: Optional[str] = None,
            azure_key: Optional[str] = None,
            azure_model_id: str = "prebuilt-read",
            hybrid: bool = False,
    ):
        """
        Extracts text, tables, and key-value pairs from documents using
        **Azure Document Intelligence** (OCR).

        Supported formats:
        - Images: JPG, PNG, TIFF, BMP, GIF
        - PDF (direct OCR or hybrid mode with native text extraction)
        - DOCX (OCR for embedded images)

        Args:
            input_data (Union[str, bytes, Path]):
                File path, binary content, or byte stream.
            extension (Optional[str], default=None):
                File extension (required if `input_data` is a stream or bytes).
            language_ocr (str, default="eng"):
                OCR language code (ISO-639-2 or ISO-639-1).
            pages (Optional[Union[int, str, List[Union[int, str]]]], default=None):
                Pages to process. Examples:
                - `1` (only page 1)
                - `"1,3,5-7"` (specific pages)
                - `[1, 3, "5-7"]` (mixed list)
            azure_endpoint (Optional[str], default=None):
                Azure Document Intelligence endpoint.  
                Example: `"https://<resource-name>.cognitiveservices.azure.com/"`.
            azure_key (Optional[str], default=None):
                Azure API key.
            azure_model_id (str, default="prebuilt-read"):
                Azure model:
                - `"prebuilt-read"` → text only
                - `"prebuilt-layout"` → text + tables + key-value fields
            hybrid (bool, default=False):
                If True, for PDFs it runs a hybrid mode:
                - Pages with text → direct extraction via PyMuPDF
                - Pages with images → Azure OCR

        Returns:
            CloudExtractionResult:
                Object containing:
                - `text_pages`: list of text pages
                - `text`: concatenated text
                - `tables`: extracted tables
                - `pretty_tables`: tables formatted as ASCII
                - `key_value`: dictionary mapping keys to list of values

        Raises:
            RuntimeError: if the Azure module is not installed.
            AzureCredentialsError: if endpoint or key is missing/invalid.
            UnsupportedExtensionAzureError: if the file format is unsupported.
            FileProcessingError: if the file does not exist or cannot be read.

        Example:
            ```python
            import wizardextract as we

            res = we.extract_text_azure(
                "invoice.pdf",
                language_ocr="ita",
                azure_endpoint="https://myocr.cognitiveservices.azure.com/",
                azure_key="xxxxxx",
                azure_model_id="prebuilt-layout"
            )

            print(res.text)           # concatenated text
            print(res.pretty_tables)  # tables in readable format
            print(res.key_value)      # extracted key-value pairs
            ```
        """
        try:
            from textwizard.wizard_extractors.ocr_service.azure_ocr import AzureOcr
        except ImportError:
            raise RuntimeError("To use Azure OCR, install: textwizard[azure]")

        client = AzureOcr(endpoint=azure_endpoint, key=azure_key)
        return client.extract(
            input_data,
            model_id=azure_model_id,
            extension=extension,
            language_ocr=language_ocr,
            pages=pages,
            hybrid=hybrid
        )
