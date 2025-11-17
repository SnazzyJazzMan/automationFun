"""
ArcticDB Enterprise Audit Example

This example demonstrates how to use ArcticDB with enterprise audit and traceability features.
All read and write operations require a user_id parameter and are automatically logged.
"""

import pandas as pd
import numpy as np
import arcticdb as adb
from arcticdb.audit import AuditedLibrary, AuditLogger


def main():
    """Demonstrate audited ArcticDB usage."""
    
    print("=" * 80)
    print("ArcticDB Enterprise Audit Example")
    print("=" * 80)
    
    # Step 1: Set up audit logging
    print("\n1. Setting up audit logging...")
    audit_logger = AuditLogger(
        log_file="./audit_logs/arcticdb_audit.log",
        enable_console=True
    )
    print("   ✓ Audit logger initialized")
    
    # Step 2: Connect to ArcticDB
    print("\n2. Connecting to ArcticDB...")
    ac = adb.Arctic('lmdb://./demo_data')
    print("   ✓ Connected to LMDB storage")
    
    # Step 3: Get library and wrap it with audit functionality
    print("\n3. Creating audited library...")
    lib = ac.get_library('demo_library', create_if_missing=True)
    audited_lib = AuditedLibrary(lib, audit_logger)
    print("   ✓ Library wrapped with audit functionality")
    
    # Step 4: Write data with user_id
    print("\n4. Writing data (requires user_id)...")
    df = pd.DataFrame({
        'price': np.random.randn(100),
        'volume': np.random.randint(1000, 10000, 100)
    }, index=pd.date_range('2024-01-01', periods=100, freq='h'))
    
    # This will work - user_id is provided
    try:
        audited_lib.write("stock_AAPL", df, user_id="alice.smith")
        print("   ✓ Data written successfully by alice.smith")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # This will fail - no user_id
    print("\n5. Attempting write without user_id (should fail)...")
    try:
        audited_lib.write("stock_GOOGL", df)
        print("   ✗ This should not happen!")
    except ValueError as e:
        print(f"   ✓ Correctly rejected: {e}")
    
    # Step 6: Read data with user_id
    print("\n6. Reading data (requires user_id)...")
    try:
        data = audited_lib.read("stock_AAPL", user_id="bob.jones")
        print(f"   ✓ Data read successfully by bob.jones")
        print(f"   Data shape: {data.data.shape}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 7: Update data
    print("\n7. Updating data...")
    update_df = pd.DataFrame({
        'price': np.random.randn(10),
        'volume': np.random.randint(1000, 10000, 10)
    }, index=pd.date_range('2024-01-01', periods=10, freq='h'))
    
    try:
        audited_lib.update("stock_AAPL", update_df, user_id="alice.smith")
        print("   ✓ Data updated successfully by alice.smith")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 8: Append data
    print("\n8. Appending data...")
    append_df = pd.DataFrame({
        'price': np.random.randn(20),
        'volume': np.random.randint(1000, 10000, 20)
    }, index=pd.date_range('2024-01-05 04:00', periods=20, freq='h'))
    
    try:
        audited_lib.append("stock_AAPL", append_df, user_id="charlie.brown")
        print("   ✓ Data appended successfully by charlie.brown")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 9: Batch operations
    print("\n9. Batch write operations...")
    from arcticdb import WritePayload
    
    payloads = [
        WritePayload("stock_MSFT", df.copy()),
        WritePayload("stock_TSLA", df.copy()),
        WritePayload("stock_NVDA", df.copy()),
    ]
    
    try:
        results = audited_lib.write_batch(payloads, user_id="alice.smith")
        print(f"   ✓ Batch write completed: {len(results)} symbols written")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 10: Batch read operations
    print("\n10. Batch read operations...")
    try:
        results = audited_lib.read_batch(
            ["stock_MSFT", "stock_TSLA", "stock_NVDA"],
            user_id="bob.jones"
        )
        print(f"   ✓ Batch read completed: {len(results)} symbols read")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 11: View audit logs
    print("\n11. Viewing recent audit logs...")
    recent_logs = audit_logger.read_logs(limit=10)
    print(f"   Recent operations (last {len(recent_logs)}):")
    for log in recent_logs[:5]:  # Show first 5
        print(f"   - {log.timestamp[:19]} | {log.actor:15} | {log.operation:15} | {log.symbols}")
    
    # Step 12: System operations
    print("\n12. System operations (using system_id)...")
    try:
        # System operations should use a system_id instead of user_id
        audited_lib.write(
            "system_config",
            pd.DataFrame({'setting': ['value1', 'value2']}),
            user_id="system_backup_job"
        )
        print("   ✓ System operation logged with system_id")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 80)
    print("Example completed successfully!")
    print("=" * 80)
    print(f"\nAudit log file: ./audit_logs/arcticdb_audit.log")
    print("All operations have been logged with user identification.")
    print("\nKey takeaways:")
    print("  • All read/write operations require user_id parameter")
    print("  • Operations are automatically logged with timestamp and actor")
    print("  • Audit logs are stored in JSON format for easy parsing")
    print("  • Both user operations and system operations are tracked")


if __name__ == "__main__":
    main()

