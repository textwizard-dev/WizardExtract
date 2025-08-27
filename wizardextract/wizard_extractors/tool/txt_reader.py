# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later


from __future__ import annotations

import io
from typing import Iterable, List, Sequence, Union

from wizardextract.utils.errors.errors import TxtFileError

__all__ = ["TxtReader"]


class TxtReader:
    __slots__ = ()

    _ENCODINGS: Sequence[str] = (
        "utf-8-sig",
        "utf-16",
        "utf-32",
        "utf-8",
        "ascii",
        "windows-1252",
        "iso-8859-1",
        "iso-8859-15",
        "latin-1",
        "cp850",
        "macroman",
    )

    def txt_reader(
        self,
        src: Union[io.BytesIO, bytes, bytearray],
        *,
        pages: Union[None, int, Iterable[int]] = None,
    ) -> str:
        """
        Parameters
        ----------
        src : BytesIO | bytes | bytearray
            Raw text bytes or BytesIO stream.
        pages : int | Iterable[int] | None, optional
            1‑based page numbers to return, where pages are delimited by
            ``\\f``. ``None`` ⇒ full text.

        Returns
        -------
        str
            Decoded (and possibly sliced) text.

        Raises
        ------
        TxtFileError
            If decoding fails for all common encodings.
        """
        raw = src.getvalue() if isinstance(src, io.BytesIO) else bytes(src)

        text = self._decode(raw)
        if pages is None:
            return text

        page_idx = self._normalize_pages(pages, text.count("\f") + 1)
        slices = text.split("\f")
        return "\n".join(slices[i] for i in page_idx)


    @classmethod
    def _decode(cls, raw: bytes) -> str:
        for enc in cls._ENCODINGS:
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        raise TxtFileError("Unable to decode text file with common encodings.")

    @staticmethod
    def _normalize_pages(
        pages: Union[int, Iterable[int]],
        total: int,
    ) -> List[int]:
        """
        Validate 1‑based `pages` and return sorted unique 0‑based indices.

        Raises
        ------
        TxtFileError
            If any page number is out of range.
        """
        if isinstance(pages, int):
            pages = [pages]

        idx: set[int] = set()
        for p in pages:
            if not isinstance(p, int) or p < 1 or p > total:
                raise TxtFileError(f"Page {p} out of range 1..{total}")
            idx.add(p - 1)
        return sorted(idx)
