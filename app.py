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
from pydantic import BaseModel
import requests

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
translator_key = "EUb333NFdTqrvbHNznxpzEsNiAfO1Ll7oaUGoNFYGwJBnaPwZD5AJQQJ99BFAC3pKaRXJ3w3AAAbACOG2mX3"
translator_endpoint = "https://api.cognitive.microsofttranslator.com"
translator_region = "eastasia"  # 如 eastasia
# 全局变量
grammar_checker = GrammarChecker(deepinfra_key)
recording_event = threading.Event()
recording_thread = None
result_text = ""
# pronunciation_recording_event = threading.Event()
# pronunciation_thread = None
# pronunciation_result = {}

class TranslationRequest(BaseModel):
    text: str
    to_lang: str

class GrammarQARequest(BaseModel):
    question: str

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

# def pronunciation_worker():
    # global pronunciation_result
    # pronunciation_result = {}
    # speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    # audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    # # reference_text设为空，启用自由朗读自动识别
    # reference_text = ""
    # pronunciation_config = speechsdk.PronunciationAssessmentConfig(
    #     reference_text=reference_text,
    #     grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
    #     granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme
    # )
    # recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    # pronunciation_scores = []
    # accuracy_scores = []
    # fluency_scores = []
    # completeness_scores = []
    # recognized_texts = []
    # def recognized_callback(evt):
    #     result = evt.result
    #     if result.reason == speechsdk.ResultReason.RecognizedSpeech:
    #         pa_result = speechsdk.PronunciationAssessmentResult(result)
    #         pronunciation_scores.append(pa_result.pronunciation_score)
    #         accuracy_scores.append(pa_result.accuracy_score)
    #         fluency_scores.append(pa_result.fluency_score)
    #         completeness_scores.append(pa_result.completeness_score)
    #         recognized_texts.append(result.text)
    # recognizer.recognized.connect(recognized_callback)
    # pronunciation_config.apply_to(recognizer)
    # recognizer.start_continuous_recognition()
    # while not pronunciation_recording_event.is_set():
    #     import time
    #     time.sleep(0.1)
    # recognizer.stop_continuous_recognition()
    # # 取平均分
    # if pronunciation_scores:
    #     avg_score = sum(pronunciation_scores) / len(pronunciation_scores)
    #     avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
    #     avg_fluency = sum(fluency_scores) / len(fluency_scores)
    #     avg_completeness = sum(completeness_scores) / len(completeness_scores)
    #     spoken_text = " ".join(recognized_texts)
    #     pronunciation_result = {
    #         "score": round(avg_score, 2),
    #         "accuracy": round(avg_accuracy, 2),
    #         "fluency": round(avg_fluency, 2),
    #         "completeness": round(avg_completeness, 2),
    #         "spoken_text": spoken_text,
    #         "feedback": f"You read: '{spoken_text}'.\nScore: {round(avg_score,2)}, Accuracy: {round(avg_accuracy,2)}, Fluency: {round(avg_fluency,2)}, Completeness: {round(avg_completeness,2)}."
    #     }
    # else:
    #     pronunciation_result = {"score": 0, "feedback": "No speech detected.", "spoken_text": ""}

@app.get("/")
async def index():
    return {
        "status": "running",
        "endpoints": {
            "/api/speech/start": "POST - 开始录音",
            "/api/speech/stop": "POST - 停止录音",
            "/api/speech/status": "GET - 获取录音状态",
            "/api/text": "POST - 处理文本输入",
            # "/api/pronunciation/start": "POST - 开始发音录音",
            # "/api/pronunciation/stop": "POST - 停止发音录音"
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
    print(f"[DEBUG] stop_recording called, result_text = {result_text}")
    if not recording_thread or not recording_thread.is_alive():
        return JSONResponse(status_code=400, content={"error": "No recording in progress"})

    recording_event.set()
    recording_thread.join()

    print(f"[DEBUG] after join, result_text = {result_text}")
    result = grammar_checker.check_grammar(result_text)
    similar = grammar_checker.get_similar_corrections(result_text)
    print(f"[DEBUG] grammar_checker.check_grammar result = {result}")
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


@app.post("/api/translate")
def translate_text(request: TranslationRequest):
    path = '/translate?api-version=3.0'
    params = f'&to={request.to_lang}'
    constructed_url = translator_endpoint + path + params

    headers = {
        'Ocp-Apim-Subscription-Key': translator_key,
        'Ocp-Apim-Subscription-Region': translator_region,
        'Content-Type': 'application/json'
    }

    body = [{
        'text': request.text
    }]

    response = requests.post(constructed_url, headers=headers, json=body)
    result = response.json()

    translation = result[0]['translations'][0]['text']

    return {
        "original_text": request.text,
        "translated_text": translation
    }


@app.post("/api/grammar/qa")
async def grammar_qa(request: GrammarQARequest):
    try:
        result = grammar_checker.get_grammar_qa(request.question)
        return result
    except Exception as e:
        return JSONResponse(status_code=500, content={"answer": f"Error: {str(e)}"})

# @app.post("/api/pronunciation/start")
# async def start_pronunciation_recording():
#     global pronunciation_thread, pronunciation_recording_event
#     if pronunciation_thread and pronunciation_thread.is_alive():
#         return JSONResponse(status_code=400, content={"error": "Recording already in progress"})
#     pronunciation_recording_event.clear()
#     pronunciation_thread = threading.Thread(target=pronunciation_worker)
#     pronunciation_thread.start()
#     return {"status": "Pronunciation recording started"}

# @app.post("/api/pronunciation/stop")
# async def stop_pronunciation_recording():
#     global pronunciation_thread, pronunciation_recording_event, pronunciation_result
#     if not pronunciation_thread or not pronunciation_thread.is_alive():
#         return JSONResponse(status_code=400, content={"error": "No recording in progress"})
#     pronunciation_recording_event.set()
#     pronunciation_thread.join()
#     return pronunciation_result