import os
import openai
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# APIキーの設定
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("エラー: OPENAI_API_KEYが設定されていません。")
    exit(1)

print(f"APIキーの最初の10文字: {api_key[:10]}...")

try:
    # OpenAI clientの初期化
    client = openai.OpenAI(api_key=api_key)
    
    # 簡単なリクエストを送信
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "こんにちは"}]
    )
    
    print("APIテスト成功!")
    print("応答:", response.choices[0].message.content)

except Exception as e:
    print("APIテストエラー:")
    print(str(e))
