# SPDX-FileCopyrightText: 2024–2025 Mattia Rubino
# SPDX-License-Identifier: AGPL-3.0-or-later

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union,Callable
from collections import defaultdict
import xml.etree.ElementTree as ET

import fitz
from azure.core.credentials import AzureKeyCredential               # type: ignore
from azure.ai.documentintelligence import DocumentIntelligenceClient  # type: ignore
from azure.ai.documentintelligence.models import AnalyzeResult        # type: ignore

from wizardextract.utils.errors.errors import (
    AzureCredentialsError,
    FileProcessingError,
    UnsupportedExtensionAzureError,
)


@dataclass(frozen=True)
class KeyValue:
    key: str
    value: str

@dataclass(frozen=True)
class CloudExtractionResult:
    text_pages:       List[str]             = field(default_factory=list)
    tables:           List[List[List[str]]] = field(default_factory=list)
    _raw_key_value:   List[KeyValue]        = field(default_factory=list, repr=False)

    @property
    def text(self) -> str:
        return "\n".join(self.text_pages)

    @property
    def pretty_tables(self) -> str:
        def _ascii(rows: List[List[str]]) -> str:
            if not rows:
                return ""
            widths = [max(len(str(c)) for c in col) for col in zip(*rows)]
            lines: List[str] = []
            for i, row in enumerate(rows):
                line = " | ".join(str(cell).ljust(widths[j]) for j, cell in enumerate(row))
                lines.append(line)
                if i == 0:
                    lines.append("-+-".join("-" * w for w in widths))
            return "\n".join(lines)
        return "\n\n".join(_ascii(tbl) for tbl in self.tables)

    @cached_property
    def key_value(self) -> Dict[str, List[str]]:
        agg: Dict[str, List[str]] = defaultdict(list)
        for kv in self._raw_key_value:
            agg[kv.key].extend(kv.value.splitlines())
        return dict(agg)

# ────────────────────────────────────────────────────────────────────────────
#  Constants & helpers
# ────────────────────────────────────────────────────────────────────────────
_SUPPORTED_MODELS = {"prebuilt-read", "prebuilt-layout"}
_IMG_EXT         = {"jpg", "jpeg", "png", "tif", "tiff", "bmp", "gif"}
_PDF_EXT         = {"pdf"}
_DOCX_EXT        = {"docx"}

_FEAT_INFO           = (("KEY_VALUE_PAIRS", "keyValuePairs"),)
_FEATURES_FOR_LAYOUT = [fb for _, fb in _FEAT_INFO]

_LANG3_TO_2 = {"eng":"en","ita":"it","fra":"fr","deu":"de","spa":"es"}

_NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "v": "urn:schemas-microsoft-com:vml",
}
def qn(p: str, t: str) -> str:
    return f"{{{_NS[p]}}}{t}"

_RELS_RX   = re.compile(r"word/_rels/[^/]+\.xml\.rels$")
_HEADER_RX = re.compile(r"word/header\d*\.xml$")
_FOOTER_RX = re.compile(r"word/footer\d*\.xml$")



def _normalize_lang(lang: Optional[str]) -> Optional[str]:
    if not lang:
        return None
    lang = lang.lower()
    return _LANG3_TO_2.get(lang, lang) if len(lang)==3 else lang

def _pages_list_to_string(pages: List[int]) -> str:
    if not pages:
        return ""
    keys = sorted(set(pages))
    out: List[str] = []
    start = prev = keys[0]
    for p in keys[1:]:
        if p == prev + 1:
            prev = p
        else:
            out.append(f"{start}-{prev}" if start!=prev else f"{start}")
            start = prev = p
    out.append(f"{start}-{prev}" if start!=prev else f"{start}")
    return ",".join(out)

def _filter_valid_pages(sel: Optional[Sequence[int]], page_count: int) -> list[int]:
    if sel is None:
        return list(range(1, page_count + 1))
    return [p for p in sel if isinstance(p, int) and 1 <= p <= page_count]


PagesLike = Optional[Union[int, str, Sequence[Union[int, str]]]]

def _parse_pages_token(tok: str) -> List[int]:
    tok = tok.strip()
    if not tok:
        return []
    if "-" in tok:
        a, b = tok.split("-", 1)
        a, b = a.strip(), b.strip()
        if not a.isdigit() or not b.isdigit():
            raise ValueError(f"Invalid page range: {tok!r}")
        ia, ib = int(a), int(b)
        if ia <= 0 or ib <= 0:
            raise ValueError("Pages must be 1-based positive integers.")
        if ia > ib:
            ia, ib = ib, ia
        return list(range(ia, ib + 1))
    else:
        if not tok.isdigit():
            raise ValueError(f"Invalid page token: {tok!r}")
        i = int(tok)
        if i <= 0:
            raise ValueError("Pages must be 1-based positive integers.")
        return [i]

