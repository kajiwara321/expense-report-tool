# Expense Report Tool

経費精算の自動化ツール（v0.2.0）

## 概要

このツールは、経費データの入力、分類、集計を自動化し、見やすいレポートを生成します。OpenAI APIを利用して、入力された経費データを自動的に適切なカテゴリに分類し、集計レポートを作成します。

**新機能**: OCRによる領収書画像からの経費データ抽出とExcelスプレッドシートへの出力機能を追加しました！

### 主な機能

- 🎯 経費データの対話的な入力
- 🤖 AIによる自動分類
- 📊 見やすい経費レポートの生成
- 🗾 日本語での入力に対応
- 🔍 高額支出の自動検出
- 📷 OCRによる領収書画像からのデータ抽出 **(New!)**
- 📑 Excelスプレッドシートへの出力 **(New!)**

## インストール

### 必要条件

- Python 3.9以上
- OpenAI APIキー
- pip（Pythonパッケージマネージャー）
- Tesseract OCR（OCR機能を使用する場合）

### セットアップ手順

1. リポジトリのクローン：
```bash
git clone https://github.com/kajiwara321/expense-report-tool.git
cd expense-report-tool
```

2. 仮想環境のセットアップ：
```bash
./setup.sh
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. Tesseract OCRのインストール（OCR機能を使用する場合）：
```bash
# macOS
brew install tesseract tesseract-lang  # 日本語対応

# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-jpn

# Windows
# https://github.com/UB-Mannheim/tesseract/wiki からインストーラをダウンロード
```

4. 環境変数の設定：
`.env`ファイルを作成し、以下の内容を設定：
```
OPENAI_API_KEY=your-api-key-here
DEBUG=false  # デバッグ出力を有効にする場合は true
```

## 使用方法

### 対話モード（従来の機能）

1. プログラムの起動：
```bash
python expense_report_tool.py
```

2. 経費データの入力例：
```
経費データを入力してください: タクシー代 2024年3月13日 ¥1,500 東京駅から会社まで
```

3. 分類結果の確認：
```json
{
  "category": "交通費",
  "amount": 1500,
  "date": "2024-03-13",
  "description": "東京駅から会社まで",
  "is_valid": true,
  "notes": ""
}
```

4. 最終レポートの例：
```
==============================
経費レポート (2024年03月13日)
==============================

【合計金額】
¥19,300

【カテゴリ別集計】
- 交通費: ¥1,500
- 宿泊費: ¥0
- 飲食費: ¥2,800
- 消耗品費: ¥0
- その他: ¥15,000

【特記事項】
- 高額支出（¥5,000以上）: 会議室利用料（¥15,000）
- その他の注意点: 特になし
```

5. スプレッドシートへの出力（オプション）：
```
経費データをスプレッドシートに出力しますか？ (y/n): y
出力ファイル名を入力してください（デフォルト: 自動生成）: expenses.xlsx
経費データを expenses.xlsx に出力しました
```

### OCRモード（新機能）

1. 単一画像の処理：
```bash
python expense_report_tool.py --ocr --image receipts/receipt1.jpg
```

2. ディレクトリ内の全画像を処理：
```bash
python expense_report_tool.py --ocr --image-dir receipts/
```

3. 出力ファイルの指定：
```bash
python expense_report_tool.py --ocr --image-dir receipts/ --output expenses.xlsx
```

4. 既存ファイルへの追記：
```bash
python expense_report_tool.py --ocr --image-dir receipts/ --output expenses.xlsx --append
```

5. デバッグモードの有効化：
```bash
python expense_report_tool.py --ocr --image-dir receipts/ --debug
```

6. ヘルプの表示：
```bash
python expense_report_tool.py --help
```

## 開発ロードマップ

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

### フェーズ3: 機能拡張
- データベース連携
- 承認ワークフロー
- レポートのカスタマイズ
- モバイルアプリ連携

## 既知の制限事項

- OCR機能は画像品質に大きく依存します
- 複雑なレイアウトの領収書は認識精度が低下する場合があります
- 手書き文字の認識は不安定な場合があります
- Tesseractのインストールが必要です

## 貢献方法

1. このリポジトリをFork
2. 新しい機能用のブランチを作成: `git checkout -b feature/amazing-feature`
3. 変更をコミット: `git commit -m 'Add amazing feature'`
4. リポジトリにPush: `git push origin feature/amazing-feature`
5. Pull Requestを作成

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 開発者向け情報

詳細な技術情報や開発者向けドキュメントは[HANDOVER.md](HANDOVER.md)を参照してください。
