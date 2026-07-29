from __future__ import annotations

from io import BytesIO
import ctypes

import barcode as upstream
import pytest

import mojo_barcode as mb
from mojo_barcode import _lib
from mojo_barcode.errors import (
    BarcodeError,
    BarcodeNotFoundError,
    IllegalCharacterError,
    NumberOfDigitsError,
    WrongCountryCodeError,
)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("ean13", "400614457735"),
        ("ean8", "6032299"),
        ("ean14", "1234567891258"),
        ("jan", "491400614457"),
        ("upca", "03600029145"),
        ("isbn13", "978376926085"),
        ("code39", "Code39"),
        ("code128", "Wikipedia"),
        ("code128", "1234567890"),
        ("itf", "12345"),
        ("itf", "1234567890"),
    ],
)
def test_patterns_and_full_codes_match_upstream(name, value):
    reference = upstream.get(name, value)
    encoded = mb.get(name, value)
    assert encoded.get_fullcode() == reference.get_fullcode()
    assert encoded.build() == reference.build()


@pytest.mark.parametrize(
    ("name", "value", "fullcode"),
    [
        ("ean13", "400614457735", "4006144577350"),
        ("ean8", "6032299", "60322999"),
        ("ean14", "1234567891258", "12345678912589"),
        ("jan", "491400614457", "4914006144575"),
        ("upca", "03600029145", "036000291452"),
        ("code39", "Code39", "CODE39W"),
        ("pzn", "103940", "PZN-1039406"),
        ("isbn10", "376926085", "9783769260854"),
        ("isbn13", "978376926085", "9783769260854"),
        ("issn", "6727893", "9776727893003"),
    ],
)
def test_published_checksum_vectors(name, value, fullcode):
    assert mb.get(name, value).get_fullcode() == fullcode


def test_ean8_published_bit_vector():
    expected = "1010100011000110100100110101111010101000100100010011100101001000101"
    assert mb.EAN8("40267708").build() == [expected]


def test_all_ean13_leading_digit_parity_patterns_match_upstream():
    for leading in "0123456789":
        value = leading + "59553401690"
        assert mb.EAN13(value).build() == upstream.get("ean13", value).build()


def test_guard_bar_patterns_match_current_upstream_vectors():
    expected = "G0G01000110001101001001101011110G0G01000100100010011100101001000G0G"
    code = mb.get("ean8", "40267708", options={"guardbar": True})
    assert code.build() == [expected]
    assert code.to_ascii().count("|") == expected.count("G") + expected.count("1")


@pytest.mark.parametrize(
    ("value", "encoded"),
    [
        ("Wikipedia", [104, 55, 73, 75, 73, 80, 69, 68, 73, 65]),
        ("9912345678", [105, 99, 12, 34, 56, 78]),
        ("12A", [105, 12, 100, 33]),
        ("123ABC456", [105, 12, 100, 19, 33, 34, 35, 20, 21, 22]),
    ],
)
def test_code128_symbol_vectors(value, encoded):
    code = mb.Code128(value)
    assert code.encoded == encoded
    assert code.build() == code.build()


def test_gs1_128_adds_fnc1_but_hides_it_from_text():
    plain = "00376401856400470087"
    code = mb.Gs1_128(plain)
    assert code.get_fullcode() == plain
    assert code.encoded == [105, 102, 0, 37, 64, 1, 85, 64, 0, 47, 0, 87]
    assert code.build() == [
        "110100111001111010111011011001100100011010001010000110011001101100100"
        "111100101010000110011011001100100011101101101100110011110010100101000"
        "110001100011101011"
    ]


def _codabar_reference(code: str, narrow: int = 2, wide: int = 5) -> str:
    data = {
        "0": "NnNnNwW",
        "1": "NnNnWwN",
        "2": "NnNwNnW",
        "3": "WwNnNnN",
        "4": "NnWnNwN",
        "5": "WnNnNwN",
        "6": "NwNnNnW",
        "7": "NwNnWnN",
        "8": "NwWnNnN",
        "9": "WnNwNnN",
        "-": "NnNwWnN",
        "$": "NnWwNnN",
        ":": "WnNnWnW",
        "/": "WnWnNnW",
        ".": "WnWnWnN",
        "+": "NnWnWnW",
    }
    ends = {
        "A": "NnWwNwN",
        "B": "NwNwNnW",
        "C": "NnNwNwW",
        "D": "NnNwWwN",
    }
    widths = ends[code[0]] + "n"
    widths += "n".join(data[char] for char in code[1:-1])
    widths += "n" + ends[code[-1]]
    return "".join(
        ("1" if char in "WN" else "0")
        * (wide if char in "Ww" else narrow)
        for char in widths
    )


@pytest.mark.parametrize("value", ["A1234B", "C90-$:/.+D"])
def test_codabar_matches_independent_reference(value):
    assert mb.CODABAR(value).build() == [_codabar_reference(value)]


