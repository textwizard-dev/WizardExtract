=============
Extract Text
=============

Text extraction from documents and in-memory binaries with optional OCR.  
Designed for heterogeneous inputs (PDF, Office, images, CSV, HTML/XML) and selective processing of **pages** and **sheets**. When ``ocr=True``, raster pages are recognized with **Tesseract** while digitally born text is read directly. Returns a single Unicode string.

.. note::
   For OCR capabilities, ensure you have `Tesseract <https://github.com/tesseract-ocr/tesseract>`_ installed on your system.

Supported formats
=================

+-----------+-------------+
| Format    | OCR option  |
+===========+=============+
| PDF       | Optional    |
+-----------+-------------+
| DOC       | No          |
+-----------+-------------+
| DOCX      | Optional    |
+-----------+-------------+
| XLSX      | No          |
+-----------+-------------+
| XLS       | No          |
+-----------+-------------+
| TXT       | No          |
+-----------+-------------+
| CSV       | No          |
+-----------+-------------+
| JSON      | No          |
+-----------+-------------+
| HTML      | No          |
+-----------+-------------+
| HTM       | No          |
+-----------+-------------+
| TIF       | Default     |
+-----------+-------------+
| TIFF      | Default     |
+-----------+-------------+
| JPG/JPEG  | Default     |
+-----------+-------------+
| PNG       | Default     |
+-----------+-------------+
| GIF       | Default     |
+-----------+-------------+

Parameters
==========

+---------------------------+--------------------------------------------------------------------------+
| **Parameter**             | **Description**                                                          |
+===========================+==========================================================================+
| ``input_data``            | (*str | bytes | Path*) Source to extract from: path string, bytes, or    |
|                           | ``pathlib.Path``.                                                        |
+---------------------------+--------------------------------------------------------------------------+
| ``extension``             | (*str, optional*) File extension when ``input_data`` is bytes            |
|                           | (e.g., ``"pdf"``, ``"png"``, ``"xlsx"``).                                |
+---------------------------+--------------------------------------------------------------------------+
| ``pages``                 | (*int | str | list[int|str] | None*) Page/sheet selection. For paged     |
|                           | formats use numbers and ranges (``1``, ``"2-5"``, ``[1, "5-7"]``). For   |
|                           | spreadsheets pass sheet index, name, or a mixed list.                    |
+---------------------------+--------------------------------------------------------------------------+
| ``ocr``                   | (*bool, optional*) Enable Tesseract OCR for images and scanned PDFs/     |
|                           | DOCX. Defaults to ``False``.                                             |
+---------------------------+--------------------------------------------------------------------------+
| ``language_ocr``          | (*str, optional*) Tesseract language code. Defaults to ``"eng"``.        |
+---------------------------+--------------------------------------------------------------------------+


Detailed parameters and examples
================================

``input_data``
--------------

Accepts a filesystem path, a ``pathlib.Path``, or raw ``bytes``.

**Path string**

.. code-block:: python

   import wizardextract as we
   text = we.extract_text("docs/report.pdf")

**pathlib.Path**

.. code-block:: python

   from pathlib import Path
   import wizardextract as we
   text = we.extract_text(Path("docs/report.pdf"))

**Bytes (must set ``extension``)**

.. code-block:: python

   from pathlib import Path
   import wizardextract as we
   raw = Path("img.png").read_bytes()
   text = we.extract_text(raw, extension="png")

**BytesIO (streams)**

.. code-block:: python

   import io, wizardextract as we
   buf = io.BytesIO(open("img.png", "rb").read())
   text = we.extract_text(buf.getvalue(), extension="png")

``extension``
-------------

Required only when passing ``bytes``. Indicates the file type.

**Example**

.. code-block:: python

   import wizardextract as we
   png_bytes = open("img.png", "rb").read()
   text = we.extract_text(png_bytes, extension="png")

.. warning::
   Passing bytes without ``extension`` raises a validation error.

``pages``
---------

Select pages (PDF/DOCX/TIFF) or sheets (XLSX/XLS).

Accepted forms by format:

- **Paged (PDF, DOCX, TIFF)** — 1-based:
  - single int: ``1``
  - range string: ``"1-3"``
  - CSV string: ``"1,3,5-7"``
  - mixed list: ``[1, 3, "5-7"]``
  Invalid tokens and out-of-range pages are silently skipped.

- **Spreadsheets (XLSX/XLS)**:
  - sheet index **0-based** (``int``) — e.g. ``0``
  - sheet name (``str``) — e.g. ``"Summary"``
  - list of the above — e.g. ``[0, "Q4", 5, 6]``
  **Range strings like** ``"5-7"`` **are not supported** for sheets; use explicit indices (``[5, 6, 7]``).

- **Images**:
  - JPG/PNG/GIF: page selection is ignored (single frame).
  - **TIFF multipage**: pass a **list of 1-based integers** (e.g. ``[1, 3, 5]``).

- **TXT/CSV/HTML/JSON**: ``pages`` is ignored.

**Examples — paged**

.. code-block:: python

   import wizardextract as we
   page1  = we.extract_text("docs/big.pdf", pages=1)
   subset = we.extract_text("docs/big.pdf", pages=[1, 3, "5-7"])

**Examples — spreadsheets**

.. code-block:: python

   import wizardextract as we
   first  = we.extract_text("tables.xlsx", pages=0)               # first sheet (0-based)
   named  = we.extract_text("tables.xlsx", pages="Summary")       # sheet by name
   multi  = we.extract_text("tables.xlsx", pages=[0, "Q4", 5, 6]) # explicit indices; no "5-7"

----------------------------

Enable OCR for raster content and scanned documents. ``language_ocr`` controls the recognition language.

**Images**

.. code-block:: python

   import wizardextract as we
   img_txt = we.extract_text("scan.tiff", ocr=True)               # default 'eng'

**Scanned PDF**

.. code-block:: python

   import wizardextract as we
   pdf_txt = we.extract_text("contract_scanned.pdf", ocr=True, language_ocr="ita")

Returns
=======

``str`` — concatenated Unicode text from the selected pages/sheets.

Errors
======

- Bytes without ``extension`` → validation error.
- Unsupported or invalid input → domain-specific error.
- Missing or unreadable file → I/O error.

See also
========

- :doc:`azure_ocr` — Cloud OCR for text, tables, and key-value
- :doc:`intro` — Overview and quick start
