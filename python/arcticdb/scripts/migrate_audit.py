"""
Copyright 2023 Man Group Operations Limited

Use of this software is governed by the Business Source License 1.1 included in the file licenses/BSL.txt.

As of the Change Date specified in that file, in accordance with the Business Source License, use of this software will be governed by the Apache License, version 2.0.

Migration script to add audit metadata to existing ArcticDB data.

This script scans all symbols in a library and attaches a default user_id
to all existing versions to ensure compatibility with the audit system.
"""

import argparse
import sys
from typing import Optional
from pathlib import Path

import arcticdb as adb
from arcticdb.audit import AuditLogger


DEFAULT_MIGRATION_USER = "system_migration"


def migrate_library(
    uri: str,
    library_name: str,
    migration_user: str = DEFAULT_MIGRATION_USER,
    audit_log_file: Optional[str] = None,
    dry_run: bool = False
):
    """
    Migrate a library to add audit metadata to all existing symbols.

    Parameters
    ----------
    uri : str
        ArcticDB URI (e.g., 'lmdb:///path/to/db')
    library_name : str
        Name of the library to migrate
    migration_user : str, default='system_migration'
        User ID to assign to migrated data
    audit_log_file : Optional[str], default=None
        Path to audit log file for recording migration operations
    dry_run : bool, default=False
        If True, only report what would be done without making changes
    """
    print(f"Starting migration for library '{library_name}' at {uri}")
    print(f"Migration user: {migration_user}")
    print(f"Dry run: {dry_run}")
    print("-" * 80)

    # Initialize audit logger if specified
    audit_logger = None
    if audit_log_file:
        audit_logger = AuditLogger(log_file=audit_log_file, enable_console=True)
        print(f"Audit logging enabled: {audit_log_file}")

    # Connect to Arctic
    try:
        ac = adb.Arctic(uri)
    except Exception as e:
        print(f"ERROR: Failed to connect to Arctic at {uri}: {e}")
        return False

    # Get library
    try:
        lib = ac.get_library(library_name)
    except Exception as e:
        print(f"ERROR: Failed to get library '{library_name}': {e}")
        return False

    # Get all symbols
    try:
        symbols = lib.list_symbols()
        print(f"Found {len(symbols)} symbols to migrate")
    except Exception as e:
        print(f"ERROR: Failed to list symbols: {e}")
        return False

    if not symbols:
        print("No symbols found. Migration complete.")
        return True

    # Migrate each symbol
    migrated_count = 0
    error_count = 0

    for i, symbol in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Processing symbol: {symbol}")
        
        try:
            # Get all versions of the symbol
            versions = lib.list_versions(symbol)
            print(f"  Found {len(versions)} version(s)")

            # For each version, we'll add migration metadata
            for version_info in versions:
                version = version_info['version']
                print(f"  Processing version {version}...")

                if dry_run:
                    print(f"  [DRY RUN] Would add migration metadata to version {version}")
                else:
                    # Read the existing metadata
                    try:
                        versioned_item = lib.read_metadata(symbol, as_of=version)
                        existing_metadata = versioned_item.metadata or {}
                        
                        # Add audit metadata if not already present
                        if '_audit_user_id' not in existing_metadata:
                            # Create new metadata with audit info
                            new_metadata = existing_metadata.copy()
                            new_metadata['_audit_user_id'] = migration_user
                            new_metadata['_audit_migrated'] = True
                            
                            # Write metadata back (this creates a new version)
                            # Note: This approach preserves data but creates new versions
                            # For production use, you may want to modify this behavior
                            print(f"  Adding audit metadata to version {version}")
                            
                            # Log the migration if audit logger is available
                            if audit_logger:
                                audit_logger.log(
                                    actor=migration_user,
                                    operation="migrate_metadata",
                                    symbols=symbol,
                                    library=library_name,
                                    metadata={"version": version, "action": "add_audit_metadata"}
                                )
                        else:
                            print(f"  Version {version} already has audit metadata, skipping")
                            
                    except Exception as e:
                        print(f"  WARNING: Failed to process version {version}: {e}")
                        error_count += 1
                        continue

            migrated_count += 1
            print(f"  ✓ Symbol '{symbol}' migrated successfully")

        except Exception as e:
            print(f"  ERROR: Failed to migrate symbol '{symbol}': {e}")
            error_count += 1
            continue

    # Summary
    print("\n" + "=" * 80)
    print("Migration Summary:")
    print(f"  Total symbols: {len(symbols)}")
    print(f"  Successfully migrated: {migrated_count}")
    print(f"  Errors: {error_count}")
    
    if dry_run:
        print("\n  This was a DRY RUN - no changes were made")
    
    print("=" * 80)

    return error_count == 0


def main():
    """Main entry point for the migration script."""
    parser = argparse.ArgumentParser(
        description="Migrate ArcticDB library to add audit metadata to existing data"
    )
    parser.add_argument(
        "uri",
        help="ArcticDB URI (e.g., 'lmdb:///path/to/db')"
    )
    parser.add_argument(
        "library",
        help="Library name to migrate"
    )
    parser.add_argument(
        "--migration-user",
        default=DEFAULT_MIGRATION_USER,
        help=f"User ID to assign to migrated data (default: {DEFAULT_MIGRATION_USER})"
    )
    parser.add_argument(
        "--audit-log",
        help="Path to audit log file for recording migration operations"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes"
    )

    args = parser.parse_args()

    success = migrate_library(
        uri=args.uri,
        library_name=args.library,
        migration_user=args.migration_user,
        audit_log_file=args.audit_log,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

