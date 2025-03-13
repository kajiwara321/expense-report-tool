"""
経費レポート自動化ツール - 基本実装

このスクリプトは、OpenAI Agents SDKを使用して、
経費データの処理と基本的なレポート生成を行います。
"""

from agents import Agent, Runner
import asyncio
from typing import Dict, List
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
import re

def print_message(message: str, end="\n"):
    """メッセージを直接標準出力に出力します。"""
    sys.stdout.write(message + end)
    sys.stdout.flush()

def print_separator():
    """区切り線を表示します。"""
    print_message("\n" + "="*50 + "\n")

# .envファイルの読み込みと環境変数の設定
load_dotenv()

# OpenAI APIキーの確認
if not os.getenv("OPENAI_API_KEY"):
    print_message("エラー: OPENAI_API_KEYが設定されていません。")
    print_message("'.env'ファイルにAPIキーを設定してください。")
    sys.exit(1)

# トレース出力の設定
os.environ["OPENAI_TRACE_ENABLED"] = "false"
os.environ["OPENAI_LOG_LEVEL"] = "ERROR"

# 標準エラー出力のリダイレクト設定
if not os.getenv("DEBUG", "false").lower() == "true":
    sys.stderr = open(os.devnull, 'w')

def get_input(prompt: str) -> str:
    """ユーザー入力を取得し、トレース出力を抑制します。"""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    user_input = sys.stdin.readline().strip()
    # 余分な出力を消去
    sys.stdout.write("\033[A\033[K")  # 1行上に移動して行を消去
    sys.stdout.write(prompt + user_input + "\n")
    sys.stdout.flush()
    return user_input

async def safe_json_parse(json_str: str) -> Dict:
    """JSONの安全な解析を行います。"""
    # マークダウンの除去
    cleaned = json_str.strip()
    cleaned = cleaned.replace('```json', '').replace('```', '').strip()
    
    try:
        # 最後の余分なカンマを削除
        cleaned = re.sub(r',(\s*})', r'\1', cleaned)
        
        # プロパティ間の不足しているカンマを追加
        lines = cleaned.split('\n')
        processed_lines = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith('{') and not line.startswith('}'):
                # 行末のカンマを削除
                line = line.rstrip(',')
                # 次の行が}でない場合はカンマを追加
                if i < len(lines) - 1 and not lines[i + 1].strip().startswith('}'):
                    line += ','
            processed_lines.append(line)
        
        cleaned = '\n'.join(processed_lines)
        
        # JSON文字列を整形
        if not cleaned.startswith('{'):
            cleaned = '{' + cleaned.split('{', 1)[1]
        
        if os.getenv("DEBUG", "false").lower() == "true":
            print_message(f"処理されたJSON:\n{cleaned}")
        
        return json.loads(cleaned)
    except (json.JSONDecodeError, IndexError) as e:
        print_message(f"JSON解析エラー: {str(e)}")
        print_message(f"解析を試みた文字列: {cleaned}")
        return {
            "category": "エラー",
            "amount": 0,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "description": "解析エラー",
            "is_valid": False,
            "notes": f"JSONパースエラー: {str(e)}"
        }

