#!/usr/bin/env python3
"""
数据库结构更新脚本
为现有的数据库添加JWT认证所需的字段
"""

import sqlite3
import os

def update_database():
    """更新现有数据库结构"""
    
    db_path = 'users.db'
    
    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print("数据库文件不存在，请先运行 check_users_db.py 初始化数据库")
        return
    
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("开始更新数据库结构...")
        
        # 检查并添加 is_active 字段
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_active' not in columns:
            print("添加 is_active 字段...")
            cursor.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
            print("is_active 字段添加成功")
        else:
            print("is_active 字段已存在")
        
        # 检查并添加 updated_at 字段
        if 'updated_at' not in columns:
            print("添加 updated_at 字段...")
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP")
            # 为现有记录设置默认值
            cursor.execute("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
            print("updated_at 字段添加成功")
        else:
            print("updated_at 字段已存在")
        
        # 更新所有现有用户的 is_active 状态
        cursor.execute("UPDATE users SET is_active = TRUE WHERE is_active IS NULL")
        
        # 检查并创建 token_blacklist 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='token_blacklist'")
        if not cursor.fetchone():
            print("创建 token_blacklist 表...")
            cursor.execute('''
                CREATE TABLE token_blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token_jti TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            print("token_blacklist 表创建成功")
        else:
            print("token_blacklist 表已存在")
        
        # 检查并创建 user_sessions 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_sessions'")
        if not cursor.fetchone():
            print("创建 user_sessions 表...")
            cursor.execute('''
                CREATE TABLE user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT UNIQUE NOT NULL,
                    refresh_token TEXT,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            print("user_sessions 表创建成功")
        else:
            print("user_sessions 表已存在")
        
        # 提交更改
        conn.commit()
        print("数据库结构更新成功！")
        
        # 验证表结构
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"数据库中的表: {[table[0] for table in tables]}")
        
        # 验证users表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("users表结构:")
        for column in columns:
            print(f"  {column[1]} {column[2]} {'NOT NULL' if column[3] else 'NULL'} {'DEFAULT ' + str(column[4]) if column[4] is not None else ''}")
        
    except Exception as e:
        print(f"数据库更新失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database()
