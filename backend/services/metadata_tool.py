"""
metadata_tool.py
================
A SAFE, LOCAL-ONLY image metadata utility.

Guarantees
----------
* The image is NEVER uploaded anywhere.
* The tool reports ONLY metadata that is explicitly present in the file.
* It does NOT infer or reverse-engineer a hidden location.
* It can write a metadata-stripped COPY, leaving the original untouched.

Implementation note
-------------------
This module deliberately avoids third-party EXIF libraries so that the
project has no extra dependencies. It performs a minimal, well-understood
parse of the JPEG APP1/Exif segment to locate the GPS IFD, then reports
only the tags it can read with confidence. Anything it cannot parse is
reported as "not parsed" rather than guessed.
"""

import os
import struct

# EXIF tag IDs we understand, and their human-readable names.
EXIF_TAGS = {
    0x010F: "Camera make",
    0x0110: "Camera model",
    0x0131: "Software",
    0x0132: "DateTime (last modified)",
    0x9003: "DateTimeOriginal",
    0x8825: "GPSInfo (pointer)",
}

GPS_TAGS = {
    0x0000: "GPSVersionID",
    0x0001: "GPSLatitudeRef",
    0x0002: "GPSLatitude",
    0x0003: "GPSLongitudeRef",
    0x0004: "GPSLongitude",
    0x0005: "GPSAltitudeRef",
    0x0006: "GPSAltitude",
    0x0007: "GPSTimeStamp",
    0x0012: "GPSMapDatum",
    0x001D: "GPSDateStamp",
}


def _read_exif_header(data):
    """Return (byte_order, ifd_offset) if a JPEG Exif segment exists."""
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        return None  # not a JPEG

    offset = 2
    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            break
        marker = data[offset + 1]
        if marker in (0xD8, 0xD9):
            offset += 2
            continue
        if offset + 4 > len(data):
            break
        segment_length = struct.unpack(">H", data[offset + 2:offset + 4])[0]
        segment = data[offset + 4: offset + 2 + segment_length]

        if marker == 0xE1 and segment[:6] == b"Exif\x00\x00":
            tiff = segment[6:]
            if len(tiff) < 8:
                return None
            byte_order = "<" if tiff[:2] == b"II" else ">"
            ifd_offset = struct.unpack(byte_order + "I", tiff[4:8])[0]
            return byte_order, tiff, ifd_offset

        offset += 2 + segment_length
    return None


def _parse_ifd(tiff, ifd_offset, byte_order):
    """Yield (tag, type, count, value_bytes, raw_offset) for one IFD."""
    entries = []
    if ifd_offset + 2 > len(tiff):
        return entries

    count = struct.unpack(byte_order + "H", tiff[ifd_offset: ifd_offset + 2])[0]
    base = ifd_offset + 2

    for i in range(count):
        entry_offset = base + i * 12
        if entry_offset + 12 > len(tiff):
            break
        tag, dtype, item_count = struct.unpack(
            byte_order + "HHI", tiff[entry_offset: entry_offset + 8]
        )
        value_field = tiff[entry_offset + 8: entry_offset + 12]
        entries.append((tag, dtype, item_count, value_field))
    return entries


def _decode_ascii(value_field, item_count):
    text = value_field[: max(0, item_count - 1)]
    return text.decode("ascii", errors="replace").strip("\x00").strip()


def read_metadata(path):
    """
    Read EXIF metadata from a local image file.

    Returns
    -------
    dict
        {
          "file": filename,
          "size_bytes": int,
          "metadata_present": bool,
          "camera": {...},
          "gps": {...},
          "warnings": [...],
          "note": str
        }
    """
    result = {
        "file": os.path.basename(path),
        "size_bytes": 0,
        "metadata_present": False,
        "camera": {},
        "gps": {},
        "warnings": [],
        "note": (
            "Local analysis only. No data left this machine. Only metadata "
            "explicitly present in the file is reported; nothing is inferred."
        ),
    }

    if not os.path.isfile(path):
        result["warnings"].append("File not found.")
        return result

    result["size_bytes"] = os.path.getsize(path)

    with open(path, "rb") as handle:
        data = handle.read()

    header = _read_exif_header(data)
    if header is None:
        result["warnings"].append(
            "No JPEG Exif segment found. The file may be PNG/WebP, already "
            "stripped, or not an image."
        )
        return result

    byte_order, tiff, ifd_offset = header
    entries = _parse_ifd(tiff, ifd_offset, byte_order)

    for tag, dtype, count, value_field in entries:
        if tag == 0x8825:  # GPSInfo pointer
            gps_offset = struct.unpack(byte_order + "I", value_field)[0]
            for g_tag, g_type, g_count, g_value in _parse_ifd(tiff, gps_offset, byte_order):
                name = GPS_TAGS.get(g_tag, f"GPS tag 0x{g_tag:04X}")
                if g_type == 2:  # ASCII
                    result["gps"][name] = _decode_ascii(g_value, g_count)
                else:
                    result["gps"][name] = "present"
            continue

        name = EXIF_TAGS.get(tag)
        if name and dtype == 2:
            result["camera"][name] = _decode_ascii(value_field, count)

    result["metadata_present"] = bool(result["camera"] or result["gps"])

    if result["gps"]:
        result["warnings"].append(
            "GPS metadata was found in this file. If you share the original "
            "file directly (email, cloud link, chat), the coordinates travel "
            "with it. Many social platforms strip metadata on upload, but "
            "direct file transfer usually does not."
        )

    return result


def strip_metadata(source_path, destination_path=None):
    """
    Write a COPY of the image with the Exif segment removed.

    The original file is never modified.
    """
    if not os.path.isfile(source_path):
        raise FileNotFoundError(source_path)

    destination_path = destination_path or os.path.join(
        os.path.dirname(source_path),
        "stripped_" + os.path.basename(source_path),
    )

    with open(source_path, "rb") as handle:
        data = handle.read()

    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        raise ValueError("Only JPEG files are supported for metadata stripping.")

    output = bytearray(data[0:2])  # SOI
    offset = 2

    while offset + 4 <= len(data):
        if data[offset] != 0xFF:
            break
        marker = data[offset + 1]

        if marker in (0xD8, 0xD9):
            offset += 2
            continue

        if offset + 4 > len(data):
            break

        segment_length = struct.unpack(">H", data[offset + 2: offset + 4])[0]
        segment = data[offset: offset + 2 + segment_length]

        is_exif = marker == 0xE1 and segment[4:10] == b"Exif\x00\x00"

        if not is_exif:
            output.extend(segment)

        offset += 2 + segment_length

        # Once we reach SOS, copy the rest verbatim (entropy-coded data).
        if marker == 0xDA:
            output.extend(data[offset:])
            break

    with open(destination_path, "wb") as handle:
        handle.write(bytes(output))

    return destination_path