curl --request POST \
  --url https://api.siliconflow.cn/v1/chat/completions \
  --header "Authorization: Bearer $OPENAI_API_KEY" \
  --header 'Content-Type: application/json' \
  --data '{
  "model": "Qwen/Qwen2.5-7B-Instruct",
  "messages": [
    {
      "role": "user",
      "content": "Generate a random Chinese word along with its pinyin and English translation in structured JSON format. json only, nothing else. format: {chinese-word: <chinese-word>, pinyin: <pinyin>, english-translation: <english-translation>}"
    }
  ],
  "max_tokens": 150,
  "n": 1,
  "response_format": {
    "type": "text"
  }
}' | jq .choices[0].message.content
