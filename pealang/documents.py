"""Multi-format document processing and OCR helpers for PeaLang.

This module provides dependency-light (pure Python) tools for:

* Extracting text and tabular data from common document formats
  (CSV, JSON, JSONL, XML, HTML, plain text, DOCX, XLSX, PDF text).
* OCR (Optical Character Recognition) via system tools (tesseract) when
  available, with a graceful fallback.

No heavy dependencies (no pandas, no PyPDF2, no python-docx) are required at
runtime; formats that need a zip/XML parser use only the standard library.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree


def _read_bytes(path: str) -> bytes:
    return Path(path).read_bytes()


def _read_text(path: str, encoding: str = "utf-8") -> str:
    return Path(path).read_text(encoding=encoding, errors="replace")


# ---------------------------------------------------------------------------
# Plain text / CSV / JSON / JSONL / XML / HTML
# ---------------------------------------------------------------------------

def read_text_file(path: str, encoding: str = "utf-8") -> str:
    return _read_text(path, encoding)


def read_csv(path: str, delimiter: str = ",", encoding: str = "utf-8") -> list[dict[str, Any]]:
    with open(path, newline="", encoding=encoding) as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        return [dict(row) for row in reader]


def read_json(path: str, encoding: str = "utf-8") -> Any:
    return json.loads(Path(path).read_text(encoding=encoding))


def read_jsonl(path: str, encoding: str = "utf-8") -> list[Any]:
    out = []
    for line in Path(path).read_text(encoding=encoding).splitlines():
        line = line.strip()
        if line:
            out.append(json.loads(line))
    return out


def read_xml(path: str, encoding: str = "utf-8") -> dict[str, Any]:
    tree = ElementTree.parse(path)
    root = tree.getroot()

    def _node(el):
        children = [_node(c) for c in el]
        text = (el.text or "").strip()
        attrs = dict(el.attrib)
        if children:
            return {"tag": el.tag, "attrs": attrs, "children": children, "text": text}
        return {"tag": el.tag, "attrs": attrs, "text": text}

    return _node(root)


def strip_html_tags(html: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def read_html(path: str, encoding: str = "utf-8") -> dict[str, Any]:
    raw = _read_text(path, encoding)
    text = strip_html_tags(raw)
    title_match = re.search(r"<title[^>]*>(.*?)</title>", raw, re.DOTALL | re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else ""
    links = re.findall(r'href=["\x27]([^"\x27]+)["\x27]', raw, re.IGNORECASE)
    return {"title": title, "text": text, "links": links, "raw_length": len(raw)}


# ---------------------------------------------------------------------------
# DOCX (zip of XML)
# ---------------------------------------------------------------------------

def read_docx(path: str) -> dict[str, Any]:
    """Extract paragraphs and tables from a .docx file."""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        paragraphs: list[str] = []
        tables: list[list[list[str]]] = []
        if "word/document.xml" in names:
            xml_bytes = z.read("word/document.xml")
            root = ElementTree.fromstring(xml_bytes)
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            for p in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p"):
                texts = [t.text or "" for t in p.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")]
                para = "".join(texts).strip()
                if para:
                    paragraphs.append(para)
            for tbl in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl"):
                table = []
                for tr in tbl.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr"):
                    row = []
                    for tc in tr.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc"):
                        cell_texts = [t.text or "" for t in tc.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")]
                        row.append("".join(cell_texts).strip())
                    table.append(row)
                if table:
                    tables.append(table)
        # headers/footers
        extras = {}
        for name in names:
            if name.startswith("word/header") or name.startswith("word/footer"):
                try:
                    x = ElementTree.fromstring(z.read(name))
                    texts = [t.text or "" for t in x.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")]
                    extras[name] = "".join(texts).strip()
                except Exception:
                    pass
    return {"paragraphs": paragraphs, "tables": tables, "extras": extras, "full_text": "\n".join(paragraphs)}


# ---------------------------------------------------------------------------
# XLSX (zip of XML)
# ---------------------------------------------------------------------------

def _xlsx_shared_strings(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    root = ElementTree.fromstring(z.read("xl/sharedStrings.xml"))
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    out = []
    for si in root.iter(f"{{{ns}}}si"):
        texts = [t.text or "" for t in si.iter(f"{{{ns}}}t")]
        out.append("".join(texts))
    return out


def read_xlsx(path: str, sheet: str | None = None) -> dict[str, Any]:
    """Extract sheets and rows from a .xlsx file."""
    with zipfile.ZipFile(path) as z:
        shared = _xlsx_shared_strings(z)
        ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
        # workbook sheets
        wb_root = ElementTree.fromstring(z.read("xl/workbook.xml"))
        sheets = []
        for sh in wb_root.iter(f"{{{ns}}}sheet"):
            sheets.append({"name": sh.get("name"), "rid": sh.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")})
        # map rid -> target
        rels_root = ElementTree.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        rid_map = {}
        for rel in rels_root.iter("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
            rid_map[rel.get("Id")] = rel.get("Target")
        result_sheets = {}
        for sh in sheets:
            target = rid_map.get(sh["rid"], "")
            if target.startswith("/"):
                target = target.lstrip("/")
            else:
                target = "xl/" + target
            if sheet is not None and sh["name"] != sheet:
                continue
            if target not in z.namelist():
                continue
            root = ElementTree.fromstring(z.read(target))
            rows = []
            for row_el in root.iter(f"{{{ns}}}row"):
                cells = []
                for c in row_el.iter(f"{{{ns}}}c"):
                    cell_type = c.get("t", "n")
                    v_el = c.find(f"{{{ns}}}v")
                    val = v_el.text if v_el is not None else ""
                    if cell_type == "s" and val.isdigit():
                        idx = int(val)
                        val = shared[idx] if idx < len(shared) else val
                    cells.append(val)
                rows.append(cells)
            # Convert first row to header if present
            if rows:
                header = rows[0]
                data_rows = []
                for r in rows[1:]:
                    row_dict = {}
                    for i, h in enumerate(header):
                        row_dict[str(h)] = r[i] if i < len(r) else None
                    data_rows.append(row_dict)
                result_sheets[sh["name"]] = {"header": header, "rows": data_rows, "raw_rows": rows}
            else:
                result_sheets[sh["name"]] = {"header": [], "rows": [], "raw_rows": []}
    return {"sheets": list(result_sheets.keys()), "data": result_sheets}


# ---------------------------------------------------------------------------
# PDF (basic text extraction)
# ---------------------------------------------------------------------------

def read_pdf_text(path: str) -> str:
    """Extract text from a PDF using basic stream parsing (no dependencies)."""
    data = _read_bytes(path)
    text_parts = []
    # Find text between BT and ET operators
    for match in re.finditer(rb"BT\s*(.*?)\s*ET", data, re.DOTALL):
        block = match.group(1)
        # Extract (text) Tj or (text) ' operators
        for t in re.finditer(rb"\(([^)]*)\)\s*Tj", block):
            text_parts.append(t.group(1).decode("latin-1", "replace"))
        for t in re.finditer(rb"\(([^)]*)\)\s*'", block):
            text_parts.append(t.group(1).decode("latin-1", "replace"))
    # Also try TJ arrays
    for match in re.finditer(rb"\[(.*?)\]\s*TJ", data, re.DOTALL):
        block = match.group(1)
        for t in re.finditer(rb"\(([^)]*)\)", block):
            text_parts.append(t.group(1).decode("latin-1", "replace"))
    text = " ".join(text_parts)
    # Unescape PDF octal sequences
    text = re.sub(r"\\(\d{3})", lambda m: chr(int(m.group(1), 8)), text)
    return text.strip()


def read_pdf(path: str) -> dict[str, Any]:
    text = read_pdf_text(path)
    pages = [p.strip() for p in text.split("\f") if p.strip()]
    if not pages:
        pages = [text]
    return {"text": text, "pages": pages, "page_count": len(pages)}


# ---------------------------------------------------------------------------
# OCR
# ---------------------------------------------------------------------------

def ocr_available() -> bool:
    """Return True if a system OCR tool (tesseract) is available."""
    return shutil.which("tesseract") is not None


def ocr_extract_text(image_path: str, language: str = "eng") -> dict[str, Any]:
    """Extract text from an image using tesseract if available."""
    tess = shutil.which("tesseract")
    if tess is None:
        return {
            "ok": False,
            "error": "tesseract not found on PATH; install tesseract-ocr for OCR support",
            "text": "",
            "available": False,
        }
    try:
        result = subprocess.run(
            [tess, str(image_path), "stdout", "-l", language],
            capture_output=True, text=True, timeout=120,
        )
        return {
            "ok": result.returncode == 0,
            "text": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "available": True,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "text": "", "available": True}


def ocr_extract_data(image_path: str, language: str = "eng") -> dict[str, Any]:
    """Extract text and attempt to parse tabular data from an OCR result."""
    result = ocr_extract_text(image_path, language)
    if not result.get("ok"):
        return result
    text = result["text"]
    lines = [ln for ln in text.splitlines() if ln.strip()]
    # Try to detect a simple table (whitespace-separated columns)
    rows = []
    for line in lines:
        cols = [c for c in re.split(r"\s{2,}", line.strip()) if c]
        if len(cols) > 1:
            rows.append(cols)
    result["lines"] = lines
    result["table_rows"] = rows
    result["line_count"] = len(lines)
    return result


# ---------------------------------------------------------------------------
# Unified document reader
# ---------------------------------------------------------------------------

_FORMAT_MAP = {
    ".txt": "text", ".md": "text", ".csv": "csv", ".json": "json",
    ".jsonl": "jsonl", ".xml": "xml", ".html": "html", ".htm": "html",
    ".docx": "docx", ".xlsx": "xlsx", ".pdf": "pdf",
    ".png": "image", ".jpg": "image", ".jpeg": "image", ".tiff": "image",
    ".tif": "image", ".bmp": "image",
}


def detect_format(path: str) -> str:
    ext = Path(path).suffix.lower()
    return _FORMAT_MAP.get(ext, "unknown")


def read_document(path: str) -> dict[str, Any]:
    """Read a document and return extracted content based on its format."""
    fmt = detect_format(path)
    if fmt == "text":
        return {"format": fmt, "content": read_text_file(path)}
    if fmt == "csv":
        return {"format": fmt, "rows": read_csv(path)}
    if fmt == "json":
        return {"format": fmt, "data": read_json(path)}
    if fmt == "jsonl":
        return {"format": fmt, "rows": read_jsonl(path)}
    if fmt == "xml":
        return {"format": fmt, "data": read_xml(path)}
    if fmt == "html":
        return {"format": fmt, "data": read_html(path)}
    if fmt == "docx":
        return {"format": fmt, "data": read_docx(path)}
    if fmt == "xlsx":
        return {"format": fmt, "data": read_xlsx(path)}
    if fmt == "pdf":
        return {"format": fmt, "data": read_pdf(path)}
    if fmt == "image":
        return {"format": fmt, "data": ocr_extract_data(path)}
    return {"format": "unknown", "error": f"Unsupported format: {fmt}"}


def build_document_namespace() -> dict[str, Any]:
    return {
        "read_text": read_text_file,
        "read_csv": read_csv,
        "read_json": read_json,
        "read_jsonl": read_jsonl,
        "read_xml": read_xml,
        "read_html": read_html,
        "strip_html": strip_html_tags,
        "read_docx": read_docx,
        "read_xlsx": read_xlsx,
        "read_pdf": read_pdf,
        "read_pdf_text": read_pdf_text,
        "ocr_available": ocr_available,
        "ocr_extract_text": ocr_extract_text,
        "ocr_extract_data": ocr_extract_data,
        "detect_format": detect_format,
        "read_document": read_document,
    }
