<img src="https://raw.githubusercontent.com/wizardextract-dev/wizardextract/main/asset/WizardExtract%20Banner.png"
     alt="WizardExtract Banner" width="800" height="300">

---

# Wizard Extract
[![PyPI - Version](https://img.shields.io/pypi/v/wizardextract)](https://pypi.org/project/wizardextract/)
[![PyPI - Downloads/month](https://img.shields.io/pypi/dm/wizardextract?label=PyPI%20downloads)](https://pypistats.org/packages/wizardextract)
[![License](https://img.shields.io/pypi/l/wizardextract)](https://github.com/wizardextract-dev/wizardextract/blob/main/LICENSE)


**WizardExtract**  is a Python library for reliable text extraction from PDFs, Office documents, and images. It supports local OCR with Tesseract and cloud OCR with Azure Document Intelligence. It provides page and sheet selection, hybrid PDF handling that combines native text with OCR, and deterministic I/O. With Azure prebuilt-layout it can also return tables and key-value pairs.

---

## Contents

- [Installation](#installation)
- [Quick start](#quick-start)
- [API overview](#api-overview)
- [Text extraction](#text-extraction)
- [Azure OCR](#azure-ocr)
- [License](#license)
- [Resources](#resources)


---
## Installation

Requires Python 3.9+.

~~~bash
pip install wizardextract
~~~

Optional extras:

- **Azure OCR**: `pip install "wizardextract[azure]"`

> For OCR capabilities, ensure you have [Tesseract](https://github.com/tesseract-ocr/tesseract) installed on your system.  

---

## Quick start

~~~python
import wizardextract as we

text = we.extract_text("example.pdf")
print(text)
~~~

---

## API overview

Method | Purpose
---|---
`extract_text` | Local text extraction with optional Tesseract OCR
`extract_text_azure` | Cloud extraction via Azure (text, tables, key-value)

---

## Text extraction

### Parameters

- `input_data`: `[str, bytes, Path]`  
- `extension`: The file extension, required only if `input_data` is `bytes`.  
- `pages`: Page/sheet selection.  
  • Paged (PDF, DOCX, TIFF): `1`, `"1-3"`, `[1, 3, "5-8"]`  
  • Excel (XLSX/XLS): sheet index (`int`), name (`str`), or mixed list  
- `ocr`: Enables OCR using Tesseract. Applies to PDF/DOCX and image-based files.  
- `language_ocr`: Language code for OCR. Defaults to `'eng'`.

### Examples

Basic:

~~~python
import wizardextract as we

txt = we.extract_text("docs/report.pdf")
~~~

From bytes:

~~~python
from pathlib import Path
import wizardextract as we

raw = Path("img.png").read_bytes()
txt_img = we.extract_text(raw, extension="png")
~~~

Paged selection and OCR:

~~~python
import wizardextract as we

sel = we.extract_text("docs/big.pdf", pages=[1, 3, "5-7"])
ocr_txt = we.extract_text("scan.tiff", ocr=True, language_ocr="ita")
~~~

#### **Supported Formats**

| Format | OCR Option |
|---|---|
| PDF | Optional |
| DOC | No |
| DOCX | Optional |
| XLSX | No |
| XLS | No |
| TXT | No |
| CSV | No |
| JSON | No |
| HTML | No |
| HTM | No |
| TIF | Default |
| TIFF | Default |
| JPG | Default |
| JPEG | Default |
| PNG | Default |
| GIF | Default |

---

## Azure OCR

### Parameters

- `input_data`: `[str, bytes, Path]`  
- `extension`: File extension when `bytes` are passed.  
- `language_ocr`: OCR language code (ISO-639).  
- `pages`: Page selection (`int`, `"1,3,5-7"`, or list).  
- `azure_endpoint`: Azure Document Intelligence endpoint URL.  
- `azure_key`: Azure API key.  
- `azure_model_id`: `"prebuilt-read"` (text only) or `"prebuilt-layout"` (text + tables + key-value).  
- `hybrid`: If `True`, for PDFs: native text via PyMuPDF and images via OCR.

### Example

~~~python
import wizardextract as we

res = we.extract_text_azure(
    "invoice.pdf",
    language_ocr="ita",
    azure_endpoint="https://<resource>.cognitiveservices.azure.com/",
    azure_key="<KEY>",
    azure_model_id="prebuilt-layout",
    hybrid=True,
)

print(res.text)
print(res.pretty_tables[:1])
print(res.key_value)
~~~

## License

[AGPL-3.0-or-later](LICENSE).

## RESOURCES

- [GitHub Repository](https://github.com/wizardextract-dev/wizardextract)
- [Documentation](https://wizardextract.readthedocs.io/en/latest/)
- [PyPI Package](https://pypi.org/project/wizardextract/)
---

## Contact & Author

**Author:** Mattia Rubino  
**Email:** <wizardextract.dev@gmail.com>
