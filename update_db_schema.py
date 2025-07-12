import sqlite3

def update_database_schema():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    try:
        # 检查email列是否存在
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 添加email列（如果不存在）
        if 'email' not in columns:
            print("Adding email column...")
            cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        
        # 添加native_language列（如果不存在）
        if 'native_language' not in columns:
            print("Adding native_language column...")
            cursor.execute("ALTER TABLE users ADD COLUMN native_language TEXT DEFAULT 'English'")
        
        # 提交更改
        conn.commit()
        print("Database schema updated successfully!")
        
        # 显示更新后的表结构
        cursor.execute("PRAGMA table_info(users)")
        print("\nUpdated table structure:")
        for column in cursor.fetchall():
            print(f"  {column[1]} ({column[2]})")
        
        # 显示现有用户数据
        cursor.execute("SELECT id, username, email, native_language FROM users")
        print("\nCurrent users:")
        for user in cursor.fetchall():
            print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2] or 'Not set'}, Language: {user[3] or 'English'}")
            
    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_database_schema() 