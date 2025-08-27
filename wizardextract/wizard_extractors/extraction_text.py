# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later

import io
from pathlib import Path
from typing import Union, Optional, List

from wizardextract.utils.errors.errors import (
    FileNotFoundCustomError,
    UnsupportedExtensionError,
    DocFileAsBytesError,
    InvalidPagesError,
)
from wizardextract.wizard_extractors.tool.docx_reader import DocxReader
from wizardextract.wizard_extractors.tool.txt_reader import TxtReader
from wizardextract.wizard_extractors.tool.doc_reader import DocReader
from wizardextract.wizard_extractors.tool.pdf_reader import PdfReader
from wizardextract.wizard_extractors.tool.image_format_reader import ImgReader
from wizardextract.wizard_extractors.tool.xlsx_xls_reader import XlsxReader
from wizardextract.wizard_extractors.tool.csv_reader import CsvReader
from wizardextract.wizard_extractors.tool.html_reader import HtmlReader
from wizardextract.wizard_extractors.tool.json_reader import JsonReader


class TextExtractor:
    """
    Handles text extraction from various formats, with optional OCR and page selection.
    """

    def __init__(self) -> None:
        # Instanzio una sola volta ciascun reader
        self._pdf = PdfReader()
        self._doc = DocReader()
        self._docx = DocxReader()
        self._xlsx = XlsxReader()
        self._txt = TxtReader()
        self._img = ImgReader()
        self._csv = CsvReader()
        self._html = HtmlReader()
        self._json = JsonReader()

    @staticmethod
    def _validate_selector(sel):
        if sel is None:
            return None
        if isinstance(sel, (int, str)):
            return [sel]
        if isinstance(sel, list) and all(isinstance(x, (int, str)) for x in sel):
            return sel
        raise InvalidPagesError(sel)

    def data_extractor(
            self,
            input_data: Union[str, bytes, Path],
            extension: Optional[str] = None,
            pages_or_sheets: Optional[Union[int, str,
            List[Union[int, str]]]] = None,
            ocr: bool = False,
            language_ocr: str = "eng",
    ) -> str:

        # 1) Validate & canonicalize pages
        selector = self._validate_selector(pages_or_sheets)

        # 2) Normalize input_data → always bytes (or path for .doc)
        if isinstance(input_data, (str, Path)):
            path = Path(input_data)
            if not path.exists():
                raise FileNotFoundCustomError(path)
            ext = path.suffix.lower().lstrip(".")
            if ext == "doc":
                # .doc reader needs a file path
                raw = str(path)
            else:
                raw = path.read_bytes()
            extension = ext
        else:
            # input is bytes
            if extension is None:
                raise UnsupportedExtensionError(None)
            extension = extension.lower()
            raw = input_data
            if extension == "doc":
                raise DocFileAsBytesError()

        # 3) Dispatch
        reader_map = {
            "pdf": lambda: self._pdf.pdf_reader(io.BytesIO(raw), pages_list=selector, ocr=ocr, language_ocr=language_ocr),
            "doc": lambda: self._doc.doc_reader(raw),
            "docx": lambda: self._docx.docx_reader(io.BytesIO(raw), pages_list=selector, ocr=ocr, language_ocr=language_ocr),
            "xlsx": lambda: self._xlsx.xlsx_reader(io.BytesIO(raw), sheets=selector),
            "xls": lambda: self._xlsx.xlsx_reader(io.BytesIO(raw), sheets=selector),
            "txt": lambda: self._txt.txt_reader(io.BytesIO(raw), pages=selector),
            # images: OCR only
            "tif": lambda: self._img.image_format_reader(io.BytesIO(raw), pages=selector, language_ocr=language_ocr),
            "tiff": lambda: self._img.image_format_reader(io.BytesIO(raw), pages=selector, language_ocr=language_ocr),
            "jpg": lambda: self._img.image_format_reader(io.BytesIO(raw), language_ocr=language_ocr),
            "jpeg": lambda: self._img.image_format_reader(io.BytesIO(raw), language_ocr=language_ocr),
            "png": lambda: self._img.image_format_reader(io.BytesIO(raw), language_ocr=language_ocr),
            "gif": lambda: self._img.image_format_reader(io.BytesIO(raw), language_ocr=language_ocr),
            # text‐only readers ignore pages/ocr
            "csv": lambda: self._csv.csv_reader(io.BytesIO(raw)),
            "html": lambda: self._html.html_reader(io.BytesIO(raw)),
            "htm": lambda: self._html.html_reader(io.BytesIO(raw)),
            "json": lambda: self._json.json_reader(io.BytesIO(raw)),
        }

        if extension not in reader_map:
            raise UnsupportedExtensionError(extension)

        return reader_map[extension]()

