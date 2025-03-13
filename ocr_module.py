"""
経費レポート自動化ツール - OCRモジュール

このモジュールは、領収書画像からテキストを抽出し、
経費データとして構造化する機能を提供します。
"""

import os
import re
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from datetime import datetime
import logging
from pillow_heif import register_heif_opener
import pathlib
import shutil

# HEIFファイルを読み込めるようにPILを拡張
register_heif_opener()

# ロギングの設定
logging.basicConfig(
    level=logging.INFO if os.getenv("DEBUG", "false").lower() == "true" else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ocr_module")

class ReceiptOCR:
    """領収書画像からテキストを抽出し、経費データに変換するクラス"""
    
    def __init__(self, lang='jpn+eng'):
        """
        OCRモジュールの初期化
        
        Args:
            lang (str): OCRで使用する言語。デフォルトは日本語と英語。
        """
        self.lang = lang
        logger.info(f"ReceiptOCR initialized with language: {lang}")
        
    def preprocess_image(self, image):
        """
        OCR精度向上のための画像前処理
        
        Args:
            image (PIL.Image): 処理する画像
            
        Returns:
            PIL.Image: 前処理された画像
        """
        try:
            # グレースケール変換
            if image.mode != 'L':
                image = image.convert('L')
            
            # コントラスト強調
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)
            
            # ノイズ除去
            image = image.filter(ImageFilter.MedianFilter())
            
            # 二値化
            threshold = 150
            image = image.point(lambda p: p > threshold and 255)
            
            logger.info("Image preprocessing completed successfully")
            return image
        except Exception as e:
            logger.error(f"Error during image preprocessing: {str(e)}")
            return image  # エラー時は元の画像を返す
    
    def convert_heic_to_jpeg(self, image_path):
        """
        HEICファイルをJPEGに変換
        
        Args:
            image_path (str): HEICファイルのパス
            
        Returns:
            tuple: (PIL.Image, str) 変換された画像オブジェクトと一時ファイルのパス
        """
        # 画像の読み込み
        image = Image.open(image_path)
        
        # JPEGに変換
        logger.info("Converting HEIC to JPEG format")
        temp_path = image_path.replace('.heic', '_temp.jpg')
        image = image.convert('RGB')
        image.save(temp_path, 'JPEG', quality=90)
        
        return image, temp_path

    def extract_text(self, image_path):
        """
        画像からテキストを抽出
        
        Args:
            image_path (str): 画像ファイルのパス
            
        Returns:
            str: 抽出されたテキスト
        """
        try:
            temp_path = None
            # 画像の拡張子を取得
            ext = pathlib.Path(image_path).suffix.lower()
            
            # HEICファイルの場合、JPEGに変換
            if ext == '.heic':
                image, temp_path = self.convert_heic_to_jpeg(image_path)
            else:
                image = Image.open(image_path)
            
            logger.info(f"Image loaded: {image_path}, size: {image.size}, mode: {image.mode}")
            
            # 画像の前処理
            processed_image = self.preprocess_image(image)
            
            # OCR処理
            text = pytesseract.image_to_string(processed_image, lang=self.lang)
            logger.info(f"Text extracted, length: {len(text)}")
            logger.debug(f"Extracted text: {text}")
            
            return text, temp_path
        except Exception as e:
            logger.error(f"Error during text extraction: {str(e)}")
            raise
    
    def parse_date(self, text):
        """
        テキストから日付を抽出
        
        Args:
            text (str): 抽出されたテキスト
            
        Returns:
            str: YYYY-MM-DD形式の日付文字列、見つからない場合は現在の日付
        """
        # 日本語の日付パターン (例: 2024年3月13日)
        jp_date_pattern = r'(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日'
        # 英語の日付パターン (例: 2024/3/13, 2024-3-13)
        en_date_pattern = r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})'
        
        # 日本語パターンの検索
        jp_match = re.search(jp_date_pattern, text)
        if jp_match:
            year, month, day = jp_match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # 英語パターンの検索
        en_match = re.search(en_date_pattern, text)
        if en_match:
            year, month, day = en_match.groups()
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # 日付が見つからない場合は現在の日付を返す
        logger.warning("Date not found in text, using current date")
        return datetime.now().strftime("%Y-%m-%d")
    
    def parse_amount(self, text):
        """
        テキストから金額を抽出
        
        Args:
            text (str): 抽出されたテキスト
            
        Returns:
            int: 抽出された金額、見つからない場合は0
        """
        # 金額パターン (例: ¥1,500、1,500円、1500円)
        amount_patterns = [
            r'¥\s*([\d,]+)',  # ¥1,500
            r'(\d[\d,]*)\s*円',  # 1500円、1,500円
            r'金額\s*:?\s*([\d,]+)',  # 金額:1500、金額: 1,500
            r'合計\s*:?\s*([\d,]+)'  # 合計:1500、合計: 1,500
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # 最大の金額を選択（複数マッチした場合）
                amounts = []
                for match in matches:
                    # カンマを除去して数値に変換
                    try:
                        amount = int(match.replace(',', ''))
                        amounts.append(amount)
                    except ValueError:
                        continue
                
                if amounts:
                    max_amount = max(amounts)
                    logger.info(f"Amount found: {max_amount}")
                    return max_amount
        
        logger.warning("Amount not found in text")
        return 0
    
    def parse_description(self, text):
        """
        テキストから説明（店舗名など）を抽出
        
        Args:
            text (str): 抽出されたテキスト
            
        Returns:
            str: 抽出された説明
        """
        # 店舗名や説明を抽出するロジック
        # 一般的には最初の数行に店舗名があることが多い
        lines = text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        if non_empty_lines:
            # 最初の非空行を店舗名/説明として使用
            description = non_empty_lines[0]
            logger.info(f"Description found: {description}")
            return description
        
        logger.warning("Description not found in text")
        return "不明"
    
    def extract_expense_data(self, image_path):
        """
        画像から経費データを抽出
        
        Args:
            image_path (str): 画像ファイルのパス
            
        Returns:
            dict: 経費データ（日付、金額、説明など）
        """
        try:
            # ディレクトリパスの解決
            receipts_dir = os.path.join(os.path.dirname(image_path))
            pending_dir = os.path.join(receipts_dir, "pending")
            processed_dir = os.path.join(receipts_dir, "processed")

            # 処理待ちディレクトリにコピー（まだ処理待ちディレクトリにない場合）
            if not os.path.exists(pending_dir):
                os.makedirs(pending_dir)

            pending_path = os.path.join(pending_dir, os.path.basename(image_path))
            if os.path.abspath(image_path) != os.path.abspath(pending_path):
                if os.path.exists(image_path):
                    shutil.copy2(image_path, pending_path)
                    logger.info(f"Copied file to pending directory: {pending_path}")
                else:
                    raise FileNotFoundError(f"Original file not found: {image_path}")
            
            # 処理待ちファイルが存在することを確認
            if not os.path.exists(pending_path):
                raise FileNotFoundError(f"Pending file not found: {pending_path}")

            # テキスト抽出とデータ処理
            text, temp_path = self.extract_text(pending_path)
            
            # データ抽出
            date = self.parse_date(text)
            amount = self.parse_amount(text)
            description = self.parse_description(text)
            
            # 処理済みディレクトリに移動準備
            if not os.path.exists(processed_dir):
                os.makedirs(processed_dir)

            # 新しいファイルパスを生成（同名ファイルが存在する場合は番号を付加）
            base_name = os.path.basename(image_path)
            new_path = os.path.join(processed_dir, base_name)
            counter = 1
            while os.path.exists(new_path):
                name, ext = os.path.splitext(base_name)
                new_path = os.path.join(processed_dir, f"{name}_{counter}{ext}")
                counter += 1

            # JPEGファイルを処理済みディレクトリに移動（HEICの場合）
            if temp_path and os.path.exists(temp_path):
                # 拡張子をjpgに変更
                processed_jpg_path = new_path.replace('.heic', '.jpg').replace('.HEIC', '.jpg')
                shutil.move(temp_path, processed_jpg_path)
                logger.info(f"Moved JPEG file to processed directory: {processed_jpg_path}")
                new_path = processed_jpg_path
            else:
                # 通常のファイル移動
                shutil.move(pending_path, new_path)
                logger.info(f"Moved file to processed directory: {new_path}")
            
            # 元のファイルを削除
            if os.path.exists(image_path):
                os.remove(image_path)
                logger.info(f"Removed original file: {image_path}")
            
            # 処理待ちディレクトリの一時ファイルを削除
            if os.path.exists(pending_path):
                os.remove(pending_path)
                logger.info(f"Removed pending file: {pending_path}")

            # 経費データの構築
            expense_data = {
                "date": date,
                "amount": amount,
                "description": description,
                "raw_text": text,
                "source_image": new_path
            }
            
            logger.info(f"Expense data extracted: {expense_data}")
            return expense_data
        except Exception as e:
            logger.error(f"Error during expense data extraction: {str(e)}")
            raise

# 単体テスト用のコード
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python ocr_module.py <画像ファイルパス>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    ocr = ReceiptOCR()
    
    try:
        expense_data = ocr.extract_expense_data(image_path)
        print("\n=== 抽出結果 ===")
        print(f"日付: {expense_data['date']}")
        print(f"金額: ¥{expense_data['amount']:,}")
        print(f"説明: {expense_data['description']}")
        print("\n=== 抽出テキスト ===")
        print(expense_data['raw_text'])
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
