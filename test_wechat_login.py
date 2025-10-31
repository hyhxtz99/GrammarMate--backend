#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信登录功能测试脚本
"""

import requests
import json
import time

def test_wechat_qr_generation():
    """测试微信二维码生成"""
    print("测试微信二维码生成...")
    
    try:
        response = requests.get('http://localhost:5000/api/wechat/qr')
        
        if response.status_code == 200:
            data = response.json()
            print("✓ 二维码生成成功")
            print(f"  - Session ID: {data['session_id']}")
            print(f"  - 过期时间: {data['expires_in']} 秒")
            print(f"  - 二维码数据长度: {len(data['qr_code'])} 字符")
            return data['session_id']
        else:
            print(f"✗ 二维码生成失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return None

def test_wechat_status_check(session_id):
    """测试微信登录状态检查"""
    print(f"\n测试微信登录状态检查 (Session: {session_id})...")
    
    try:
        response = requests.post('http://localhost:5000/api/wechat/status', 
                               json={'session_id': session_id})
        
        if response.status_code == 200:
            data = response.json()
            print("✓ 状态检查成功")
            print(f"  - 状态: {data['status']}")
            return True
        else:
            print(f"✗ 状态检查失败: {response.status_code}")
            print(f"  错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def test_api_endpoints():
    """测试所有API端点"""
    print("测试API端点...")
    
    try:
        response = requests.get('http://localhost:5000/')
        
        if response.status_code == 200:
            data = response.json()
            print("✓ API端点测试成功")
            
            # 检查微信相关端点
            endpoints = data.get('endpoints', {})
            wechat_endpoints = [k for k in endpoints.keys() if 'wechat' in k]
            
            if wechat_endpoints:
                print("✓ 发现微信登录端点:")
                for endpoint in wechat_endpoints:
                    print(f"  - {endpoint}: {endpoints[endpoint]}")
            else:
                print("✗ 未发现微信登录端点")
                
            return True
        else:
            print(f"✗ API端点测试失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 微信登录功能测试 ===\n")
    
    # 测试API端点
    if not test_api_endpoints():
        print("\n请确保后端服务正在运行 (python app.py)")
        return
    
    # 测试二维码生成
    session_id = test_wechat_qr_generation()
    if not session_id:
        print("\n二维码生成测试失败")
        return
    
    # 测试状态检查
    test_wechat_status_check(session_id)
    
    print("\n=== 测试完成 ===")
    print("\n注意事项:")
    print("1. 当前使用模拟的微信登录流程")
    print("2. 生产环境需要配置真实的微信开放平台应用")
    print("3. 查看 WECHAT_LOGIN_SETUP.md 了解详细配置说明")

if __name__ == "__main__":
    main()
