# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

from pathlib import Path
from typing import IO, List, Sequence, Union

import fitz 

from wizardextract.utils.errors.errors import (
    FileProcessingError,
    OCRNotConfiguredError,
)
from wizardextract.wizard_extractors.utils.selector import  normalize_pages_selector

__all__ = ["PdfReader"]


class PdfReader:
    """
    PDF reader with optional OCR and page selection.

    Methods
    -------
    pdf_reader(source, pages_list, ocr, language_ocr) -> str
        Extract text from PDF bytes, path, or file-like.
    count_images(source) -> int
        Count embedded images in the PDF.
    """

    __slots__ = ("ocr_dpi",)

    def __init__(self, ocr_dpi: int = 300) -> None:
        self.ocr_dpi: int = ocr_dpi

    def pdf_reader(
        self,
        pdf_source: Union[bytes, str, Path, IO[bytes]],
        pages_list: Sequence[Union[int, str]] | None = None,
        ocr: bool = False,
        language_ocr: str = "eng",
    ) -> str:
        """
        Parameters
        ----------
        pdf_source : bytes | str | Path | file-like
            PDF content or path or open file.
        pages_list : Sequence[int | str] | None
            Page selection (1-based). Accepts ints, ranges and CSV:
              • 1
              • "3-5"
              • "1,3,5-7"
              • [1, "3-4", "9,11-12"]
            Invalid tokens are ignored; out-of-range pages are skipped.
            None = all pages.
        ocr : bool
            Enable OCR on pages with images.
        language_ocr : str
            Tesseract language code.

        Returns
        -------
        str
            Concatenated text of extracted pages.

        Raises
        ------
        FileProcessingError
            On file I/O or parsing errors.
        OCRNotConfiguredError
            If OCR is requested but pytesseract/Pillow are missing.
        """
        raw = self._read_input(pdf_source)

        try:
            doc = fitz.open(stream=raw, filetype="pdf")
        except Exception as exc:
            raise FileProcessingError(f"Cannot open PDF: {exc}") from exc

        try:
            idxs: List[int] = normalize_pages_selector(pages_list, doc.page_count)
            out: List[str] = []
            for idx in idxs:
                page = doc.load_page(idx)
                if not ocr:
                    out.append(page.get_text() + "\n")
                    continue
                has_img = bool(page.get_images(full=True))
                out.append(self._perform_ocr(page, language_ocr) if has_img else page.get_text() + "\n")
            return "".join(out)
        finally:
            doc.close()

    @staticmethod
    def _read_input(src: Union[bytes, str, Path, IO[bytes]]) -> bytes:
        if isinstance(src, (bytes, bytearray)):
            return bytes(src)
        if hasattr(src, "read"):
            data = src.read()
            return data if isinstance(data, (bytes, bytearray)) else bytes(data)
        path = Path(src)
        try:
            return path.read_bytes()
        except Exception as exc:
            raise FileProcessingError(f"Cannot read file {path!s}: {exc}") from exc
        

    def _perform_ocr(self, page: fitz.Page, lang: str) -> str:

        try:
            import pytesseract  # noqa: F401
            from PIL import Image  # noqa: F401
        except ModuleNotFoundError as exc:
            raise OCRNotConfiguredError("OCR requested but pytesseract/Pillow not installed.") from exc
        try:
            tpage = page.get_textpage_ocr(dpi=self.ocr_dpi, full=True, language=lang)
            return page.get_text(textpage=tpage)
        except Exception as exc:
            raise FileProcessingError(f"OCR failed: {exc}") from exc