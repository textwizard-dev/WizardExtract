# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import io
from pathlib import Path
from typing import Iterable, List, Sequence, Union

import pandas as pd

from wizardextract.utils.errors.errors import FileFormatError, FileProcessingError
from wizardextract.wizard_extractors.utils.selector import  normalize_sheets_selector 

__all__ = ["XlsxReader"]


class XlsxReader:
    __slots__ = ()

    def xlsx_reader(
        self,
        source: Union[bytes, str, Path, io.BytesIO],
        *,
        sheets: Union[None, int, str, Iterable[int | str]] = None,
    ) -> str:
        """
        Extract plain text from Excel workbooks.
        - `sheets`: None = all sheets; otherwise accepts 0-based indices, names,
          and CSV/ranges inside strings (e.g. "0,2,4-6"). Invalid selectors are ignored.
        """
        try:
            buf = self._to_bytes_io(source)
            xls = pd.ExcelFile(buf)
        except Exception as exc:
            raise FileFormatError(f"Invalid Excel file: {exc}") from exc

        sheet_names = list(xls.sheet_names)
        sel_list: Sequence[int | str] | None
        if sheets is None:
            sel_idx = list(range(len(sheet_names)))
        else:
            if isinstance(sheets, (int, str)):
                sel_list = [sheets]
            else:
                sel_list = list(sheets)
            sel_idx = normalize_sheets_selector(sel_list, sheet_names)

        if not sel_idx:
            return ""

        sel_names = [sheet_names[i] for i in sel_idx]

        try:
            frames = pd.read_excel(xls, sheet_name=sel_names)  # dict[name, DataFrame]
        except Exception as exc:
            raise FileProcessingError(f"Excel processing error: {exc}") from exc

        out: List[str] = []
        for name in sel_names:
            df = frames[name]
            if df.empty:
                continue
            out.append(f"Sheet: {name}")
            out.append(df.to_string(index=False, index_names=False))
            out.append("")

        return "\n".join(out).rstrip()

    @staticmethod
    def _to_bytes_io(src) -> io.BytesIO:
        if isinstance(src, io.BytesIO):
            src.seek(0)
            return src
        if isinstance(src, (bytes, bytearray)):
            return io.BytesIO(src)
        path = Path(src)
        try:
            return io.BytesIO(path.read_bytes())
        except Exception as exc:
            raise FileProcessingError(f"Cannot read Excel file {path!s}: {exc}") from exc
