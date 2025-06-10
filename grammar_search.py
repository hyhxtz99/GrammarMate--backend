import chromadb
from chromadb.utils import embedding_functions
import requests
import json
from typing import Dict, List, Tuple

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
        self.collection = self.client.create_collection(
            name="grammar_corrections",
            embedding_function=embedding_functions.DefaultEmbeddingFunction()
        )

    def check_grammar(self, sentence: str) -> Dict:
        """
        Check grammar of a given sentence using Meta-Llama-3-70B-Instruct model
        """
        system_prompt = """You are a professional English grammar checker. Your task is to:
1. Identify all grammar errors in the given sentence
2. Provide the corrected version
3. Explain each correction in detail

You must respond in JSON format only, with the following structure:
{
    "errors": ["error1", "error2", ...],
    "corrected_sentence": "corrected version",
    "explanations": ["explanation1", "explanation2", ...]
}"""

        user_prompt = f"Please check the grammar of this sentence: '{sentence}'"

        payload = {
            "model": "meta-llama/Meta-Llama-3-70B-Instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Ensure we have valid JSON
            try:
                analysis = json.loads(content)
            except json.JSONDecodeError:
                # If the response isn't valid JSON, try to extract JSON from the text
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse response as JSON")
            
            # Validate the response structure
            required_keys = ["errors", "corrected_sentence", "explanations"]
            if not all(key in analysis for key in required_keys):
                raise ValueError("Response missing required fields")
            
            # Store in ChromaDB for future reference
            self.collection.add(
                documents=[sentence],
                metadatas=[{"correction": analysis["corrected_sentence"]}],
                ids=[f"correction_{len(self.collection.get()['ids']) + 1}"]
            )
            
            return analysis
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {str(e)}")
            return {
                "error": f"API request failed: {str(e)}",
                "errors": [],
                "corrected_sentence": sentence,
                "explanations": []
            }
        except Exception as e:
            print(f"Error processing response: {str(e)}")
            return {
                "error": f"Error processing response: {str(e)}",
                "errors": [],
                "corrected_sentence": sentence,
                "explanations": []
            }

    def get_similar_corrections(self, sentence: str, n_results: int = 3) -> List[Dict]:
        """
        Retrieve similar corrections from the database
        """
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

def main():
    # Replace with your actual DeepInfra API key
    api_key = "CIKsKJJeHBT4nsqIWKHOXdDdjJEs4O2E"
    
    checker = GrammarChecker(api_key)
    
    # Example usage
    test_sentence = "He don't know how to swim."
    result = checker.check_grammar(test_sentence)
    
    print("\nOriginal sentence:", test_sentence)
    print("\nGrammar Analysis:")
    if "error" in result:
        print("Error:", result["error"])
    else:
        print("Errors found:", result["errors"])
        print("Corrected sentence:", result["corrected_sentence"])
        print("\nExplanations:")
        for exp in result["explanations"]:
            print(f"- {exp}")
    
    # Get similar corrections
    print("\nSimilar corrections from database:")
    similar = checker.get_similar_corrections(test_sentence)
    if similar:
        for item in similar:
            print(f"Original: {item['original']}")
            print(f"Correction: {item['correction']}\n")
    else:
        print("No similar corrections found in database.")

if __name__ == "__main__":
    main()