def _normalize_pages(pages: PagesLike) -> Optional[List[int]]:
    """
    Accepts:
      - int                -> 1-based page number
      - str                -> "1,3,5-7"
      - sequence[int|str]  -> [1, "3-4", 8]
    Returns a sorted unique List[int] (1-based) or None.
    """
    if pages is None:
        return None

    out: List[int] = []

    if isinstance(pages, int):
        out.append(pages)

    elif isinstance(pages, str):
        for part in pages.split(","):
            out.extend(_parse_pages_token(part))

    elif isinstance(pages, Sequence):
        for item in pages:
            if isinstance(item, int):
                if item <= 0:
                    raise ValueError("Pages must be 1-based positive integers.")
                out.append(item)
            elif isinstance(item, str):
                for part in item.split(","):
                    out.extend(_parse_pages_token(part))
            else:
                raise TypeError(f"Unsupported pages element type: {type(item).__name__}")
    else:
        raise TypeError(f"Unsupported pages type: {type(pages).__name__}")

    out = sorted(set(out))
    return out or None



# ────────────────────────────────────────────────────────────────────────────
#  AzureOcr client
# ────────────────────────────────────────────────────────────────────────────
class AzureOcr:
    __slots__ = ("_client",)

    def __init__(self, *, endpoint: str, key: str) -> None:
        if not endpoint or not key:
            raise AzureCredentialsError()
        try:
            self._client = DocumentIntelligenceClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key),
            )
        except Exception as exc:
            raise AzureCredentialsError() from exc

    def extract(
        self,
        source: Union[str, bytes, Path, io.BytesIO],
        *,
        model_id: str = "prebuilt-read",
        extension: Optional[str] = None,
        language_ocr: Optional[str] = None,
        pages: PagesLike = None,
        hybrid: bool = False,
    ) -> CloudExtractionResult:
        if model_id not in _SUPPORTED_MODELS:
            raise ValueError("model_id must be 'prebuilt-read' or 'prebuilt-layout'")
        blob, ext = self._normalize_source(source, extension)
        pages_norm = _normalize_pages(pages)
        if   ext in _IMG_EXT:   return self._process_image(blob, model_id, ext, language_ocr)
        elif ext in _PDF_EXT:   return self._process_pdf(blob, model_id, language_ocr, pages_norm, hybrid)
        elif ext in _DOCX_EXT:  return self._process_docx(blob, model_id, language_ocr, pages_norm)
        else: raise UnsupportedExtensionAzureError(ext)

    def _normalize_source(self, src, ext) -> Tuple[bytes,str]:
        if isinstance(src,(bytes,bytearray)) or hasattr(src,"read"):
            if not ext: raise UnsupportedExtensionAzureError(None)
            data = src.getvalue() if hasattr(src,"getvalue") else bytes(src)
            return data, ext.lower()
        path = Path(src)
        if not path.exists():
            raise FileProcessingError(f"File '{path}' not found")
        return path.read_bytes(), path.suffix.lstrip(".").lower()

    def _make_call(self, blob, model_id, ext, lang, pages_str=None) -> AnalyzeResult:
        kwargs: Dict[str,Any] = {
            "content_type": f"image/{ext}" if ext in _IMG_EXT else f"application/{ext}"
        }
        ln = _normalize_lang(lang)
        if ln:         kwargs["locale"]   = ln
        if pages_str:  kwargs["pages"]    = pages_str
        if model_id!="prebuilt-read":
            kwargs["features"] = _FEATURES_FOR_LAYOUT
        return self._client.begin_analyze_document(model_id, blob, **kwargs).result()

    def _process_image(self, blob, model_id, ext, lang):
        res = self._make_call(blob, model_id, ext, lang)
        return self._build_result(res, model_id)

    def _process_pdf(self, blob, model_id, lang, pages, hybrid):
        if hybrid:
            return self._pdf_hybrid(blob, model_id, lang, pages)
        pages_str = _pages_list_to_string(list(pages)) if pages else None
        res = self._make_call(blob, model_id, "pdf", lang, pages_str)
        return self._build_result(res, model_id)

    def _pdf_hybrid(self, blob, model_id, lang, sel):
        doc = fitz.open(stream=blob, filetype="pdf")
        try:
            valid_1based = _filter_valid_pages(sel, doc.page_count)
            if not valid_1based:
                return CloudExtractionResult(text_pages=[])

            all_idx = [p - 1 for p in valid_1based]  # 0-based
            img_pages: list[int] = []  # 1-based per Azure
            txt_map: dict[int, str] = {}

            for i in all_idx:
                pg = doc.load_page(i)
                if pg.get_images(full=True):
                    img_pages.append(i + 1)
                else:
                    txt_map[i] = pg.get_text() + "\n"

            if not img_pages:
                return CloudExtractionResult(text_pages=[txt_map[i] for i in all_idx])

            if len(img_pages) == len(all_idx):
                return self._process_pdf(blob, model_id, lang, img_pages, False)

            pages_str = _pages_list_to_string(img_pages)
            az = self._make_call(blob, model_id, "pdf", lang, pages_str)
            built = self._build_result(az, model_id)

            out, queue = [], built.text_pages.copy()
            for i in all_idx:
                if (i + 1) in img_pages:
                    out.append(queue.pop(0) if queue else "")
                else:
                    out.append(txt_map[i])

            return CloudExtractionResult(
                text_pages=out,
                tables=built.tables,
                _raw_key_value=built._raw_key_value,
            )
        finally:
            doc.close()
            
    def _process_docx(self, blob, model_id, lang, pages):
        parser = _DocxParser(
            parent=self,
            blob=blob,
            model_id=model_id,
            lang=lang or "eng",
            pages_sel=pages,
        )
        return parser.extract()

    def _build_result(self, res: AnalyzeResult, model_id: str) -> CloudExtractionResult:
        pages = ["".join(line.content+"\n" for line in p.lines) for p in getattr(res,"pages",[])]
        if model_id=="prebuilt-read":
            return CloudExtractionResult(text_pages=pages)
        tbls,kvs = [],[]
        for t in getattr(res,"tables",[]) or []:
            mat=[["" for _ in range(t.column_count)] for _ in range(t.row_count)]
            for c in t.cells: mat[c.row_index][c.column_index]=c.content
            tbls.append(mat)
        for pair in getattr(res,"key_value_pairs",[]) or []:
            if pair.key and pair.value:
                kvs.append(KeyValue(pair.key.content.strip(),pair.value.content.strip()))
        return CloudExtractionResult(text_pages=pages, tables=tbls, _raw_key_value=kvs)