class ExpenseReportTool:
    def __init__(self):
        try:
            # 経費分類エージェントの設定
            self.classifier = Agent(
                name="ExpenseClassifier",
                instructions="""
                あなたは経費分類の専門家です。提供された経費情報を適切なカテゴリに分類し、必要な情報を抽出してください。

                返答は必ず以下の形式の有効なJSONのみを返してください：
                {
                    "category": "交通費/宿泊費/飲食費/消耗品費/その他",
                    "amount": 数値（カンマや通貨記号を除去）,
                    "date": "YYYY-MM-DD",
                    "description": "詳細説明",
                    "is_valid": true,
                    "notes": "特記事項があれば記入"
                }

                注意点：
                - 説明文やマークダウンは使用せず、純粋なJSONのみを返すこと
                - JSONの各行の終わりに不要なカンマを付けないこと
                - 数値フィールドには数字以外の文字を含めないこと
                - 日付は必ずYYYY-MM-DD形式で返すこと
                """
            )

            # レポート生成エージェントの設定
            self.reporter = Agent(
                name="ExpenseReporter",
                instructions="""
                あなたは経費レポートの作成者です。
                分類された経費データを基に、以下の形式で経費レポートを作成してください。

                ==============================
                経費レポート (YYYY年MM月DD日)
                ==============================

                【合計金額】
                ¥XXX,XXX

                【カテゴリ別集計】
                - 交通費: ¥XXX,XXX
                - 宿泊費: ¥XXX,XXX
                - 飲食費: ¥XXX,XXX
                - 消耗品費: ¥XXX,XXX
                - その他: ¥XXX,XXX

                【特記事項】
                - 高額支出（¥5,000以上）: XXX
                - その他の注意点: XXX
                """
            )
            print_message("エージェントの初期化が完了しました。")
        except Exception as e:
            print_message(f"エージェントの初期化中にエラーが発生しました: {str(e)}")
            raise

    async def classify_expense(self, expense_text: str) -> Dict:
        """経費情報を分類します。"""
        try:
            print_message(f"経費データを分類中: {expense_text}")
            result = await Runner.run(
                self.classifier,
                input=f"以下の経費を分類してください：\n\n{expense_text}"
            )
            
            # 改善されたJSON解析の実行
            parsed_result = await safe_json_parse(result.final_output)
            if parsed_result.get("is_valid", False):
                print_message("分類が完了しました")
            return parsed_result

        except Exception as e:
            print_message(f"経費分類中にエラーが発生しました: {str(e)}")
            raise

    async def generate_report(self, expenses: List[Dict]) -> str:
        """経費レポートを生成します。"""
        try:
            print_message("レポート生成を開始します")
            expenses_json = json.dumps(expenses, ensure_ascii=False, indent=2)
            result = await Runner.run(
                self.reporter,
                input=f"以下の経費データからレポートを作成してください：\n\n{expenses_json}"
            )
            print_message("レポート生成が完了しました")
            return result.final_output
        except Exception as e:
            print_message(f"レポート生成中にエラーが発生しました: {str(e)}")
            raise

async def main():
    print_separator()
    print_message("=== 経費レポート自動化ツール ===\n")
    print_message("経費データを入力してください（終了するには 'q' を入力）\n")
    print_message("入力形式: 項目名 日付 金額 詳細説明")
    print_message("例: タクシー代 2024年3月13日 ¥1,500 東京駅から会社まで\n")
    print_separator()

    try:
        tool = ExpenseReportTool()
        expenses = []

        while True:
            try:
                expense_input = get_input("経費データを入力してください: ")
                print_separator()
                
                if expense_input.lower() == 'q':
                    break

                result = await tool.classify_expense(expense_input)
                if result["is_valid"]:
                    expenses.append(result)
                print_message(f"=== 分類結果 ===\n{json.dumps(result, ensure_ascii=False, indent=2)}")
                print_separator()

                continue_input = get_input("続けて入力しますか？ (y/n): ")
                if continue_input.lower() != 'y':
                    break

            except Exception as e:
                print_message(f"エラーが発生しました: {str(e)}")
                retry = get_input("再試行しますか？ (y/n): ")
                if retry.lower() != 'y':
                    break
                continue

        if expenses:
            print_separator()
            print_message("=== 経費レポートの生成中 ===\n")
            report = await tool.generate_report(expenses)
            print_separator()
            print_message(report)
            print_separator()
        else:
            print_message("\n経費データが入力されていません。")

    except KeyboardInterrupt:
        print_message("\n\nプログラムを終了します。")
    except Exception as e:
        print_message(f"\n予期せぬエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