def test_batch_ean13_matches_upstream():
    bases = [f"5901234{i:05d}" for i in range(250)]
    complete = [upstream.get("ean13", value).get_fullcode() for value in bases]
    expected = [upstream.get("ean13", value).build()[0] for value in complete]
    assert mb.encode_ean13_batch(complete) == expected


@pytest.mark.parametrize("size", [1, 17])
def test_code39_simd_tail(size):
    unit = upstream.get(
        "code39", "A", options={"add_checksum": False}
    ).build()[0]
    expected = unit[:15] + unit[15:31] * size + unit[31:]
    assert mb.Code39("A" * size, add_checksum=False).build() == [expected]


def test_code39_all_packed_records_match_upstream():
    value = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ-. $/+%"
    reference = upstream.get(
        "code39", value, options={"add_checksum": False}
    ).build()
    assert mb.Code39(value, add_checksum=False).build() == reference


def test_registry_aliases_and_class_lookup():
    assert mb.PROVIDED_BARCODES == sorted(mb.PROVIDED_BARCODES)
    assert mb.get("ean") is mb.EAN13
    assert mb.get_barcode_class("nw-7") is mb.CODABAR
    with pytest.raises(BarcodeNotFoundError):
        mb.get("qr")


def test_validation_errors_match_upstream_behavior():
    with pytest.raises(IllegalCharacterError):
        mb.EAN13("ABC")
    with pytest.raises(NumberOfDigitsError):
        mb.EAN13("123")
    with pytest.raises(WrongCountryCodeError):
        mb.JAN("123456789012")
    with pytest.raises(IllegalCharacterError):
        mb.Code128("snowman \N{SNOWMAN}")
    with pytest.raises(BarcodeError):
        mb.CODABAR("X123A").build()
    with pytest.raises(ValueError, match="positive integers"):
        mb.ITF("12", narrow=0).build()
    with pytest.raises(ValueError, match="positive integers"):
        mb.CODABAR("A1B", wide=1.5).build()


def test_code128_current_upstream_odd_numeric_prefix_vector():
    # Current python-barcode starts in C and flushes the odd digit through B.
    assert mb.Code128("007A").encoded == [105, 0, 100, 23, 33]


def test_native_boundary_rejects_null_and_short_buffers():
    native = _lib.lib()
    assert native.mb_check_digit(0, 12) == -1

    source = b"4006144577350"
    output = (ctypes.c_uint8 * 95)()
    assert native.mb_ean(_lib.address(source), 13, _lib.address(output), 94, 0) == -1
    assert native.mb_ean(0, 13, _lib.address(output), 95, 0) == -1

    codes = (ctypes.c_int64 * 10)()
    assert (
        native.mb_code128(
            _lib.address(b"12"),
            2,
            _lib.address(output),
            95,
            _lib.address(codes),
            1,
            0,
        )
        == -1
    )


def test_no_checksum_uses_supplied_digit():
    code = mb.EAN13("8421671433229", no_checksum=True)
    assert code.ean == "8421671433229"
    assert code.calculate_checksum() == 5


def test_ascii_output_has_same_width_as_pattern():
    for code in (mb.EAN13("400614457735"), mb.Code39("ABC"), mb.ITF("1234")):
        assert len(code.to_ascii()) == len(code.build()[0])


def test_svg_render_write_and_generate(tmp_path):
    code = mb.EAN13("400614457735")
    rendered = code.render({"write_text": False})
    assert rendered.startswith(b'<?xml version="1.0"')
    assert b"<svg" in rendered and b"<rect" in rendered
    stream = BytesIO()
    code.write(stream)
    assert stream.getvalue().endswith(b"</svg>")
    path_output = tmp_path / "ean.svg"
    assert mb.generate("ean13", "400614457735", output=path_output) is None
    assert path_output.read_bytes().startswith(b"<?xml")
    filename = mb.generate("ean13", "400614457735", output=str(tmp_path / "saved"))
    assert filename == str(tmp_path / "saved.svg")


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("ean13-guard", "400614457735"),
        ("ean8-guard", "6032299"),
        ("pzn", "103940"),
        ("isbn10", "376926085"),
        ("isbn13", "978376926085"),
        ("issn", "6727893"),
        ("gs1_128", "00376401856400470087"),
        ("codabar", "A1234B"),
    ],
)
def test_every_documented_format_builds_and_renders(name, value):
    code = mb.get(name, value)
    pattern = code.build()
    assert len(pattern) == 1
    assert pattern[0] and set(pattern[0]) <= {"0", "1", "G"}
    assert code.render({"write_text": False}).endswith(b"</svg>")


def test_generate_requires_output():
    with pytest.raises(TypeError, match="'output' cannot be None"):
        mb.generate("ean13", "400614457735")
