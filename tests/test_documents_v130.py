"""Regression coverage for v130 document processing and OCR."""

import json
import tempfile
import os
from pathlib import Path

from pealang.documents import (
    build_document_namespace,
    detect_format,
    ocr_available,
    read_csv,
    read_document,
    read_docx,
    read_html,
    read_json,
    read_jsonl,
    read_pdf_text,
    read_text_file,
    read_xlsx,
    read_xml,
    strip_html_tags,
)


def test_detect_format():
    assert detect_format("a.csv") == "csv"
    assert detect_format("a.pdf") == "pdf"
    assert detect_format("a.docx") == "docx"
    assert detect_format("a.xlsx") == "xlsx"
    assert detect_format("a.txt") == "text"


def test_strip_html_tags():
    html = "<p>Hello <b>world</b></p>"
    assert strip_html_tags(html) == "Hello world"


def test_read_text_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("hello world")
        path = f.name
    try:
        assert read_text_file(path) == "hello world"
    finally:
        os.unlink(path)


def test_read_csv():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        f.write("name,age\nAlice,30\nBob,25\n")
        path = f.name
    try:
        rows = read_csv(path)
        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
    finally:
        os.unlink(path)


def test_read_json():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"a": 1}, f)
        path = f.name
    try:
        data = read_json(path)
        assert data == {"a": 1}
    finally:
        os.unlink(path)


def test_read_jsonl():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        f.write('{"a": 1}\n{"a": 2}\n')
        path = f.name
    try:
        rows = read_jsonl(path)
        assert len(rows) == 2
    finally:
        os.unlink(path)


def test_read_xml():
    xml = '<?xml version="1.0"?><root><item id="1">hello</item></root>'
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
        f.write(xml)
        path = f.name
    try:
        data = read_xml(path)
        assert data["tag"] == "root"
        assert data["children"][0]["text"] == "hello"
    finally:
        os.unlink(path)


def test_read_html():
    html = "<html><head><title>Test</title></head><body><p>Hello</p><a href='/x'>link</a></body></html>"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html)
        path = f.name
    try:
        data = read_html(path)
        assert data["title"] == "Test"
        assert "Hello" in data["text"]
        assert "/x" in data["links"]
    finally:
        os.unlink(path)


def test_read_document():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("hello")
        path = f.name
    try:
        result = read_document(path)
        assert result["format"] == "text"
        assert result["content"] == "hello"
    finally:
        os.unlink(path)


def test_ocr_available_returns_bool():
    result = ocr_available()
    assert isinstance(result, bool)


def test_build_document_namespace():
    ns = build_document_namespace()
    assert "read_document" in ns
    assert "ocr_extract_text" in ns
    assert "read_pdf" in ns
    assert "read_docx" in ns
    assert "read_xlsx" in ns
    assert len(ns) >= 15
