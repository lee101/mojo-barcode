from __future__ import annotations

from .ean import EuropeanArticleNumber13
from .errors import BarcodeError, WrongCountryCodeError


class InternationalStandardBookNumber13(EuropeanArticleNumber13):
    name = "ISBN-13"

    def __init__(self, isbn, writer=None, no_checksum=False, guardbar=False) -> None:
        isbn = isbn.replace("-", "")
        self.isbn13 = isbn
        if isbn[:3] not in ("978", "979"):
            raise WrongCountryCodeError("ISBN must start with 978 or 979.")
        if isbn[:3] == "979" and isbn[3:4] not in ("1", "8"):
            raise BarcodeError("ISBN must start with 97910 or 97911.")
        super().__init__(isbn, writer, no_checksum, guardbar)


class InternationalStandardBookNumber10(InternationalStandardBookNumber13):
    name = "ISBN-10"
    isbn_digits = 9

    def __init__(self, isbn, writer=None) -> None:
        isbn = isbn.replace("-", "")[: self.isbn_digits]
        super().__init__("978" + isbn, writer)
        self.isbn10 = isbn
        self.isbn10 = f"{isbn}{self._calculate_checksum()}"

    def _calculate_checksum(self):
        value = sum(i * int(char) for i, char in enumerate(self.isbn10[:9], 1)) % 11
        return "X" if value == 10 else value

    def __str__(self) -> str:
        return self.isbn10


class InternationalStandardSerialNumber(EuropeanArticleNumber13):
    name = "ISSN"
    issn_digits = 7

    def __init__(self, issn, writer=None) -> None:
        issn = issn.replace("-", "")[: self.issn_digits]
        self.issn = f"{issn}{self._calculate_checksum(issn)}"
        super().__init__(self.make_ean(), writer)

    def _calculate_checksum(self, value=None):
        source = value if value is not None else self.issn[:7]
        result = (
            11
            - sum(i * int(char) for i, char in enumerate(reversed(source), start=2))
            % 11
        ) % 11
        return "X" if result == 10 else result

    def make_ean(self):
        return f"977{self.issn[:7]}00{self._calculate_checksum()}"

    def __str__(self) -> str:
        return self.issn


ISBN13 = InternationalStandardBookNumber13
ISBN10 = InternationalStandardBookNumber10
ISSN = InternationalStandardSerialNumber
