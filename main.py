#!/usr/bin/env python3
"""News Image entry for make.fun (news-image-20261121).

Copies the entry image (entry.png, in this repository) to /output/entry.png.

The harness runs this program twice in a fresh container with no network,
read-only /bot (this repository at the submitted commit) and writable
/output, and both runs must write the same bytes. This program is fully
deterministic: it only copies fixed bytes and validates them first.

Validation (the competition's image rules):
  - the file must be a PNG or a JPEG (checked by magic bytes)
  - at most 1 MiB (1048576 bytes)
  - at most 1024 by 1024 pixels
"""

import os
import struct
import sys

MAX_BYTES = 1048576
MAX_DIMENSION = 1024

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def read_png_dimensions(data):
    """Return (width, height) of a PNG from its IHDR chunk."""
    # 8-byte signature, then 4-byte length, 4-byte chunk type "IHDR",
    # then width and height as big-endian unsigned 32-bit integers.
    if len(data) < 24 or data[12:16] != b"IHDR":
        raise ValueError("not a valid PNG (missing IHDR chunk)")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def read_jpeg_dimensions(data):
    """Return (width, height) of a JPEG by scanning for a SOF marker."""
    pos = 2
    while pos + 9 < len(data):
        if data[pos] != 0xFF:
            raise ValueError("not a valid JPEG (bad marker)")
        marker = data[pos + 1]
        # Standalone markers have no length field.
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
        if length < 2:
            raise ValueError("not a valid JPEG (bad segment length)")
        # SOF0 (0xC0), SOF1 (0xC1), SOF2 (0xC2) carry the dimensions.
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[pos + 5:pos + 9])
            return width, height
        pos += 2 + length
    raise ValueError("not a valid JPEG (no SOF marker found)")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "entry.png")
    with open(source, "rb") as f:
        data = f.read()

    if data[:8] == PNG_MAGIC:
        kind = "PNG"
        width, height = read_png_dimensions(data)
    elif data[:3] == JPEG_MAGIC:
        kind = "JPEG"
        width, height = read_jpeg_dimensions(data)
    else:
        print("error: entry.png is neither a PNG nor a JPEG", file=sys.stderr)
        return 1

    if len(data) > MAX_BYTES:
        print(
            f"error: entry.png is {len(data)} bytes, over the 1 MiB limit",
            file=sys.stderr,
        )
        return 1
    if width > MAX_DIMENSION or height > MAX_DIMENSION:
        print(
            f"error: entry.png is {width}x{height}, over the 1024x1024 limit",
            file=sys.stderr,
        )
        return 1

    os.makedirs("/output", exist_ok=True)
    destination = os.path.join("/output", "entry.png")
    with open(destination, "wb") as f:
        f.write(data)

    print(f"wrote /output/entry.png ({kind}, {width}x{height}, {len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
