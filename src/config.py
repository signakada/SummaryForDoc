"""
設定管理モジュール
APIキーや設定値を管理します
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()


class Config:
    """アプリケーション設定クラス"""

    # APIキー
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # 使用するAIプロバイダー（anthropic または openai）
    AI_PROVIDER = os.getenv("AI_PROVIDER", "anthropic")

    # 使用するモデル
    AI_MODEL = os.getenv("AI_MODEL", "claude-3-5-haiku-20241022")

    # ディレクトリ設定
    BASE_DIR = Path(__file__).parent.parent
    OUTPUT_DIR = BASE_DIR / "output"
    TESTS_DIR = BASE_DIR / "tests"

    # 出力ディレクトリが存在しない場合は作成
    OUTPUT_DIR.mkdir(exist_ok=True)
    TESTS_DIR.mkdir(exist_ok=True)

    # ファイルサイズ制限（MB）
    MAX_FILE_SIZE_MB = 10

    # 対応ファイル形式
    SUPPORTED_TEXT_FORMATS = [".txt"]
    SUPPORTED_PDF_FORMATS = [".pdf"]
    SUPPORTED_IMAGE_FORMATS = [".jpg", ".jpeg", ".png"]

    @classmethod
    def get_all_supported_formats(cls):
        """すべての対応ファイル形式を取得"""
        return (
            cls.SUPPORTED_TEXT_FORMATS +
            cls.SUPPORTED_PDF_FORMATS +
            cls.SUPPORTED_IMAGE_FORMATS
        )

    @classmethod
    def is_api_key_configured(cls):
        """APIキーが設定されているか確認"""
        if cls.AI_PROVIDER == "anthropic":
            return bool(cls.ANTHROPIC_API_KEY)
        elif cls.AI_PROVIDER == "openai":
            return bool(cls.OPENAI_API_KEY)
        return False

    @classmethod
    def get_api_key(cls):
        """現在のプロバイダーのAPIキーを取得"""
        if cls.AI_PROVIDER == "anthropic":
            return cls.ANTHROPIC_API_KEY
        elif cls.AI_PROVIDER == "openai":
            return cls.OPENAI_API_KEY
        return None

    @classmethod
    def validate_config(cls):
        """設定の検証"""
        errors = []

        if not cls.is_api_key_configured():
            errors.append(
                f"APIキーが設定されていません。"
                f".envファイルに{cls.AI_PROVIDER.upper()}_API_KEYを設定してください。"
            )

        if cls.AI_PROVIDER not in ["anthropic", "openai"]:
            errors.append(
                f"AI_PROVIDERの値が不正です: {cls.AI_PROVIDER}"
                f"（anthropic または openai を指定してください）"
            )

        return errors


# 設定インスタンス
config = Config()


if __name__ == "__main__":
    # テスト用
    print("=== 設定情報 ===")
    print(f"AIプロバイダー: {config.AI_PROVIDER}")
    print(f"AIモデル: {config.AI_MODEL}")
    print(f"APIキー設定済み: {config.is_api_key_configured()}")
    print(f"出力ディレクトリ: {config.OUTPUT_DIR}")
    print(f"対応ファイル形式: {config.get_all_supported_formats()}")

    # 設定の検証
    errors = config.validate_config()
    if errors:
        print("\n=== 設定エラー ===")
        for error in errors:
            print(f"❌ {error}")
    else:
        print("\n✅ 設定は正常です")
