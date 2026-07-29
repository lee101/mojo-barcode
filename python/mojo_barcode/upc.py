from __future__ import annotations

from . import _lib
from .base import Barcode
from .errors import IllegalCharacterError, NumberOfDigitsError


class UniversalProductCodeA(Barcode):
    name = "UPC-A"
    digits = 11

    def __init__(self, upc, writer=None, make_ean=False) -> None:
        self.ean = make_ean
        upc = upc[: self.digits]
        if not upc.isdigit():
            raise IllegalCharacterError("UPC code can only contain numbers.")
        if len(upc) != self.digits:
            raise NumberOfDigitsError(
                f"UPC must have {self.digits} digits, not {len(upc)}."
            )
        self.upc = f"{upc}{_lib.check_digit(upc)}"
        self.writer = writer or self.default_writer()

    def __str__(self) -> str:
        return ("0" if self.ean else "") + self.upc

    def get_fullcode(self):
        return str(self)

    def calculate_checksum(self):
        return _lib.check_digit(self.upc[: self.digits])

    def build(self) -> list[str]:
        return [_lib.encode_ean("0" + self.upc)]

    def to_ascii(self) -> str:
        return self.build()[0].replace("1", "|").replace("0", "_")

    def render(self, writer_options=None, text=None):
        options = {"module_width": 0.33}
        options.update(writer_options or {})
        return super().render(options, text)


UPCA = UniversalProductCodeA
