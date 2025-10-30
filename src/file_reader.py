"""
ファイル読み込みモジュール
テキスト、PDF、画像（OCR）からテキストを抽出します
"""

from pathlib import Path
from typing import Union, List, Tuple
import PyPDF2
from PIL import Image
import pytesseract


class FileReader:
    """ファイル読み込みクラス"""

    @staticmethod
    def read_text_file(file_path: Union[str, Path]) -> str:
        """
        テキストファイルを読み込む

        Args:
            file_path: ファイルパス

        Returns:
            str: ファイルの内容

        Raises:
            FileNotFoundError: ファイルが見つからない
            UnicodeDecodeError: エンコーディングエラー
        """
        file_path = Path(file_path)

        # エンコーディングを試す順番
        encodings = ['utf-8', 'shift_jis', 'cp932', 'euc_jp', 'iso2022_jp']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return content
            except UnicodeDecodeError:
                continue

        # すべて失敗した場合
        raise UnicodeDecodeError(
            'utf-8', b'', 0, 1,
            f"ファイル {file_path} を読み込めませんでした。"
            f"エンコーディングを確認してください。"
        )

    @staticmethod
    def read_pdf_file(file_path: Union[str, Path]) -> str:
        """
        PDFファイルからテキストを抽出

        Args:
            file_path: PDFファイルのパス

        Returns:
            str: 抽出されたテキスト

        Raises:
            FileNotFoundError: ファイルが見つからない
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        text_content = []

        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)

                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text.strip():
                        text_content.append(f"--- Page {page_num + 1} ---\n{text}")

            return "\n\n".join(text_content)

        except Exception as e:
            raise Exception(f"PDF読み込みエラー: {str(e)}")

    @staticmethod
    def read_image_file(file_path: Union[str, Path], lang: str = 'jpn') -> str:
        """
        画像ファイルからOCRでテキストを抽出

        Args:
            file_path: 画像ファイルのパス
            lang: OCR言語（デフォルト: jpn）

        Returns:
            str: 抽出されたテキスト

        Raises:
            FileNotFoundError: ファイルが見つからない
            Exception: OCRエラー
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"ファイルが見つかりません: {file_path}")

        try:
            # 画像を開く
            image = Image.open(file_path)

            # OCR実行
            # Tesseractの設定: 日本語 + 英語
            text = pytesseract.image_to_string(
                image,
                lang=f'{lang}+eng',
                config='--psm 6'  # 単一の均一なテキストブロックと仮定
            )

            return text.strip()

        except Exception as e:
            raise Exception(f"OCR処理エラー: {str(e)}")

    @classmethod
    def read_file(cls, file_path: Union[str, Path]) -> Tuple[str, str]:
        """
        ファイルの種類を自動判定して読み込む

        Args:
            file_path: ファイルパス

        Returns:
            Tuple[str, str]: (テキスト内容, ファイル種別)
            ファイル種別: 'text', 'pdf', 'image'

        Raises:
            ValueError: サポートされていないファイル形式
            Exception: 読み込みエラー
        """
        file_path = Path(file_path)
        suffix = file_path.suffix.lower()

        try:
            # テキストファイル
            if suffix in ['.txt']:
                content = cls.read_text_file(file_path)
                return content, 'text'

            # PDF
            elif suffix in ['.pdf']:
                content = cls.read_pdf_file(file_path)
                return content, 'pdf'

            # 画像
            elif suffix in ['.jpg', '.jpeg', '.png']:
                content = cls.read_image_file(file_path)
                return content, 'image'

            else:
                raise ValueError(
                    f"サポートされていないファイル形式: {suffix}\n"
                    f"対応形式: .txt, .pdf, .jpg, .jpeg, .png"
                )

        except Exception as e:
            raise Exception(f"ファイル読み込みエラー ({file_path.name}): {str(e)}")

    @classmethod
    def read_multiple_files(cls, file_paths: List[Union[str, Path]]) -> str:
        """
        複数のファイルを読み込んで結合
        ファイル名も個人情報マスク処理の対象になります

        Args:
            file_paths: ファイルパスのリスト

        Returns:
            str: 結合されたテキスト

        Raises:
            Exception: 読み込みエラー
        """
        # PIIRemoverをインポート（循環参照を避けるため関数内でインポート）
        from src.pii_remover import PIIRemover

        all_content = []
        errors = []
        remover = PIIRemover()

        for file_path in file_paths:
            try:
                content, file_type = cls.read_file(file_path)
                file_name = Path(file_path).name

                # ファイル名からも個人情報を削除
                masked_file_name, _ = remover.clean_text(file_name)

                all_content.append(
                    f"{'='*60}\n"
                    f"ファイル: {masked_file_name} (種別: {file_type})\n"
                    f"{'='*60}\n"
                    f"{content}\n"
                )

            except Exception as e:
                # エラーメッセージのファイル名もマスク
                original_name = Path(file_path).name
                masked_name, _ = remover.clean_text(original_name)
                errors.append(f"❌ {masked_name}: {str(e)}")

        if errors:
            error_msg = "\n".join(errors)
            if not all_content:
                raise Exception(f"すべてのファイルの読み込みに失敗しました:\n{error_msg}")
            else:
                print(f"⚠️  一部のファイルの読み込みに失敗しました:\n{error_msg}")

        return "\n\n".join(all_content)


if __name__ == "__main__":
    # テスト用
    import sys

    reader = FileReader()

    if len(sys.argv) > 1:
        # コマンドライン引数からファイルパスを取得
        file_path = sys.argv[1]
        try:
            content, file_type = reader.read_file(file_path)
            print(f"=== {Path(file_path).name} ({file_type}) ===")
            print(content[:500])  # 最初の500文字を表示
            print(f"\n... (全{len(content)}文字)")
        except Exception as e:
            print(f"エラー: {e}")
    else:
        print("使い方: python file_reader.py <ファイルパス>")
