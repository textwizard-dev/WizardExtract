==========
Wizard Extract
==========

.. figure:: _static/img/WizardExtractBanner.png
   :alt: WizardExtract Banner
   :width: 800
   :height: 300
   :align: center

.. image:: https://img.shields.io/pypi/v/wizardextract.svg
   :target: https://pypi.org/project/wizardextract/
   :alt: PyPI - Version

.. image:: https://img.shields.io/pypi/dm/wizardextract.svg?label=PyPI%20downloads
   :target: https://pypistats.org/packages/wizardextract
   :alt: PyPI - Downloads/month

.. image:: https://img.shields.io/pypi/l/wizardextract.svg
   :target: https://github.com/textwizard-dev/wizardextract/blob/main/LICENSE
   :alt: License


**WizardExtract**  is a Python library for reliable text extraction from PDFs, Office documents, and images. It supports local OCR with Tesseract and cloud OCR with Azure Document Intelligence. It provides page and sheet selection, hybrid PDF handling that combines native text with OCR, and deterministic I/O. With Azure prebuilt-layout it can also return tables and key-value pairs.


Installation
============

Requires Python 3.9+.

.. code-block:: bash

   pip install wizardextract

Optional extras:

.. code-block:: bash

   # Azure OCR
   pip install "wizardextract[azure]"


.. note::
   For OCR, install `Tesseract <https://github.com/tesseract-ocr/tesseract>`_.  

Quick start
===========

.. code-block:: python

   import wizardextract as we

   text = we.extract_text("example.pdf")
   print(text)


API overview
============

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - Method
     - Purpose
   * - ``extract_text``
     - Local text extraction with optional Tesseract OCR
   * - ``extract_text_azure``
     - Cloud extraction via Azure (text, tables, key-value)


Text extraction
===============

Parameters
----------

- ``input_data``: ``str | bytes | Path``
- ``extension``: Required only if ``input_data`` is ``bytes``.
- ``pages``: Page/sheet selection.
  
  - Paged (PDF, DOCX, TIFF): ``1``, ``"1-3"``, ``[1, 3, "5-8"]``
  - Excel (XLSX/XLS): sheet index (``int``), name (``str``), or mixed list

- ``ocr``: Enable Tesseract OCR for images and scanned PDFs/DOCX.
- ``language_ocr``: OCR language, default ``"eng"``.

Examples
--------

Basic:

.. code-block:: python

   import wizardextract as we
   txt = we.extract_text("docs/report.pdf")
   print(txt)


From bytes:

.. code-block:: python

   from pathlib import Path
   import wizardextract as we

   raw = Path("img.png").read_bytes()
   txt_img = we.extract_text(raw, extension="png")
   print(txt_img)

Paged selection and OCR:

.. code-block:: python

   import wizardextract as we

   sel = we.extract_text("docs/big.pdf", pages=[1, 3, "5-7"])
   ocr_txt = we.extract_text("scan.tiff", ocr=True, language_ocr="ita")
   print(sel); print(ocr_txt)


Supported Formats
-----------------

+---------+----------+
| Format  | OCR      |
+=========+==========+
| PDF     | Optional |
+---------+----------+
| DOC     | No       |
+---------+----------+
| DOCX    | Optional |
+---------+----------+
| XLSX    | No       |
+---------+----------+
| XLS     | No       |
+---------+----------+
| TXT     | No       |
+---------+----------+
| CSV     | No       |
+---------+----------+
| JSON    | No       |
+---------+----------+
| HTML    | No       |
+---------+----------+
| HTM     | No       |
+---------+----------+
| TIF     | Default  |
+---------+----------+
| TIFF    | Default  |
+---------+----------+
| JPG     | Default  |
+---------+----------+
| JPEG    | Default  |
+---------+----------+
| PNG     | Default  |
+---------+----------+
| GIF     | Default  |
+---------+----------+

Azure OCR
=========

Parameters
----------

- ``input_data``: ``str | bytes | Path``
- ``extension``: File extension when ``bytes`` are passed.
- ``language_ocr``: OCR language code (ISO-639).
- ``pages``: Page selection (``int``, ``"1,3,5-7"``, or list).
- ``azure_endpoint``: Azure Document Intelligence endpoint URL.
- ``azure_key``: Azure API key.
- ``azure_model_id``: ``"prebuilt-read"`` (text only) or ``"prebuilt-layout"`` (text + tables + key-value).
- ``hybrid``: If ``True``, for PDFs: native text for text pages and OCR for raster pages.

Example
-------

.. code-block:: python

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
   print(res.pretty_tables)
   print(res.key_value)
   
License
=======

`AGPL-3.0-or-later <_static/LICENSE>`_.

Resources
=========

- `PyPI Package <https://pypi.org/project/wizardextract/>`_
- `Documentation <https://wizardextract.readthedocs.io/en/latest/>`_
- `GitHub Repository <https://github.com/textwizard-dev/wizardextract>`_

.. _contact_author:

Contact & Author
================

:Author: Mattia Rubino
:Email: `textwizard.dev@gmail.com <mailto:wizardextract.dev@gmail.com>`_