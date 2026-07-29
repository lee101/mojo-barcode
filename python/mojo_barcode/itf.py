from __future__ import annotations

from . import _lib
from .base import Barcode
from .errors import IllegalCharacterError


MIN_SIZE = 0.2
MIN_QUIET_ZONE = 6.4


class ITF(Barcode):
    name = "ITF"

    def __init__(self, code, writer=None, narrow=2, wide=5) -> None:
        if not code.isdigit():
            raise IllegalCharacterError("ITF code can only contain numbers.")
        if len(code) % 2:
            code = "0" + code
        self.code = code
        self.writer = writer or self.default_writer()
        self.narrow = narrow
        self.wide = wide

    def __str__(self) -> str:
        return self.code

    def get_fullcode(self):
        return self.code

    def build(self) -> list[str]:
        return [_lib.encode_itf(self.code, self.narrow, self.wide)]

    def render(self, writer_options, text=None):
        options = {
            "module_width": MIN_SIZE / self.narrow,
            "quiet_zone": MIN_QUIET_ZONE,
        }
        options.update(writer_options or {})
        return super().render(options, text)
