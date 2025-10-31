#!/usr/bin/env python3
"""
测试向后兼容的API接口
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:5000"

def test_legacy_register():
    """测试向后兼容的注册接口"""
    print("测试向后兼容的注册接口...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/register", json={
            "username": "legacyuser",
            "password": "legacypassword123",
            "email": "legacy@example.com"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"注册成功: {data}")
            return True
        else:
            print(f"注册失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"网络错误: {e}")
        return False

def test_legacy_login():
    """测试向后兼容的登录接口"""
    print("\n测试向后兼容的登录接口...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/login", json={
            "username": "legacyuser",
            "password": "legacypassword123"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"登录成功: {data}")
            return True
        else:
            print(f"登录失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"网络错误: {e}")
        return False

def test_jwt_login():
    """测试JWT登录接口"""
    print("\n测试JWT登录接口...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "legacyuser",
            "password": "legacypassword123"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"JWT登录成功")
            print(f"访问令牌: {data.get('access_token', '')[:50]}...")
            print(f"刷新令牌: {data.get('refresh_token', '')[:50]}...")
            return data.get('access_token')
        else:
            print(f"JWT登录失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"网络错误: {e}")
        return None

def test_protected_endpoint(access_token):
    """测试受保护的端点"""
    print("\n测试受保护的端点...")
    
    if not access_token:
        print("没有访问令牌，跳过测试")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"受保护端点访问成功: {data}")
            return True
        else:
            print(f"受保护端点访问失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"网络错误: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试向后兼容的API接口")
    print("=" * 50)
    
    # 测试向后兼容的注册
    test_legacy_register()
    
    # 测试向后兼容的登录
    test_legacy_login()
    
    # 测试JWT登录
    access_token = test_jwt_login()
    
    # 测试受保护的端点
    if access_token:
        test_protected_endpoint(access_token)
    
    print("\n" + "=" * 50)
    print("向后兼容API接口测试完成！")

if __name__ == "__main__":
    main()
