# grammar_checker.py

import chromadb
from chromadb.utils import embedding_functions
import requests
import json
import sqlite3
from typing import Dict, List
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
# from chromadb.config import Settings

# 加载环境变量
load_dotenv()

model = SentenceTransformer('all-MiniLM-L6-v2')

class MyEmbeddingFunction:
    def __init__(self, model):
        self.model = model

    def __call__(self, input):   # 注意这里必须叫 input！
        return self.model.encode(input).tolist()

    def name(self):
        return "sentence-transformers-embedding"

class GrammarChecker:
    def __init__(self, deepinfra_api_key: str):
        self.api_key = deepinfra_api_key
        self.api_url = "https://api.deepinfra.com/v1/openai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 在App Engine中，使用内存存储而不是持久化存储
        # 注意：这会导致数据在实例重启时丢失
        self.client = chromadb.Client()
       
    
        embed_fn = MyEmbeddingFunction(model)
        self.collection = self.client.get_or_create_collection(
          name="grammar_corrections",
          embedding_function=embed_fn
)
       


    def _log_to_database(self, user_id: int, question: str, correction: str, error_types: List[str]):
        """记录语法检查结果到数据库"""
        try:
            conn = sqlite3.connect("users.db")
            cursor = conn.cursor()
            
            # 将错误类型列表转换为JSON字符串
            error_types_json = json.dumps(error_types)
            
            cursor.execute("""
                INSERT INTO grammar_logs (user_id, question, correction, error_types, created_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, question, correction, error_types_json))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error logging to database: {str(e)}")

    def check_grammar(self, sentence: str, n_results: int = 3, user_id: int = None) -> Dict:
    # 1. 调用你现成的 get_similar_corrections 方法检索相似 correction
        error_types = {
            "subject-verb agreement": "The verb should agree with the subject in number and person.",
            "tense": "Incorrect tense used; choose the correct tense based on the time context.",
            "article usage": "Incorrect article usage; use 'a', 'an', or 'the' appropriately before nouns.",
            "preposition": "Incorrect or inappropriate preposition used in the sentence.",
            "plural form": "Incorrect plural form; missing or incorrect use of plural suffix.",
            "word order": "Word order error; the sentence structure does not follow natural English syntax.",
            "pronoun reference": "Unclear or incorrect pronoun reference; the pronoun should clearly refer to a noun.",
            "comparative/superlative": "Incorrect use of comparative or superlative form based on comparison context."
}
        common_rules = {
            "subject_verb_agreement": {
                "description": "The verb must agree with the subject in number and person. 'You are' uses 'are' not because 'you' is plural, but because it is second person.",
                "example": ["I am", "You are", "He/She/It is", "They are"]
            },
            "past_vs_present_perfect": {
                "description": "Use past simple for actions at a definite past time; use present perfect for actions connected to present or indefinite past.",
                "example": ["I went to the store yesterday.", "I have been to France."]
            },
            "articles": {
                "description": "'a' before consonant sounds, 'an' before vowel sounds, 'the' for specific or previously mentioned nouns.",
                "example": ["I saw a dog.", "I saw the dog that you mentioned.", "I ate an apple."]
            },
            "countable_vs_uncountable": {
                "description": "Use many/few with countable nouns; much/little with uncountable nouns. Plural nouns take -s.",
                "example": ["I have many books.", "I have much water."]
            },
            "prepositions_of_time_and_place": {
                "description": "Use different prepositions for time and place: 'at' for specific point, 'on' for day/date, 'in' for month/year/period.",
                "example": ["at 5 pm", "on Monday", "in September", "at the bus stop", "on the table", "in the room"]
            },
            "pronoun_reference": {
                "description": "A pronoun must clearly refer to a specific noun to avoid ambiguity.",
                "example": ["John told Peter, 'I am tired.'", "John told Peter that John was tired."]
            },
            "verb_forms_after_modals": {
                "description": "Modals (can, could, will, should, must) are followed by the base form of the verb.",
                "example": ["She can go now.", "He should study more."]
            },
            "conditional_sentences": {
                "description": "Zero: if + present, present. First: if + present, will + verb. Second: if + past, would + verb.",
                "example": ["If you heat water, it boils.", "If it rains, I will stay home.", "If I were rich, I would travel the world."]
            }
};

        similar_corrections = self.get_similar_corrections(sentence, n_results)
        # print(similar_corrections)
    # 2. 构造带 RAG 上下文的提示词
        reference_examples = "\n".join(
            f"Original: {item['original']} -> Correction: {item['correction']}"
            for item in similar_corrections
            ) if similar_corrections else "No similar sentences found."
        print(reference_examples)

        system_prompt = f"""You are an expert English grammar checker. You can refer to {common_rules} and your answer should not conflict with these common rules.

            You can refer to the following previous corrections:
            {reference_examples}.  if the original sentence and correction content are completely 
            the same, ONLY return:
                 {{
        "errors": ["none"],
        "corrected_sentence": "corrected version",
        
        "explanations": ["correct"]
                }}

            if they are different,

                then, please:
            1. Identify all grammar errors in the given sentence, referring to {error_types}.
            2. Provide the corrected version.
            
            3. Explain each correction.

        Respond ONLY in JSON format like:
            {{
        "errors": ["error1", "error2"],
        "corrected_sentence": "corrected version",
        "explanations": ["explanation1", "explanation2"]
                }}
                """

        user_prompt = f"Please check the grammar of this sentence: '{sentence}'"

        payload = {
            # "model": "meta-llama/Meta-Llama-3-70B-Instruct",
             "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 300,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()

            result = response.json()
            print(result)
            content = result['choices'][0]['message']['content']

            # Ensure valid JSON
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse response as JSON")

            required_keys = ["errors", "corrected_sentence", "explanations"]
            if not all(key in analysis for key in required_keys):
                raise ValueError("Response missing required fields")

            # 记录到数据库
            if user_id is not None:
                self._log_to_database(
                    user_id=user_id,
                    question=sentence,
                    correction=analysis["corrected_sentence"],
                    error_types=analysis["errors"]
                )

            # Store in ChromaDB
            if analysis["explanations"] == ["correct"]:
                return analysis
            else:
                # 将explanations列表合并为一个字符串
                explanation_text = " ".join(analysis["explanations"]) if analysis["explanations"] else ""
                self.collection.add(
                    documents=[sentence],
                    metadatas=[{
                        "correction": analysis["corrected_sentence"],
                        "explanation": explanation_text
                    }],
                    ids=[f"correction_{len(self.collection.get()['ids']) + 1}"]
            )

            return analysis

        except requests.exceptions.RequestException as e:
            return {
                "error": f"API request failed: {str(e)}",
                "errors": [],
                "corrected_sentence": sentence,
                "explanations": []
            }
        except Exception as e:
            return {
                "error": f"Error processing response: {str(e)}",
                "errors": [],
                "corrected_sentence": sentence,
                "explanations": []
            }

    def get_similar_corrections(self, sentence: str, n_results: int = 3) -> List[Dict]:
        try:
            results = self.collection.query(
                query_texts=[sentence],
                n_results=n_results
            )

            corrections = []
            if results["documents"][0] and results["metadatas"][0]:
                for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                    correction = {
                        "original": doc,
                        "correction": meta.get("correction", doc),
                        "explanation": meta.get("explanation", "")
                    }
                    corrections.append(correction)
            
            return corrections
        except Exception as e:
            print(f"Error retrieving similar corrections: {str(e)}")
            return []

    def _clean_response(self, text: str) -> str:
        """清理响应文本，保留段落分隔但移除多余的空白行"""
        if not text:
            return text
        
        # 移除开头和结尾的空白字符
        text = text.strip()
        
        import re
        
        # 将3个或更多连续换行符替换为2个换行符（保留段落分隔）
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # 将单个换行符替换为空格（保持段落内连续）
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        # 将多个连续空格替换为单个空格
        text = re.sub(r' +', ' ', text)
        
        return text.strip()

    def get_grammar_qa(self, question: str) -> dict:
        # 1. 检索相似问题（可用collection.query）
        similar_qas = self.collection.query(query_texts=[question], n_results=3)
        reference_examples = "\n".join(
            f"Q: {doc} -> A: {meta.get('correction', '')}"
            for doc, meta in zip(similar_qas["documents"][0], similar_qas["metadatas"][0])
        ) if similar_qas["documents"][0] else "No similar Q&A found."

        # 2. 构造RAG prompt
        system_prompt = f"""You are a professional English grammar expert. Answer the user's grammar question concisely in 200-300 words maximum. You can use 2-3 paragraphs for better organization, but avoid excessive blank lines between paragraphs. If the answer is already covered in the reference examples, provide a brief summary. Otherwise, give a detailed but concise explanation based on your knowledge. Return only the answer text, no additional formatting or information.

Reference examples:
{reference_examples}"""
        
        user_prompt = f"Question: {question}"
        payload = {
            "model": "meta-llama/Meta-Llama-3-70B-Instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 400
        }
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            answer = result['choices'][0]['message']['content']
            
            # 清理回答中的多余空白行和空格
            answer = self._clean_response(answer)
            
            return {"answer": answer}
        except Exception as e:
            return {"answer": f"Error: {str(e)}"}

