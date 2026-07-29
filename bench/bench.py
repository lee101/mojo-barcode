from __future__ import annotations

import math
import os
import platform
import sys
import time

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "python")
)

import barcode as upstream  # noqa: E402
import mojo_barcode as mb  # noqa: E402


def timeit(function, repeat=5):
    best = math.inf
    result = None
    for _ in range(repeat):
        start = time.perf_counter()
        result = function()
        best = min(best, time.perf_counter() - start)
    return best, result


def main() -> None:
    batch = [
        f"5901234{i:05d}{mb._lib.check_digit(f'5901234{i:05d}')}"
        for i in range(100_000)
    ]
    code39_text = "MOJO-BARCODE 1234567890/" * 4_000
    numeric = "1234567890" * 20_000
    itf_numeric = "1234567890" * 1_000

    cases = [
        (
            "EAN-13 batch (100k)",
            lambda: mb.encode_ean13_batch(batch),
            lambda: [
                upstream.get("ean13", value[:12]).build()[0]
                for value in batch
            ],
        ),
        (
            "Code 39 (100k chars)",
            lambda: mb.Code39(code39_text, add_checksum=False).build(),
            lambda: upstream.get(
                "code39", code39_text, options={"add_checksum": False}
            ).build(),
        ),
        (
            "Code 128-C (200k digits)",
            lambda: mb.Code128(numeric).build(),
            lambda: upstream.get("code128", numeric).build(),
        ),
        (
            "ITF (10k digits)",
            lambda: mb.ITF(itf_numeric).build(),
            lambda: upstream.get("itf", itf_numeric).build(),
        ),
    ]

    mb.EAN13("400614457735").build()
    print(f"Machine: {platform.processor() or platform.machine()}; {platform.platform()}")
    print()
    print("| Case | mojo-barcode | python-barcode | Speedup |")
    print("|---|---:|---:|---:|")
    for name, ours, reference in cases:
        mojo_seconds, mojo_result = timeit(ours)
        python_seconds, python_result = timeit(reference)
        assert mojo_result == python_result
        print(
            f"| {name} | {mojo_seconds * 1000:.2f} ms | "
            f"{python_seconds * 1000:.2f} ms | "
            f"{python_seconds / mojo_seconds:.2f}x |"
        )


if __name__ == "__main__":
    main()
