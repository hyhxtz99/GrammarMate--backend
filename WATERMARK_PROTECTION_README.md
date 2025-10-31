# GrammarMate PDF Watermark Protection System

## 概述

GrammarMate 实现了先进的多层PDF水印保护系统，确保导出的PDF文件带有难以删除的GrammarMate水印，并防止用户恶意删除水印。

## 🔒 保护特性

### 1. 多层水印保护
- **可见水印**: 对角线"GrammarMate"文字水印
- **不可见水印**: 嵌入在文档元数据中的隐藏签名
- **隐写术水印**: 在像素最低有效位中嵌入数据
- **篡改检测**: 通过校验和检测内容修改

### 2. 用户特定保护
- 每个PDF包含唯一的用户签名
- 服务器端验证水印完整性
- 时间戳和用户ID绑定

### 3. 防篡改技术
- 内容校验和验证
- 签名完整性检查
- 多层验证机制

## 🛠️ 技术实现

### 前端实现
```javascript
// 生成受保护的PDF
const result = await downloadProtectedPDF(messages, {
  title: 'GrammarMate Q&A Session',
  watermarkText: 'GrammarMate',
  userId: userId,
  filename: 'GrammarMate_QA.pdf'
});
```

### 后端验证
```python
@app.post("/api/watermark/verify")
async def verify_watermark(request: Request, current_user: dict = Depends(get_current_user)):
    # 验证水印签名
    # 检查用户ID匹配
    # 验证内容完整性
```

## 📁 文件结构

```
my-app/src/
├── utils/
│   ├── pdfGenerator.js          # PDF生成和水印保护
│   └── watermarkProtection.js   # 高级水印保护技术
├── components/
│   ├── GrammarQA.jsx            # 问答组件（已更新）
│   └── WatermarkDemo.jsx        # 水印演示组件
└── app.py                       # 后端API（已更新）
```

## 🚀 使用方法

### 1. 基本PDF导出
```javascript
// 在GrammarQA组件中
const handleExport = async () => {
  const result = await downloadProtectedPDF(messages, {
    title: 'GrammarMate Q&A Session',
    userId: userId,
    filename: 'GrammarMate_QA.pdf'
  });
};
```

### 2. 高级水印配置
```javascript
const result = await downloadProtectedPDF(messages, {
  title: 'GrammarMate Q&A Session',
  watermarkText: 'GrammarMate',
  watermarkOptions: {
    opacity: 0.1,        // 水印透明度
    fontSize: 20,        // 字体大小
    angle: -45,          // 旋转角度
    color: '#cccccc',    // 颜色
    spacing: 100         // 间距
  },
  userId: userId,
  filename: 'protected_document.pdf'
});
```

## 🔍 水印验证

### 服务器端验证
```python
# 验证水印完整性
POST /api/watermark/verify
{
  "signature": "GrammarMate_user123_timestamp",
  "checksum": "content_checksum",
  "content": "document_content"
}
```

### 获取保护信息
```python
# 获取当前用户的水印保护信息
GET /api/watermark/info
```

## 🛡️ 防删除技术

### 1. 多层嵌入
- **可见层**: 用户可以看到的水印
- **元数据层**: 嵌入在PDF属性中
- **隐写术层**: 隐藏在像素数据中
- **校验和层**: 内容完整性验证

### 2. 用户绑定
- 每个PDF包含用户特定签名
- 服务器端验证用户身份
- 时间戳绑定防止重放攻击

### 3. 篡改检测
- 内容校验和验证
- 签名完整性检查
- 多层验证机制

## 📊 保护级别

| 级别 | 技术 | 描述 | 删除难度 |
|------|------|------|----------|
| 1 | 可见水印 | 对角线文字水印 | 中等 |
| 2 | 元数据水印 | 嵌入在PDF属性中 | 高 |
| 3 | 隐写术水印 | 隐藏在像素数据中 | 很高 |
| 4 | 校验和验证 | 内容完整性检查 | 极高 |

## 🔧 配置选项

### 水印选项
```javascript
const watermarkOptions = {
  opacity: 0.1,        // 透明度 (0-1)
  fontSize: 20,        // 字体大小
  angle: -45,         // 旋转角度
  color: '#cccccc',   // 颜色
  spacing: 100        // 间距
};
```

### 保护选项
```javascript
const protectionOptions = {
  userId: userId,                    // 用户ID
  signature: true,                  // 启用签名
  tamperDetection: true,            // 启用篡改检测
  steganography: true,              // 启用隐写术
  serverVerification: true          // 启用服务器验证
};
```

## 🚨 安全考虑

### 1. 客户端保护
- 水印嵌入在客户端完成
- 使用加密算法保护签名
- 防止简单的文本替换

### 2. 服务器端验证
- 所有水印验证在服务器端进行
- 用户身份验证
- 内容完整性检查

### 3. 防篡改
- 多层校验和验证
- 签名完整性检查
- 时间戳防重放

## 📈 性能优化

### 1. 客户端优化
- 异步PDF生成
- 内存使用优化
- 进度指示器

### 2. 服务器端优化
- 缓存验证结果
- 批量验证支持
- 异步处理

## 🔄 更新日志

### v1.0.0 (当前版本)
- ✅ 基础PDF生成
- ✅ 多层水印保护
- ✅ 用户特定签名
- ✅ 服务器端验证
- ✅ 篡改检测
- ✅ 隐写术水印

### 计划功能
- 🔄 数字签名支持
- 🔄 区块链验证
- 🔄 高级加密算法
- 🔄 批量PDF处理

## 📞 技术支持

如有问题或建议，请联系开发团队：
- 邮箱: support@grammarmate.com
- 文档: https://docs.grammarmate.com
- 问题反馈: https://github.com/grammarmate/issues

## 📄 许可证

本水印保护系统受版权保护，未经授权不得复制或修改。
