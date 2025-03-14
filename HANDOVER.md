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

### v0.4.0の主な変更点
1. **OpenAI APIへの移行**
   - OpenAI Agents SDKからOpenAI APIへの移行完了
   - `Agent`クラスと`Runner.run()`の代わりに`openai.OpenAI().chat.completions.create()`を使用
   - 既存のプロンプトを維持しつつ、APIの呼び出し方法を変更
   - APIキー管理の強化と環境変数の整理

2. **スプレッドシートモジュールの強化**
   - 行番号の連番化機能追加（追記時に自動的に連番を振り直し）
   - 空行削除機能追加（追記時に不要な空行を自動的に削除）
   - 合計行の処理改善（追記時に古い合計行を削除し、新しい合計を計算）
   - 列幅の自動調整機能の強化（日本語文字を考慮）

### v0.3.0の変更点
- OCRによる領収書画像からの経費データ抽出
  - HEICファイルのサポート追加
  - 画像処理フローの改善

### 基本機能
- ローカル環境での経費精算基本機能
- コマンドライン入力による経費データ処理
- AIによる自動分類と集計レポート生成
- スプレッドシートへの経費データ出力

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
1. SSHキー設定
```bash
# SSHキーの生成
ssh-keygen -t ed25519 -C "your_email@example.com"

# 公開鍵の表示（この内容をGitHubに登録）
cat ~/.ssh/id_ed25519.pub

# SSHエージェントの起動と鍵の追加
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# GitHubへの接続テスト
ssh -T git@github.com
```

2. リモートリポジトリ設定
```bash
# 既存のリモートの確認
git remote -v

# リモートが未設定の場合、追加
git remote add origin git@github.com:kajiwara321/expense-report-tool.git

# リモートが既に存在する場合、URLの更新
git remote set-url origin git@github.com:kajiwara321/expense-report-tool.git
```

3. ブランチ管理
```bash
# メインブランチの作成（初回のみ）
git checkout -b main

# 開発用ブランチの作成
git checkout -b feature/your-feature-name

# 変更のプッシュ
git push -u origin feature/your-feature-name
```

4. プッシュ時の注意点
- 機密情報（APIキー、環境変数）が含まれていないことを確認
- テストデータやサンプル画像は含めない
- 必ず.gitignoreが最新であることを確認
- コミット前にテストを実行（`python -m pytest`）

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
  - **receipts/** - メインディレクトリ（プロジェクトルート直下に作成）
  - **receipts/pending/** - 処理待ちファイル配置ディレクトリ（ここに画像を配置）
  - **receipts/processed/** - 処理済みファイル保存ディレクトリ（自動的に移動）

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
   - **receipts/pending/** ディレクトリに処理待ちファイルを配置
   - 処理後、自動的に **receipts/processed/** ディレクトリに移動
   - **注意: 入れ子になった複数のpending/processedディレクトリは使用しない**
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

## OCR処理の正しい使用方法

### 画像配置場所
1. 領収書画像は **必ずプロジェクトルート直下の `receipts/pending/` ディレクトリに配置**
2. 入れ子になった複数のpending/processedディレクトリは使用しない
3. 処理済み画像は自動的に `receipts/processed/` ディレクトリに移動

### 処理フロー
1. 領収書画像を `receipts/pending/` ディレクトリに配置
2. OCRモードでツールを実行
   ```bash
   python expense_report_tool.py --ocr --image-dir receipts/pending
   ```
3. 画像が処理され、テキストが抽出される
4. 抽出されたデータが経費情報として構造化
5. 処理済み画像が `receipts/processed/` ディレクトリに移動
6. 必要に応じてスプレッドシートに出力
   ```bash
   python expense_report_tool.py --ocr --image-dir receipts/pending --output expenses.xlsx
   ```

### ディレクトリ構造の修正方法
現在、入れ子になった複数のpending/processedディレクトリが存在する場合は、以下の手順で修正してください：

1. プロジェクトルート直下に正しいディレクトリ構造を作成
   ```bash
   mkdir -p receipts/pending receipts/processed
   ```

2. 入れ子になったディレクトリから重要なファイルを移動
   ```bash
   # 例: 入れ子になったディレクトリから画像ファイルを移動
   find receipts -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.heic" -o -name "*.HEIC" \) -exec mv {} receipts/pending/ \;
   ```

3. 不要なディレクトリを削除
   ```bash
   # 注意: 重要なファイルを移動した後に実行
   find receipts -type d -not -path "receipts" -not -path "receipts/pending" -not -path "receipts/processed" -exec rm -rf {} \;
   ```

4. .gitkeepファイルを作成
   ```bash
   touch receipts/pending/.gitkeep receipts/processed/.gitkeep
