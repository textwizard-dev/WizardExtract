# SPDX-License-Identifier: AGPL-3.0-or-later
# © 2024–2025 Mattia Rubino

import io
from typing import IO, Sequence, Union

from PIL import Image, UnidentifiedImageError
from wizardextract.utils.errors.errors import ImageProcessingError, OCRNotConfiguredError
from wizardextract.wizard_extractors.utils.selector import  normalize_pages_selector  # <- your shared util


class ImgReader:
    """OCR for bitmap formats (TIFF multipage, JPG/PNG/GIF, …) with optional frame selection."""

    __slots__ = ()

    @staticmethod
    def image_format_reader(
        content: Union[IO[bytes], io.BytesIO],
        *,
        pages: Sequence[Union[int, str]] | None = None,  # 1-based ints / "csv" / "a-b"
        language_ocr: str = "eng",
    ) -> str:
        """
        Return concatenated OCR text. Invalid/out-of-range frame selectors are ignored.
        If no selected frames exist, returns an empty string.
        """
        try:
            img = Image.open(content)
        except UnidentifiedImageError:
            raise ImageProcessingError("Invalid or unsupported image data.")
        except Exception as exc:
            raise ImageProcessingError(f"Error opening image: {exc}") from exc

        try:
            total = int(getattr(img, "n_frames", 1))
            sel = normalize_pages_selector(pages, total) if pages is not None else list(range(total))

            try:
                import pytesseract  # noqa: F401
            except ModuleNotFoundError as exc:
                raise OCRNotConfiguredError("Tesseract OCR requested but pytesseract not installed.") from exc

            out: list[str] = []
            for i in sel:
                try:
                    img.seek(i)
                    frame = img.convert("RGB")  
                    text = pytesseract.image_to_string(frame, lang=language_ocr)
                    out.append(text.strip())
                except Exception as ocr_exc:
                    continue

            return "\n".join(t for t in out if t)
        finally:
            try:
                img.close()
            except Exception:
                pass
