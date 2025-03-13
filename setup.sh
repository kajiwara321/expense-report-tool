#!/bin/bash

# エラーが発生したら中断
set -e

echo "経費レポートツール セットアップスクリプト"
echo "========================================"

# Pythonの存在確認
if ! command -v python3 &> /dev/null; then
    echo "エラー: Python 3がインストールされていません"
    exit 1
fi

# 仮想環境の作成
if [ ! -d "venv" ]; then
    echo "仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境を有効化
source venv/bin/activate

# pipのアップグレード
echo "pipをアップグレード中..."
pip install --upgrade pip

# 依存パッケージのインストール
echo "依存パッケージをインストール中..."
pip install -r requirements.txt

# .envファイルの作成（存在しない場合）
if [ ! -f ".env" ]; then
    echo "サンプル.envファイルを作成中..."
    cat > .env << EOL
# OpenAI API Key
OPENAI_API_KEY=your-api-key-here

# その他の設定
DEBUG=false  # デバッグ出力を有効にする場合は true
EOL
    echo ".envファイルが作成されました。APIキーを設定してください。"
fi

echo ""
echo "セットアップが完了しました。"
echo "1. .env ファイルにOpenAI APIキーを設定してください。"
echo "2. 仮想環境を有効化するには以下のコマンドを実行してください："
echo "   source venv/bin/activate"
