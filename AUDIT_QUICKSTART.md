# ArcticDB Enterprise Audit - Quick Start Guide

## Overview

ArcticDB now includes enterprise-grade audit and traceability features. All read and write operations require user identification and are automatically logged.

## Installation

No additional installation required - audit functionality is included with ArcticDB.

## Basic Usage

### 1. Set Up Audit Logging

```python
import arcticdb as adb
from arcticdb.audit import AuditedLibrary, AuditLogger

# Create audit logger
audit_logger = AuditLogger(log_file="./audit_logs/arcticdb.log")
```

### 2. Wrap Your Library

```python
# Connect to ArcticDB
ac = adb.Arctic('lmdb://./data')

# Get library
lib = ac.get_library('my_library', create_if_missing=True)

# Wrap with audit functionality
audited_lib = AuditedLibrary(lib, audit_logger)
```

### 3. Use with user_id Parameter

```python
import pandas as pd

# Write data - user_id is REQUIRED
df = pd.DataFrame({'price': [100, 101, 102]})
audited_lib.write("stock_AAPL", df, user_id="alice.smith")

# Read data - user_id is REQUIRED
data = audited_lib.read("stock_AAPL", user_id="bob.jones")

# Update data
audited_lib.update("stock_AAPL", new_df, user_id="alice.smith")

# Append data
audited_lib.append("stock_AAPL", more_df, user_id="charlie.brown")
```

## What Gets Logged?

Every operation logs:
- **Timestamp**: When the operation occurred (UTC)
- **Actor**: Who performed it (user_id)
- **Operation**: What was done (read, write, update, etc.)
- **Symbols**: Which symbols were affected
- **Library**: Which library was accessed
- **Metadata**: Additional context (optional)

## Audit Log Format

Logs are stored as JSON, one entry per line:

```json
{"timestamp": "2024-01-15T10:30:45.123456", "actor": "alice.smith", "operation": "write", "symbols": ["stock_AAPL"], "library": "my_library", "metadata": {"prune_previous_versions": false}}
```

## Migrating Existing Data

If you have existing ArcticDB data, run the migration script:

```bash
# Dry run first
python -m arcticdb.scripts.migrate_audit lmdb:///path/to/db library_name --dry-run

# Actual migration
python -m arcticdb.scripts.migrate_audit lmdb:///path/to/db library_name \
    --audit-log migration_audit.log
```

## Common Patterns

### System Operations

For automated systems, use descriptive system IDs:

```python
audited_lib.write(
    "daily_backup",
    backup_data,
    user_id="system_backup_job"
)
```

### Batch Operations

```python
from arcticdb import WritePayload

payloads = [
    WritePayload("sym1", df1),
    WritePayload("sym2", df2),
]

audited_lib.write_batch(payloads, user_id="alice.smith")
```

### Reading Audit Logs

```python
# Get recent audit entries
recent_logs = audit_logger.read_logs(limit=100)

for log in recent_logs:
    print(f"{log.timestamp} - {log.actor} - {log.operation} - {log.symbols}")
```

## Error Handling

If you forget to provide `user_id`, you'll get a clear error:

```python
try:
    audited_lib.write("symbol", df)  # Missing user_id
except ValueError as e:
    print(e)  # "write requires 'user_id' parameter for audit logging..."
```

## Configuration Options

### Audit Logger Options

```python
audit_logger = AuditLogger(
    log_file="/var/log/arcticdb/audit.log",  # Path to log file
    enable_console=True  # Also log to console
)
```

### Migration Options

```bash
python -m arcticdb.scripts.migrate_audit \
    lmdb:///path/to/db \
    library_name \
    --migration-user system_migration \  # User ID for migrated data
    --audit-log migration.log \          # Log migration operations
    --dry-run                            # Preview without changes
```

## Best Practices

1. **Use descriptive user IDs**: "alice.smith" not "user123"
2. **Use system IDs for automation**: "system_backup_job" not "admin"
3. **Store logs securely**: Use appropriate file permissions
4. **Rotate logs regularly**: Prevent disk space issues
5. **Test migrations**: Always use --dry-run first
6. **Monitor audit logs**: Set up alerts for unusual activity

## Complete Example

See `examples/audit_example.py` for a comprehensive working example.

## Troubleshooting

### "write requires 'user_id' parameter"
- **Solution**: Add `user_id="your_user_id"` to the operation

### "No such file or directory" for audit log
- **Solution**: Ensure the directory exists or let AuditLogger create it

### Migration fails
- **Solution**: Run with `--dry-run` first to identify issues

## Further Reading

- **Detailed Rules**: See `.augment/rules.md` for complete audit requirements
- **README**: See README.md "Enterprise Audit and Traceability" section
- **Example Code**: See `examples/audit_example.py`

## Support

For questions or issues with audit functionality, please refer to the documentation or contact your system administrator.

