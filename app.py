from flask import Flask, request, jsonify
from flask_cors import CORS
import speech
import azure.cognitiveservices.speech as speechsdk
import os
from datetime import datetime
from grammar_search import GrammarChecker

app = Flask(__name__)
CORS(app)

# 配置 Azure Speech 服务
deepinfra_key="CIKsKJJeHBT4nsqIWKHOXdDdjJEs4O2E"
speech_key = "6RPQ7KXIBTodcoU17xo0dsdsLKZaXeQgKbMyBbGpaYpqxPcrcpxZJQQJ99BFAC3pKaRXJ3w3AAAYACOGwgQD"
service_region = "eastasia"

@app.route('/')
def index():
    return jsonify({
        "status": "running",
        "endpoints": {
            "/api/speech": "POST - 处理语音输入",
            "/api/text": "POST - 处理文本输入"
        }
    })

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
        checker = GrammarChecker(deepinfra_key)
    
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

# @app.route('/api/text', methods=['POST'])
# def process_text():
#     """处理文本输入"""
#     try:
#         data = request.get_json()
#         text = data.get('text')
        
#         if not text:
#             return jsonify({"error": "No text provided"}), 400

#         # 保存文本到文件
#         filename = save_text_to_file(text)
        
#         # 调用 grammar_search 进行处理
#         grammar_result = grammar_search.process_text(text)
        
#         return jsonify({
#             "text": text,
#             "grammar_result": grammar_result
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)