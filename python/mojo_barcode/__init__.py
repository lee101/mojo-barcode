from __future__ import annotations

import os

from ._lib import encode_ean13_batch
from .base import Barcode
from .codabar import CODABAR
from .codex import PZN, Code39, Code128, Gs1_128
from .ean import EAN8, EAN8_GUARD, EAN13, EAN13_GUARD, EAN14, JAN
from .errors import BarcodeNotFoundError
from .isxn import ISBN10, ISBN13, ISSN
from .itf import ITF
from .upc import UPCA


__version__ = "0.1.0"

_BARCODE_MAP = {
    "codabar": CODABAR,
    "code128": Code128,
    "code39": Code39,
    "ean": EAN13,
    "ean13": EAN13,
    "ean13-guard": EAN13_GUARD,
    "ean14": EAN14,
    "ean8": EAN8,
    "ean8-guard": EAN8_GUARD,
    "gs1": ISBN13,
    "gs1_128": Gs1_128,
    "gtin": EAN14,
    "isbn": ISBN13,
    "isbn10": ISBN10,
    "isbn13": ISBN13,
    "issn": ISSN,
    "itf": ITF,
    "jan": JAN,
    "nw-7": CODABAR,
    "pzn": PZN,
    "upc": UPCA,
    "upca": UPCA,
}

PROVIDED_BARCODES = sorted(_BARCODE_MAP)


def get(name: str, code: str | None = None, writer=None, options: dict | None = None):
    try:
        barcode_class = _BARCODE_MAP[name.lower()]
    except KeyError as error:
        raise BarcodeNotFoundError(f"The barcode {name!r} is not known.") from error
    if code is not None:
        return barcode_class(code, writer, **(options or {}))
    return barcode_class


def get_class(name: str):
    return get(name)


def generate(
    name: str,
    code: str,
    writer=None,
    output=None,
    writer_options: dict | None = None,
    text: str | None = None,
):
    if output is None:
        raise TypeError("'output' cannot be None")
    writer = writer or Barcode.default_writer()
    writer.set_options(writer_options or {})
    barcode = get(name, code, writer)
    if isinstance(output, str):
        return barcode.save(output, writer_options, text)
    if isinstance(output, os.PathLike):
        with open(output, "wb") as stream:
            barcode.write(stream, writer_options, text)
        return None
    barcode.write(output, writer_options, text)
    return None


get_barcode = get
get_barcode_class = get_class
