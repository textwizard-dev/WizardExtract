====================
Extract Text (Azure)
====================

Cloud OCR and layout extraction via **Azure Document Intelligence**.  
Processes scanned and born-digital documents, returning unified text plus optional **tables** and **key-value pairs** (with the *layout* model).  
Supports selective **page** processing and a **hybrid** mode that mixes native extraction with OCR for PDFs.

.. note::
   Requires an Azure resource (endpoint + key). See
   `Azure Document Intelligence <https://learn.microsoft.com/azure/ai-services/document-intelligence/>`_.

Supported formats
=================

+-----------+----------------------------+
| Format    | Notes                      |
+===========+============================+
| PDF       | OCR or hybrid              |
+-----------+----------------------------+
| DOCX      | OCR for embedded images    |
+-----------+----------------------------+
| JPG/JPEG  | OCR                        |
+-----------+----------------------------+
| PNG       | OCR                        |
+-----------+----------------------------+
| TIF/TIFF  | OCR                        |
+-----------+----------------------------+
| GIF       | OCR                        |
+-----------+----------------------------+

Parameters
==========

+---------------------+--------------------------------------------------------------------------+
| **Parameter**       | **Description**                                                          |
+=====================+==========================================================================+
| ``input_data``      | (*str | bytes | Path*) Path string, bytes, or ``pathlib.Path``.          |
+---------------------+--------------------------------------------------------------------------+
| ``extension``       | (*str, optional*) Required if ``input_data`` is bytes (e.g. ``"pdf"``).  |
+---------------------+--------------------------------------------------------------------------+
| ``language_ocr``    | (*str, optional*) OCR language code (ISO). Default ``"eng"``.            |
+---------------------+--------------------------------------------------------------------------+
| ``pages``           | (*int | str | list[int|str] | None*) Page selection: ``1``,              |
|                     | ``"1,3,5-7"`` or mixed list ``[1, 3, "5-7"]``. **1-based.**              |
+---------------------+--------------------------------------------------------------------------+
| ``azure_endpoint``  | (*str*) Azure endpoint URL.                                              |
+---------------------+--------------------------------------------------------------------------+
| ``azure_key``       | (*str*) Azure API key.                                                   |
+---------------------+--------------------------------------------------------------------------+
| ``azure_model_id``  | (*str*) ``"prebuilt-read"`` for text only; ``"prebuilt-layout"`` adds    |
|                     | tables and key-value pairs.                                              |
+---------------------+--------------------------------------------------------------------------+
| ``hybrid``          | (*bool, optional*) PDFs: native text for text pages, OCR for raster.     |
|                     | Default ``False``.                                                       |
+---------------------+--------------------------------------------------------------------------+

Return value
============

``CloudExtractionResult`` with:

+-------------------+-----------------------------------------------------------+
| Field             | Meaning                                                   |
+===================+===========================================================+
| ``text``          | Concatenated full text.                                   |
+-------------------+-----------------------------------------------------------+
| ``text_pages``    | List of page texts (one string per page).                 |
+-------------------+-----------------------------------------------------------+
| ``tables``        | Raw tables as matrices ``list[list[list[str]]]``.         |
+-------------------+-----------------------------------------------------------+
| ``pretty_tables`` | Tables rendered as readable ASCII blocks.                 |
+-------------------+-----------------------------------------------------------+
| ``key_value``     | Dict of extracted key→values (layout model only).         |
+-------------------+-----------------------------------------------------------+

Examples
========

Path string
-----------

.. code-block:: python

   import wizardextract as we

   res = we.extract_text_azure(
       "invoice.pdf",
       azure_endpoint="https://<resource>.cognitiveservices.azure.com/",
       azure_key="<KEY>",
   )
   print(res.text)

Bytes (set ``extension``)
-------------------------

.. code-block:: python

   from pathlib import Path
   import wizardextract as we

   raw = Path("scan.jpg").read_bytes()
   res = we.extract_text_azure(
       raw,
       extension="jpg",
       azure_endpoint="https://<resource>.cognitiveservices.azure.com/",
       azure_key="<KEY>",
   )
   print(res.text)

Page selection (1-based)
------------------------

.. code-block:: python

   import wizardextract as we

   # single page
   p1 = we.extract_text_azure("report.pdf", pages=1, azure_endpoint="...", azure_key="...")

   # ranges and lists
   subset = we.extract_text_azure(
       "report.pdf",
       pages=[1, 3, "5-7"],
       azure_endpoint="...",
       azure_key="...",
   )

Text-only vs Layout (tables + key-value)
----------------------------------------

.. code-block:: python

   import wizardextract as we

   # Fast, plain text
   read = we.extract_text_azure(
       "doc.pdf",
       azure_model_id="prebuilt-read",
       azure_endpoint="...",
       azure_key="...",
   )
   print(read.text_pages[:1])

   # Layout: text + tables + key-value
   layout = we.extract_text_azure(
       "invoice.pdf",
       azure_model_id="prebuilt-layout",
       azure_endpoint="...",
       azure_key="...",
   )
   print(layout.pretty_tables)
   print(layout.key_value)

Hybrid mode (PDF)
-----------------

.. code-block:: python

   import wizardextract as we

   res = we.extract_text_azure(
       "mixed.pdf",
       azure_model_id="prebuilt-layout",
       hybrid=True,                    # native text for text pages, OCR for scanned pages
       azure_endpoint="...",
       azure_key="...",
   )
   print(len(res.text_pages), "pages")

DOCX with embedded images (OCR per image)
-----------------------------------------

.. code-block:: python

   import wizardextract as we

   docx = we.extract_text_azure(
       "contract.docx",
       azure_model_id="prebuilt-layout",   # to collect tables/kv from images too
       language_ocr="ita",                 # image OCR locale; pages are 1-based
       pages=[1, 2],
       azure_endpoint="...",
       azure_key="...",
   )
   print(docx.text_pages[0])
   print(docx.tables and docx.pretty_tables)

Operational notes
=================

- Use ``prebuilt-read`` for text extraction.  
- Use ``prebuilt-layout`` for tables and key-value pairs.  
- **Hybrid** reduces OCR cost on digitally born PDFs while handling scanned pages.  
- ``pages`` applies to **PDF** and **DOCX** (1-based). Ignored for single-image inputs.  
- Some 3-letter locales (e.g. ``"eng"``, ``"ita"``) are normalised to ISO-639-1 (``"en"``, ``"it"``).  
- Azure request limits and file size constraints apply; consult the official docs.

Errors
======

- Missing/invalid ``azure_endpoint`` or ``azure_key`` → authentication error.  
- Unsupported ``azure_model_id`` → configuration error.  
- Unsupported format or unreadable input → validation/I/O error.


See also
========

- :doc:`extract_text` — Local extraction with optional Tesseract OCR  
- :doc:`intro` — Overview and quick start
