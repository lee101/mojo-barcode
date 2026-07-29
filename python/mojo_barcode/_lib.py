from __future__ import annotations

import ctypes
import os
import shutil
import subprocess
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, "src")
LIB = os.environ.get("MOJO_BARCODE_LIB") or os.path.join(
    ROOT, "dist", "libmojo-barcode.so"
)

I = ctypes.c_int64

_SIGNATURES = {
    "mb_check_digit": ([I, I], I),
    "mb_ean": ([I, I, I, I, I], I),
    "mb_ean8": ([I, I, I, I, I], I),
    "mb_ean13_batch": ([I, I, I, I], I),
    "mb_code39": ([I, I, I, I], I),
    "mb_code128": ([I, I, I, I, I, I, I], I),
    "mb_itf": ([I, I, I, I, I, I], I),
    "mb_codabar": ([I, I, I, I, I, I], I),
}


class BuildError(RuntimeError):
    pass


def mojo_command() -> list[str]:
    override = os.environ.get("MOJO_BARCODE_MOJO")
    if override:
        return override.split()
    found = shutil.which("mojo")
    if found:
        return [found]
    pixi = shutil.which("pixi") or os.path.expanduser("~/.pixi/bin/pixi")
    if os.path.exists(pixi):
        return [pixi, "run", "--manifest-path", os.path.join(ROOT, "pixi.toml"), "mojo"]
    raise BuildError("mojo not found; set MOJO_BARCODE_MOJO=/path/to/mojo")


def build(force: bool = False) -> str:
    if os.environ.get("MOJO_BARCODE_LIB") and os.path.exists(LIB) and not force:
        return LIB
    sources = [
        os.path.join(path, name)
        for path, _, names in os.walk(SRC)
        for name in names
        if name.endswith(".mojo")
    ]
    if not sources:
        if os.path.exists(LIB):
            return LIB
        raise BuildError(f"no Mojo sources at {SRC} and no library at {LIB}")
    if not force and os.path.exists(LIB):
        if os.path.getmtime(LIB) >= max(os.path.getmtime(path) for path in sources):
            return LIB
    os.makedirs(os.path.dirname(LIB), exist_ok=True)
    command = mojo_command() + [
        "build",
        "--emit",
        "shared-lib",
        "-I",
        SRC,
        os.path.join(SRC, "capi.mojo"),
        "-o",
        LIB,
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=1800)
    if proc.returncode or not os.path.exists(LIB):
        raise BuildError((proc.stderr or proc.stdout).strip()[:4000])
    return LIB


_loaded: ctypes.CDLL | None = None


def lib() -> ctypes.CDLL:
    global _loaded
    if _loaded is None:
        _loaded = ctypes.CDLL(build())
        for name, (argtypes, restype) in _SIGNATURES.items():
            function = getattr(_loaded, name)
            function.argtypes = argtypes
            function.restype = restype
    return _loaded


def input_buffer(data: bytes):
    return data


def output_buffer(size: int):
    return (ctypes.c_uint8 * size)()


def address(buffer) -> int:
    if isinstance(buffer, bytes):
        value = ctypes.cast(buffer, ctypes.c_void_p).value
        if value is None:
            raise ValueError("buffer has no address")
        return value
    if isinstance(buffer, bytearray):
        return ctypes.addressof((ctypes.c_uint8 * len(buffer)).from_buffer(buffer))
    return ctypes.addressof(buffer)


def output_bytes(buffer, size: int) -> bytes:
    return ctypes.string_at(address(buffer), size)


def checked_output(buffer, capacity: int, result: int) -> str:
    if result < 0:
        raise RuntimeError("native barcode encoder rejected unsafe arguments")
    if result > capacity:
        raise RuntimeError("native barcode encoder returned an invalid length")
    return output_bytes(buffer, result).decode("ascii")


def checked_widths(narrow: int, wide: int) -> tuple[int, int]:
    if (
        isinstance(narrow, bool)
        or isinstance(wide, bool)
        or not isinstance(narrow, int)
        or not isinstance(wide, int)
        or narrow <= 0
        or wide <= 0
    ):
        raise ValueError("narrow and wide must be positive integers")
    return narrow, wide


