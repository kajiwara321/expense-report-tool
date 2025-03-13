# Expense Report Tool

経費精算の自動化ツール（v0.1.0）

## 概要

このツールは、経費データの入力、分類、集計を自動化し、見やすいレポートを生成します。OpenAI APIを利用して、入力された経費データを自動的に適切なカテゴリに分類し、集計レポートを作成します。

### 主な機能

- 🎯 経費データの対話的な入力
- 🤖 AIによる自動分類
- 📊 見やすい経費レポートの生成
- 🗾 日本語での入力に対応
- 🔍 高額支出の自動検出

## インストール

### 必要条件

- Python 3.9以上
- OpenAI APIキー
- pip（Pythonパッケージマネージャー）

### セットアップ手順

1. リポジトリのクローン：
```bash
git clone https://github.com/[your-username]/expense-report-tool.git
cd expense-report-tool
```

2. 仮想環境のセットアップ：
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. 環境変数の設定：
`.env`ファイルを作成し、以下の内容を設定：
```
OPENAI_API_KEY=your-api-key-here
DEBUG=false  # デバッグ出力を有効にする場合は true
```

## 使用方法

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

## 開発ロードマップ

### フェーズ1: OCR実装 (Next)
- 領収書の画像からのデータ抽出
- テキスト認識精度の向上

### フェーズ2: Web実装
- Webインターフェースの開発
- ユーザー認証システム

### フェーズ3: 機能拡張
- データベース連携
- 承認ワークフロー
- レポートのカスタマイズ

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