# ────────────────────────────────────────────────────────────────────
#  Parser DOCX + Azure OCR
# ────────────────────────────────────────────────────────────────────

class _DocxParser:
    def __init__(self, parent: "AzureOcr", blob: bytes,
                 model_id: str, lang: str, pages_sel: Sequence[int] | None,
                 debug: bool = False) -> None:
        self._parent  = parent
        self._zf      = zipfile.ZipFile(io.BytesIO(blob))
        self._model   = model_id
        self._lang    = lang
        self._debug   = debug
        self._pages_sel = pages_sel  # 1-based list or None

        self._rels: Dict[str,str] = {}
        self._ocr_cache: Dict[str, CloudExtractionResult] = {}
        self._pages: List[str] = []
        self._buf:   List[str] = []
        self._tables: List[List[List[str]]] = []
        self._kvs:    List[KeyValue] = []

        self._load_relationships()

    def extract(self) -> CloudExtractionResult:
        parts = [(n, self._zf.read(n)) for n in sorted(self._zf.namelist())
                 if n.endswith(".xml") and (
                        n == "word/document.xml"
                        or _HEADER_RX.fullmatch(n)
                        or _FOOTER_RX.fullmatch(n))]

        emit = self._buf.append
        for _name, data in parts:
            for _ev, el in ET.iterparse(io.BytesIO(data), events=("end",)):
                tag = el.tag
                if tag == qn("w","t"):        emit(el.text or "")
                elif tag == qn("w","tab"):    emit("\t")
                elif tag in (qn("w","br"), qn("w","cr")): emit("\n")
                elif tag == qn("w","p"):      emit("\n\n")
                elif tag == qn("w","lastRenderedPageBreak"):
                    self._flush_page()
                elif tag == qn("a","blip"):
                    self._handle_image(el.get(qn("r","embed")), emit)
                elif tag == qn("v","imagedata"):
                    self._handle_image(el.get(qn("r","id")), emit)
                el.clear()

        self._flush_page()
        self._zf.close()

        # — filter page —
        pages = self._pages
        if self._pages_sel:
            sel = [p-1 for p in self._pages_sel if 1 <= p <= len(pages)]
            pages = [pages[i] for i in sel]

        return CloudExtractionResult(
            text_pages=pages,
            tables=self._tables,
            _raw_key_value=self._kvs
        )

    # ---------------- internals ----------------
    def _flush_page(self):
        self._pages.append("".join(self._buf).strip())
        self._buf.clear()

    def _load_relationships(self):
        for n in self._zf.namelist():
            if not _RELS_RX.fullmatch(n): continue
            for rel in ET.fromstring(self._zf.read(n)):
                rid, tgt = rel.get("Id"), rel.get("Target")
                if rid and tgt:
                    tgt = tgt.replace("\\","/").lstrip("/")
                    while tgt.startswith("../"): tgt = tgt[3:]
                    self._rels[rid] = tgt

    def _handle_image(self, rid: str | None, emit: Callable[[str],None]):
        if not rid or rid not in self._rels:
            return
        target = self._rels[rid]
        if target not in self._ocr_cache:
            member = f"word/{target}" if not target.startswith("word/") else target
            try:
                img_bytes = self._zf.read(member)
            except KeyError:                      
                return
            res = self._parent._make_call(
                img_bytes, self._model, Path(target).suffix.lstrip("."), self._lang
            )
            self._ocr_cache[target] = self._parent._build_result(res, self._model)

        ocr_res = self._ocr_cache[target]
        self._tables.extend(ocr_res.tables)
        self._kvs.extend(ocr_res._raw_key_value)

        emit("\n" + ocr_res.text.strip() + "\n")
