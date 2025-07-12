import requests
import json

# Azure Translator API 配置
translator_key = "EUb333NFdTqrvbHNznxpzEsNiAfO1Ll7oaUGoNFYGwJBnaPwZD5AJQQJ99BFAC3pKaRXJ3w3AAAbACOG2mX3"
translator_endpoint = "https://api.cognitive.microsofttranslator.com"
translator_region = "eastasia"

def test_azure_translate():
    # 构建翻译API URL
    constructed_url = f"{translator_endpoint}/translate?api-version=3.0&to=zh-Hans"
    
    headers = {
        'Ocp-Apim-Subscription-Key': translator_key,
        'Ocp-Apim-Subscription-Region': translator_region,
        'Content-Type': 'application/json'
    }
    
    body = [{
        'text': 'Hello, how are you?'
    }]
    
    print(f"Testing Azure Translator API...")
    print(f"URL: {constructed_url}")
    print(f"Headers: {headers}")
    print(f"Body: {body}")
    
    try:
        response = requests.post(constructed_url, headers=headers, json=body)
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Translation Result: {result}")
            if result and len(result) > 0:
                translation = result[0]['translations'][0]['text']
                print(f"Translation: {translation}")
            else:
                print("No translation result")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_azure_translate() 