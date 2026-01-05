#!/usr/bin/env python3
"""
Compression utilities for IR Log Database - Phase 229.

Provides zlib compression for raw_record and audit_data columns
to reduce storage by ~60-70%.

Usage:
    from claude.tools.m365_ir.compression import compress_json, decompress_json

    # Compress before INSERT
    compressed = compress_json(json.dumps(row))
    cursor.execute("INSERT ... VALUES (?)", (compressed,))

    # Decompress after SELECT
    decompressed = decompress_json(row['raw_record'])
    data = json.loads(decompressed)

Author: Maia System (SRE Principal Engineer Agent)
Created: 2025-01-05
Phase: 229 - IR Log Database Compression
"""

import json
import zlib
from typing import Union

# Compression level 6 = balanced speed/ratio
# Level 1-3: Fast, lower compression
# Level 4-6: Balanced (recommended)
# Level 7-9: Best compression, slower
COMPRESSION_LEVEL = 6


def compress_json(data: Union[str, dict]) -> bytes:
    """
    Compress JSON string or dict to bytes using zlib.

    Args:
        data: JSON string or dict to compress

    Returns:
        Compressed bytes (zlib format)

    Example:
        >>> compressed = compress_json({"key": "value"})
        >>> isinstance(compressed, bytes)
        True
    """
    if isinstance(data, dict):
        data = json.dumps(data)

    return zlib.compress(data.encode('utf-8'), level=COMPRESSION_LEVEL)


def decompress_json(data: Union[bytes, str]) -> str:
    """
    Decompress bytes to JSON string.

    Handles backwards compatibility with uncompressed TEXT data:
    - If data is already a string, returns as-is
    - If data is bytes, decompresses with zlib

    Args:
        data: Compressed bytes or uncompressed string

    Returns:
        JSON string (decompressed if needed)

    Example:
        >>> compressed = compress_json('{"key": "value"}')
        >>> decompress_json(compressed)
        '{"key": "value"}'
        >>> decompress_json('{"key": "value"}')  # backwards compat
        '{"key": "value"}'
    """
    if data is None:
        return None

    # Backwards compatibility: if already a string, return as-is
    if isinstance(data, str):
        return data

    # Decompress bytes
    return zlib.decompress(data).decode('utf-8')


def is_compressed(data: Union[bytes, str]) -> bool:
    """
    Check if data is zlib compressed.

    Detects zlib magic bytes at start of data.
    Level 6 compression uses header 0x78 0x9c.

    Args:
        data: Data to check

    Returns:
        True if data is zlib compressed bytes, False otherwise

    Example:
        >>> compressed = compress_json('{"key": "value"}')
        >>> is_compressed(compressed)
        True
        >>> is_compressed('plain string')
        False
    """
    if isinstance(data, str):
        return False

    if not isinstance(data, bytes):
        return False

    if len(data) < 2:
        return False

    # zlib magic bytes: 0x78 followed by compression level indicator
    # 0x78 0x01 = no compression
    # 0x78 0x5e = fast compression
    # 0x78 0x9c = default compression (level 6)
    # 0x78 0xda = best compression
    return data[0] == 0x78 and data[1] in (0x01, 0x5e, 0x9c, 0xda)


if __name__ == "__main__":
    # Quick demo
    sample = {
        "UserPrincipalName": "user@example.com",
        "IPAddress": "192.168.1.1",
        "Country": "Australia",
        "Browser": "Chrome 120.0.0.0",
        "Status": "Success"
    }

    original = json.dumps(sample)
    compressed = compress_json(original)
    decompressed = decompress_json(compressed)

    print(f"Original size: {len(original)} bytes")
    print(f"Compressed size: {len(compressed)} bytes")
    print(f"Reduction: {100 - (len(compressed) / len(original) * 100):.1f}%")
    print(f"Roundtrip OK: {original == decompressed}")
    print(f"Is compressed: {is_compressed(compressed)}")
