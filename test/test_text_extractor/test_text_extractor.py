from __future__ import annotations

import re
import os
import json
import hashlib
import unicodedata
import difflib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import unittest
import wizardextract as we 

# ── Switches ───────────────────────────────────────────────────────────────────
UPDATE = 1          # 1 = create/update baselines, 0 = use existing baselines
SAVE_ARTIFACTS = 0   # 1 = write artifacts to disk, 0 = skip writing artifacts
OCR_LANG = "eng"    

if os.name == "nt" and "TESSDATA_PREFIX" not in os.environ:
    default_tess = r"C:\Program Files\Tesseract-OCR"
    if Path(default_tess).exists():
        os.environ["TESSDATA_PREFIX"] = default_tess

# ── Paths ──────────────────────────────────────────────────────────────────────
TEST_DIR = Path(__file__).resolve().parent
FILES_DIR = TEST_DIR / "files_test"
BASELINE_PATH = TEST_DIR / "baselines" / "text_extractor.json"
ARTIFACTS_DIR = TEST_DIR / "artifacts"

BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
if SAVE_ARTIFACTS:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Utils ──────────────────────────────────────────────────────────────────────
_WS = re.compile(r"\s+", re.MULTILINE)

def normalize(text: str, ocr: bool) -> str:
    s = unicodedata.normalize("NFKC", text)
    if ocr:
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
        s = s.lower()
    return _WS.sub(" ", s).strip()

def hnorm(s: str) -> str:
    return hashlib.blake2b(s.encode("utf-8", "replace"), digest_size=16).hexdigest()

def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()

def load_baseline() -> dict:
    if BASELINE_PATH.exists():
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return {}

def save_baseline(data: dict) -> None:
    BASELINE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def key(relpath: str, ext: str, ocr: bool, lang: str, pages) -> str:
    return f"{relpath}|ext={ext}|ocr={int(ocr)}|lang={lang}|pages={pages or 'ALL'}"

def tesseract_ready(lang: str) -> tuple[bool, str]:
    """Return (ready, info). Checks if tesseract is callable and lang is available."""
    try:
        out = subprocess.run(
            ["tesseract", "--list-langs"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=True,
        ).stdout
        langs = {
            line.strip()
            for line in out.splitlines()
            if line.strip() and not line.startswith("List of available languages")
        }
        return (lang in langs, f"available={sorted(langs)}")
    except Exception as e:
        return (False, f"tesseract not callable: {e}")

# ── Fixed cases (files in tests/files_test) ────────────────────────────────────
CASES = [
    # Non-OCR deterministic
    dict(rel="file1.txt",  ext="txt",  ocr=False, min_ratio=None),
    dict(rel="file1.csv",  ext="csv",  ocr=False, min_ratio=None),
    dict(rel="file1.html", ext="html", ocr=False, min_ratio=None),
    dict(rel="file1.pdf",  ext="pdf",  ocr=False, min_ratio=None),
    dict(rel="file1.docx", ext="docx", ocr=False, min_ratio=None),
    dict(rel="file1.xlsx", ext="xlsx", ocr=False, min_ratio=None),
    # OCR fuzzy
    dict(rel="file1.jpeg", ext="jpeg", ocr=True,  min_ratio=0.92),
    dict(rel="file1.png",  ext="png",  ocr=True,  min_ratio=0.92),
    dict(rel="file1.tif",  ext="tif",  ocr=True,  min_ratio=0.90),
    dict(rel="file1.pdf",  ext="pdf",  ocr=True,  min_ratio=0.95),
    dict(rel="file1.docx", ext="docx", ocr=True,  min_ratio=0.93),
]

INPUT_MODES = ("path", "bytes", "str") 

# ── Tests ──────────────────────────────────────────────────────────────────────
class TestTextExtractorSnapshots(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snap = load_baseline()
        cls.changed = False
        cls.ocr_ok, cls.ocr_info = tesseract_ready(OCR_LANG)

    def _safe(self, s: str) -> str:
        return re.sub(r"[^\w.-]+", "_", s)

    def _extract_in_mode(self, file_path: Path, ext: str, ocr: bool, lang: str, mode: str) -> str:
        if mode == "path":
            return we.extract_text(input_data=file_path, extension=ext, pages=None, ocr=ocr, language_ocr=lang)
        if mode == "str":
            return we.extract_text(input_data=str(file_path), extension=ext, pages=None, ocr=ocr, language_ocr=lang)
        if mode == "bytes":
            return we.extract_text(input_data=file_path.read_bytes(), extension=ext, pages=None, ocr=ocr, language_ocr=lang)
        raise ValueError(mode)

    def _compare_or_update(self, case_key: str, content: str, ocr: bool, min_ratio):
        n = normalize(content, ocr)
        if UPDATE == 1 or case_key not in self.snap:
            self.snap[case_key] = {
                "text": content,                           # kept for fuzzy OCR diff
                "norm_hash": hnorm(n),                     # deterministic comparison
                "len": len(content),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "min_ratio": min_ratio,
            }
            self.__class__.changed = True
            if UPDATE == 0:
                self.fail(f"Missing baseline for {case_key}. Set UPDATE=1 and re-run.")
        else:
            base = self.snap[case_key]
            if base.get("min_ratio") is None:
                self.assertEqual(base["norm_hash"], hnorm(n), "Snapshot hash mismatch")
            else:
                old_norm = normalize(base["text"], True)
                r = similarity(old_norm, n)
                self.assertGreaterEqual(r, float(base["min_ratio"]), f"OCR similarity {r:.3f} < {base['min_ratio']:.3f}")

    def _run_case(self, c: dict):
        f = FILES_DIR / c["rel"]
        ext, ocr, min_ratio = c["ext"], bool(c["ocr"]), c["min_ratio"]
        k = key(c["rel"], ext, ocr, OCR_LANG, None)

        if ocr and not self.ocr_ok:
            self.skipTest(f"OCR not available ({self.ocr_info}). Check Tesseract and language '{OCR_LANG}'.")
            return

        for mode in INPUT_MODES:
            with self.subTest(key=k, mode=mode):
                content = self._extract_in_mode(f, ext, ocr, OCR_LANG, mode)
                self.assertIsInstance(content, str)
                self.assertGreater(len(content.strip()), 0)
                self._compare_or_update(k, content, ocr, min_ratio)

                if SAVE_ARTIFACTS:
                    (ARTIFACTS_DIR / f"{self._safe(k)}.{mode}.txt").write_text(content, encoding="utf-8")

    def test_all(self):
        for c in CASES:
            self._run_case(c)

    @classmethod
    def tearDownClass(cls):
        if UPDATE == 1 and cls.changed:
            save_baseline(cls.snap)

if __name__ == "__main__":
    unittest.main()
