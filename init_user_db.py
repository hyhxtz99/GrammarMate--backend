import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

# 创建 users 表
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    email TEXT,
    native_language TEXT DEFAULT 'English',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 创建 grammar_logs 表
cursor.execute("""
CREATE TABLE IF NOT EXISTS grammar_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    question TEXT,
    correction TEXT,
    error_types TEXT,  -- JSON 数组字符串
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 插入默认管理员账户
cursor.execute("INSERT OR IGNORE INTO users (username, password, email, native_language) VALUES (?, ?, ?, ?)", 
              ('admin', '123', 'admin@example.com', 'English'))

conn.commit()
conn.close()

print("Database initialized.")
