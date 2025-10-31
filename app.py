from fastapi import FastAPI, WebSocket, UploadFile, File, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

import sqlite3

import azure.cognitiveservices.speech as speechsdk
from datetime import datetime
from grammar_search import GrammarChecker
import threading
import asyncio
import os
import azure.cognitiveservices.speech as speechsdk
from pydantic import BaseModel
import requests
import json
from dotenv import load_dotenv
import qrcode
import io
import base64
import uuid
import time
from datetime import datetime, timedelta

# JWT认证相关导入
from jwt_config import jwt_handler
import jwt

# 加载环境变量
load_dotenv()

# GitHub OAuth配置
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "Ov23lipc6lITYFJuQ8ZF")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "3b01aa7f1a47fd1a3b496bcf194a0321186f1ef9")
GITHUB_REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", "http://localhost:3000/auth/callback")

app = FastAPI()

# CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# JWT安全配置
security = HTTPBearer()

# 认证依赖函数
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    try:
        token = credentials.credentials
        payload = jwt_handler.verify_token(token, "access")
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 检查用户是否仍然活跃
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, is_active FROM users WHERE id = ?", (payload["user_id"],))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not user[2]:  # is_active
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {
            "user_id": user[0],
            "username": user[1],
            "is_active": user[2]
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# 可选认证依赖函数（用于某些端点）
async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    """可选获取当前用户"""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

# 配置 Azure Speech 服务
deepinfra_key = os.getenv("DEEPINFRA_API_KEY")
speech_key = os.getenv("AZURE_SPEECH_KEY")
service_region = os.getenv("AZURE_SPEECH_REGION")
translator_key = os.getenv("AZURE_TRANSLATOR_KEY")
translator_endpoint = os.getenv("AZURE_TRANSLATOR_ENDPOINT")
translator_region = os.getenv("AZURE_TRANSLATOR_REGION")
# 全局变量 - 注意：在App Engine中，全局变量在实例重启时会重置
grammar_checker = None
recording_event =threading.Event()
recording_thread = None
result_text = ""

def get_grammar_checker():
    global grammar_checker
    if grammar_checker is None:
        grammar_checker = GrammarChecker(deepinfra_key)
    return grammar_checker

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str = ""

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class TranslationRequest(BaseModel):
    text: str
    to_lang: str

class GrammarQARequest(BaseModel):
    question: str

class UserProfileRequest(BaseModel):
    username: str
    email: str

class ChangePasswordRequest(BaseModel):
    new_password: str
    confirm_password: str

class PersonalizedExerciseRequest(BaseModel):
    count: int
    errorStats: dict

class GitHubLoginRequest(BaseModel):
    session_id: str

class GitHubCallbackRequest(BaseModel):
    code: str
    state: str

def recording_worker():
    global result_text
    result_text = ""
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "en-US"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    def recognized_callback(evt):
        global result_text
        print(f"[DEBUG] recognized_callback: evt.result.text = {evt.result.text}")
        result_text += evt.result.text + " "
        print(f"[DEBUG] result_text (in callback) = {result_text}")

    speech_recognizer.recognized.connect(recognized_callback)
    speech_recognizer.start_continuous_recognition()

    while not recording_event.is_set():
        import time
        time.sleep(0.1)

    speech_recognizer.stop_continuous_recognition()
    print(f"[DEBUG] recording_worker finished, result_text = {result_text}")

@app.get("/")
async def index():
    return {
        "status": "running",
        "endpoints": {
            "/api/login": "POST - 用户登录 (向后兼容)",
            "/api/register": "POST - 用户注册 (向后兼容)",
            "/api/auth/login": "POST - JWT用户登录",
            "/api/auth/register": "POST - JWT用户注册",
            "/api/auth/refresh": "POST - 刷新令牌",
            "/api/auth/logout": "POST - 用户登出",
            "/api/auth/me": "GET - 获取当前用户信息",
            "/api/speech/start": "POST - 开始录音",
            "/api/speech/stop": "POST - 停止录音",
            "/api/speech/status": "GET - 获取录音状态",
            "/api/text": "POST - 处理文本输入",
            "/api/grammar/qa": "POST - 语法问答",
            "/api/grammar/history/{user_id}": "GET - 获取语法历史",
            "/api/user/profile/{user_id}": "GET - 获取用户资料",
            "/api/user/profile/{user_id}": "PUT - 更新用户资料",
            "/api/user/password/{user_id}": "PUT - 修改密码",
            "/api/grammar/personalized/{user_id}": "POST - 个性化练习",
        }
    }
# 向后兼容的登录接口
@app.post("/api/login")
async def legacy_login(data: LoginRequest):
    """向后兼容的登录接口"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # 查询用户
    cursor.execute("SELECT id, username, password, is_active FROM users WHERE username=?", (data.username,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    user_id, username, hashed_password, is_active = user
    
    # 检查用户是否活跃
    if not is_active:
        conn.close()
        raise HTTPException(status_code=401, detail="User account is disabled")
    
    # 验证密码
    if not jwt_handler.verify_password(data.password, hashed_password):
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    conn.close()
    
    return {"success": True, "user_id": user_id, "username": username}

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(data: LoginRequest):
    """用户登录"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # 查询用户
    cursor.execute("SELECT id, username, password, is_active FROM users WHERE username=?", (data.username,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    user_id, username, hashed_password, is_active = user
    
    # 检查用户是否活跃
    if not is_active:
        conn.close()
        raise HTTPException(status_code=401, detail="User account is disabled")
    
    # 验证密码
    if not jwt_handler.verify_password(data.password, hashed_password):
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    # 创建访问令牌和刷新令牌
    access_token = jwt_handler.create_access_token(data={"user_id": user_id, "username": username})
    refresh_token = jwt_handler.create_refresh_token(data={"user_id": user_id, "username": username})
    
    # 保存会话到数据库
    cursor.execute("""
        INSERT INTO user_sessions (user_id, session_token, refresh_token, expires_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, access_token, refresh_token, datetime.utcnow() + timedelta(days=7)))
    
    conn.commit()
    conn.close()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800  # 30分钟
    )

# 向后兼容的注册接口
@app.post("/api/register")
async def legacy_register(data: RegisterRequest):
    """向后兼容的注册接口"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # 检查用户名是否已存在
    cursor.execute("SELECT * FROM users WHERE username=?", (data.username,))
    if cursor.fetchone():
        conn.close()
        return JSONResponse(status_code=400, content={"success": False, "message": "Username already exists"})
    
    # 检查邮箱是否已存在
    if data.email:
        cursor.execute("SELECT * FROM users WHERE email=?", (data.email,))
        if cursor.fetchone():
            conn.close()
            return JSONResponse(status_code=400, content={"success": False, "message": "Email already exists"})
    
    # 加密密码
    hashed_password = jwt_handler.get_password_hash(data.password)
    
    # 插入新用户
    cursor.execute("""
        INSERT INTO users (username, password, email, is_active)
        VALUES (?, ?, ?, ?)
    """, (data.username, hashed_password, data.email, True))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Registration successful"}

@app.post("/api/auth/register")
async def register(data: RegisterRequest):
    """用户注册"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # 检查用户名是否已存在
    cursor.execute("SELECT * FROM users WHERE username=?", (data.username,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # 检查邮箱是否已存在
    if data.email:
        cursor.execute("SELECT * FROM users WHERE email=?", (data.email,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # 加密密码
    hashed_password = jwt_handler.get_password_hash(data.password)
    
    # 插入新用户
    cursor.execute("""
        INSERT INTO users (username, password, email, is_active)
        VALUES (?, ?, ?, ?)
    """, (data.username, hashed_password, data.email, True))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Registration successful"}

@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """刷新访问令牌"""
    # 验证刷新令牌
    payload = jwt_handler.verify_token(data.refresh_token, "refresh")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # 检查用户是否存在且活跃
    cursor.execute("SELECT id, username, is_active FROM users WHERE id=?", (payload["user_id"],))
    user = cursor.fetchone()
    
    if not user or not user[2]:  # is_active
        conn.close()
        raise HTTPException(status_code=401, detail="User account is disabled")
    
    # 创建新的访问令牌
    access_token = jwt_handler.create_access_token(data={"user_id": user[0], "username": user[1]})
    
    # 更新会话
    cursor.execute("""
        UPDATE user_sessions 
        SET session_token = ?
        WHERE user_id = ? AND refresh_token = ?
    """, (access_token, user[0], data.refresh_token))
    
    conn.commit()
    conn.close()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=data.refresh_token,
        expires_in=1800  # 30分钟
    )

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """用户登出"""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # 删除用户会话
    cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (current_user["user_id"],))
    
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Logout successful"}

@app.get("/api/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "is_active": current_user["is_active"]
    }

@app.post("/api/speech/start")
async def start_recording(current_user: dict = Depends(get_current_user)):
    global recording_thread, recording_event
    if recording_thread and recording_thread.is_alive():
        return JSONResponse(status_code=400, content={"error": "Recording already in progress"})

    recording_event.clear()
    recording_thread = threading.Thread(target=recording_worker)
    recording_thread.start()
    return {"status": "Recording started"}


@app.post("/api/speech/stop")
async def stop_recording(request: Request, current_user: dict = Depends(get_current_user)):
    global recording_thread, recording_event, result_text
    print(f"[DEBUG] stop_recording called, result_text = {result_text}")
    if not recording_thread or not recording_thread.is_alive():
        return JSONResponse(status_code=400, content={"error": "No recording in progress"})

    recording_event.set()
    recording_thread.join()

    print(f"[DEBUG] after join, result_text = {result_text}")
    
    # 使用认证用户的ID
    user_id = current_user["user_id"]
    
    result = get_grammar_checker().check_grammar(result_text, user_id=user_id)
    
    print(f"[DEBUG] grammar_checker.check_grammar result = {result}")
    return {
        "text": result_text,
        "corrected_sentence":result['corrected_sentence'],
        "grammar_errors":result['errors'],
        "explanations": result['explanations']
    }

@app.get("/api/speech/status")
async def get_recording_status():
    is_recording = recording_thread is not None and recording_thread.is_alive()
    return {"is_recording": is_recording}




@app.post("/api/text")
async def process_text(request: Request, current_user: dict = Depends(get_current_user)):
    try:
        data = await request.json()
        text = data.get('text')

        if not text:
            return JSONResponse(status_code=400, content={"error": "No text provided"})

        # 使用认证用户的ID
        user_id = current_user["user_id"]
        result = get_grammar_checker().check_grammar(text, user_id=user_id)

        return {
            "text": text,
            "explanations": result['explanations'],
            "corrected_sentence": result['corrected_sentence'],
            "grammar_errors": result['errors']
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/translate")
async def translate_text(request: TranslationRequest):
    try:
        # 构建正确的翻译API URL
        constructed_url = f"{translator_endpoint}/translate?api-version=3.0&to={request.to_lang}"
        headers = {
            'Ocp-Apim-Subscription-Key': translator_key,
            'Ocp-Apim-Subscription-Region': translator_region,
            'Content-Type': 'application/json'
        }
        body = [{
            'text': request.text
        }]
        response = requests.post(constructed_url, headers=headers, json=body) 
        # 检查响应状态
        if response.status_code != 200:
            return JSONResponse(
                status_code=500, 
                content={"error": f"Translation API error: {response.status_code} - {response.text}"}
            )
        result = response.json()
        if not result or len(result) == 0:
            return JSONResponse(
                status_code=500, 
                content={"error": "No translation result received"}
            )
        translation = result[0]['translations'][0]['text']
        return {
            "original_text": request.text,
            "translated_text": translation
        }
    except Exception as e:
        import traceback
        traceback.print_exc()  # 打印完整的错误堆栈
        return JSONResponse(status_code=500, content={"error": f"Translation failed: {str(e)}"})

@app.post("/api/grammar/qa")
async def grammar_qa(request: GrammarQARequest, current_user: dict = Depends(get_current_user)):
    try:
        result = get_grammar_checker().get_grammar_qa(request.question)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"answer": f"Error: {str(e)}"})

@app.get("/api/grammar/qa/stream")
async def grammar_qa_stream(q: str, token: Optional[str] = None, current_user: dict = Depends(get_current_user_optional)):
    """
    Server-Sent Events endpoint to stream the QA answer progressively.
    EventSource requires GET, so the question is passed as query param `q`.
    Token can be passed as query parameter for SSE authentication.
    """
    # If token is provided via URL parameter, verify it
    if token and not current_user:
        try:
            payload = jwt_handler.verify_token(token, "access")
            if payload:
                # Create a mock current_user for authenticated requests
                current_user = {
                    "user_id": payload["user_id"],
                    "username": payload["username"],
                    "is_active": True
                }
        except:
            # If token verification fails, continue without authentication
            pass
    try:
        # Get the full answer first (non-streaming backend), then stream it in chunks
        result = get_grammar_checker().get_grammar_qa(q)
        # Expecting dict like {"answer": "..."}; fallback to str(result)
        if isinstance(result, dict):
            full_answer = result.get("answer") or result.get("data") or ""
        else:
            full_answer = str(result)
        if not isinstance(full_answer, str):
            full_answer = str(full_answer)

        async def event_generator():
            # Send an initial event to signal start
            yield f"event: start\ndata: {''}\n\n"
            # Stream by small chunks (words) to feel responsive
            buffer = []
            for token in full_answer.split(" "):
                buffer.append(token)
                # flush every 1-2 words for smoother effect
                if len(buffer) >= 2:
                    chunk = " ".join(buffer)
                    yield f"data: {chunk}\n\n"
                    buffer = []
            if buffer:
                yield f"data: {' '.join(buffer)}\n\n"
            # Signal completion
            yield f"event: end\ndata: {''}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        # Stream an error event if something goes wrong
        async def error_stream():
            yield f"event: error\ndata: {str(e)}\n\n"
        return StreamingResponse(error_stream(), media_type="text/event-stream")

@app.get("/api/grammar/history/{user_id}")
async def get_grammar_history(user_id: int, current_user: dict = Depends(get_current_user)):
    # 检查用户权限
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT question, correction, error_types, created_at 
            FROM grammar_logs 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 50
        """, (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        history = []
        for row in results:
            question, correction, error_types_json, created_at = row
            try:
                error_types = json.loads(error_types_json)
            except:
                error_types = []
            history.append({
                "question": question,
                "correction": correction,
                "error_types": error_types,
                "created_at": created_at
            })
        
        return {"history": history}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/user/profile/{user_id}")
async def get_user_profile(user_id: int, current_user: dict = Depends(get_current_user)):
    # 检查用户权限
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT username, email 
            FROM users 
            WHERE id = ?
        """, (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        if user:
            return {
                "username": user[0],
                "email": user[1] or ""
            }
        else:
            return JSONResponse(status_code=404, content={"error": "User not found"})
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.put("/api/user/profile/{user_id}")
async def update_user_profile(user_id: int, request: UserProfileRequest, current_user: dict = Depends(get_current_user)):
    # 检查用户权限
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        # 获取当前用户信息
        cursor.execute("""
            SELECT username FROM users WHERE id = ?
        """, (user_id,))
        
        current_user_data = cursor.fetchone()
        if not current_user_data:
            conn.close()
            return JSONResponse(status_code=404, content={"error": "User not found"})
        
        current_username = current_user_data[0]
        
        # 只有当用户名发生变化时才检查冲突
        if request.username != current_username:
            cursor.execute("""
                SELECT id FROM users 
                WHERE username = ? AND id != ?
            """, (request.username, user_id))
            
            if cursor.fetchone():
                conn.close()
                return JSONResponse(status_code=400, content={"error": "Username already exists"})
        
        # 更新用户信息
        cursor.execute("""
            UPDATE users 
            SET username = ?, email = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (request.username, request.email, user_id))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Profile updated successfully"}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.put("/api/user/password/{user_id}")
async def change_password(user_id: int, request: ChangePasswordRequest, current_user: dict = Depends(get_current_user)):
    # 检查用户权限
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # 获取当前用户密码
        cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            raise HTTPException(status_code=404, detail="User not found")
        
        # 验证当前密码
        if not jwt_handler.verify_password(request.current_password, user[0]):
            conn.close()
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # 加密新密码
        hashed_new_password = jwt_handler.get_password_hash(request.new_password)
        
        # 更新密码
        cursor.execute("""
            UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (hashed_new_password, user_id))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



@app.post("/api/grammar/personalized/{user_id}")
async def get_personalized_exercises(user_id: int, request: PersonalizedExerciseRequest, current_user: dict = Depends(get_current_user)):
    # 检查用户权限
    if current_user["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    import random, time
    try:
        # 根据用户的错误统计，从ChromaDB中获取相关的练习题
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # 获取用户的语法检查历史
        cursor.execute("""
            SELECT error_types FROM grammar_logs 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 50
        """, (user_id,))
        
        history = cursor.fetchall()
        conn.close()
        
        # 分析用户的错误模式
        error_patterns = []
        for record in history:
            try:
                error_types = json.loads(record[0])
                if isinstance(error_types, list):
                    # 过滤掉 "none" 错误类型
                    valid_errors = [error for error in error_types if error != "none"]
                    error_patterns.extend(valid_errors)
            except:
                continue
        
        # 随机种子：用时间戳+用户id，确保每次都不同
        random.seed(time.time() + user_id)
        
        # 根据错误模式生成个性化练习题
        exercises = []
        used_questions = set()
        
        # 从ChromaDB获取相关的练习题
        try:
            # 获取用户的错误类型作为查询关键词
            if error_patterns:
                # 使用最常见的错误类型作为查询
                from collections import Counter
                error_counter = Counter(error_patterns)
                most_common_errors = [error for error, count in error_counter.most_common(3)]
                
                # 计算每种错误类型需要多少练习题
                exercises_per_error = max(1, request.count // len(most_common_errors))
                
                # 从ChromaDB查询相关练习
                for error_type in most_common_errors:
                    similar_exercises = get_grammar_checker().get_similar_corrections(error_type, 10)  # 一次多取一些
                    random.shuffle(similar_exercises)
                    for exercise in similar_exercises:
                        if len(exercises) >= exercises_per_error * len(most_common_errors):
                            break
                        if exercise["original"] not in used_questions:
                            exercises.append({
                                "question": exercise["original"],
                                "answer": exercise["correction"],
                                "error_type": error_type,
                                "explanation": exercise.get("explanation", ""),
                            })
                            used_questions.add(exercise["original"])
            
            # 如果还不够，添加一些通用练习
            remaining_count = request.count - len(exercises)
            if remaining_count > 0:
                # 尝试多种通用查询关键词
                general_keywords = ["grammar practice", "english grammar", "sentence correction", "grammar exercise"]
                for keyword in general_keywords:
                    if remaining_count <= 0:
                        break
                    general_exercises = get_grammar_checker().get_similar_corrections(keyword, 10)
                    random.shuffle(general_exercises)
                    for exercise in general_exercises:
                        if remaining_count <= 0:
                            break
                        if exercise["original"] not in used_questions:
                            exercises.append({
                                "question": exercise["original"],
                                "answer": exercise["correction"],
                                "error_type": "general",
                                "explanation": exercise.get("explanation", ""),
                            })
                            used_questions.add(exercise["original"])
                            remaining_count -= 1
            
            # 如果ChromaDB中没有足够的练习，使用默认练习
            if len(exercises) < request.count:
                default_exercises = [
                    {
                        "question": "I goes to school every day.",
                        "answer": "I go to school every day.",
                        "error_type": "subject-verb agreement",
                        "explanation": "The subject 'I' is first person singular, so the verb should be 'go' without the 's'. The 's' form is only for third person singular subjects like 'he', 'she', or 'it'."
                    },
                    {
                        "question": "She have been studying for hours.",
                        "answer": "She has been studying for hours.",
                        "error_type": "subject-verb agreement",
                        "explanation": "The subject 'she' is third person singular, so the correct auxiliary verb is 'has', not 'have'. 'Have' is used for I/you/we/they."
                    },
                    {
                        "question": "I am going to the store yesterday.",
                        "answer": "I went to the store yesterday.",
                        "error_type": "tense",
                        "explanation": "The time expression 'yesterday' requires the verb to be in the past tense. 'Am going' is present continuous and is incompatible with 'yesterday', so it should be 'went'."
                    },
                    {
                        "question": "I saw a elephant at the zoo.",
                        "answer": "I saw an elephant at the zoo.",
                        "error_type": "article usage",
                        "explanation": "The article 'an' is used before words that start with a vowel sound. Since 'elephant' begins with a vowel sound, it should be 'an elephant', not 'a elephant'."
                    },
                    {
                        "question": "The book is on the table.",
                        "answer": "The book is on the table.",
                        "error_type": "preposition",
                        "explanation": "This sentence is actually correct. The preposition 'on' is properly used to describe something resting on a surface. No correction is needed."
                    },
                    {
                        "question": "They is going to the party.",
                        "answer": "They are going to the party.",
                        "error_type": "subject-verb agreement",
                        "explanation": "The subject 'they' is plural, so the verb should be 'are', not 'is'. 'Is' is used for singular subjects."
                    },
                    {
                        "question": "I have been working here since 2 years.",
                        "answer": "I have been working here for 2 years.",
                        "error_type": "preposition",
                        "explanation": "Use 'for' with periods of time (2 years) and 'since' with specific points in time (since 2020)."
                    },
                    {
                        "question": "The children plays in the park.",
                        "answer": "The children play in the park.",
                        "error_type": "subject-verb agreement",
                        "explanation": "The subject 'children' is plural, so the verb should be 'play', not 'plays'. 'Plays' is used for singular subjects."
                    },
                    {
                        "question": "I want to buy a apple.",
                        "answer": "I want to buy an apple.",
                        "error_type": "article usage",
                        "explanation": "Use 'an' before words that begin with a vowel sound. 'Apple' starts with a vowel sound, so it should be 'an apple'."
                    },
                    {
                        "question": "She don't like coffee.",
                        "answer": "She doesn't like coffee.",
                        "error_type": "subject-verb agreement",
                        "explanation": "The subject 'she' is third person singular, so the correct form is 'doesn't', not 'don't'. 'Don't' is used for I/you/we/they."
                    }
                ]
                random.shuffle(default_exercises)
                # 添加默认练习直到达到请求的数量
                for exercise in default_exercises:
                    if len(exercises) >= request.count:
                        break
                    if exercise["question"] not in used_questions:
                        exercises.append(exercise)
                        used_questions.add(exercise["question"])
            
            # 限制返回数量
            exercises = exercises[:request.count]
            
            return {
                "success": True,
                "exercises": exercises,
                "total": len(exercises),
                "user_error_patterns": [error for error, count in Counter(error_patterns).most_common(5)]  # 返回前5个错误模式
            }
            
        except Exception as e:
            # 如果ChromaDB查询失败，返回默认练习
            default_exercises = [
                {
                    "question": "I goes to school every day.",
                    "answer": "I go to school every day.",
                    "error_type": "subject-verb agreement",
                    "explanation": "The subject 'I' is first person singular, so the verb should be 'go' without the 's'. The 's' form is only for third person singular subjects like 'he', 'she', or 'it'."
                },
                {
                    "question": "She have been studying for hours.",
                    "answer": "She has been studying for hours.",
                    "error_type": "subject-verb agreement",
                    "explanation": "The subject 'she' is third person singular, so the correct auxiliary verb is 'has', not 'have'. 'Have' is used for I/you/we/they."
                },
                {
                    "question": "I am going to the store yesterday.",
                    "answer": "I went to the store yesterday.",
                    "error_type": "tense",
                    "explanation": "The time expression 'yesterday' requires the verb to be in the past tense. 'Am going' is present continuous and is incompatible with 'yesterday', so it should be 'went'."
                },
                {
                    "question": "I saw a elephant at the zoo.",
                    "answer": "I saw an elephant at the zoo.",
                    "error_type": "article usage",
                    "explanation": "The article 'an' is used before words that start with a vowel sound. Since 'elephant' begins with a vowel sound, it should be 'an elephant', not 'a elephant'."
                },
                {
                    "question": "The book is on the table.",
                    "answer": "The book is on the table.",
                    "error_type": "preposition",
                    "explanation": "This sentence is actually correct. The preposition 'on' is properly used to describe something resting on a surface. No correction is needed."
                }
            ]
            random.shuffle(default_exercises)
            exercises = []
            used_questions = set()
            for exercise in default_exercises:
                if len(exercises) >= request.count:
                    break
                if exercise["question"] not in used_questions:
                    exercises.append(exercise)
                    used_questions.add(exercise["question"])
            return {
                "success": True,
                "exercises": exercises,
                "total": min(request.count, len(exercises)),
                "user_error_patterns": [error for error, count in Counter(error_patterns).most_common(5)]
            }
            
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error generating personalized exercises: {str(e)}"})

# GitHub OAuth相关API
@app.get("/api/github/login")
async def github_login():
    """获取GitHub登录URL"""
    try:
        # 生成唯一的session_id
        session_id = str(uuid.uuid4())
        
        # 构建GitHub OAuth URL
        auth_url = f"https://github.com/login/oauth/authorize?" \
                   f"client_id={GITHUB_CLIENT_ID}&" \
                   f"redirect_uri={GITHUB_REDIRECT_URI}&" \
                   f"scope=user:email&" \
                   f"state={session_id}"
        
        # 连接数据库
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # 存储会话到数据库 - 延长过期时间到30分钟
        from datetime import timezone
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
        cursor.execute("""
            INSERT INTO github_login_sessions (session_id, auth_url, status, expires_at)
            VALUES (?, ?, 'pending', ?)
        """, (session_id, auth_url, expires_at.isoformat()))
        
        conn.commit()
        conn.close()
        
        return {
            "auth_url": auth_url,
            "session_id": session_id,
            "expires_in": 1800  # 30分钟 = 1800秒
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error generating GitHub login URL: {str(e)}"})

@app.post("/api/github/status")
async def github_status(request: GitHubLoginRequest):
    """检查GitHub登录状态"""
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # 查询会话状态
        cursor.execute("""
            SELECT status, user_id, github_id, github_username
            FROM github_login_sessions 
            WHERE session_id=?
        """, (request.session_id,))
        
        session = cursor.fetchone()
        conn.close()
        
        if not session:
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        
        if session[0] == 'success':
            return {
                "status": "success",
                "user_id": session[1],
                "username": session[3],
                "github_id": session[2]
            }
        elif session[0] == 'expired':
            return {"status": "expired"}
        else:
            return {"status": "pending"}
            
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error checking GitHub status: {str(e)}"})

@app.get("/api/github/callback")
async def github_callback(code: str, state: str):
    """处理GitHub OAuth回调"""
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # 验证session_id
        cursor.execute("SELECT * FROM github_login_sessions WHERE session_id=?", (state,))
        session = cursor.fetchone()
        
        if not session:
            conn.close()
            return JSONResponse(status_code=404, content={"error": "Session not found"})
        
        # 修复时间比较逻辑
        if session[6]:
            try:
                # 处理不同的时间格式
                expires_str = session[6]
                if expires_str.endswith('Z'):
                    expires_str = expires_str[:-1] + '+00:00'
                elif '+' not in expires_str and 'T' in expires_str:
                    expires_str += '+00:00'
                
                expires_at = datetime.fromisoformat(expires_str)
                # 使用timezone-aware的UTC时间进行比较
                from datetime import timezone
                current_utc = datetime.now(timezone.utc)
                if expires_at < current_utc:
                    conn.close()
                    return JSONResponse(status_code=410, content={"error": "Session expired"})
            except Exception as e:
                print(f"时间解析错误: {e}")
                # 如果时间解析失败，不认为会话过期
        
        # 用code换取access_token
        token_response = requests.post("https://github.com/login/oauth/access_token", 
                                     data={
                                         "client_id": GITHUB_CLIENT_ID,
                                         "client_secret": GITHUB_CLIENT_SECRET,
                                         "code": code
                                     },
                                     headers={"Accept": "application/json"})
        
        if token_response.status_code != 200:
            conn.close()
            return JSONResponse(status_code=400, content={"error": "Failed to exchange code for token"})
        
        access_token = token_response.json().get('access_token')
        if not access_token:
            conn.close()
            return JSONResponse(status_code=400, content={"error": "No access token received"})
        
        # 获取GitHub用户信息
        user_response = requests.get("https://api.github.com/user", 
                                   headers={"Authorization": f"token {access_token}"})
        
        if user_response.status_code != 200:
            conn.close()
            return JSONResponse(status_code=400, content={"error": "Failed to get GitHub user info"})
        
        github_user = user_response.json()
        github_id = str(github_user['id'])
        github_username = github_user['login']
        github_email = github_user.get('email', '')
        
        # 检查是否已存在GitHub用户绑定
        cursor.execute("SELECT user_id FROM github_users WHERE github_id=?", (github_id,))
        existing_binding = cursor.fetchone()
        
        if existing_binding:
            # 更新现有用户信息
            user_id = existing_binding[0]
            cursor.execute("""
                UPDATE github_users 
                SET github_username=?, github_email=?
                WHERE github_id=?
            """, (github_username, github_email, github_id))
        else:
            # 创建新用户
            cursor.execute("""
                INSERT INTO users (username, password, email, is_active)
                VALUES (?, ?, ?, ?)
            """, (f"github_{github_username}", "", github_email, True))
            
            user_id = cursor.lastrowid
            
            # 创建GitHub用户绑定
            cursor.execute("""
                INSERT INTO github_users (user_id, github_id, github_username, github_email)
                VALUES (?, ?, ?, ?)
            """, (user_id, github_id, github_username, github_email))
        
        # 生成JWT token
        access_token = jwt_handler.create_access_token(data={"user_id": user_id, "username": github_username})
        refresh_token = jwt_handler.create_refresh_token(data={"user_id": user_id, "username": github_username})
        
        # 存储token到数据库
        cursor.execute("""
            INSERT INTO user_sessions (user_id, session_token, refresh_token, expires_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, access_token, refresh_token, datetime.utcnow() + timedelta(days=7)))
        
        # 更新会话状态
        cursor.execute("""
            UPDATE github_login_sessions 
            SET status='success', user_id=?, github_id=?
            WHERE session_id=?
        """, (user_id, github_id, state))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True, 
            "message": "GitHub login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user_id,
            "username": github_username
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Error processing GitHub callback: {str(e)}"})

@app.post("/api/watermark/verify")
async def verify_watermark(request: Request, current_user: dict = Depends(get_current_user)):
    """验证PDF水印完整性"""
    try:
        data = await request.json()
        signature = data.get("signature")
        checksum = data.get("checksum")
        content = data.get("content")
        
        if not all([signature, checksum, content]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # 验证签名格式
        if not signature.startswith("GrammarMate_"):
            return {"valid": False, "reason": "Invalid signature format"}
        
        # 验证用户ID匹配
        user_id_from_signature = signature.split("_")[-1] if "_" in signature else None
        if user_id_from_signature and str(current_user["user_id"]) != user_id_from_signature:
            return {"valid": False, "reason": "User ID mismatch"}
        
        # 验证内容完整性
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()
        expected_checksum = str(abs(hash(content)))  # 简单的校验和计算
        
        if str(checksum) != expected_checksum:
            return {"valid": False, "reason": "Content tampered"}
        
        return {
            "valid": True,
            "user_id": current_user["user_id"],
            "timestamp": data.get("timestamp"),
            "message": "Watermark verification successful"
        }
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/watermark/info")
async def get_watermark_info(current_user: dict = Depends(get_current_user)):
    """获取水印信息"""
    return {
        "user_id": current_user["user_id"],
        "watermark_text": "GrammarMate",
        "protection_level": "Advanced",
        "features": [
            "Multi-layer watermark",
            "Tamper detection",
            "User signature",
            "Invisible watermark"
        ]
    }