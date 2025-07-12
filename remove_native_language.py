import sqlite3

def remove_native_language_column():
    """移除users表中的native_language列"""
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("当前表结构:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # 检查是否存在native_language列
        has_native_language = any(col[1] == 'native_language' for col in columns)
        
        if has_native_language:
            print("\n正在移除native_language列...")
            
            # 首先检查是否有重复的用户名
            cursor.execute("""
                SELECT username, COUNT(*) as count
                FROM users 
                GROUP BY username 
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            
            if duplicates:
                print("发现重复的用户名:")
                for username, count in duplicates:
                    print(f"  {username}: {count} 次")
                
                # 删除重复的用户名，保留ID最小的
                for username, count in duplicates:
                    cursor.execute("""
                        DELETE FROM users 
                        WHERE username = ? 
                        AND id NOT IN (
                            SELECT MIN(id) 
                            FROM users 
                            WHERE username = ?
                        )
                    """, (username, username))
                
                print("已清理重复的用户名")
            
            # 删除可能存在的临时表
            cursor.execute("DROP TABLE IF EXISTS users_temp")
            
            # 创建临时表（不包含native_language列）
            cursor.execute("""
                CREATE TABLE users_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    email TEXT
                )
            """)
            
            # 复制数据到临时表
            cursor.execute("""
                INSERT INTO users_temp (id, username, password, email)
                SELECT id, username, password, email FROM users
            """)
            
            # 删除原表
            cursor.execute("DROP TABLE users")
            
            # 重命名临时表
            cursor.execute("ALTER TABLE users_temp RENAME TO users")
            
            print("native_language列已成功移除")
        else:
            print("native_language列不存在，无需移除")
        
        # 显示更新后的表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\n更新后的表结构:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        conn.commit()
        conn.close()
        
        print("\n数据库迁移完成！")
        
    except Exception as e:
        print(f"迁移过程中出错: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    remove_native_language_column() 