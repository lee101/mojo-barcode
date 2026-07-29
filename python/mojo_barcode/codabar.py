from __future__ import annotations

from . import _lib
from .base import Barcode
from .errors import BarcodeError, IllegalCharacterError


class CODABAR(Barcode):
    name = "Codabar (NW-7)"
    _data = set("0123456789-$:/.+")

    def __init__(self, code, writer=None, narrow=2, wide=5) -> None:
        self.code = code
        self.writer = writer or self.default_writer()
        self.narrow = narrow
        self.wide = wide

    def __str__(self) -> str:
        return self.code

    def get_fullcode(self):
        return self.code

    def build(self) -> list[str]:
        if not self.code or self.code[0] not in "ABCD":
            raise BarcodeError("Codabar should start with either A,B,C or D")
        if self.code[-1] not in "ABCD":
            raise BarcodeError("Codabar should end with either A,B,C or D")
        if any(char not in self._data for char in self.code[1:-1]):
            raise IllegalCharacterError(
                "Codabar can only contain numerics or $:/.+-"
            )
        return [_lib.encode_codabar(self.code, self.narrow, self.wide)]
