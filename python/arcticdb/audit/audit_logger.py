"""
Copyright 2023 Man Group Operations Limited

Use of this software is governed by the Business Source License 1.1 included in the file licenses/BSL.txt.

As of the Change Date specified in that file, in accordance with the Business Source License, use of this software will be governed by the Apache License, version 2.0.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Union
from threading import Lock


@dataclass
class AuditEntry:
    """Represents a single audit log entry."""
    timestamp: str
    actor: str  # user_id or system_id
    operation: str  # read, write, update, append, delete, etc.
    symbols: List[str]
    library: str
    metadata: Optional[dict] = None

    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self):
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


class AuditLogger:
    """
    Thread-safe audit logger for ArcticDB operations.
    
    Logs all read and write operations with timestamp, actor, operation type, and affected symbols.
    """

    def __init__(self, log_file: Optional[Union[str, Path]] = None, enable_console: bool = True):
        """
        Initialize the audit logger.

        Parameters
        ----------
        log_file : Optional[Union[str, Path]]
            Path to the audit log file. If None, only console logging is used.
        enable_console : bool, default=True
            Whether to also log to console/standard logging.
        """
        self.log_file = Path(log_file) if log_file else None
        self.enable_console = enable_console
        self._lock = Lock()
        
        # Set up standard logger
        self.logger = logging.getLogger("arcticdb.audit")
        self.logger.setLevel(logging.INFO)
        
        # Add console handler if enabled
        if enable_console and not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

        # Create log file if specified
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.log_file.exists():
                self.log_file.touch()

    def log(
        self,
        actor: str,
        operation: str,
        symbols: Union[str, List[str]],
        library: str,
        metadata: Optional[dict] = None
    ):
        """
        Log an audit entry.

        Parameters
        ----------
        actor : str
            User ID or system ID performing the operation
        operation : str
            Type of operation (read, write, update, append, delete, etc.)
        symbols : Union[str, List[str]]
            Symbol or list of symbols affected
        library : str
            Library name
        metadata : Optional[dict]
            Additional metadata to log
        """
        # Normalize symbols to list
        if isinstance(symbols, str):
            symbols = [symbols]

        # Create audit entry
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            actor=actor,
            operation=operation,
            symbols=symbols,
            library=library,
            metadata=metadata
        )

        # Thread-safe logging
        with self._lock:
            # Log to console/standard logger
            if self.enable_console:
                self.logger.info(
                    f"actor={actor} operation={operation} library={library} "
                    f"symbols={symbols} metadata={metadata}"
                )

            # Log to file
            if self.log_file:
                with open(self.log_file, 'a') as f:
                    f.write(entry.to_json() + '\n')

    def read_logs(self, limit: Optional[int] = None) -> List[AuditEntry]:
        """
        Read audit logs from file.

        Parameters
        ----------
        limit : Optional[int]
            Maximum number of entries to return (most recent first)

        Returns
        -------
        List[AuditEntry]
            List of audit entries
        """
        if not self.log_file or not self.log_file.exists():
            return []

        entries = []
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    entries.append(AuditEntry(**data))
                except (json.JSONDecodeError, TypeError):
                    continue

        # Return most recent first
        entries.reverse()
        
        if limit:
            return entries[:limit]
        return entries

