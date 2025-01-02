import requests
import os
import ast
from dotenv import load_dotenv

load_dotenv()

def _llm_call(api_base, key, model, prompt):
    # Set OpenAI's API key and API base to use SiliconFlow's API server.
    url = api_base + "/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 150,
        "n": 1,
        "response_format": {"type": "text"}
    }
    headers = {
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    res = response.json()

    return res["choices"][0]["message"]["content"]

if __name__ == "__main__":
    api_base = os.getenv("OPENAI_API_BASE")
    key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_API_MODEL", "Qwen/Qwen2.5-7B-Instruct")

    prompt = "Generate a random Chinese word along with its pinyin and English translation in structured JSON format. json only, nothing else. format: {chinese_word: <chinese_word>, pinyin: <pinyin>, english_translation: <english_translation>}"
    result = _llm_call(api_base, key, model, prompt)

    print(result)

    res=ast.literal_eval(result)

    chinese_word = res["chinese_word"]
    pinyin = res["pinyin"]
    english_translation = res["english_translation"]

    print(f"chinese_word: {chinese_word}, pinyin: {pinyin}, english_translation: {english_translation}", chinese_word, pinyin, english_translation)
