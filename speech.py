import azure.cognitiveservices.speech as speechsdk

# 配置你的 Azure Speech 服务 Key 和 Region
speech_key = "6RPQ7KXIBTodcoU17xo0dsdsLKZaXeQgKbMyBbGpaYpqxPcrcpxZJQQJ99BFAC3pKaRXJ3w3AAAYACOGwgQD"
service_region = "eastasia"

# 创建语音配置对象
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_recognition_language = "en-US"

# 创建麦克风音频流
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# 创建语音识别器
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

# 定义识别完成后的回调函数
def recognized_callback(evt):
    result = evt.result
    print(f"📝 识别文本: {result.text}")

# 绑定事件监听
speech_recognizer.recognized.connect(recognized_callback)

# 启动识别（持续监听）
print("🎙️ 开始语音识别，请说话...")
speech_recognizer.start_continuous_recognition()

# 保持程序运行（Ctrl+C 退出）
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("⛔ 停止识别")
    speech_recognizer.stop_continuous_recognition()
