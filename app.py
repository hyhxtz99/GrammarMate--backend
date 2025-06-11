from flask import Flask, request, jsonify
from flask_cors import CORS
import speech
import azure.cognitiveservices.speech as speechsdk
import os
from datetime import datetime
from grammar_search import GrammarChecker
import threading

app = Flask(__name__)
CORS(app)

# 配置 Azure Speech 服务
deepinfra_key="CIKsKJJeHBT4nsqIWKHOXdDdjJEs4O2E"
speech_key = "6RPQ7KXIBTodcoU17xo0dsdsLKZaXeQgKbMyBbGpaYpqxPcrcpxZJQQJ99BFAC3pKaRXJ3w3AAAYACOGwgQD"
service_region = "eastasia"

# 全局变量用于控制录音
recording_thread = None
recording_event = threading.Event()
result_text = ""
grammar_checker = None

def get_grammar_checker():
    global grammar_checker
    if grammar_checker is None:
        grammar_checker = GrammarChecker(deepinfra_key)
    return grammar_checker

@app.route('/')
def index():
    return jsonify({
        "status": "running",
        "endpoints": {
            "/api/speech/start": "POST - 开始录音",
            "/api/speech/stop": "POST - 停止录音",
            "/api/speech/status": "GET - 获取录音状态",
            "/api/text": "POST - 处理文本输入"
        }
    })

def recording_worker():
    global result_text
    result_text = ""
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "en-US"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    def recognized_callback(evt):
        global result_text
        result = evt.result
        print(f"📝 识别文本: {result.text}")
        result_text += result.text + " "
    
    speech_recognizer.recognized.connect(recognized_callback)
    speech_recognizer.start_continuous_recognition()
    
    while not recording_event.is_set():
        import time
        time.sleep(0.1)
    
    speech_recognizer.stop_continuous_recognition()

@app.route('/api/speech/start', methods=['POST'])
def start_recording():
    global recording_thread, recording_event
    if recording_thread and recording_thread.is_alive():
        return jsonify({"error": "Recording already in progress"}), 400
    
    recording_event.clear()
    recording_thread = threading.Thread(target=recording_worker)
    recording_thread.start()
    return jsonify({"status": "Recording started"})

@app.route('/api/speech/stop', methods=['POST'])
def stop_recording():
    global recording_thread, recording_event, result_text
    if not recording_thread or not recording_thread.is_alive():
        return jsonify({"error": "No recording in progress"}), 400
    
    recording_event.set()
    recording_thread.join()
    
    # 处理识别到的文本
    checker = get_grammar_checker()
    result = checker.check_grammar(result_text)
    similar = checker.get_similar_corrections(result_text)
    
    return jsonify({
        "text": result_text,
        "grammar_result": result['explanations']
    })

@app.route('/api/speech/status', methods=['GET'])
def get_recording_status():
    is_recording = recording_thread is not None and recording_thread.is_alive()
    return jsonify({"is_recording": is_recording})

def save_text_to_file(text):
    """保存文本到文件"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"input_{timestamp}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    return filename

@app.route('/api/speech', methods=['POST'])
def speech_to_text():
    """处理语音输入"""
    try:
        # 获取音频文件
        audio_file = request.files['audio']
        if not audio_file:
            return jsonify({"error": "No audio file provided"}), 400

        # 保存音频文件
        audio_path = "temp_audio.wav"
        audio_file.save(audio_path)

        text=speech.start_recognition(speech_key, service_region)
        checker = get_grammar_checker()
    
        # 语法检查
        result = checker.check_grammar(text)
        print("\nGrammar check result:")
        print(result)
        # 相似历史纠错
        similar = checker.get_similar_corrections(text)
        print("\nSimilar corrections:")
        print(similar)
        
        if result['error'] == ['none']:
            os.remove(audio_path)
            
            return jsonify({
                "text": result['corrected_sentence'],
                "grammar_result": result['explanations']
            })
        else:
            return jsonify({"error": "Speech recognition failed"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/text', methods=['POST'])
def process_text():
    """处理文本输入"""
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({"error": "No text provided"}), 400

        checker = get_grammar_checker()
        
        result = checker.check_grammar(text)
        similar = checker.get_similar_corrections(text)        
        
        
        return jsonify({
            "text": text,
            "grammar_result": result['explanations']
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)