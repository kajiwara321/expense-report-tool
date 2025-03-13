# 経費レポートツール - 引き継ぎドキュメント

## プロジェクト概要

経費データを入力し、自動的に分類・集計してレポートを生成するツールです。
OpenAI Agents SDKを使用して、経費の分類と集計レポートの生成を行います。
OCR機能による領収書画像からの経費データ抽出とスプレッドシート出力機能を追加しました。

## リポジトリ情報
- GitHub URL: https://github.com/kajiwara321/expense-report-tool
- ブランチ: main

## バージョン情報

現在のバージョン: v0.2.0 (OCR・スプレッドシート機能追加)
- ローカル環境での経費精算基本機能の実装
- コマンドライン入力による経費データ処理
- AIによる自動分類と集計レポート生成
- OCRによる領収書画像からの経費データ抽出
- スプレッドシートへの経費データ出力

## モジュール構成

### 1. メインモジュール (`expense_report_tool.py`)
- 対話モードとOCRモードの両方をサポート
- コマンドライン引数の処理
- 全体のワークフロー制御

### 2. OCRモジュール (`ocr_module.py`)
- 領収書画像からのテキスト抽出
- 画像前処理（グレースケール変換、コントラスト調整など）
- 抽出テキストからの経費データ構造化

### 3. スプレッドシートモジュール (`spreadsheet_module.py`)
- 経費データのExcelスプレッドシートへの出力
- 書式設定（ヘッダー、データ行、合計行など）
- 既存ファイルへの追記機能

## AI処理フロー

### 1. 入力データの処理
```json
// 対話モード入力
{
  "input": {
    "description": "タクシー代",
    "date": "2024年3月13日",
    "amount": "¥1,500",
    "detail": "東京駅から会社まで"
  }
}

// OCRモード入力
{
  "image_path": "receipts/receipt1.jpg",
  "raw_text": "株式会社〇〇タクシー\n2024年3月13日\n領収書\n金額: 1,500円\n東京駅→会社",
  "extracted_data": {
    "date": "2024-03-13",
    "amount": 1500,
    "description": "株式会社〇〇タクシー"
  }
}
```

### 2. 期待される分類結果
```json
{
  "category": "交通費",
  "sub_category": "タクシー",
  "amount": 1500,
  "date": "2024-03-13",
  "purpose": "business",
  "is_valid": true,
  "notes": "通常の通勤経路外の移動として承認可能",
  "source_image": "receipts/receipt1.jpg"  // OCRモードの場合のみ
}
```

### 3. レポート生成
```json
{
  "summary": {
    "total_amount": 19300,
    "categories": {
      "交通費": 1500,
      "食費": 2800,
      "会議費": 15000
    },
    "high_value_expenses": [
      {
        "description": "会議室利用料",
        "amount": 15000,
        "justification": "取引先との商談のため必要"
      }
    ]
  }
}
```

### 4. スプレッドシート出力
- 経費データをExcelスプレッドシートに出力
- ヘッダー行、データ行、合計行の書式設定
- 既存ファイルへの追記または新規ファイルの作成

## エラーハンドリングとリカバリー

### 1. JSON解析エラー

```python
async def safe_json_parse(json_str: str) -> Dict:
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
            # 行の処理（カンマの追加/削除など）
            # 詳細な実装は expense_report_tool.py を参照
        
        return json.loads(cleaned)
    except (json.JSONDecodeError, IndexError) as e:
        # エラー時のフォールバック処理
        return {
            "category": "エラー",
            "amount": 0,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "description": "解析エラー",
            "is_valid": False,
            "notes": f"JSONパースエラー: {str(e)}"
        }
```

### 2. OCR処理エラー

```python
async def process_image(self, image_path: str) -> Optional[Dict]:
    try:
        # 画像からテキストを抽出
        ocr_data = self.ocr.extract_expense_data(image_path)
        
        # 抽出したデータを分類
        classified_data = await self.classify_ocr_result(ocr_data)
        
        return classified_data
    except Exception as e:
        print_message(f"画像処理中にエラーが発生しました: {str(e)}")
        return None  # エラー時はNoneを返して呼び出し元で処理
```

### 3. スプレッドシート出力エラー

```python
def export_to_spreadsheet(self, expenses: List[Dict], output_path: Optional[str] = None, append: bool = False) -> str:
    try:
        # スプレッドシートへの出力処理
        if append and os.path.exists(self.spreadsheet.output_path):
            result_path = self.spreadsheet.append_expense_data(expenses)
        else:
            result_path = self.spreadsheet.write_expense_data(expenses)
        
        return result_path
    except Exception as e:
        print_message(f"スプレッドシート出力中にエラーが発生しました: {str(e)}")
        raise  # 呼び出し元でエラーハンドリング
```

## セットアップ手順

1. リポジトリのクローン
```bash
git clone https://github.com/kajiwara321/expense-report-tool.git
cd expense-report-tool
```

2. 環境のセットアップ
```bash
./setup.sh
source venv/bin/activate
```

3. 追加依存関係のインストール
```bash
# OCR関連
pip install pytesseract pillow numpy

# スプレッドシート関連
pip install openpyxl

# Tesseractのインストール（OSによって異なる）
# macOS
brew install tesseract tesseract-lang  # 日本語対応

# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-jpn
```

4. APIキーの設定
- `.env`ファイルに以下を設定：
```
OPENAI_API_KEY=your-api-key-here
DEBUG=false  # デバッグ出力を有効にする場合は true
```

## 使用方法

### 1. 対話モード（従来の機能）
```bash
python expense_report_tool.py
```

