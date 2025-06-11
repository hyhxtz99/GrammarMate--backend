# grammar_checker.py

import chromadb
from chromadb.utils import embedding_functions
import requests
import json
from typing import Dict, List
from sentence_transformers import SentenceTransformer

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
        
        # Initialize ChromaDB
        self.client = chromadb.Client()
        embed_fn = MyEmbeddingFunction(model)
        self.collection = self.client.get_or_create_collection(
          name="grammar_corrections",
          embedding_function=embed_fn
)


    def check_grammar(self, sentence: str,n_results:int =3) -> Dict:
    # 1. 调用你现成的 get_similar_corrections 方法检索相似 correction
        similar_corrections = self.get_similar_corrections(sentence, n_results)

    # 2. 构造带 RAG 上下文的提示词
        reference_examples = "\n".join(
            f"Original: {item['original']} -> Correction: {item['correction']}"
            for item in similar_corrections
            ) if similar_corrections else "No similar sentences found."
        print(reference_examples)

        system_prompt = f"""You are an expert English grammar checker.

            You can refer to the following previous corrections:
            {reference_examples} if the original sentence and correction content are completely 
            the same, ONLY return:
                 {{
        "errors": ["none"],
        "corrected_sentence": "corrected version",
        "explanations": ["correct"]
                }}

            if they are different,

                then, please:
            1. Identify all grammar errors in the given sentence.
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
            "model": "meta-llama/Meta-Llama-3-70B-Instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 300,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()

            result = response.json()
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

            # Store in ChromaDB
            self.collection.add(
                documents=[sentence],
                metadatas=[{"correction": analysis["corrected_sentence"]}],
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

            return [
                {
                    "original": doc,
                    "correction": meta["correction"]
                }
                for doc, meta in zip(results["documents"][0], results["metadatas"][0])
            ]
        except Exception as e:
            print(f"Error retrieving similar corrections: {str(e)}")
            return []

    def get_grammar_qa(self, question: str) -> Dict:
        system_prompt = """You are a professional English grammar checker. Your task is to:give detailed
         explanations for the given question.
        """

