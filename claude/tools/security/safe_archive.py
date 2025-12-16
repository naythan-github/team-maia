#!/usr/bin/env python3
"""
Safe Archive Extraction Utilities
Phase 224.1 - Security Hardening

Provides secure extraction of tar/zip archives with protection against:
- Path traversal attacks (../)
- Absolute path injection
- Symlink attacks
"""
import tarfile
import zipfile
import os
from pathlib import Path
from typing import Optional, List


def safe_extract_tar(tar_path: Path, extract_to: Path,
                     allow_symlinks: bool = False) -> List[str]:
    """
    Safely extract tar file with path traversal protection.

    Args:
        tar_path: Path to tar archive
        extract_to: Destination directory
        allow_symlinks: Whether to allow symlinks (default False for security)

    Returns:
        List of extracted file paths

    Raises:
        ValueError: If archive contains malicious entries
        FileNotFoundError: If tar_path doesn't exist
    """
    tar_path = Path(tar_path)
    extract_to = Path(extract_to).resolve()

    if not tar_path.exists():
        raise FileNotFoundError(f"Archive not found: {tar_path}")

    if not extract_to.exists():
        extract_to.mkdir(parents=True, exist_ok=True)

    extracted_files = []

    with tarfile.open(tar_path, 'r:*') as tar:
        for member in tar.getmembers():
            # Security check 1: Reject absolute paths
            if member.name.startswith('/'):
                raise ValueError(
                    f"Absolute path not allowed in archive: {member.name}"
                )

            # Security check 2: Reject path traversal
            # Resolve the full path and check it stays within extract_to
            member_path = (extract_to / member.name).resolve()
            if not str(member_path).startswith(str(extract_to) + os.sep) and \
               member_path != extract_to:
                raise ValueError(
                    f"Path traversal detected in archive: {member.name}"
                )

            # Security check 3: Reject symlinks unless explicitly allowed
            if (member.issym() or member.islnk()) and not allow_symlinks:
                raise ValueError(
                    f"Symlinks not allowed in archive: {member.name}"
                )

            # If symlinks allowed, validate symlink target
            if member.issym() and allow_symlinks:
                link_target = Path(extract_to / member.name).parent / member.linkname
                link_resolved = link_target.resolve()
                if not str(link_resolved).startswith(str(extract_to)):
                    raise ValueError(
                        f"Symlink target escapes extraction directory: {member.name} -> {member.linkname}"
                    )

            extracted_files.append(member.name)

        # All checks passed, safe to extract
        tar.extractall(path=extract_to)  # nosec B202 - validated above

    return extracted_files


def safe_extract_zip(zip_path: Path, extract_to: Path) -> List[str]:
    """
    Safely extract zip file with path traversal protection.

    Args:
        zip_path: Path to zip archive
        extract_to: Destination directory

    Returns:
        List of extracted file paths

    Raises:
        ValueError: If archive contains malicious entries
        FileNotFoundError: If zip_path doesn't exist
    """
    zip_path = Path(zip_path)
    extract_to = Path(extract_to).resolve()

    if not zip_path.exists():
        raise FileNotFoundError(f"Archive not found: {zip_path}")

    if not extract_to.exists():
        extract_to.mkdir(parents=True, exist_ok=True)

    extracted_files = []

    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            # Security check 1: Reject absolute paths
            if name.startswith('/'):
                raise ValueError(
                    f"Absolute path not allowed in archive: {name}"
                )

            # Security check 2: Reject path traversal
            member_path = (extract_to / name).resolve()
            if not str(member_path).startswith(str(extract_to) + os.sep) and \
               member_path != extract_to:
                raise ValueError(
                    f"Path traversal detected in archive: {name}"
                )

            extracted_files.append(name)

        # All checks passed, safe to extract
        zf.extractall(path=extract_to)  # nosec B202 - validated above

    return extracted_files


def validate_archive_members(tar_path: Path, allow_symlinks: bool = False) -> dict:
    """
    Validate archive contents without extracting.

    Args:
        tar_path: Path to tar archive
        allow_symlinks: Whether symlinks are allowed

    Returns:
        dict with 'valid' bool and 'issues' list
    """
    issues = []

    try:
        with tarfile.open(tar_path, 'r:*') as tar:
            for member in tar.getmembers():
                if member.name.startswith('/'):
                    issues.append(f"Absolute path: {member.name}")

                if '..' in member.name:
                    issues.append(f"Potential path traversal: {member.name}")

                if (member.issym() or member.islnk()) and not allow_symlinks:
                    issues.append(f"Symlink: {member.name}")

    except Exception as e:
        issues.append(f"Archive error: {str(e)}")

    return {
        'valid': len(issues) == 0,
        'issues': issues
    }


if __name__ == "__main__":
    # CLI for testing
    import argparse

    parser = argparse.ArgumentParser(description="Safe archive extraction")
    parser.add_argument("archive", help="Path to archive file")
    parser.add_argument("--validate", action="store_true", help="Validate only, don't extract")
    parser.add_argument("--extract-to", help="Extraction directory")
    parser.add_argument("--allow-symlinks", action="store_true", help="Allow symlinks")

    args = parser.parse_args()

    archive_path = Path(args.archive)

    if args.validate:
        result = validate_archive_members(archive_path, args.allow_symlinks)
        if result['valid']:
            print(f"Archive is safe: {archive_path}")
        else:
            print(f"Archive has issues:")
            for issue in result['issues']:
                print(f"  - {issue}")
    else:
        extract_to = Path(args.extract_to) if args.extract_to else Path.cwd() / "extracted"
        try:
            files = safe_extract_tar(archive_path, extract_to, args.allow_symlinks)
            print(f"Extracted {len(files)} files to {extract_to}")
        except ValueError as e:
            print(f"Security error: {e}")
            exit(1)
