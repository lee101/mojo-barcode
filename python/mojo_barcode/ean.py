from __future__ import annotations

from . import _lib
from .base import Barcode
from .errors import IllegalCharacterError, NumberOfDigitsError, WrongCountryCodeError


SIZES = {
    "SC0": 0.27,
    "SC1": 0.297,
    "SC2": 0.33,
    "SC3": 0.363,
    "SC4": 0.396,
    "SC5": 0.445,
    "SC6": 0.495,
    "SC7": 0.544,
    "SC8": 0.61,
    "SC9": 0.66,
}


class EuropeanArticleNumber13(Barcode):
    name = "EAN-13"
    digits = 12

    def __init__(
        self, ean: str, writer=None, no_checksum: bool = False, guardbar: bool = False
    ) -> None:
        if not ean[: self.digits].isdigit():
            raise IllegalCharacterError(f"EAN code can only contain numbers {ean}.")
        if len(ean) < self.digits:
            raise NumberOfDigitsError(
                f"EAN must have {self.digits} digits, received {len(ean)}."
            )
        base = ean[: self.digits]
        if no_checksum:
            last = (
                int(ean[self.digits])
                if len(ean) > self.digits and ean[self.digits].isdigit()
                else 0
            )
        else:
            last = self.calculate_checksum(base)
        self.ean = f"{base}{last}"
        self.guardbar = guardbar
        self.writer = writer or self.default_writer()

    def __str__(self) -> str:
        return self.ean

    def get_fullcode(self) -> str:
        if self.guardbar:
            return self.ean[0] + " " + self.ean[1:7] + " " + self.ean[7:] + " >"
        return self.ean

    def calculate_checksum(self, value: str | None = None) -> int:
        return _lib.check_digit(value or self.ean[: self.digits])

    def build(self) -> list[str]:
        return [_lib.encode_ean(self.ean, self.guardbar)]

    def to_ascii(self) -> str:
        return self.build()[0].replace("G", "|").replace("1", "|").replace("0", " ")

    def render(self, writer_options: dict | None = None, text: str | None = None):
        options = {"module_width": SIZES["SC2"]}
        options.update(writer_options or {})
        return super().render(options, text)


class EuropeanArticleNumber13WithGuard(EuropeanArticleNumber13):
    name = "EAN-13 with guards"

    def __init__(self, ean, writer=None, no_checksum=False, guardbar=True) -> None:
        super().__init__(ean, writer, no_checksum, guardbar)


class JapanArticleNumber(EuropeanArticleNumber13):
    name = "JAN"
    valid_country_codes = list(range(450, 460)) + list(range(490, 500))

    def __init__(self, jan, *args, **kwargs) -> None:
        if int(jan[:3]) not in self.valid_country_codes:
            raise WrongCountryCodeError(
                "Country code isn't between 450-460 or 490-500."
            )
        super().__init__(jan, *args, **kwargs)


class EuropeanArticleNumber8(EuropeanArticleNumber13):
    name = "EAN-8"
    digits = 7

    def build(self) -> list[str]:
        return [_lib.encode_ean8(self.ean, self.guardbar)]

    def get_fullcode(self):
        if self.guardbar:
            return "< " + self.ean[:4] + " " + self.ean[4:] + " >"
        return self.ean


class EuropeanArticleNumber8WithGuard(EuropeanArticleNumber8):
    name = "EAN-8 with guards"

    def __init__(
        self, ean: str, writer=None, no_checksum: bool = False, guardbar: bool = True
    ) -> None:
        super().__init__(ean, writer, no_checksum, guardbar)


class EuropeanArticleNumber14(EuropeanArticleNumber13):
    name = "EAN-14"
    digits = 13


EAN14 = EuropeanArticleNumber14
EAN13 = EuropeanArticleNumber13
EAN13_GUARD = EuropeanArticleNumber13WithGuard
EAN8 = EuropeanArticleNumber8
EAN8_GUARD = EuropeanArticleNumber8WithGuard
JAN = JapanArticleNumber
