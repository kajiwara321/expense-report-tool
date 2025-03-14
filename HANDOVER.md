# 経費レポートツール - 引き継ぎドキュメント

## プロジェクト概要

経費データを入力し、自動的に分類・集計してレポートを生成するツールです。
OpenAI APIを使用して、経費の分類と集計レポートの生成を行います。
OCR機能による領収書画像からの経費データ抽出とスプレッドシート出力機能を追加しました。

## リポジトリ情報
- GitHub URL: https://github.com/kajiwara321/expense-report-tool
- ブランチ: main

## バージョン情報

現在のバージョン: v0.4.0 (OpenAI API移行とスプレッドシート機能強化)
- ローカル環境での経費精算基本機能の実装
- コマンドライン入力による経費データ処理
- AIによる自動分類と集計レポート生成
  - OpenAI Agents SDKからOpenAI APIへの移行（v0.4.0）
- OCRによる領収書画像からの経費データ抽出
  - HEICファイルのサポート追加（v0.3.0）
  - 画像処理フローの改善（v0.3.0）
- スプレッドシートへの経費データ出力
  - 行番号の連番化と空行削除機能の追加（v0.4.0）
  - 追記モードの改善（v0.4.0）

## Gitリポジトリ管理

### ディレクトリ構造
```
expense-report-tool/
├── expense_report_tool.py  # メインモジュール
├── ocr_module.py          # OCR処理モジュール
├── spreadsheet_module.py  # スプレッドシート出力モジュール
├── requirements.txt       # 依存パッケージリスト
├── setup.sh              # 環境セットアップスクリプト 
├── .env                  # 環境変数設定ファイル
└── receipts/             # 領収書画像処理ディレクトリ
    ├── pending/          # 処理待ちファイル用
    └── processed/        # 処理済みファイル用
```

### バージョン管理対象外ファイル (.gitignore)
```
# 環境変数
.env

# キャッシュファイル
__pycache__/
*.py[cod]
*$py.class

# 仮想環境
venv/
env/

# APIキー関連
*api_key*

# 領収書画像
receipts/*
!receipts/pending/.gitkeep
!receipts/processed/.gitkeep

# 出力ファイル
*.xlsx
*.csv

# macOS関連
.DS_Store
```

### GitHub連携設定
1. リモートリポジトリ設定
```bash
git remote add origin git@github.com:kajiwara321/expense-report-tool.git
```

2. SSHキー設定
- GitHubアカウントにSSHキーを登録していることを確認
- 必要に応じて新規SSHキーを生成：
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
```

3. プッシュ時の注意点
- 機密情報（APIキー、環境変数）が含まれていないことを確認
- テストデータやサンプル画像は含めない
- 必ず.gitignoreが最新であることを確認

## モジュール構成

### 1. メインモジュール (`expense_report_tool.py`)
- 対話モードとOCRモードの両方をサポート
- コマンドライン引数の処理
- 全体のワークフロー制御
- OpenAI APIを使用した経費分類と集計レポート生成

### 2. OCRモジュール (`ocr_module.py`)
- 領収書画像からのテキスト抽出
- 画像前処理（グレースケール変換、コントラスト調整など）
- 抽出テキストからの経費データ構造化
- HEICファイルの自動変換機能
- ファイル処理フロー
  - receipts/ - 入力ファイル配置ディレクトリ
  - receipts/pending/ - 処理待ちファイル
  - receipts/processed/ - 処理済みファイル

### 3. スプレッドシートモジュール (`spreadsheet_module.py`)
- 経費データのExcelスプレッドシートへの出力
- 書式設定（ヘッダー、データ行、合計行など）
- 既存ファイルへの追記機能
- 行番号の連番化と空行削除機能
- 合計金額の自動計算

## 最新の更新内容（v0.4.0）

### OpenAI API移行
- OpenAI Agents SDKからOpenAI APIへの移行
- 経費分類と集計レポート生成機能の改善
- APIキー管理の強化

### スプレッドシート機能強化
- 行番号の連番化機能
  - 追記時に行番号が正しく連番になるよう改善
- 空行削除機能
  - 追記時に不要な空行を自動的に削除
- 合計行の処理改善
  - 追記時に古い合計行を削除し、新しい合計を計算

### 依存関係の更新
```bash
# OpenAI API用
pip install openai

# requirements.txtにも追加済み
```

### テスト済み機能
- [x] OpenAI APIによる経費分類
- [x] OpenAI APIによるレポート生成
- [x] 複数領収書の一括処理
- [x] スプレッドシートへの出力（行番号連番化）
- [x] 既存ファイルへの追記（空行削除）

## 注意事項とベストプラクティス

### セキュリティ
1. 環境変数
   - APIキーなどの機密情報は必ず.envファイルで管理
   - .envファイルは.gitignoreに含める

2. テストデータ
   - 実際の領収書画像はGitにコミットしない
   - テスト用のダミーデータのみをコミット可

### ファイル管理
1. 画像ファイル
   - pending/ディレクトリに処理待ちファイルを配置
   - processed/ディレクトリに処理済みファイルを移動
   - 両ディレクトリは.gitkeepで管理

2. 出力ファイル
   - Excelファイルはバージョン管理対象外
   - 必要に応じてバックアップを作成

### コード管理
1. コミット前の確認事項
   - 機密情報が含まれていないか
   - 不要なファイルが含まれていないか
   - .gitignoreが最新か

2. プッシュ前の確認事項
   - テストが全て通過しているか
   - ローカルブランチが最新か
