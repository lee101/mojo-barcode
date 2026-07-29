from barcode import (
    BPtr,
    IPtr,
    digit,
    ean,
    ean8,
    encode_codabar,
    encode_code128,
    encode_code39,
    encode_itf,
)


@export("mb_check_digit")
def mb_check_digit(src_addr: Int, n: Int) abi("C") -> Int:
    if src_addr == 0 or n <= 0:
        return -1
    var src = BPtr(unsafe_from_address=src_addr)
    var total = 0
    var weight = 3
    for i in range(n - 1, -1, -1):
        total += digit(src, i) * weight
        weight = 1 if weight == 3 else 3
    return (10 - total % 10) % 10


@export("mb_ean")
def mb_ean(
    src_addr: Int, n: Int, dst_addr: Int, dst_capacity: Int, guard: Int
) abi("C") -> Int:
    var required = 7 * n + 4
    if src_addr == 0 or dst_addr == 0 or n < 8 or dst_capacity < required:
        return -1
    return ean(
        BPtr(unsafe_from_address=src_addr),
        n,
        BPtr(unsafe_from_address=dst_addr),
        guard != 0,
    )


@export("mb_ean8")
def mb_ean8(
    src_addr: Int, n: Int, dst_addr: Int, dst_capacity: Int, guard: Int
) abi("C") -> Int:
    if src_addr == 0 or dst_addr == 0 or n != 8 or dst_capacity < 67:
        return -1
    return ean8(
        BPtr(unsafe_from_address=src_addr),
        BPtr(unsafe_from_address=dst_addr),
        guard != 0,
    )


@export("mb_ean13_batch")
def mb_ean13_batch(
    src_addr: Int, src_length: Int, dst_addr: Int, dst_capacity: Int
) abi("C") -> Int:
    if (
        src_addr == 0
        or dst_addr == 0
        or src_length < 0
        or src_length % 13 != 0
        or dst_capacity < (src_length // 13) * 95
    ):
        return -1
    var src = BPtr(unsafe_from_address=src_addr)
    var dst = BPtr(unsafe_from_address=dst_addr)
    var count = src_length // 13
    for row in range(count):
        _ = ean(src + row * 13, 13, dst + row * 95, False)
    return count * 95


@export("mb_code39")
def mb_code39(
    src_addr: Int, n: Int, dst_addr: Int, dst_capacity: Int
) abi("C") -> Int:
    if src_addr == 0 or dst_addr == 0 or n < 0 or dst_capacity < 16 * n + 31:
        return -1
    return encode_code39(
        BPtr(unsafe_from_address=src_addr), n, BPtr(unsafe_from_address=dst_addr)
    )


@export("mb_code128")
def mb_code128(
    src_addr: Int,
    n: Int,
    dst_addr: Int,
    dst_capacity: Int,
    codes_addr: Int,
    codes_capacity: Int,
    fnc1_special: Int,
) abi("C") -> Int:
    if (
        src_addr == 0
        or dst_addr == 0
        or codes_addr == 0
        or n < 0
        or dst_capacity < 24 * n + 64
        or codes_capacity < 2 * n + 8
    ):
        return -1
    return encode_code128(
        BPtr(unsafe_from_address=src_addr),
        n,
        BPtr(unsafe_from_address=dst_addr),
        IPtr(unsafe_from_address=codes_addr),
        fnc1_special != 0,
    )


@export("mb_itf")
def mb_itf(
    src_addr: Int, n: Int, narrow: Int, wide: Int, dst_addr: Int, dst_capacity: Int
) abi("C") -> Int:
    if (
        src_addr == 0
        or dst_addr == 0
        or n < 2
        or n % 2 != 0
        or narrow <= 0
        or wide <= 0
        or dst_capacity < (5 * n + 7) * max(narrow, wide)
    ):
        return -1
    return encode_itf(
        BPtr(unsafe_from_address=src_addr),
        n,
        narrow,
        wide,
        BPtr(unsafe_from_address=dst_addr),
    )


@export("mb_codabar")
def mb_codabar(
    src_addr: Int, n: Int, narrow: Int, wide: Int, dst_addr: Int, dst_capacity: Int
) abi("C") -> Int:
    if (
        src_addr == 0
        or dst_addr == 0
        or n < 2
        or narrow <= 0
        or wide <= 0
        or dst_capacity < (8 * n - 1) * max(narrow, wide)
    ):
        return -1
    return encode_codabar(
        BPtr(unsafe_from_address=src_addr),
        n,
        narrow,
        wide,
        BPtr(unsafe_from_address=dst_addr),
    )
