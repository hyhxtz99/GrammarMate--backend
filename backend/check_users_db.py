import sqlite3

conn = sqlite3.connect('D:/internal project/users.db')
cursor = conn.cursor()

# 查看表结构
cursor.execute("PRAGMA table_info(users)")
print(cursor.fetchall())

# 查询所有用户数据
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
for row in rows:
    print(row)

cursor.execute("SELECT * FROM grammar_logs")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
