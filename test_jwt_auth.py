#!/usr/bin/env python3
"""
JWT认证功能测试脚本
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:5000"

def test_register():
    """测试用户注册"""
    print("测试用户注册...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": "testuser",
            "password": "testpassword123",
            "email": "test@example.com"
        })
        
        if response.status_code == 200:
            print("用户注册成功")
            return True
        else:
            print(f"用户注册失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"网络错误: {e}")
        return False

def test_login():
    """测试用户登录"""
    print("\n测试用户登录...")
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        
        if response.status_code == 200:
            data = response.json()
            print("用户登录成功")
            print(f"访问令牌: {data.get('access_token', '')[:50]}...")
            print(f"刷新令牌: {data.get('refresh_token', '')[:50]}...")
            return data.get('access_token')
        else:
            print(f"用户登录失败: {response.status_code} - {response.text}")
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
            print("受保护端点访问成功")
            print(f"用户信息: {data}")
            return True
        else:
            print(f"受保护端点访问失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"网络错误: {e}")
        return False

def test_refresh_token(refresh_token):
    """测试令牌刷新"""
    print("\n测试令牌刷新...")
    
    if not refresh_token:
        print("没有刷新令牌，跳过测试")
        return False
    
    try:
        response = requests.post(f"{BASE_URL}/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        if response.status_code == 200:
            data = response.json()
            print("令牌刷新成功")
            print(f"新访问令牌: {data.get('access_token', '')[:50]}...")
            return True
        else:
            print(f"令牌刷新失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"网络错误: {e}")
        return False

def test_logout(access_token):
    """测试用户登出"""
    print("\n测试用户登出...")
    
    if not access_token:
        print("没有访问令牌，跳过测试")
        return False
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(f"{BASE_URL}/api/auth/logout", headers=headers)
        
        if response.status_code == 200:
            print("用户登出成功")
            return True
        else:
            print(f"用户登出失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"网络错误: {e}")
        return False

def main():
    """主测试函数"""
    print("开始JWT认证功能测试")
    print("=" * 50)
    
    # 测试注册
    register_success = test_register()
    
    # 测试登录
    login_data = None
    access_token = None
    refresh_token = None
    
    if register_success:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "testuser",
            "password": "testpassword123"
        })
        if response.status_code == 200:
            login_data = response.json()
            access_token = login_data.get('access_token')
            refresh_token = login_data.get('refresh_token')
    
    # 测试受保护的端点
    if access_token:
        test_protected_endpoint(access_token)
    
    # 测试令牌刷新
    if refresh_token:
        test_refresh_token(refresh_token)
    
    # 测试登出
    if access_token:
        test_logout(access_token)
    
    print("\n" + "=" * 50)
    print("JWT认证功能测试完成！")

if __name__ == "__main__":
    main()
