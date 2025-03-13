"""
経費レポート自動化ツール - 拡張実装

このスクリプトは、OpenAI Agents SDKを使用して、
経費データの処理と基本的なレポート生成を行います。
OCR機能とスプレッドシート出力機能を追加しています。
"""

from agents import Agent, Runner
import asyncio
from typing import Dict, List, Optional
import json
from datetime import datetime
import os
from dotenv import load_dotenv
import sys
import re
import argparse
from pathlib import Path

# 追加モジュールのインポート
from ocr_module import ReceiptOCR
from spreadsheet_module import ExpenseSpreadsheet

def print_message(message: str, end="\n"):
    """メッセージを直接標準出力に出力します。"""
    sys.stdout.write(message + end)
    sys.stdout.flush()

def print_separator():
    """区切り線を表示します。"""
    print_message("\n" + "="*50 + "\n")

def parse_arguments():
    """コマンドライン引数を解析します。"""
    parser = argparse.ArgumentParser(description="経費レポート自動化ツール")
    
    # 動作モードの指定
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--interactive", action="store_true", help="対話モードで実行（デフォルト）")
    mode_group.add_argument("--ocr", action="store_true", help="OCRモードで実行")
    
    # OCRモード用の引数
    parser.add_argument("--image", type=str, help="OCR処理する画像ファイルのパス")
    parser.add_argument("--image-dir", type=str, help="OCR処理する画像ファイルのディレクトリ")
    parser.add_argument("--lang", type=str, default="jpn+eng", help="OCRで使用する言語（デフォルト: jpn+eng）")
    
    # 出力関連の引数
    parser.add_argument("--output", type=str, help="出力するExcelファイルのパス")
    parser.add_argument("--append", action="store_true", help="既存のExcelファイルに追記する")
    
    # デバッグモード
    parser.add_argument("--debug", action="store_true", help="デバッグモードを有効にする")
    
    args = parser.parse_args()
    
    # デバッグモードの設定
    if args.debug:
        os.environ["DEBUG"] = "true"
    
    # 対話モードがデフォルト
    if not (args.ocr):
        args.interactive = True
    
    # OCRモードで画像が指定されていない場合はエラー
    if args.ocr and not (args.image or args.image_dir):
        parser.error("OCRモードでは --image または --image-dir を指定してください")
    
    return args

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
            
            # OCRモジュールの初期化
            self.ocr = None
            
            # スプレッドシートモジュールの初期化
            self.spreadsheet = None
            
            print_message("エージェントの初期化が完了しました。")
        except Exception as e:
            print_message(f"エージェントの初期化中にエラーが発生しました: {str(e)}")
            raise
    
    def init_ocr(self, lang='jpn+eng'):
        """OCRモジュールを初期化します。"""
        try:
            self.ocr = ReceiptOCR(lang=lang)
            print_message(f"OCRモジュールを初期化しました（言語: {lang}）")
        except Exception as e:
            print_message(f"OCRモジュールの初期化中にエラーが発生しました: {str(e)}")
            raise
    
    def init_spreadsheet(self, output_path=None):
        """スプレッドシートモジュールを初期化します。"""
        try:
            self.spreadsheet = ExpenseSpreadsheet(output_path=output_path)
            print_message(f"スプレッドシートモジュールを初期化しました（出力先: {self.spreadsheet.output_path}）")
        except Exception as e:
            print_message(f"スプレッドシートモジュールの初期化中にエラーが発生しました: {str(e)}")
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
    
    async def classify_ocr_result(self, ocr_data: Dict) -> Dict:
        """OCR結果から抽出した経費データを分類します。"""
        try:
            # OCRデータから経費情報を構築
            expense_text = (
                f"{ocr_data['description']} "
                f"{ocr_data['date']} "
                f"¥{ocr_data['amount']} "
                f"詳細: {ocr_data.get('raw_text', '')[:100]}..."  # 最初の100文字だけ使用
            )
            
            # 経費分類を実行
            result = await self.classify_expense(expense_text)
            
            # OCRデータの情報で補完
            if not result.get("is_valid", False):
                # 分類に失敗した場合はOCRデータをそのまま使用
                result = {
                    "category": "その他",
                    "amount": ocr_data["amount"],
                    "date": ocr_data["date"],
                    "description": ocr_data["description"],
                    "is_valid": True,
                    "notes": "OCRデータから直接抽出"
                }
            
            # 元の画像ファイルパスを保持
            result["source_image"] = ocr_data.get("source_image", "")
            
            return result
        except Exception as e:
            print_message(f"OCR結果の分類中にエラーが発生しました: {str(e)}")
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
    
    async def process_image(self, image_path: str) -> Optional[Dict]:
        """画像を処理して経費データを抽出・分類します。"""
        try:
            if not self.ocr:
                self.init_ocr()
            
            print_message(f"画像の処理を開始します: {image_path}")
            
            # 画像からテキストを抽出
            ocr_data = self.ocr.extract_expense_data(image_path)
            print_message(f"OCR結果: 日付={ocr_data['date']}, 金額=¥{ocr_data['amount']}, 説明={ocr_data['description']}")
            
            # 抽出したデータを分類
            classified_data = await self.classify_ocr_result(ocr_data)
            print_message(f"分類結果: カテゴリ={classified_data['category']}, 金額=¥{classified_data['amount']}")
            
            return classified_data
        except Exception as e:
            print_message(f"画像処理中にエラーが発生しました: {str(e)}")
            return None
    
    async def process_image_directory(self, directory_path: str) -> List[Dict]:
        """ディレクトリ内の画像を処理して経費データを抽出・分類します。"""
        try:
            if not self.ocr:
                self.init_ocr()
            
            print_message(f"ディレクトリの処理を開始します: {directory_path}")
            
            # 画像ファイルの拡張子
            image_extensions = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
            
            # ディレクトリ内の画像ファイルを取得
            image_files = []
            for ext in image_extensions:
                image_files.extend(list(Path(directory_path).glob(f"*{ext}")))
                image_files.extend(list(Path(directory_path).glob(f"*{ext.upper()}")))
            
            if not image_files:
                print_message(f"ディレクトリ内に画像ファイルが見つかりませんでした: {directory_path}")
                return []
            
            print_message(f"{len(image_files)}個の画像ファイルを処理します")
            
            # 各画像を処理
            results = []
            for image_file in image_files:
                try:
                    result = await self.process_image(str(image_file))
                    if result:
                        results.append(result)
                        print_message(f"処理完了: {image_file.name}")
                    else:
                        print_message(f"処理失敗: {image_file.name}")
                except Exception as e:
                    print_message(f"画像 {image_file.name} の処理中にエラーが発生しました: {str(e)}")
            
            print_message(f"{len(results)}/{len(image_files)}個の画像の処理が完了しました")
            return results
        except Exception as e:
            print_message(f"ディレクトリ処理中にエラーが発生しました: {str(e)}")
            return []
    
    def export_to_spreadsheet(self, expenses: List[Dict], output_path: Optional[str] = None, append: bool = False) -> str:
        """経費データをスプレッドシートに出力します。"""
        try:
            if not self.spreadsheet:
                self.init_spreadsheet(output_path)
            elif output_path:
                self.spreadsheet.output_path = output_path
            
            print_message(f"スプレッドシートへの出力を開始します: {self.spreadsheet.output_path}")
            
            # 既存ファイルへの追記または新規ファイルの作成
            if append and os.path.exists(self.spreadsheet.output_path):
                result_path = self.spreadsheet.append_expense_data(expenses)
                print_message(f"既存のスプレッドシートに経費データを追記しました: {result_path}")
            else:
                result_path = self.spreadsheet.write_expense_data(expenses)
                print_message(f"新しいスプレッドシートに経費データを書き込みました: {result_path}")
            
            return result_path
        except Exception as e:
            print_message(f"スプレッドシート出力中にエラーが発生しました: {str(e)}")
            raise

