class BarcodeError(Exception):
    def __init__(self, msg) -> None:
        self.msg = msg

    def __str__(self) -> str:
        return self.msg


class IllegalCharacterError(BarcodeError):
    pass


class BarcodeNotFoundError(BarcodeError):
    pass


class NumberOfDigitsError(BarcodeError):
    pass


class WrongCountryCodeError(BarcodeError):
    pass
