# 微信扫码登录配置指南

## 功能概述

本项目已集成微信扫码登录功能，用户可以通过扫描二维码快速登录系统。

## 配置步骤

### 1. 微信开放平台配置

1. 访问 [微信开放平台](https://open.weixin.qq.com/)
2. 注册并创建应用
3. 获取 `AppID` 和 `AppSecret`
4. 设置授权回调域名

### 2. 环境变量配置

在项目根目录创建 `.env` 文件，添加以下配置：

```env
# 微信开放平台配置
WECHAT_APP_ID=your_wechat_app_id
WECHAT_APP_SECRET=your_wechat_app_secret
WECHAT_REDIRECT_URI=http://localhost:5000/api/wechat/callback
```

### 3. 数据库初始化

运行数据库初始化脚本：

```bash
python check_users_db.py
```

这将创建以下新表：
- `wechat_login_sessions`: 存储微信登录会话
- `wechat_users`: 存储微信用户绑定信息

### 4. 安装依赖

```bash
pip install -r requirements.txt
```

新增的依赖包：
- `qrcode==7.4.2`: 生成二维码
- `Pillow==10.0.1`: 图像处理

## API 端点

### 获取微信登录二维码
```
GET /api/wechat/qr
```

返回：
```json
{
  "session_id": "uuid",
  "qr_code": "data:image/png;base64,...",
  "expires_in": 300
}
```

### 检查登录状态
```
POST /api/wechat/status
```

请求体：
```json
{
  "session_id": "uuid"
}
```

### 微信登录回调
```
GET /api/wechat/callback?code=xxx&state=xxx
```

## 前端使用

### 微信登录组件

```jsx
import WechatLogin from './components/WechatLogin';

<WechatLogin 
  onLoginSuccess={handleLoginSuccess}
  onClose={handleClose}
/>
```

### 登录页面集成

登录页面已自动集成微信登录选项，用户可以选择：
1. 传统用户名/密码登录
2. 微信扫码登录

## 功能特性

- ✅ 二维码生成和显示
- ✅ 实时登录状态检查
- ✅ 自动过期处理
- ✅ 用户信息绑定
- ✅ 响应式设计
- ✅ 错误处理

## 注意事项

1. **开发环境**: 当前使用模拟的微信登录流程，生产环境需要配置真实的微信开放平台应用
2. **安全性**: 确保妥善保管 `AppSecret`，不要提交到版本控制系统
3. **回调域名**: 确保回调域名与微信开放平台配置一致
4. **HTTPS**: 生产环境建议使用 HTTPS

## 故障排除

### 常见问题

1. **二维码生成失败**
   - 检查依赖包是否正确安装
   - 确认后端服务正常运行

2. **登录状态检查失败**
   - 检查数据库连接
   - 确认会话ID有效

3. **回调处理失败**
   - 检查微信开放平台配置
   - 确认回调域名设置正确

### 调试模式

在开发环境中，可以通过浏览器开发者工具查看：
- 网络请求状态
- 控制台错误信息
- 数据库查询结果
