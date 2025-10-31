# GitHub登录Token问题修复说明

## 问题描述
GitHub登录后出现401/403权限错误，无法访问需要认证的API。

## 问题原因
1. **后端未生成JWT Token**：GitHub登录成功后，后端没有生成JWT access token和refresh token
2. **前端Token存储不一致**：前端存储的token键名与auth.js中读取的键名不匹配
3. **旧Token干扰**：localStorage中可能存在旧的、结构不同的token

## 修复内容

### 1. 后端修复 (app.py)
在GitHub回调处理函数中添加JWT token生成逻辑：

```python
# 生成JWT token
access_token = jwt_handler.create_access_token(data={"user_id": user_id, "username": github_username})
refresh_token = jwt_handler.create_refresh_token(data={"user_id": user_id, "username": github_username})

# 存储token到数据库
cursor.execute("""
    INSERT INTO user_sessions (user_id, session_token, refresh_token, expires_at)
    VALUES (?, ?, ?, ?)
""", (user_id, access_token, refresh_token, datetime.utcnow() + timedelta(days=7)))

# 返回token信息
return {
    "success": True, 
    "message": "GitHub login successful",
    "access_token": access_token,
    "refresh_token": refresh_token,
    "user_id": user_id,
    "username": github_username
}
```

### 2. 前端修复 (GitHubCallback.jsx)
在GitHub回调处理中：
- 清除所有旧的localStorage数据
- 存储新的token和用户信息
- 使用正确的键名（`access_token`和`refresh_token`）

```javascript
// 清除所有旧的认证信息
localStorage.clear();

// 存储新的token和用户信息
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
localStorage.setItem('userId', data.user_id);
localStorage.setItem('username', data.username);
```

## 测试步骤
1. 清除浏览器localStorage中的所有数据
2. 访问 http://localhost:3000/login
3. 点击"GitHub登录"按钮
4. 完成GitHub授权
5. 登录成功后，尝试访问需要认证的功能（如语法历史、个人中心）
6. 确认不再出现401/403错误

## 注意事项
1. **清除旧数据**：如果之前登录过，建议清除浏览器localStorage中的所有数据后重新登录
2. **Token一致性**：确保所有地方使用相同的localStorage键名（`access_token`和`refresh_token`）
3. **Token结构**：JWT token的payload必须包含`user_id`和`username`字段

## 相关文件
- `app.py` - 后端API，GitHub回调处理
- `my-app/src/components/GitHubCallback.jsx` - 前端GitHub回调处理
- `my-app/src/utils/auth.js` - 认证工具函数
- `jwt_config.py` - JWT配置和处理

## 验证方法
使用浏览器开发者工具检查：
1. **Network标签**：查看API请求是否携带正确的Authorization头
2. **Application标签**：查看localStorage中是否存储了正确的token
3. **Console标签**：查看是否有认证相关的错误信息


