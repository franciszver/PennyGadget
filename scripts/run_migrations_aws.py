#!/usr/bin/env python3
"""
Run database migrations on AWS RDS PostgreSQL instance
Usage: python scripts/run_migrations_aws.py
Environment variables required:
- DB_HOST: RDS endpoint
- DB_PORT: Database port (default: 5432)
- DB_NAME: Database name
- DB_USER: Database username
- DB_PASSWORD: Database password
"""

import sys
import os
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql


def run_migration_file(conn, migration_file):
    """Run a single migration file"""
    print(f"  Running migration: {migration_file.name}")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    try:
        cursor = conn.cursor()
        # Execute the entire SQL file
        cursor.execute(sql_content)
        conn.commit()
        cursor.close()
        print(f"  [OK] Successfully applied: {migration_file.name}")
        return True
    except psycopg2.errors.DuplicateTable:
        print(f"  [SKIP] Tables already exist in: {migration_file.name}")
        conn.rollback()
        return True
    except psycopg2.errors.DuplicateObject:
        print(f"  [SKIP] Objects already exist in: {migration_file.name}")
        conn.rollback()
        return True
    except Exception as e:
        error_msg = str(e).lower()
        if 'already exists' in error_msg or 'duplicate' in error_msg:
            print(f"  [SKIP] Some objects already exist in: {migration_file.name}")
            conn.rollback()
            return True
        else:
            print(f"  [ERROR] Error in {migration_file.name}: {e}")
            conn.rollback()
            return False


def main():
    parser = argparse.ArgumentParser(description='Run database migrations on AWS RDS')
    parser.add_argument('--host', help='Database host (or use DB_HOST env var)')
    parser.add_argument('--port', type=int, default=5432, help='Database port (default: 5432)')
    parser.add_argument('--database', help='Database name (or use DB_NAME env var)')
    parser.add_argument('--user', help='Database user (or use DB_USER env var)')
    parser.add_argument('--password', help='Database password (or use DB_PASSWORD env var)')
    parser.add_argument('--migrations-dir', default='migrations', help='Path to migrations directory')
    
    args = parser.parse_args()
    
    # Get connection parameters from args or environment
    db_host = args.host or os.getenv('DB_HOST')
    db_port = args.port or int(os.getenv('DB_PORT', '5432'))
    db_name = args.database or os.getenv('DB_NAME')
    db_user = args.user or os.getenv('DB_USER')
    db_password = args.password or os.getenv('DB_PASSWORD')
    
    if not all([db_host, db_name, db_user, db_password]):
        print("Error: Missing required database connection parameters")
        print("Provide via arguments or environment variables:")
        print("  DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
        sys.exit(1)
    
    # Get migrations directory
    project_root = Path(__file__).parent.parent
    migrations_dir = project_root / args.migrations_dir
    
    if not migrations_dir.exists():
        print(f"Error: Migrations directory not found: {migrations_dir}")
        sys.exit(1)
    
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print(f"Warning: No migration files found in {migrations_dir}")
        sys.exit(0)
    
    print("=" * 60)
    print("AWS RDS Migration Runner")
    print("=" * 60)
    print(f"Host: {db_host}")
    print(f"Database: {db_name}")
    print(f"User: {db_user}")
    print(f"Migrations found: {len(migration_files)}")
    print("=" * 60)
    print()
    
    # Connect to database
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            connect_timeout=10
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("[OK] Connected successfully")
        print()
    except Exception as e:
        print(f"[ERROR] Failed to connect to database: {e}")
        sys.exit(1)
    
    # Run migrations
    success_count = 0
    failed_count = 0
    
    for migration_file in migration_files:
        if run_migration_file(conn, migration_file):
            success_count += 1
        else:
            failed_count += 1
        print()
    
    conn.close()
    
    # Summary
    print("=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total migrations: {len(migration_files)}")
    print(f"Successful: {success_count}")
    if failed_count > 0:
        print(f"Failed: {failed_count}")
    print("=" * 60)
    
    if failed_count > 0:
        sys.exit(1)
    else:
        print("\n[SUCCESS] All migrations completed successfully!")
        sys.exit(0)


if __name__ == '__main__':
    main()

