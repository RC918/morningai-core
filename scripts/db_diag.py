#!/usr/bin/env python3
"""
Database Connection Diagnostic Script
用於診斷和測試數據庫連接問題
"""

import os
import sys
import psycopg
from urllib.parse import urlparse, parse_qs

def test_database_connection():
    """測試數據庫連接"""
    print("=== MorningAI Database Connection Diagnostic ===")
    print()
    
    # 獲取 DATABASE_URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        return False
    
    print(f"🔍 DATABASE_URL: {database_url[:50]}...")
    
    # 解析 URL
    try:
        parsed = urlparse(database_url)
        print(f"📋 Connection Details:")
        print(f"   Scheme: {parsed.scheme}")
        print(f"   Host: {parsed.hostname}")
        print(f"   Port: {parsed.port}")
        print(f"   Database: {parsed.path[1:] if parsed.path else 'N/A'}")
        print(f"   Username: {parsed.username}")
        print(f"   Password: {'*' * len(parsed.password) if parsed.password else 'N/A'}")
        
        # 檢查查詢參數
        query_params = parse_qs(parsed.query)
        print(f"   Query params: {query_params}")
        
    except Exception as e:
        print(f"❌ ERROR parsing DATABASE_URL: {e}")
        return False
    
    print()
    
    # 測試連接
    try:
        print("🔌 Testing database connection...")
        
        # 使用 psycopg 連接
        with psycopg.connect(database_url) as conn:
            print("✅ Connection successful!")
            
            # 測試基本查詢
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"📊 PostgreSQL Version: {version}")
                
                # 測試當前數據庫信息
                cur.execute("SELECT current_database(), current_user, inet_server_addr(), inet_server_port();")
                db_info = cur.fetchone()
                print(f"📋 Database Info:")
                print(f"   Current DB: {db_info[0]}")
                print(f"   Current User: {db_info[1]}")
                print(f"   Server Address: {db_info[2]}")
                print(f"   Server Port: {db_info[3]}")
                
                # 測試 SSL 狀態
                cur.execute("SHOW ssl;")
                ssl_status = cur.fetchone()[0]
                print(f"🔒 SSL Status: {ssl_status}")
                
        print()
        print("✅ All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        return False

def main():
    """主函數"""
    success = test_database_connection()
    
    if success:
        print("\n🎉 Database connection is working correctly!")
        sys.exit(0)
    else:
        print("\n💥 Database connection failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()

