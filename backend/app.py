from fastapi import FastAPI, WebSocket, UploadFile, File, Request,HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

import sqlite3

import azure.cognitiveservices.speech as speechsdk
from datetime import datetime
from grammar_search import GrammarChecker
import threading
import asyncio
import os
import speech
from pydantic import BaseModel
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

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
            "/api/login":"POST-  登录",
            "/api/register":"POST- 注册用户",
            "/api/speech/start": "POST - 开始录音",
            "/api/speech/stop": "POST - 停止录音",
            "/api/speech/status": "GET - 获取录音状态",
            "/api/text": "POST - 处理文本输入",
        }
    }
@app.post("/api/login")
async def login(data: LoginRequest):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE username=? AND password=?", (data.username, data.password))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"success": True, "user_id": user[0], "username": user[1]}
    else:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

@app.post("/api/register")
async def register(data: RegisterRequest):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # 检查用户名是否已存在
    cursor.execute("SELECT * FROM users WHERE username=?", (data.username,))
    if cursor.fetchone():
        conn.close()
        return JSONResponse(status_code=400, content={"success": False, "message": "Username already exists"})
    # 插入新用户（包含email）
    cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                  (data.username, data.password, data.email))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Registration successful"}

@app.post("/api/speech/start")
async def start_recording():
    global recording_thread, recording_event
    if recording_thread and recording_thread.is_alive():
        return JSONResponse(status_code=400, content={"error": "Recording already in progress"})

    recording_event.clear()
    recording_thread = threading.Thread(target=recording_worker)
    recording_thread.start()
    return {"status": "Recording started"}


@app.post("/api/speech/stop")
async def stop_recording(request: Request):
    global recording_thread, recording_event, result_text
    print(f"[DEBUG] stop_recording called, result_text = {result_text}")
    if not recording_thread or not recording_thread.is_alive():
        return JSONResponse(status_code=400, content={"error": "No recording in progress"})

    recording_event.set()
    recording_thread.join()

    print(f"[DEBUG] after join, result_text = {result_text}")
    
    # 获取用户ID（如果有的话）
    try:
        data = await request.json()
        user_id = data.get('user_id')
    except:
        user_id = None
    
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

@app.post("/api/speech")
async def speech_to_text(audio: UploadFile = File(...), request: Request = None):
    try:
        # 注意：App Engine不支持本地文件操作，需要使用云存储
        # 这里简化为直接返回错误，实际部署时需要修改为使用云存储
        return JSONResponse(status_code=501, content={"error": "File upload not configured for cloud environment"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/text")
async def process_text(request: Request):
    try:
        data = await request.json()
        text = data.get('text')
        user_id = data.get('user_id')

        if not text:
            return JSONResponse(status_code=400, content={"error": "No text provided"})

        result = get_grammar_checker().check_grammar(text, user_id=user_id)
      

        return {
            "text": text,
            "explanations": result['explanations'],
            "corrected_sentence":result['corrected_sentence'],
            "grammar_errors":result['errors'],

           
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
async def grammar_qa(request: GrammarQARequest):
    try:
        result = get_grammar_checker().get_grammar_qa(request.question)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"answer": f"Error: {str(e)}"})

@app.get("/api/grammar/history/{user_id}")
async def get_grammar_history(user_id: int):
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
async def get_user_profile(user_id: int):
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
async def update_user_profile(user_id: int, request: UserProfileRequest):
    try:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        # 获取当前用户信息
        cursor.execute("""
            SELECT username FROM users WHERE id = ?
        """, (user_id,))
        
        current_user = cursor.fetchone()
        if not current_user:
            conn.close()
            return JSONResponse(status_code=404, content={"error": "User not found"})
        
        current_username = current_user[0]
        
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
            SET username = ?, email = ?
            WHERE id = ?
        """, (request.username, request.email, user_id))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Profile updated successfully"}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.put("/api/user/password/{user_id}")
async def change_password(user_id: int, request: ChangePasswordRequest):
    try:
        # 验证新密码和确认密码是否一致
        if request.new_password != request.confirm_password:
            return JSONResponse(status_code=400, content={"error": "New passwords do not match"})
        
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        
        # 更新密码
        cursor.execute("""
            UPDATE users SET password = ? WHERE id = ?
        """, (request.new_password, user_id))
        
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "Password changed successfully"}
        
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



@app.post("/api/grammar/personalized/{user_id}")
async def get_personalized_exercises(user_id: int, request: PersonalizedExerciseRequest):
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