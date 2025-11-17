"""
Basic test to verify audit functionality works correctly.

This script performs basic operations to ensure the audit system is functioning.
"""

import sys
import tempfile
import shutil
from pathlib import Path

try:
    import pandas as pd
    import numpy as np
    import arcticdb as adb
    from arcticdb.audit import AuditedLibrary, AuditLogger
    
    print("✓ All imports successful")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def test_audit_basic():
    """Test basic audit functionality."""
    
    # Create temporary directories
    temp_dir = tempfile.mkdtemp()
    audit_log = Path(temp_dir) / "audit.log"
    db_path = Path(temp_dir) / "test_db"
    
    try:
        print("\n" + "=" * 60)
        print("Testing ArcticDB Audit Functionality")
        print("=" * 60)
        
        # 1. Set up audit logger
        print("\n1. Setting up audit logger...")
        audit_logger = AuditLogger(log_file=str(audit_log), enable_console=False)
        print("   ✓ Audit logger created")
        
        # 2. Create ArcticDB instance
        print("\n2. Creating ArcticDB instance...")
        ac = adb.Arctic(f'lmdb://{db_path}')
        print("   ✓ Arctic instance created")
        
        # 3. Get library and wrap it
        print("\n3. Creating audited library...")
        lib = ac.get_library('test_lib', create_if_missing=True)
        audited_lib = AuditedLibrary(lib, audit_logger)
        print("   ✓ Library wrapped with audit functionality")
        
        # 4. Test write with user_id
        print("\n4. Testing write with user_id...")
        df = pd.DataFrame({
            'value': np.random.randn(10)
        }, index=pd.date_range('2024-01-01', periods=10, freq='D'))
        
        audited_lib.write("test_symbol", df, user_id="test_user")
        print("   ✓ Write successful")
        
        # 5. Test write without user_id (should fail)
        print("\n5. Testing write without user_id (should fail)...")
        try:
            audited_lib.write("test_symbol2", df)
            print("   ✗ Should have raised ValueError!")
            return False
        except ValueError as e:
            if "user_id" in str(e):
                print("   ✓ Correctly rejected write without user_id")
            else:
                print(f"   ✗ Wrong error: {e}")
                return False
        
        # 6. Test read with user_id
        print("\n6. Testing read with user_id...")
        data = audited_lib.read("test_symbol", user_id="another_user")
        print(f"   ✓ Read successful, shape: {data.data.shape}")
        
        # 7. Test read without user_id (should fail)
        print("\n7. Testing read without user_id (should fail)...")
        try:
            audited_lib.read("test_symbol")
            print("   ✗ Should have raised ValueError!")
            return False
        except ValueError as e:
            if "user_id" in str(e):
                print("   ✓ Correctly rejected read without user_id")
            else:
                print(f"   ✗ Wrong error: {e}")
                return False
        
        # 8. Verify audit log exists and has entries
        print("\n8. Verifying audit log...")
        if not audit_log.exists():
            print("   ✗ Audit log file not created!")
            return False
        
        logs = audit_logger.read_logs()
        if len(logs) < 2:  # Should have at least write and read
            print(f"   ✗ Expected at least 2 log entries, got {len(logs)}")
            return False
        
        print(f"   ✓ Audit log has {len(logs)} entries")
        
        # 9. Verify log content
        print("\n9. Verifying log content...")
        write_log = next((l for l in logs if l.operation == "write"), None)
        read_log = next((l for l in logs if l.operation == "read"), None)
        
        if not write_log:
            print("   ✗ No write operation in logs!")
            return False
        if not read_log:
            print("   ✗ No read operation in logs!")
            return False
        
        if write_log.actor != "test_user":
            print(f"   ✗ Wrong actor in write log: {write_log.actor}")
            return False
        
        if read_log.actor != "another_user":
            print(f"   ✗ Wrong actor in read log: {read_log.actor}")
            return False
        
        print("   ✓ Log content verified")
        print(f"     - Write: {write_log.actor} -> {write_log.symbols}")
        print(f"     - Read: {read_log.actor} -> {read_log.symbols}")
        
        # 10. Test update operation
        print("\n10. Testing update operation...")
        update_df = pd.DataFrame({
            'value': [999.0]
        }, index=pd.date_range('2024-01-01', periods=1, freq='D'))
        
        audited_lib.update("test_symbol", update_df, user_id="updater")
        print("   ✓ Update successful")
        
        print("\n" + "=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        print("\nCleaning up temporary files...")
        shutil.rmtree(temp_dir, ignore_errors=True)
        print("✓ Cleanup complete")


if __name__ == "__main__":
    success = test_audit_basic()
    sys.exit(0 if success else 1)

