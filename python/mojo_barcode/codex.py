from __future__ import annotations

import re

from . import _lib
from .base import Barcode
from .errors import BarcodeError, IllegalCharacterError, NumberOfDigitsError


MIN_SIZE = 0.2
MIN_QUIET_ZONE = 2.54
CODE39_REF = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%"
CODE39_VALUES = {char: i for i, char in enumerate(CODE39_REF)}
CODE39_INVALID = re.compile(r"[^0-9A-Z. $/+%\-]")
CODE128_SPECIAL = {"ñ", "ò", "ó", "ô"}


class Code39(Barcode):
    name = "Code 39"

    def __init__(self, code: str, writer=None, add_checksum: bool = True) -> None:
        self.code = code.upper()
        invalid = CODE39_INVALID.findall(self.code)
        if invalid:
            raise IllegalCharacterError(
                f"The following characters are not valid for {self.name}: "
                + ", ".join(invalid)
            )
        if add_checksum:
            self.code += self.calculate_checksum()
        self.writer = writer or self.default_writer()

    def __str__(self) -> str:
        return self.code

    def get_fullcode(self) -> str:
        return self.code

    def calculate_checksum(self) -> str:
        value = sum(CODE39_VALUES[char] for char in self.code) % 43
        return CODE39_REF[value]

    def build(self) -> list[str]:
        return [_lib.encode_code39(self.code)]

    def render(self, writer_options=None, text=None):
        options = {"module_width": MIN_SIZE, "quiet_zone": MIN_QUIET_ZONE}
        options.update(writer_options or {})
        return super().render(options, text)


class PZN7(Code39):
    name = "Pharmazentralnummer"
    digits = 6

    def __init__(self, pzn, writer=None) -> None:
        pzn = pzn[: self.digits]
        if not pzn.isdigit():
            raise IllegalCharacterError("PZN can only contain numbers.")
        if len(pzn) != self.digits:
            raise NumberOfDigitsError(
                f"PZN must have {self.digits} digits, not {len(pzn)}."
            )
        self.pzn = pzn
        self.pzn = f"{pzn}{self.calculate_checksum()}"
        super().__init__(f"PZN-{self.pzn}", writer, add_checksum=False)

    def get_fullcode(self):
        return f"PZN-{self.pzn}"

    def calculate_checksum(self):
        total = sum(i * int(char) for i, char in enumerate(self.pzn, start=2))
        checksum = total % 11
        if checksum == 10:
            raise BarcodeError("Checksum can not be 10 for PZN.")
        return checksum


class PZN8(PZN7):
    digits = 7


class Code128(Barcode):
    name = "Code 128"

    def __init__(self, code: str, writer=None) -> None:
        self.code = code
        invalid = [
            char
            for char in code
            if not (ord(char) <= 127 or char in CODE128_SPECIAL)
        ]
        if invalid:
            raise IllegalCharacterError(
                f"The following characters are not valid for {self.name}: "
                + ", ".join(invalid)
            )
        self.writer = writer or self.default_writer()

    def __str__(self) -> str:
        return self.code

    @property
    def encoded(self) -> list[int]:
        return _lib.encode_code128(self.code, self._fnc1_special())[1]

    def _fnc1_special(self) -> bool:
        return False

    def get_fullcode(self) -> str:
        return self.code

    def build(self) -> list[str]:
        return [_lib.encode_code128(self.code, self._fnc1_special())[0]]

    def render(self, writer_options=None, text=None):
        options = {"module_width": MIN_SIZE, "quiet_zone": MIN_QUIET_ZONE}
        options.update(writer_options or {})
        return super().render(options, text)


class Gs1_128(Code128):
    name = "GS1-128"
    FNC1_CHAR = "\xf1"

    def __init__(self, code, writer=None) -> None:
        super().__init__(self.FNC1_CHAR + code, writer)

    def get_fullcode(self):
        return self.code[1:]

    def _fnc1_special(self) -> bool:
        return True


PZN = PZN7