def check_digit(data: str) -> int:
    raw = input_buffer(data.encode("ascii"))
    result = int(lib().mb_check_digit(address(raw), len(raw)))
    if not 0 <= result <= 9:
        raise RuntimeError("native check digit calculation failed")
    return result


def encode_ean(data: str, guard: bool = False) -> str:
    raw = input_buffer(data.encode("ascii"))
    capacity = 7 * len(raw) + 16
    result = output_buffer(capacity)
    n = lib().mb_ean(address(raw), len(raw), address(result), capacity, int(guard))
    return checked_output(result, capacity, n)


def encode_ean8(data: str, guard: bool = False) -> str:
    raw = input_buffer(data.encode("ascii"))
    capacity = 67
    result = output_buffer(capacity)
    n = lib().mb_ean8(address(raw), len(raw), address(result), capacity, int(guard))
    return checked_output(result, capacity, n)


def encode_ean13_batch(codes) -> list[str]:
    values = list(codes)
    if not values:
        return []
    for value in values:
        if len(value) != 13 or not value.isascii() or not value.isdigit():
            raise ValueError("each batch item must be a complete 13-digit EAN")
    packed = "".join(values).encode("ascii")
    raw = input_buffer(packed)
    capacity = 95 * len(values)
    result = output_buffer(capacity)
    n = lib().mb_ean13_batch(address(raw), len(raw), address(result), capacity)
    if n != capacity:
        raise RuntimeError("native batch encoder failed")
    encoded = bytes(result)
    return [
        encoded[i * 95 : (i + 1) * 95].decode("ascii")
        for i in range(len(values))
    ]


def encode_code39(data: str) -> str:
    raw = input_buffer(data.encode("ascii"))
    capacity = 16 * len(raw) + 31
    result = output_buffer(capacity)
    n = lib().mb_code39(address(raw), len(raw), address(result), capacity)
    return checked_output(result, capacity, n)


_CODE128_MARKERS = {"ñ": 241, "ò": 242, "ó": 243, "ô": 244}


def code128_bytes(data: str) -> bytes | bytearray:
    if data.isascii():
        return data.encode("ascii")
    values = bytearray()
    for char in data:
        point = ord(char)
        if point <= 127:
            values.append(point)
        elif char in _CODE128_MARKERS:
            values.append(_CODE128_MARKERS[char])
        else:
            raise UnicodeEncodeError("code128", char, 0, 1, "unsupported character")
    return values


def encode_code128(data: str, fnc1_special: bool = False) -> tuple[str, list[int]]:
    packed = code128_bytes(data)
    raw = input_buffer(packed)
    capacity = 24 * len(packed) + 64
    codes_capacity = 2 * len(packed) + 8
    result = output_buffer(capacity)
    code_values = (ctypes.c_int64 * codes_capacity)()
    n = lib().mb_code128(
        address(raw),
        len(packed),
        address(result),
        capacity,
        address(code_values),
        codes_capacity,
        int(fnc1_special),
    )
    encoded_count = int(code_values[0])
    if n < 0 or not 0 <= encoded_count < codes_capacity:
        raise RuntimeError("native Code 128 encoder failed")
    encoded = [int(code_values[i]) for i in range(1, encoded_count + 1)]
    return checked_output(result, capacity, n), encoded


def encode_itf(data: str, narrow: int, wide: int) -> str:
    narrow, wide = checked_widths(narrow, wide)
    raw = input_buffer(data.encode("ascii"))
    capacity = (5 * len(raw) + 7) * max(narrow, wide)
    result = output_buffer(capacity)
    n = lib().mb_itf(address(raw), len(raw), narrow, wide, address(result), capacity)
    return checked_output(result, capacity, n)


def encode_codabar(data: str, narrow: int, wide: int) -> str:
    narrow, wide = checked_widths(narrow, wide)
    raw = input_buffer(data.encode("ascii"))
    capacity = (8 * len(raw) - 1) * max(narrow, wide)
    result = output_buffer(capacity)
    n = lib().mb_codabar(
        address(raw), len(raw), narrow, wide, address(result), capacity
    )
    return checked_output(result, capacity, n)


def main() -> int:
    print(build(force="--force" in sys.argv))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
