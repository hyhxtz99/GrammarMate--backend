import sqlite3
import os

def init_database():
    """初始化用户数据库"""
    
    # 确保数据库文件存在
    db_path = 'users.db'
    
    # 连接数据库（如果不存在会自动创建）
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建语法检查日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grammar_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question TEXT NOT NULL,
                correction TEXT,
                error_types TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建GitHub登录会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_login_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                auth_url TEXT,
                status TEXT DEFAULT 'pending',
                user_id INTEGER,
                github_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建GitHub用户绑定表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS github_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                github_id TEXT UNIQUE NOT NULL,
                github_username TEXT,
                github_email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建JWT令牌黑名单表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS token_blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_jti TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 创建用户会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                refresh_token TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 提交更改
        conn.commit()
        print("数据库初始化成功！")
        print("创建了 users 表")
        print("创建了 grammar_logs 表")
        print("创建了 github_login_sessions 表")
        print("创建了 github_users 表")
        print("创建了 token_blacklist 表")
        print("创建了 user_sessions 表")
        
        # 验证表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"数据库中的表: {[table[0] for table in tables]}")
        
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    init_database()
