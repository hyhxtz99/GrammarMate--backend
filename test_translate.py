import requests
import json

# 测试翻译API
def test_translate():
    url = "http://localhost:5000/api/translate"
    
    data = {
        "text": "Hello, how are you?",
        "to_lang": "zh-Hans"
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Translation: {result.get('translated_text', 'No translation')}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    test_translate() 