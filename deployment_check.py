#!/usr/bin/env python3
"""
部署狀態檢查腳本
檢查Auth和Referral端點是否已部署
"""
import requests
import json
import time
from datetime import datetime

BASE_URL = "https://morningai-core.onrender.com"

def check_endpoint(path, description):
    """檢查單個端點"""
    url = f"{BASE_URL}{path}"
    try:
        response = requests.get(url, timeout=10)
        print(f"✅ {description}: {response.status_code}")
        if response.status_code == 200:
            try:
                data = response.json()
                if "features" in data:
                    print(f"   Features: {data['features']}")
                elif "auth_routes_count" in data:
                    print(f"   Auth routes: {data['auth_routes_count']}, Referral routes: {data['referral_routes_count']}")
                return True
            except:
                print(f"   Response: {response.text[:100]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ {description}: Error - {e}")
        return False

def main():
    print(f"🔍 部署狀態檢查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 檢查基本端點
    endpoints = [
        ("/", "根路徑"),
        ("/health", "健康檢查"),
        ("/openapi.json", "OpenAPI文檔"),
        ("/api/v1/diagnosis", "診斷端點"),
        ("/api/v1/auth/register", "Auth註冊端點"),
        ("/api/v1/auth/login", "Auth登入端點"),
        ("/api/v1/referral/stats", "推薦統計端點"),
    ]
    
    results = {}
    for path, desc in endpoints:
        results[path] = check_endpoint(path, desc)
        time.sleep(0.5)  # 避免過快請求
    
    print("\n📊 檢查結果摘要:")
    print("=" * 60)
    
    total = len(results)
    success = sum(results.values())
    
    print(f"總端點數: {total}")
    print(f"成功端點: {success}")
    print(f"成功率: {success/total*100:.1f}%")
    
    if success >= 5:  # 至少5個端點成功
        print("🎉 部署狀態: 良好")
    elif success >= 3:
        print("⚠️ 部署狀態: 部分成功")
    else:
        print("❌ 部署狀態: 需要檢查")
    
    # 檢查OpenAPI文檔中的路由
    print("\n🔍 OpenAPI路由檢查:")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json", timeout=10)
        if response.status_code == 200:
            openapi_data = response.json()
            paths = openapi_data.get("paths", {})
            auth_paths = [p for p in paths.keys() if "/auth" in p]
            referral_paths = [p for p in paths.keys() if "/referral" in p]
            
            print(f"總路由數: {len(paths)}")
            print(f"Auth路由數: {len(auth_paths)}")
            print(f"Referral路由數: {len(referral_paths)}")
            
            if auth_paths:
                print("Auth路由:", auth_paths)
            if referral_paths:
                print("Referral路由:", referral_paths)
        else:
            print("無法獲取OpenAPI文檔")
    except Exception as e:
        print(f"OpenAPI檢查失敗: {e}")

if __name__ == "__main__":
    main()

