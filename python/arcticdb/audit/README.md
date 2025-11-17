# ArcticDB Audit Module

Enterprise audit and traceability functionality for ArcticDB.

## Overview

This module provides comprehensive audit logging for all ArcticDB read and write operations, ensuring compliance with enterprise data governance requirements.

## Components

### AuditLogger

Thread-safe audit logger that records all operations to JSON log files.

```python
from arcticdb.audit import AuditLogger

audit_logger = AuditLogger(
    log_file="/var/log/arcticdb/audit.log",
    enable_console=True
)
```

### AuditEntry

Data class representing a single audit log entry.

```python
@dataclass
class AuditEntry:
    timestamp: str
    actor: str
    operation: str
    symbols: List[str]
    library: str
    metadata: Optional[dict] = None
```

### AuditedLibrary

Wrapper around ArcticDB Library that enforces user_id parameter and automatic audit logging.

```python
from arcticdb.audit import AuditedLibrary

lib = ac.get_library('my_library')
audited_lib = AuditedLibrary(lib, audit_logger)

# All operations require user_id
audited_lib.write("symbol", df, user_id="alice")
audited_lib.read("symbol", user_id="bob")
```

## Features

- **Mandatory User Identification**: All operations require user_id parameter
- **Comprehensive Logging**: Timestamp, actor, operation, symbols, library
- **Thread-Safe**: Safe for concurrent operations
- **JSON Format**: Easy to parse and integrate with log aggregation tools
- **Flexible Configuration**: File and/or console logging
- **Migration Support**: Tools to migrate existing data

## Usage

### Basic Setup

```python
import arcticdb as adb
from arcticdb.audit import AuditedLibrary, AuditLogger

# 1. Create audit logger
audit_logger = AuditLogger(log_file="audit.log")

# 2. Get library
ac = adb.Arctic('lmdb://./data')
lib = ac.get_library('my_lib', create_if_missing=True)

# 3. Wrap with audit functionality
audited_lib = AuditedLibrary(lib, audit_logger)

# 4. Use with user_id
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
audited_lib.write("symbol", df, user_id="alice")
data = audited_lib.read("symbol", user_id="bob")
```

### Reading Audit Logs

```python
# Get recent logs
logs = audit_logger.read_logs(limit=100)

for log in logs:
    print(f"{log.timestamp} - {log.actor} performed {log.operation} on {log.symbols}")
```

### System Operations

```python
# Use descriptive system IDs for automated operations
audited_lib.write(
    "backup_data",
    df,
    user_id="system_backup_job"
)
```

## Supported Operations

All major Library operations are supported:

- `write()` - Write data to symbol
- `read()` - Read data from symbol
- `update()` - Update existing data
- `append()` - Append data to symbol
- `delete()` - Delete symbol or versions
- `write_batch()` - Batch write operations
- `read_batch()` - Batch read operations

## Log Format

Audit logs are stored as JSON lines:

```json
{"timestamp": "2024-01-15T10:30:45.123456", "actor": "alice", "operation": "write", "symbols": ["symbol1"], "library": "my_lib", "metadata": {}}
```

## Migration

For existing databases, use the migration script:

```bash
python -m arcticdb.scripts.migrate_audit lmdb:///path/to/db library_name
```

## Error Handling

Missing user_id raises clear error:

```python
try:
    audited_lib.write("symbol", df)  # Missing user_id
except ValueError as e:
    # "write requires 'user_id' parameter for audit logging..."
    pass
```

## Thread Safety

The AuditLogger uses threading locks to ensure safe concurrent access:

```python
# Safe to use from multiple threads
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=10) as executor:
    futures = [
        executor.submit(audited_lib.write, f"sym_{i}", df, user_id=f"user_{i}")
        for i in range(100)
    ]
```

## Best Practices

1. **Use descriptive user IDs**: "alice.smith" not "user123"
2. **Use system IDs for automation**: "system_backup" not "admin"
3. **Store logs securely**: Appropriate file permissions
4. **Rotate logs**: Prevent disk space issues
5. **Monitor logs**: Set up alerts for unusual activity

## Documentation

- **Quick Start**: See `AUDIT_QUICKSTART.md` in repository root
- **Complete Rules**: See `.augment/rules.md`
- **Examples**: See `examples/audit_example.py`
- **README**: See main README.md Enterprise Audit section

## License

Same as ArcticDB - Business Source License 1.1

