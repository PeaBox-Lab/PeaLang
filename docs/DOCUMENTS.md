# Document processing and OCR (v130)

PeaLang provides dependency-light tools for extracting data from multiple
document formats and for OCR (Optical Character Recognition) via system tools.

## Supported formats

| Format | Reader | Returns |
|--------|--------|---------|
| Plain text / Markdown | `read_text` | string |
| CSV | `read_csv` | list of dicts |
| JSON | `read_json` | parsed value |
| JSONL | `read_jsonl` | list of values |
| XML | `read_xml` | nested dict |
| HTML | `read_html` | title, text, links |
| DOCX | `read_docx` | paragraphs, tables |
| XLSX | `read_xlsx` | sheets, rows |
| PDF | `read_pdf` | text, pages |
| Images (PNG/JPG/etc.) | `ocr_extract_text` / `ocr_extract_data` | OCR text |

## Unified reader

`read_document(path)` auto-detects format from the file extension and returns
a dict with a `format` key plus extracted content.

## OCR

OCR requires `tesseract` on PATH. Check availability with `ocr_available()`.
`ocr_extract_text(image_path)` returns text; `ocr_extract_data(image_path)`
also attempts to parse tabular data from the OCR result.

## Example

```python
from pealang.analysis import read_document, ocr_available

doc = read_document("report.pdf")
print(doc["data"]["text"])

if ocr_available():
    result = ocr_extract_text("scan.png")
    print(result["text"])
```