async def interactive_mode():
    """対話モードで経費データを入力・処理します。"""
    print_separator()
    print_message("=== 経費レポート自動化ツール - 対話モード ===\n")
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
            
            # スプレッドシートへの出力確認
            export_input = get_input("経費データをスプレッドシートに出力しますか？ (y/n): ")
            if export_input.lower() == 'y':
                output_path = get_input("出力ファイル名を入力してください（デフォルト: 自動生成）: ")
                if not output_path:
                    output_path = None
                
                try:
                    result_path = tool.export_to_spreadsheet(expenses, output_path)
                    print_message(f"経費データを {result_path} に出力しました")
                except Exception as e:
                    print_message(f"スプレッドシート出力中にエラーが発生しました: {str(e)}")
        else:
            print_message("\n経費データが入力されていません。")

    except KeyboardInterrupt:
        print_message("\n\nプログラムを終了します。")
    except Exception as e:
        print_message(f"\n予期せぬエラーが発生しました: {str(e)}")

async def ocr_mode(args):
    """OCRモードで画像から経費データを抽出・処理します。"""
    print_separator()
    print_message("=== 経費レポート自動化ツール - OCRモード ===\n")
    print_separator()

    try:
        tool = ExpenseReportTool()
        tool.init_ocr(args.lang)
        
        expenses = []
        
        # 単一画像の処理
        if args.image:
            print_message(f"画像ファイルの処理を開始します: {args.image}")
            result = await tool.process_image(args.image)
            if result and result.get("is_valid", False):
                expenses.append(result)
                print_message(f"画像の処理が完了しました: {args.image}")
            else:
                print_message(f"画像の処理に失敗しました: {args.image}")
        
        # ディレクトリ内の画像処理
        elif args.image_dir:
            print_message(f"ディレクトリの処理を開始します: {args.image_dir}")
            results = await tool.process_image_directory(args.image_dir)
            if results:
                expenses.extend(results)
                print_message(f"{len(results)}個の画像の処理が完了しました")
            else:
                print_message("処理可能な画像がありませんでした")
        
        # 経費データが抽出できた場合
        if expenses:
            print_separator()
            print_message(f"=== 抽出された経費データ ({len(expenses)}件) ===\n")
            for i, expense in enumerate(expenses, 1):
                print_message(f"[{i}] {expense['date']} {expense['description']}: ¥{expense['amount']:,} ({expense['category']})")
            print_separator()
            
            # レポート生成
            print_message("=== 経費レポートの生成中 ===\n")
            report = await tool.generate_report(expenses)
            print_separator()
            print_message(report)
            print_separator()
            
            # スプレッドシートへの出力
            output_path = args.output
            if not output_path:
                export_input = get_input("経費データをスプレッドシートに出力しますか？ (y/n): ")
                if export_input.lower() == 'y':
                    output_path = get_input("出力ファイル名を入力してください（デフォルト: 自動生成）: ")
            
            if output_path or export_input.lower() == 'y':
                try:
                    result_path = tool.export_to_spreadsheet(expenses, output_path, args.append)
                    print_message(f"経費データを {result_path} に出力しました")
                except Exception as e:
                    print_message(f"スプレッドシート出力中にエラーが発生しました: {str(e)}")
        else:
            print_message("\n経費データが抽出できませんでした。")

    except KeyboardInterrupt:
        print_message("\n\nプログラムを終了します。")
    except Exception as e:
        print_message(f"\n予期せぬエラーが発生しました: {str(e)}")

async def main():
    """メイン関数"""
    try:
        # コマンドライン引数の解析
        args = parse_arguments()
        
        # 動作モードに応じた処理
        if args.ocr:
            await ocr_mode(args)
        else:
            await interactive_mode()
            
    except KeyboardInterrupt:
        print_message("\n\nプログラムを終了します。")
    except Exception as e:
        print_message(f"\n予期せぬエラーが発生しました: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
