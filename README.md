# 智能语法纠正系统 (Intelligent Grammar Correction System)
一个基于AI的智能语法纠正和语言学习平台，集成了语音识别、语法检查、翻译和个性化练习功能。

网站效果demo可在https://www.bilibili.com/video/BV1j9bfzpEfe/?spm_id_from=333.1387.homepage.video_card.click&vd_source=4301d59ff881ef08cadce8c59747ae54 查看；

前端页面代码可在 https://github.com/hyhxtz99/grammarMate-frontend 查看；

前端页面已部署在https://vercel.com/he-yihans-projects/grammar-mate-frontend

## 🌟 主要功能

### 1. 智能语法纠正 (Grammar Correction)
- **文本输入检查**: 支持手动输入文本进行语法检查
- **语音识别**: 集成Azure语音服务，支持语音输入和实时转写
- **错误分析**: 详细分析语法错误类型和位置
- **纠正建议**: 提供正确的语法建议和解释
- **多语言翻译**: 支持将检查结果翻译成多种语言

### 2. 语法问答系统 (Grammar Q&A)
- **智能问答**: 基于AI的语法问题解答
- **聊天历史**: 保存用户问答记录
- **实时翻译**: 支持问答内容的实时翻译
- **导出功能**: 支持将问答记录导出为文本文件
- **示例问题**: 提供常用语法问题示例

### 3. 个性化练习 (Personalized Practice)
- **错误统计**: 分析用户语法错误类型和频率
- **学习进度**: 跟踪今日、本周和总体的学习数据
- **针对性练习**: 基于用户错误模式生成个性化练习题
- **练习模式**: 支持5题和10题两种练习模式
- **详细解释**: 提供正确答案和详细解释

### 4. 用户管理系统
- **用户注册/登录**: 完整的用户认证系统
- **个人中心**: 用户信息管理和密码修改
- **学习历史**: 查看详细的语法检查历史记录
- **错误详情**: 按错误类型查看历史问题详情

## 🛠️ 技术栈

### 后端 (Backend)
- **FastAPI**: 现代化的Python Web框架
- **SQLite**: 轻量级数据库
- **Azure Cognitive Services**: 
  - Azure Speech Service (语音识别)
  - Azure Translator (多语言翻译)
- **DeepInfra API**: AI语法检查和问答服务
- **ChromaDB**: 向量数据库用于语义搜索
- **Sentence Transformers**: 文本嵌入和语义理解

### 前端 (Frontend)
- **React 18**: 现代化的JavaScript框架
- **React Router**: 单页应用路由管理
- **Bootstrap**: 响应式UI组件库
- **ECharts**: 数据可视化图表库
- **CSS3**: 自定义样式和动画

## 📋 系统要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn
- 麦克风设备 (用于语音功能)

## 🚀 安装和部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd internal-project
```

### 2. 后端设置

#### 安装Python依赖
```bash
pip install -r requirements.txt
```

#### 环境变量配置
创建 `.env` 文件并配置以下环境变量：
```env
# Azure Speech Service
AZURE_SPEECH_KEY=your_azure_speech_key
AZURE_SPEECH_REGION=your_azure_region

# Azure Translator
AZURE_TRANSLATOR_KEY=your_translator_key
AZURE_TRANSLATOR_ENDPOINT=your_translator_endpoint
AZURE_TRANSLATOR_REGION=your_translator_region

# DeepInfra API
DEEPINFRA_API_KEY=your_deepinfra_api_key
```

#### 初始化数据库
```bash
python init_user_db.py
```

#### 启动后端服务
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 5000
```

### 3. 前端设置

#### 进入前端目录
```bash
cd my-app
```

#### 安装依赖
```bash
npm install
```

#### 启动开发服务器
```bash
npm start
```

前端将在 `http://localhost:3000` 启动

## 📖 使用指南

### 1. 用户注册和登录
- 访问应用首页，点击"Register"进行用户注册
- 或使用现有账户登录系统

### 2. 语法纠正功能
- **文本检查**: 在文本框中输入要检查的句子，点击"Check Grammar"
- **语音输入**: 点击"Start recording"开始录音，说话完成后点击"Stop recording"
- **查看结果**: 系统会显示语法错误分析和纠正建议
- **翻译结果**: 点击翻译按钮将结果翻译成指定语言

### 3. 语法问答
- 在问答界面输入语法相关问题
- 系统会提供详细的语法解释
- 可以点击翻译按钮翻译问答内容
- 支持导出问答记录

### 4. 个性化练习
- 查看个人错误统计和学习进度
- 选择练习题目数量（5题或10题）
- 根据提示选择是否知道答案
- 查看正确答案和详细解释

## 🔧 项目结构

```
internal-project/
├── app.py                          # FastAPI主应用
├── requirements.txt                # Python依赖
├── init_user_db.py                # 数据库初始化
├── grammar_search.py              # 语法检查核心逻辑
├── speech.py                      # 语音处理模块
├── my-app/                        # React前端应用
│   ├── src/
│   │   ├── components/            # React组件
│   │   │   ├── GrammarCorrection.jsx
│   │   │   ├── GrammarQA.jsx
│   │   │   ├── PersonaliseCorrection.jsx
│   │   │   ├── LoginPage.jsx
│   │   │   └── ...
│   │   ├── App.js                 # 主应用组件
│   │   └── index.js               # 应用入口
│   ├── package.json               # Node.js依赖
│   └── public/                    # 静态资源
├── chromadb/                      # 向量数据库存储
└── *.png                          # 项目截图和文档
```

## 🌐 API接口

### 主要API端点
- `POST /api/login` - 用户登录
- `POST /api/register` - 用户注册
- `POST /api/text` - 文本语法检查
- `POST /api/speech/start` - 开始语音录制
- `POST /api/speech/stop` - 停止语音录制
- `POST /api/translate` - 文本翻译
- `POST /api/grammar/qa` - 语法问答
- `GET /api/grammar/history/{user_id}` - 获取用户历史记录
- `POST /api/grammar/personalized/{user_id}` - 获取个性化练习

## 🎯 特色功能

1. **多模态输入**: 支持文本和语音两种输入方式
2. **智能错误分析**: 准确识别8种常见语法错误类型
3. **个性化学习**: 基于用户错误模式提供针对性练习
4. **多语言支持**: 支持多种语言的翻译功能
5. **学习追踪**: 详细的学习进度和错误统计
6. **用户友好**: 直观的界面设计和交互体验


## 📊 性能优化

- 向量数据库缓存
- 异步API处理
- 前端组件懒加载
- 响应式设计适配




