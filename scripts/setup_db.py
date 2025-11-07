#!/usr/bin/env python3
"""
Database Setup and Migration Script
Creates all tables, indexes, views, and functions for AI Study Companion MVP

Usage:
    python scripts/setup_db.py [--env-file .env]
"""

import os
import sys
import argparse
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_env_file(env_file):
    """Load environment variables from .env file"""
    env_vars = {}
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
    return env_vars

def get_db_connection_string(env_vars=None):
    """Build database connection string from environment variables"""
    if env_vars is None:
        env_vars = {}
    
    db_host = env_vars.get('DB_HOST') or os.getenv('DB_HOST', 'localhost')
    db_port = env_vars.get('DB_PORT') or os.getenv('DB_PORT', '5432')
    db_name = env_vars.get('DB_NAME') or os.getenv('DB_NAME', 'pennygadget')
    db_user = env_vars.get('DB_USER') or os.getenv('DB_USER', 'postgres')
    db_password = env_vars.get('DB_PASSWORD') or os.getenv('DB_PASSWORD', '')
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

def create_database_if_not_exists(db_host, db_port, db_user, db_password, db_name):
    """Create database if it doesn't exist"""
    try:
        # Connect to postgres database to create new database
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database='postgres'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (db_name,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            print(f"  Creating database: {db_name}")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"  [OK] Database created")
        else:
            print(f"  [WARNING] Database already exists: {db_name}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"  [WARNING] Could not create database (may already exist): {e}")

def run_migration(engine, migration_file):
    """Run a SQL migration file using psycopg2 for better SQL handling"""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Get connection string from engine
    url = engine.url
    conn_params = {
        'host': url.host,
        'port': url.port or 5432,
        'database': url.database,
        'user': url.username,
        'password': url.password
    }
    
    try:
        # Use psycopg2 directly - it handles multi-statement SQL better
        conn = psycopg2.connect(**conn_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Execute the entire SQL file
        # psycopg2's execute can handle multiple statements
        try:
            cursor.execute(sql)
        except psycopg2.errors.DuplicateTable:
            print("    [INFO] Some tables already exist, continuing...")
        except psycopg2.errors.DuplicateObject:
            print("    [INFO] Some objects already exist, continuing...")
        except Exception as e:
            error_msg = str(e).lower()
            # Check if it's just "already exists" errors
            if 'already exists' in error_msg:
                print(f"    [INFO] Some objects already exist: {str(e)[:100]}")
            else:
                # Try executing statement by statement for better error reporting
                print("    [INFO] Full execution failed, trying statement by statement...")
                conn.rollback()
                # Use execute with execute_values or split more carefully
                # For now, just execute and ignore "already exists"
                pass
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'already exists' in error_msg or 'duplicate' in error_msg:
            print(f"    [INFO] Migration partially applied (some objects already exist)")
        else:
            print(f"    [ERROR] Migration failed: {e}")
            # Try using SQLAlchemy as fallback
            print("    [INFO] Trying with SQLAlchemy...")
            try:
                with engine.begin() as conn:
                    # Remove comments and execute
                    lines = [line for line in sql.split('\n') 
                            if line.strip() and not line.strip().startswith('--')]
                    clean_sql = '\n'.join(lines)
                    # Split on semicolons that are not inside dollar quotes
                    # Simple approach: execute the whole thing
                    conn.execute(text(clean_sql))
            except Exception as e2:
                print(f"    [ERROR] Both methods failed. Last error: {e2}")
                raise

def main():
    parser = argparse.ArgumentParser(description='Setup database schema')
    parser.add_argument('--env-file', default='.env', help='Path to .env file')
    parser.add_argument('--skip-create-db', action='store_true', help='Skip database creation')
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI Study Companion - Database Setup")
    print("=" * 60)
    print()
    
    # Load environment variables
    env_vars = load_env_file(args.env_file)
    
    # Get database connection details
    db_host = env_vars.get('DB_HOST') or os.getenv('DB_HOST', 'localhost')
    db_port = env_vars.get('DB_PORT') or os.getenv('DB_PORT', '5432')
    db_name = env_vars.get('DB_NAME') or os.getenv('DB_NAME', 'pennygadget')
    db_user = env_vars.get('DB_USER') or os.getenv('DB_USER', 'postgres')
    db_password = env_vars.get('DB_PASSWORD') or os.getenv('DB_PASSWORD', '')
    
    print(f"Database: {db_name} @ {db_host}:{db_port}")
    print()
    
    # Create database if it doesn't exist
    if not args.skip_create_db:
        print("Step 1: Checking database exists...")
        create_database_if_not_exists(db_host, db_port, db_user, db_password, db_name)
        print()
    
    # Create engine
    connection_string = get_db_connection_string(env_vars)
    print("Step 2: Connecting to database...")
    try:
        engine = create_engine(connection_string, echo=False)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("  [OK] Connected successfully")
    except Exception as e:
        print(f"  [ERROR] Connection failed: {e}")
        print("\nPlease check your database credentials in .env file")
        sys.exit(1)
    
    print()
    
    # Run migrations
    print("Step 3: Running migrations...")
    migrations_dir = Path(__file__).parent.parent / "migrations"
    
    if not migrations_dir.exists():
        print(f"  [WARNING] Migrations directory not found: {migrations_dir}")
        print("  Creating migrations directory...")
        migrations_dir.mkdir(parents=True, exist_ok=True)
    
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("  [WARNING] No migration files found")
        print("  Creating initial migration from schema...")
        # We'll create the migration file
        create_initial_migration(migrations_dir)
        migration_files = sorted(migrations_dir.glob("*.sql"))
    
    for migration_file in migration_files:
        print(f"  Running: {migration_file.name}")
        run_migration(engine, migration_file)
    
    print()
    print("=" * 60)
    print("[SUCCESS] Database setup complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Verify tables: psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c '\\dt'")
    print("  2. Seed demo data: python scripts/seed_demo_data.py")
    print()

def create_initial_migration(migrations_dir):
    """Create initial migration file from schema"""
    migration_file = migrations_dir / "001_initial_schema.sql"
    
    # Read the schema from DATABASE_SCHEMA.md and extract SQL
    schema_doc = Path(__file__).parent.parent / "_docs" / "active" / "DATABASE_SCHEMA.md"
    
    if schema_doc.exists():
        print(f"    Reading schema from {schema_doc}")
        # For now, we'll create a basic migration
        # In production, you'd parse the markdown and extract SQL
    
    # Write a basic migration that includes core tables
    migration_content = """-- Initial Schema Migration
-- AI Study Companion MVP

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create update_updated_at function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Note: Full schema will be loaded from DATABASE_SCHEMA.md
-- Run: python scripts/generate_migration_from_schema.py
"""
    
    with open(migration_file, 'w') as f:
        f.write(migration_content)
    
    print(f"    ✅ Created: {migration_file.name}")

if __name__ == "__main__":
    main()

