#!/usr/bin/env python3
"""Copy the bundled news summary image to the harness output path.

The make.fun program harness runs this script twice and requires the
two runs to write byte-identical output. This script is deliberately
trivial: it reads the entry.png sitting next to it, checks that it is
a well-formed PNG within the competition's size limits, and writes
the exact same bytes to /output/entry.png.

Standard library only; no network access.
"""

import os
import struct
import sys

# Where the harness expects the finished image.
OUTPUT_PATH = "/output/entry.png"

# Competition limits.
MAX_FILE_BYTES = 1_048_576  # 1 MiB
MAX_SIDE_PIXELS = 1024

# First eight bytes of every PNG file.
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

USAGE = """usage: python3 main.py [--help]

Validate entry.png (PNG, at most 1 MiB, at most 1024x1024px) and
copy it byte-for-byte to /output/entry.png.
"""


def fail(message):
    """Print an error and stop with a non-zero exit code."""
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def image_dimensions(png_bytes):
    """Return (width, height) read from the IHDR chunk of a PNG.

    The PNG layout is: 8-byte signature, then chunks. The first
    chunk is always IHDR: 4-byte big-endian length, the ASCII tag
    "IHDR", then 13 bytes of header data whose first eight bytes
    are the width and height as big-endian unsigned 32-bit ints.
    """
    header_needed = 8 + 4 + 4 + 13
    if len(png_bytes) < header_needed:
        fail("entry.png is too short to contain a PNG header")
    tag = png_bytes[12:16]
    if tag != b"IHDR":
        fail("first PNG chunk is not IHDR")
    width, height = struct.unpack(">II", png_bytes[16:24])
    return width, height


def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(USAGE, end="")
        return 0
    if len(sys.argv) > 1:
        fail(f"unknown argument: {sys.argv[1]} (see --help)")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(script_dir, "entry.png")

    try:
        with open(source_path, "rb") as handle:
            png_bytes = handle.read()
    except FileNotFoundError:
        fail(f"could not find {source_path}")
    except OSError as exc:
        fail(f"could not read {source_path}: {exc}")

    if len(png_bytes) < len(PNG_SIGNATURE) or \
            png_bytes[: len(PNG_SIGNATURE)] != PNG_SIGNATURE:
        fail("entry.png does not start with the PNG signature")

    if len(png_bytes) > MAX_FILE_BYTES:
        fail(
            f"entry.png is {len(png_bytes)} bytes, "
            f"over the {MAX_FILE_BYTES}-byte limit"
        )

    width, height = image_dimensions(png_bytes)
    if width > MAX_SIDE_PIXELS or height > MAX_SIDE_PIXELS:
        fail(
            f"entry.png is {width}x{height}px, "
            f"over the {MAX_SIDE_PIXELS}x{MAX_SIDE_PIXELS} limit"
        )

    output_dir = os.path.dirname(OUTPUT_PATH)
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(OUTPUT_PATH, "wb") as handle:
            handle.write(png_bytes)
    except OSError as exc:
        fail(f"could not write {OUTPUT_PATH}: {exc}")

    print(
        f"Wrote {len(png_bytes)} bytes "
        f"({width}x{height}px) to {OUTPUT_PATH}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
