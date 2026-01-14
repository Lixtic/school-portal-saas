#!/usr/bin/env python
"""
Quick Migration Script for Production Database
Run this to migrate your Neon database from your local machine.
"""

import os
import sys

def main():
    print("=" * 70)
    print("PRODUCTION DATABASE MIGRATION")
    print("=" * 70)
    
    # Check if DATABASE_URL is set
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        print("\n❌ ERROR: DATABASE_URL environment variable not set!")
        print("\nPlease set it first:")
        print("  Windows PowerShell:")
        print("    $env:DATABASE_URL=\"postgresql://user:pass@host/db\"")
        print("\n  Windows CMD:")
        print("    set DATABASE_URL=postgresql://user:pass@host/db")
        print("\n  Linux/Mac:")
        print("    export DATABASE_URL=postgresql://user:pass@host/db")
        print("\nGet your connection string from: https://console.neon.tech/")
        print("=" * 70)
        sys.exit(1)
    
    # Verify it's a PostgreSQL URL
    if not db_url.startswith('postgres'):
        print(f"\n⚠️  WARNING: DATABASE_URL doesn't look like a PostgreSQL URL")
        print(f"   Current value: {db_url[:50]}...")
        response = input("\nContinue anyway? (y/N): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    print(f"\n✓ DATABASE_URL is set (connecting to: {db_url.split('@')[1].split('/')[0]})")
    print("\nStarting migration process...")
    print("-" * 70)
    
    # Import and run the migration script
    sys.path.insert(0, os.path.dirname(__file__))
    from migrate_remote import migrate_remote
    
    migrate_remote()

if __name__ == '__main__':
    main()
