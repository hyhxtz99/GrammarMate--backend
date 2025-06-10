import os
import requests
from serpapi import GoogleSearch

# 设置API Key
DEEPINFRA_API_KEY = 'CIKsKJJeHBT4nsqIWKHOXdDdjJEs4O2E'  # 请替换为你的 DeepInfra API Key
SERPAPI_API_KEY = 'cdc4857354353a39bfb262095d4f283666a7ac68f855428fab5931d94e44a7ac'

def generate_with_deepinfra(prompt, temperature=0.3, max_tokens=100):
    url = "https://api.deepinfra.com/v1/openai/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Meta-Llama-3-70B-Instruct",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response.text}"

def extract_keywords(query):
    prompt = f"""
请从以下查询中提取关键词，每个关键词用逗号分隔：
查询：{query}
关键词：
"""
    
    response = generate_with_deepinfra(prompt, temperature=0.3, max_tokens=100)
    if not response.startswith("Error"):
        return response.strip()
    else:
        return response

def search_digestive_diseases(query, num_results=10):
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num": num_results,
        "gl": "us",  # 地区，可改
        "hl": "en"   # 语言
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    snippets = []
    for result in results.get("organic_results", []):
        if 'snippet' in result:
            snippets.append(result['snippet'])
    return snippets

def filter_with_qwen(texts, question):
    # 拼接文本
    combined_text = "\n".join(texts)
    prompt = f"""
请从以下内容中筛选出与"{question}"最相关的段落，去掉不相关的段落。
只返回筛选后的内容，不要添加任何解释或总结。
内容：
{combined_text}
筛选后的内容：
"""
    
    response = generate_with_deepinfra(prompt, temperature=0.3, max_tokens=1000)
    if not response.startswith("Error"):
        return response
    else:
        return response

def summarize_with_qwen(text, question):
    prompt = f"""
请对以下内容进行总结，面向低识字人群，语言尽量简单易懂。
内容：
{text}
总结：
"""
    
    response = generate_with_deepinfra(prompt, temperature=0.3, max_tokens=500)
    if not response.startswith("Error"):
        return response
    else:
        return response

def main():
    query = "digestive system diseases common symptoms treatment"
    num_results = 10  # 设置想要获取的结果数量
    
    print("=== 提取关键词 ===")
    keywords = extract_keywords(query)
    print(f"查询：{query}")
    print(f"提取的关键词：{keywords}")
    
    print(f"\n开始搜索关键词: {query}")
    search_results = search_digestive_diseases(query, num_results)
    print(f"抓取到 {len(search_results)} 条相关内容。")

    print("\n=== 第一步：筛选相关内容 ===")
    filtered_text = filter_with_qwen(search_results, query)
    print("筛选后的内容：")
    print(filtered_text)

    print("\n=== 第二步：总结内容 ===")
    summary = summarize_with_qwen(filtered_text, query)
    print("总结结果：")
    print(summary)

if __name__ == "__main__":
    main() 