### 2. OCRモード（新機能）
```bash
# 単一画像の処理
python expense_report_tool.py --ocr --image receipts/receipt1.jpg

# ディレクトリ内の全画像を処理
python expense_report_tool.py --ocr --image-dir receipts/

# 言語指定（デフォルトは日本語と英語）
python expense_report_tool.py --ocr --image-dir receipts/ --lang eng

# 出力ファイル指定
python expense_report_tool.py --ocr --image-dir receipts/ --output expenses.xlsx

# 既存ファイルへの追記
python expense_report_tool.py --ocr --image-dir receipts/ --output expenses.xlsx --append

# デバッグモード
python expense_report_tool.py --ocr --image-dir receipts/ --debug
```

## AIモデルへの指示

### 1. 経費分類時の考慮事項
- 業務関連性の判断
- 金額の妥当性確認
- 必要書類の確認
- 税務上の考慮事項

### 2. レポート生成時の注意点
- 異常値の検出
- 重複チェック
- コンプライアンス違反の可能性
- 承認フローの提案

### 3. OCR処理時の考慮事項
- 画像品質の評価
- テキスト認識の信頼性
- 構造化データの妥当性
- 補完が必要な情報の特定

### 4. 改善提案の生成
- コスト削減機会の特定
- 経費パターンの分析
- プロセス改善の提案
- 自動化可能な部分の特定

## 現状の実装

### 機能
- 経費データの対話的な入力
- AIによる経費の自動分類
- 分類された経費データからのレポート生成
- 堅牢なJSON解析処理
- デバッグモードのサポート
- OCRによる領収書画像からの経費データ抽出
- スプレッドシートへの経費データ出力

### ファイル構成
- `expense_report_tool.py`: メインの実装ファイル
- `ocr_module.py`: OCR処理モジュール
- `spreadsheet_module.py`: スプレッドシート出力モジュール
- `README.md`: 使用方法の説明
- `HANDOVER.md`: このドキュメント
- `test_api_key.py`: APIキー検証用スクリプト

## テスト方法

### 1. APIキーのテスト
```bash
python test_api_key.py
```

### 2. 基本機能のテスト（対話モード）
```bash
python expense_report_tool.py
```

入力例：
```
タクシー代 2024年3月13日 ¥1,500 東京駅から会社まで
昼食代 2024年3月13日 ¥2,800 取引先との打ち合わせ
会議室利用料 2024年3月13日 ¥15,000 取引先との商談
```

### 3. OCR機能のテスト
```bash
# テスト用の画像が必要です
python ocr_module.py path/to/receipt.jpg

# メインプログラムからのOCR機能テスト
python expense_report_tool.py --ocr --image path/to/receipt.jpg --debug
```

### 4. スプレッドシート出力のテスト
```bash
# 単体テスト
python spreadsheet_module.py

# メインプログラムからのテスト
python expense_report_tool.py
# 経費データ入力後、スプレッドシート出力を選択
```

## デバッグ方法

### 1. デバッグモードの有効化
```
# .envファイルで設定
DEBUG=true

# または実行時に指定
python expense_report_tool.py --debug
python expense_report_tool.py --ocr --image-dir receipts/ --debug
```

### 2. デバッグ情報の確認
- JSON解析の中間状態
- APIレスポンスの詳細
- OCR処理の詳細（画像サイズ、抽出テキストなど）
- スプレッドシート操作の詳細
- エラーのスタックトレース

### 3. モジュール別のデバッグ
```bash
# OCRモジュールのデバッグ
python ocr_module.py path/to/receipt.jpg

# スプレッドシートモジュールのデバッグ
python spreadsheet_module.py
```

## 既知の制限事項

### 1. 入力形式
- 対話モードはコマンドライン入力のみ
- 日付形式は限定的

### 2. OCR機能
- 画像品質に大きく依存
- 複雑なレイアウトの領収書は認識精度が低下
- 手書き文字の認識は不安定
- Tesseractのインストールが必要

### 3. データ永続化
- スプレッドシート出力はあるが、データベースは未実装
- 画像と経費データの関連付けは限定的

### 4. レポート形式
- 固定テンプレート
- カスタマイズ不可

## 今後の展開計画

### フェーズ1: OCR機能の強化 (Current)
- ✅ 基本的なOCR機能の実装
- ✅ 画像前処理の実装
- ✅ スプレッドシート出力機能
- ⬜ OCR精度の向上（機械学習モデルの活用）
- ⬜ 複数フォーマットの領収書対応
- ⬜ QRコード/バーコード読み取り対応

### フェーズ2: Web実装
- Webインターフェースの開発
- ユーザー認証システム
- クラウドストレージ連携
- ドラッグ&ドロップによる画像アップロード

### フェーズ3: 拡張機能
- 経費データの永続化（データベース実装）
- レポートテンプレートのカスタマイズ
- 承認ワークフローの実装
- 経費データの分析・可視化
- モバイルアプリ連携

## リファレンス

- [OpenAI API Documentation](https://platform.openai.com/docs/api-reference)
- [Python Documentation](https://docs.python.org/)
- [Tesseract OCR Documentation](https://github.com/tesseract-ocr/tesseract)
- [PyTesseract Documentation](https://github.com/madmaze/pytesseract)
- [OpenPyXL Documentation](https://openpyxl.readthedocs.io/)
- [Project GitHub Repository](https://github.com/kajiwara321/expense-report-tool)

## 問題報告・連絡先

問題や質問がある場合は、以下に連絡してください：
- [GitHub Issues](https://github.com/kajiwara321/expense-report-tool/issues)
