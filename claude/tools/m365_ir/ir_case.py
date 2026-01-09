#!/usr/bin/env python3
"""
IRCase - Incident Response Case Management.

Manages case folder structure, source file handling, and database configuration.

Directory structure:
    ~/work_projects/ir_cases/
    └── PIR-{CUSTOMER}-{TICKET}/        # Ticket-based (preferred)
    └── PIR-{CUSTOMER}-{YYYY-MM-DD}/    # Date-based (fallback)
        ├── source-files/
        │   └── Export_2025-12-01.zip
        ├── reports/
        │   └── (analysis outputs)
        └── PIR-{CUSTOMER}-{TICKET}_logs.db

Case ID Formats:
    - Ticket-based (preferred): PIR-SGS-11111111
    - Date-based (fallback): PIR-SGS-2026-01-09

Usage:
    # Create new case from ticket reference (PREFERRED)
    case = IRCase.from_ticket(ticket="11111111", customer="SGS")
    case.initialize()

    # Create case from zip with ticket
    case = IRCase.from_zip(zip_path, customer="SGS", ticket="11111111")
    case.initialize()
    case.move_source_zip()

    # Create case from zip (date-based fallback)
    case = IRCase.from_zip(zip_path, customer="FYNA")
    case.initialize()

    # Import logs
    db = case.get_database()
    db.create()
    importer = LogImporter(db)
    importer.import_all(case.source_files_dir / "export.zip")

    # Open existing case
    case = IRCase(case_id="PIR-SGS-11111111", base_path="~/work_projects/ir_cases")

Author: Maia System
Created: 2025-01-05 (Phase 226.1)
Updated: 2026-01-09 (Added ticket-based case ID support)
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from .log_database import IRLogDatabase

# Default base path for IR cases
DEFAULT_IR_CASES_PATH = Path.home() / ".maia" / "ir-cases"


class IRCase:
    """
    Manages an incident response case folder and its contents.

    Handles:
    - Case ID generation from zip file metadata
    - Directory structure creation
    - Source file management (moving zips to case folder)
    - Database path configuration
    - Reports directory access
    """

    def __init__(
        self,
        case_id: str,
        base_path: Optional[Union[str, Path]] = None,
        _zip_path: Optional[Path] = None,
    ):
        """
        Initialize case with existing case ID.

        Args:
            case_id: Case identifier (e.g., PIR-FYNA-2025-12-15)
            base_path: Base directory for IR cases
            _zip_path: Internal - original zip path for from_zip()
        """
        self.case_id = case_id
        self.base_path = Path(base_path) if base_path else DEFAULT_IR_CASES_PATH
        self._original_zip_path = _zip_path

    @classmethod
    def from_ticket(
        cls,
        ticket: str,
        customer: str,
        base_path: Optional[Union[str, Path]] = None,
        zip_path: Optional[Union[str, Path]] = None,
    ) -> "IRCase":
        """
        Create a new case from a ticket reference number.

        Generates case ID from customer name and ticket number.
        Format: PIR-{CUSTOMER}-{TICKET}

        Args:
            ticket: Ticket reference number (e.g., 11111111)
            customer: Customer name (will be sanitized for case ID)
            base_path: Base directory for IR cases
            zip_path: Optional zip path to associate with case

        Returns:
            IRCase instance with ticket-based case ID
        """
        # Sanitize customer name
        customer_slug = cls._sanitize_customer_name(customer)

        # Sanitize ticket (remove any non-alphanumeric chars)
        ticket_clean = re.sub(r'[^A-Z0-9]+', '', ticket.upper())

        # Generate case ID: PIR-{CUSTOMER}-{TICKET}
        case_id = f"PIR-{customer_slug}-{ticket_clean}"

        return cls(
            case_id=case_id,
            base_path=base_path,
            _zip_path=Path(zip_path) if zip_path else None,
        )

    @classmethod
    def from_zip(
        cls,
        zip_path: Union[str, Path],
        customer: str,
        base_path: Optional[Union[str, Path]] = None,
        ticket: Optional[str] = None,
    ) -> "IRCase":
        """
        Create a new case from a zip file.

        Generates case ID from customer name and either ticket number (preferred)
        or zip file modification date (fallback).

        Args:
            zip_path: Path to the zip file
            customer: Customer name (will be sanitized for case ID)
            base_path: Base directory for IR cases
            ticket: Optional ticket reference number (if provided, uses ticket instead of date)

        Returns:
            IRCase instance with generated case ID
        """
        zip_path = Path(zip_path)

        # If ticket provided, use ticket-based case ID
        if ticket:
            return cls.from_ticket(
                ticket=ticket,
                customer=customer,
                base_path=base_path,
                zip_path=zip_path,
            )

        # Get zip file modification time
        mtime = zip_path.stat().st_mtime
        file_date = datetime.fromtimestamp(mtime)

        # Sanitize customer name
        customer_slug = cls._sanitize_customer_name(customer)

        # Generate case ID: PIR-{CUSTOMER}-{YYYY-MM-DD}
        date_str = file_date.strftime("%Y-%m-%d")
        case_id = f"PIR-{customer_slug}-{date_str}"

        return cls(
            case_id=case_id,
            base_path=base_path,
            _zip_path=zip_path,
        )

    @classmethod
    def from_directory(
        cls,
        dir_path: Union[str, Path],
        customer: str,
        base_path: Optional[Union[str, Path]] = None,
        ticket: Optional[str] = None,
    ) -> "IRCase":
        """
        Create a new case from an export directory.

        Generates case ID from customer name and either ticket number (preferred)
        or earliest CSV file modification date (fallback).

        Args:
            dir_path: Path to the export directory
            customer: Customer name (will be sanitized for case ID)
            base_path: Base directory for IR cases
            ticket: Optional ticket reference number (if provided, uses ticket instead of date)

        Returns:
            IRCase instance with generated case ID
        """
        dir_path = Path(dir_path)

        # If ticket provided, use ticket-based case ID
        if ticket:
            return cls.from_ticket(
                ticket=ticket,
                customer=customer,
                base_path=base_path,
            )

        # Find earliest mtime among CSV files
        csv_files = list(dir_path.glob("*.csv"))
        if csv_files:
            earliest_mtime = min(f.stat().st_mtime for f in csv_files)
            file_date = datetime.fromtimestamp(earliest_mtime)
        else:
            # Fallback to directory mtime if no CSVs found
            file_date = datetime.fromtimestamp(dir_path.stat().st_mtime)

        # Sanitize customer name
        customer_slug = cls._sanitize_customer_name(customer)

        # Generate case ID: PIR-{CUSTOMER}-{YYYY-MM-DD}
        date_str = file_date.strftime("%Y-%m-%d")
        case_id = f"PIR-{customer_slug}-{date_str}"

        return cls(
            case_id=case_id,
            base_path=base_path,
        )

    @staticmethod
    def _sanitize_customer_name(name: str) -> str:
        """
        Sanitize customer name for use in case ID.

        - Uppercase
        - Replace spaces and special chars with hyphens
        - Remove trailing hyphens
        """
        # Uppercase
        name = name.upper()

        # Replace non-alphanumeric with hyphens
        name = re.sub(r'[^A-Z0-9]+', '-', name)

        # Remove leading/trailing hyphens
        name = name.strip('-')

        return name

    @property
    def case_dir(self) -> Path:
        """Case directory path."""
        return self.base_path / self.case_id

    @property
    def source_files_dir(self) -> Path:
        """Source files directory path."""
        return self.case_dir / "source-files"

    @property
    def reports_dir(self) -> Path:
        """Reports directory path."""
        return self.case_dir / "reports"

    @property
    def db_path(self) -> Path:
        """Database file path."""
        return self.case_dir / f"{self.case_id}_logs.db"

    def initialize(self) -> None:
        """
        Create case directory structure.

        Creates:
        - Case directory
        - source-files subdirectory
        - reports subdirectory
        """
        self.case_dir.mkdir(parents=True, exist_ok=True)
        self.source_files_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)

    def move_source_zip(self) -> Path:
        """
        Move the original zip file to source-files directory.

        Returns:
            New path of the moved zip file

        Raises:
            ValueError: If case was not created from a zip file
            FileNotFoundError: If original zip no longer exists
        """
        if self._original_zip_path is None:
            raise ValueError("Case was not created from a zip file")

        if not self._original_zip_path.exists():
            raise FileNotFoundError(f"Original zip not found: {self._original_zip_path}")

        return self.add_source_file(self._original_zip_path)

    def add_source_file(self, file_path: Union[str, Path]) -> Path:
        """
        Move a source file to the source-files directory.

        Handles filename conflicts by adding numeric suffix.

        Args:
            file_path: Path to file to move

        Returns:
            New path of the moved file
        """
        file_path = Path(file_path)
        target_path = self.source_files_dir / file_path.name

        # Handle duplicate names
        if target_path.exists():
            base = target_path.stem
            suffix = target_path.suffix
            counter = 1
            while target_path.exists():
                target_path = self.source_files_dir / f"{base}_{counter}{suffix}"
                counter += 1

        # Move file
        shutil.move(str(file_path), str(target_path))

        return target_path

    def get_database(self) -> IRLogDatabase:
        """
        Get configured IRLogDatabase for this case.

        Returns:
            IRLogDatabase instance pointing to case database
        """
        # IRLogDatabase expects case_id and base_path where it creates
        # {base_path}/{case_id}/{case_id}_logs.db
        # But we want the db in case_dir directly, so we pass case_dir as base_path
        # with case_id as empty string... actually that won't work.

        # Let's create a custom approach - we'll create the db ourselves
        # Actually, looking at IRLogDatabase, it does:
        #   self.db_path = Path(base_path) / case_id / f"{case_id}_logs.db"
        #
        # So if we pass base_path=self.base_path and case_id=self.case_id,
        # it will create: base_path/case_id/case_id_logs.db
        # Which is exactly what we want!

        return IRLogDatabase(
            case_id=self.case_id,
            base_path=str(self.base_path)
        )

    def exists(self) -> bool:
        """Check if case directory exists."""
        return self.case_dir.exists()

    def __repr__(self) -> str:
        return f"IRCase(case_id='{self.case_id}', path='{self.case_dir}')"
