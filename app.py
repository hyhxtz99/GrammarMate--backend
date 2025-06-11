from fastapi import FastAPI, WebSocket, UploadFile, File, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import azure.cognitiveservices.speech as speechsdk
from datetime import datetime
from grammar_search import GrammarChecker
import threading
import asyncio
import os
import speech

app = FastAPI()

# CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置 Azure Speech 服务
deepinfra_key = "CIKsKJJeHBT4nsqIWKHOXdDdjJEs4O2E"
speech_key = "6RPQ7KXIBTodcoU17xo0dsdsLKZaXeQgKbMyBbGpaYpqxPcrcpxZJQQJ99BFAC3pKaRXJ3w3AAAYACOGwgQD"
service_region = "eastasia"

# 全局变量
grammar_checker = GrammarChecker(deepinfra_key)
recording_event = threading.Event()
recording_thread = None
result_text = ""


def recording_worker():
    global result_text
    result_text = ""
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "en-US"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    def recognized_callback(evt):
        global result_text
        result_text += evt.result.text + " "

    speech_recognizer.recognized.connect(recognized_callback)
    speech_recognizer.start_continuous_recognition()

    while not recording_event.is_set():
        import time
        time.sleep(0.1)

    speech_recognizer.stop_continuous_recognition()


@app.get("/")
async def index():
    return {
        "status": "running",
        "endpoints": {
            "/api/speech/start": "POST - 开始录音",
            "/api/speech/stop": "POST - 停止录音",
            "/api/speech/status": "GET - 获取录音状态",
            "/api/text": "POST - 处理文本输入"
        }
    }


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
async def stop_recording():
    global recording_thread, recording_event, result_text
    if not recording_thread or not recording_thread.is_alive():
        return JSONResponse(status_code=400, content={"error": "No recording in progress"})

    recording_event.set()
    recording_thread.join()

    result = grammar_checker.check_grammar(result_text)
    similar = grammar_checker.get_similar_corrections(result_text)

    return {
        "text": result_text,
        "grammar_result": result['explanations']
    }


@app.get("/api/speech/status")
async def get_recording_status():
    is_recording = recording_thread is not None and recording_thread.is_alive()
    return {"is_recording": is_recording}


@app.post("/api/speech")
async def speech_to_text(audio: UploadFile = File(...)):
    try:
        audio_path = "temp_audio.wav"
        with open(audio_path, "wb") as f:
            f.write(await audio.read())

        text = speech.start_recognition(speech_key, service_region)
        result = grammar_checker.check_grammar(text)
        similar = grammar_checker.get_similar_corrections(text)

        if result['error'] == ['none']:
            os.remove(audio_path)
            return {
                "text": result['corrected_sentence'],
                "grammar_result": result['explanations']
            }
        else:
            return JSONResponse(status_code=400, content={"error": "Speech recognition failed"})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/text")
async def process_text(request: Request):
    try:
        data = await request.json()
        text = data.get('text')

        if not text:
            return JSONResponse(status_code=400, content={"error": "No text provided"})

        result = grammar_checker.check_grammar(text)
        similar = grammar_checker.get_similar_corrections(text)

        return {
            "text": text,
            "grammar_result": result['explanations']
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
