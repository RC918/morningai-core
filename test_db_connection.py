#!/usr/bin/env python3
"""
Test Supabase database connection
"""
import os
import sys
try:
    import psycopg2
    from psycopg2 import sql
except ImportError:
    print("Installing psycopg2...")
    os.system("pip install psycopg2-binary")
    import psycopg2
    from psycopg2 import sql

def test_connection():
    """Test database connection"""
    connection_string = "postgresql://postgres.deuytovttpkgewgzqjxx:hgQtFxlxWefSJsmZ@aws-1-ap-southeast-1.pooler.supabase.com:6543/postgres"
    
    try:
        print("Testing Supabase database connection...")
        conn = psycopg2.connect(connection_string)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        # Check existing tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f"\n📋 Existing tables ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if we have the expected schema
        expected_tables = ['tenants', 'users', 'roles', 'user_roles', 'referral_codes', 'audit_logs']
        existing_table_names = [table[0] for table in tables]
        
        print(f"\n🔍 Schema validation:")
        for table in expected_tables:
            if table in existing_table_names:
                print(f"  ✅ {table} - exists")
            else:
                print(f"  ❌ {table} - missing")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)

