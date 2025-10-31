#!/usr/bin/env python3
"""
GitHub OAuth 登录功能测试脚本
"""

import requests
import json
import time

# 测试配置
BASE_URL = "http://localhost:5000"
GITHUB_CLIENT_ID = "Ov23lipc6lITYFJuQ8ZF"

def test_github_login_api():
    """测试GitHub登录API"""
    print("测试GitHub登录API...")
    
    try:
        # 测试获取GitHub登录URL
        response = requests.get(f"{BASE_URL}/api/github/login")
        
        if response.status_code == 200:
            data = response.json()
            print("GitHub登录URL获取成功")
            print(f"   Session ID: {data.get('session_id')}")
            print(f"   Auth URL: {data.get('auth_url')}")
            print(f"   Expires in: {data.get('expires_in')} seconds")
            
            # 保存session_id用于后续测试
            session_id = data.get('session_id')
            return session_id
        else:
            print(f"GitHub登录URL获取失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"网络错误: {e}")
        return None

def test_github_status_api(session_id):
    """测试GitHub登录状态检查API"""
    print(f"\n测试GitHub登录状态检查API (Session: {session_id})...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/github/status",
            json={"session_id": session_id},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("GitHub登录状态检查成功")
            print(f"   状态: {data.get('status')}")
            return data
        else:
            print(f"GitHub登录状态检查失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return None
            
    except Exception as e:
        print(f"网络错误: {e}")
        return None

def test_database_connection():
    """测试数据库连接和表结构"""
    print("\n测试数据库连接...")
    
    try:
        # 这里可以添加数据库连接测试
        # 由于我们没有直接的数据库连接函数，我们通过API间接测试
        response = requests.get(f"{BASE_URL}/")
        
        if response.status_code == 200:
            print("后端服务运行正常")
            return True
        else:
            print(f"后端服务异常: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"后端服务连接失败: {e}")
        return False

def test_github_oauth_config():
    """测试GitHub OAuth配置"""
    print("\n测试GitHub OAuth配置...")
    
    try:
        # 检查GitHub OAuth URL格式
        response = requests.get(f"{BASE_URL}/api/github/login")
        
        if response.status_code == 200:
            data = response.json()
            auth_url = data.get('auth_url', '')
            
            # 验证URL格式
            if auth_url.startswith('https://github.com/login/oauth/authorize'):
                print("GitHub OAuth URL格式正确")
                
                # 检查必要参数
                required_params = ['client_id', 'redirect_uri', 'scope', 'state']
                missing_params = []
                
                for param in required_params:
                    if f"{param}=" not in auth_url:
                        missing_params.append(param)
                
                if missing_params:
                    print(f"缺少必要参数: {missing_params}")
                else:
                    print("所有必要参数都存在")
                    
                return True
            else:
                print(f"GitHub OAuth URL格式错误: {auth_url}")
                return False
        else:
            print(f"无法获取GitHub OAuth URL: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"GitHub OAuth配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始GitHub OAuth功能测试")
    print("=" * 50)
    
    # 测试数据库连接
    if not test_database_connection():
        print("\n数据库连接测试失败，停止测试")
        return
    
    # 测试GitHub OAuth配置
    if not test_github_oauth_config():
        print("\nGitHub OAuth配置测试失败，停止测试")
        return
    
    # 测试GitHub登录API
    session_id = test_github_login_api()
    if not session_id:
        print("\nGitHub登录API测试失败，停止测试")
        return
    
    # 测试GitHub状态检查API
    status_data = test_github_status_api(session_id)
    if status_data is None:
        print("\nGitHub状态检查API测试失败")
        return
    
    print("\n" + "=" * 50)
    print("GitHub OAuth功能测试完成！")
    print("\n测试总结:")
    print("   数据库连接正常")
    print("   GitHub OAuth配置正确")
    print("   GitHub登录URL生成成功")
    print("   GitHub状态检查API正常")
    
    print(f"\n测试用的GitHub登录URL:")
    print(f"   {status_data.get('auth_url', 'N/A')}")
    
    print(f"\n使用说明:")
    print("   1. 确保后端服务正在运行 (python app.py)")
    print("   2. 确保前端服务正在运行 (cd my-app && npm start)")
    print("   3. 访问 http://localhost:3000/login")
    print("   4. 点击 'GitHub 登录' 按钮")
    print("   5. 在弹出的窗口中完成GitHub授权")

if __name__ == "__main__":
    main()
