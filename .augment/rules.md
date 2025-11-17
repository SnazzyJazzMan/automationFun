# ArcticDB Enterprise Audit Rules

## Overview

This document defines the mandatory audit and traceability requirements for ArcticDB in enterprise environments. All developers and AI agents working on this codebase must adhere to these rules.

## Mandatory Requirements

### 1. User Identification Required

**RULE**: All read and write operations MUST include a `user_id` parameter that identifies the actor performing the operation.

- **For human users**: Use their actual user ID (e.g., "john.doe", "jane.smith")
- **For system operations**: Use a descriptive system ID (e.g., "system_backup_job", "etl_pipeline", "data_sync_service")
- **For migrations**: Use "system_migration" as the default user ID

**Implementation**:
```python
# ✓ CORRECT - user_id provided
audited_lib.write("symbol", data, user_id="john.doe")
audited_lib.read("symbol", user_id="jane.smith")

# ✗ INCORRECT - missing user_id
lib.write("symbol", data)  # Will raise ValueError
lib.read("symbol")  # Will raise ValueError
```

### 2. Use AuditedLibrary Wrapper

**RULE**: In production environments, always use `AuditedLibrary` wrapper instead of direct `Library` access.

**Implementation**:
```python
from arcticdb.audit import AuditedLibrary, AuditLogger

# Set up audit logger
audit_logger = AuditLogger(log_file="/var/log/arcticdb/audit.log")

# Get library and wrap it
lib = ac.get_library('my_library')
audited_lib = AuditedLibrary(lib, audit_logger)

# Use audited_lib for all operations
audited_lib.write("symbol", data, user_id="user123")
```

### 3. Audit Log Configuration

**RULE**: Audit logs MUST be configured with appropriate storage location and retention policies.

**Requirements**:
- Log files should be stored in a secure, backed-up location
- Log rotation should be configured to prevent disk space issues
- Logs should be retained according to compliance requirements (typically 7+ years)
- Log files should have restricted permissions (read-only for auditors)

**Recommended Configuration**:
```python
audit_logger = AuditLogger(
    log_file="/var/log/arcticdb/audit.log",  # Secure location
    enable_console=True  # Also log to console for monitoring
)
```

### 4. Migration of Existing Data

**RULE**: Before enabling audit requirements on existing databases, run the migration script to add audit metadata.

**Process**:
```bash
# 1. Dry run to see what will be changed
python -m arcticdb.scripts.migrate_audit lmdb:///path/to/db library_name --dry-run

# 2. Run actual migration with audit logging
python -m arcticdb.scripts.migrate_audit lmdb:///path/to/db library_name \
    --audit-log /var/log/arcticdb/migration_audit.log \
    --migration-user system_migration

# 3. Verify migration completed successfully
```

### 5. Audit Log Format

**RULE**: Audit logs are stored in JSON format with the following required fields:

```json
{
  "timestamp": "ISO 8601 UTC timestamp",
  "actor": "user_id or system_id",
  "operation": "operation type (read, write, update, append, delete, etc.)",
  "symbols": ["list", "of", "affected", "symbols"],
  "library": "library name",
  "metadata": {"optional": "additional context"}
}
```

### 6. Supported Operations

**RULE**: The following operations MUST be audited:

- `write` - Writing new data or creating new versions
- `read` - Reading data from symbols
- `update` - Updating existing data
- `append` - Appending data to symbols
- `delete` - Deleting symbols or versions
- `write_batch` - Batch write operations
- `read_batch` - Batch read operations
- `write_metadata` - Writing metadata only
- `read_metadata` - Reading metadata only

### 7. Error Handling

**RULE**: If `user_id` is not provided, operations MUST fail with a clear error message.

**Expected Behavior**:
```python
try:
    audited_lib.write("symbol", data)  # Missing user_id
except ValueError as e:
    # Error message: "write requires 'user_id' parameter for audit logging..."
    pass
```

### 8. Thread Safety

**RULE**: Audit logging MUST be thread-safe to support concurrent operations.

**Implementation**: The `AuditLogger` class uses threading locks to ensure safe concurrent access.

### 9. Performance Considerations

**RULE**: Audit logging should not significantly impact performance.

**Guidelines**:
- Audit logs are written asynchronously where possible
- File I/O is buffered and flushed periodically
- Audit metadata is lightweight (no data duplication)

### 10. Security and Privacy

**RULE**: Audit logs MUST NOT contain sensitive data values, only metadata about operations.

**What to log**:
- ✓ Symbol names
- ✓ Operation types
- ✓ User IDs
- ✓ Timestamps
- ✓ Library names

**What NOT to log**:
- ✗ Actual data values
- ✗ Passwords or credentials
- ✗ Personal identifiable information (PII) from data

## Code Examples

### Basic Usage

```python
import arcticdb as adb
from arcticdb.audit import AuditedLibrary, AuditLogger

# Initialize
audit_logger = AuditLogger(log_file="audit.log")
ac = adb.Arctic('lmdb://./data')
lib = ac.get_library('my_lib', create_if_missing=True)
audited_lib = AuditedLibrary(lib, audit_logger)

# Write with user_id
import pandas as pd
df = pd.DataFrame({'a': [1, 2, 3]})
audited_lib.write("my_symbol", df, user_id="alice")

# Read with user_id
data = audited_lib.read("my_symbol", user_id="bob")
```

### System Operations

```python
# For automated systems, use descriptive system IDs
audited_lib.write(
    "daily_snapshot",
    snapshot_data,
    user_id="system_daily_backup"
)
```

### Batch Operations

```python
from arcticdb import WritePayload

payloads = [
    WritePayload("sym1", df1),
    WritePayload("sym2", df2),
]

audited_lib.write_batch(payloads, user_id="alice")
```

## Compliance and Governance

### Audit Trail Requirements

1. **Immutability**: Audit logs should be write-once, read-many
2. **Completeness**: All operations must be logged without exception
3. **Accuracy**: Timestamps must be accurate and in UTC
4. **Availability**: Logs must be available for compliance reviews

### Access Control

1. Audit log files should have restricted write access
2. Only authorized personnel should read audit logs
3. Log tampering should be detectable

## For AI Agents and Developers

When implementing new features or modifying existing code:

1. **Always use `AuditedLibrary`** for any production code
2. **Never bypass audit requirements** - if user_id is missing, fail fast
3. **Test with audit logging enabled** to ensure it works correctly
4. **Document any new operations** that need to be audited
5. **Preserve backward compatibility** - existing code should continue to work with migration

## Questions and Support

For questions about audit requirements:
- Review this document first
- Check `examples/audit_example.py` for usage patterns
- Consult the README.md Enterprise Audit section
- Review the implementation in `python/arcticdb/audit/`

## Version History

- **v1.0** (2024-01-15): Initial audit requirements established

