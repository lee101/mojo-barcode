# mojo-barcode

`mojo-barcode` is a standalone Mojo port of the linear encoding core from
[`python-barcode`](https://github.com/WhyNotHugo/python-barcode). It produces
the module patterns that scanners read and provides a Python API with the same
class names, constructor signatures, registry aliases, checksums, and
`build()`/`render()`/`save()` workflow for the covered formats.

The Python module is named `mojo_barcode` so it can be installed beside the
upstream `barcode` package for parity testing:

```python
import mojo_barcode as barcode
```

## Coverage

The following upstream names and aliases are covered:

- EAN-8, EAN-13, EAN-14, guarded EAN-8/13, JAN, and UPC-A
- ISBN-10, ISBN-13, and ISSN, rendered as EAN-13
- Code 39 and PZN
- Code 128 and GS1-128, including automatic A/B/C charset switching
- Interleaved 2 of 5
- Codabar / NW-7
- `get`, `get_barcode`, `get_barcode_class`, `generate`, `PROVIDED_BARCODES`
- ASCII output and dependency-free SVG rendering, writing, and saving

`encode_ean13_batch()` is an additional native batch API for workloads that
would otherwise make one Python call per barcode.

Not covered:

- Pillow-backed raster output (`ImageWriter`)
- the upstream command-line program
- arbitrary callback-based custom writers beyond the compatible writer object
  protocol used by the covered classes
- two-dimensional formats such as QR, Data Matrix, and PDF417; these are
  outside this repository's linear-barcode scope

The test environment uses the real conda-forge `python-barcode` 0.13.1 package
for direct parity. Codabar and upstream fixes newer than that package are
checked against independent encoders and vectors from the current upstream
test suite. In particular, the port retains current behavior for Code 128
leading `99`, repeated builds, ISBN/ISSN digit handling, and GS1-128.

## Install

The pinned Mojo nightly and all test dependencies are managed by Pixi:

```bash
pixi install
pixi run build
pixi run test
```

The build creates `dist/libmojo-barcode.so`. The Python wrapper finds that
library automatically. Set `MOJO_BARCODE_LIB` to use a library installed
elsewhere.

For a Python package install from the checkout:

```bash
pixi run python -m pip install -e .
```

## Usage

```python
import mojo_barcode as barcode

ean = barcode.get("ean13", "400614457735")
print(ean.get_fullcode())       # 4006144577350
print(len(ean.build()[0]))      # 95 modules
filename = ean.save("product")  # product.svg

code128 = barcode.Code128("AB123456CD")
print(code128.encoded)
```

Batch EAN-13 encoding accepts complete 13-digit values:

```python
patterns = barcode.encode_ean13_batch(
    ["4006144577350", "5901234123457"]
)
```

## Benchmarks

Measured in the final review with `pixi run bench`, which holds
`/tmp/mojo-bench.lock`. The command reported
`x86_64; Linux-6.8.0-136-generic-x86_64-with-glibc2.39`. Times are the best of
five runs and include Python wrapper allocation and conversion. A value above
1.0x means `mojo-barcode` is faster.

| Case | mojo-barcode | python-barcode | Speedup |
|---|---:|---:|---:|
| EAN-13 batch (100k) | 72.86 ms | 1126.77 ms | 15.46x |
| Code 39 (100k chars) | 1.45 ms | 23.78 ms | 16.35x |
| Code 128-C (200k digits) | 23.57 ms | 202.02 ms | 8.57x |
| ITF (10k digits) | 0.28 ms | 17.07 ms | 60.83x |

No GPU path is included. Linear barcode encoding is table lookup and byte
expansion with well under two arithmetic operations per byte moved, so host
to device transfers and kernel launch overhead are not justified. No threaded
CPU path is included either: after removing wrapper materialization, the
remaining per-character work is a short memory-bound copy.

## How it works

`src/capi.mojo` is the single compiled entry point. Python passes ASCII input,
explicit lengths, and caller-owned output buffers with capacities across a C
ABI as integer addresses. Each entry point rejects null addresses, invalid
dimensions, and insufficient output capacity before reconstructing
`UnsafePointer[..., AnyOrigin[mut=True]]` values inside Mojo, so no Mojo
allocation or ownership crosses the boundary. Negative native status values
become Python exceptions, and returned lengths are checked before buffers are
read.

Patterns are stored as packed lookup tables in the shared library. Mojo writes
one byte per output module (`0`, `1`, or `G`) into contiguous Python-owned
memory. Code 128 also writes its symbol numbers to a contiguous `int64`
scratch buffer, allowing the compatible `encoded` property and the final bar
pattern to come from the same native pass. SVG conversion stays in Python
because it is formatting and I/O rather than the encoding hot path.

Python `bytes` inputs are passed directly to Mojo without a ctypes input copy.
Output conversion reads the completed contiguous buffer directly instead of
slicing a ctypes array into a temporary list of Python integers. Code 39 uses
packed 16-byte records for full-width SIMD copies; Code 128 uses SIMD table
copies with a scalar remainder.
