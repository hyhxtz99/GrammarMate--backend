import azure.cognitiveservices.speech as speechsdk

def start_recognition(speech_key, service_region):
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    speech_config.speech_recognition_language = "en-US"
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    result_text=''
    def recognized_callback(evt):
        nonlocal result_text
        result = evt.result
        print(f"📝 识别文本: {result.text}")
        result_text+=result.text
        
    
    speech_recognizer.recognized.connect(recognized_callback)
    print("🎙️ 开始语音识别，请说话...")
    speech_recognizer.start_continuous_recognition()

   

    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("⛔ 停止识别")
        speech_recognizer.stop_continuous_recognition()
    
    return result_text

