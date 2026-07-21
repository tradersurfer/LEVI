"""Small synthetic fixtures for evidence-ingestion tests."""

from __future__ import annotations

import base64
from pathlib import Path

from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject


def encryption_key() -> str:
    return base64.urlsafe_b64encode(b"k" * 32).decode("ascii")


def make_image(path: Path, size: tuple[int, int] = (120, 80)) -> Path:
    Image.new("RGB", size, color=(12, 34, 56)).save(path)
    return path


def make_pdf(path: Path, text: str | None = None, *, encrypted: bool = False) -> Path:
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=200)
    if text:
        safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        stream = DecodedStreamObject()
        stream.set_data(f"BT /F1 12 Tf 20 150 Td ({safe}) Tj ET".encode("latin-1"))
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        })
        resources = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})
        })
        page[NameObject("/Resources")] = resources
        page[NameObject("/Contents")] = writer._add_object(stream)
    if encrypted:
        writer.encrypt("secret")
    with path.open("wb") as handle:
        writer.write(handle)
    return path
