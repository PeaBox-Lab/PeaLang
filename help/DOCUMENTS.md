# Document processing and OCR (v130)

PeaLang provides dependency-light tools for extracting data from multiple
document formats and for OCR (Optical Character Recognition) via system tools.

## Supported formats

Plain text, CSV, JSON, JSONL, XML, HTML, DOCX, XLSX, PDF, and images (OCR).

## Unified reader

`read_document(path)` auto-detects format from the file extension.

## OCR

OCR requires `tesseract` on PATH. Check with `ocr_available()`.