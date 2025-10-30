"""
設定管理モジュール
APIキーや設定値を管理します
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from src.config_manager import ConfigManager

# .envファイルを読み込み（後方互換性のため）
load_dotenv()

# 設定マネージャーを初期化
_config_manager = ConfigManager()


class Config:
    """アプリケーション設定クラス"""

    # ConfigManagerから設定を読み込み、なければ環境変数から読み込み（後方互換性）
    _user_config = _config_manager.load_config()

    # APIキー
    ANTHROPIC_API_KEY = (
        _user_config.get("anthropic_api_key") if _user_config
        else os.getenv("ANTHROPIC_API_KEY")
    )
    OPENAI_API_KEY = (
        _user_config.get("openai_api_key") if _user_config
        else os.getenv("OPENAI_API_KEY")
    )

    # 使用するAIプロバイダー（anthropic または openai）
    AI_PROVIDER = (
        _user_config.get("ai_provider") if _user_config
        else os.getenv("AI_PROVIDER", "anthropic")
    )

    # 使用するモデル
    AI_MODEL = (
        _user_config.get("ai_model") if _user_config
        else os.getenv("AI_MODEL", "claude-3-5-haiku-20241022")
    )

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
    def reload_config(cls):
        """設定を再読み込み"""
        cls._user_config = _config_manager.load_config()

        # APIキー
        cls.ANTHROPIC_API_KEY = (
            cls._user_config.get("anthropic_api_key") if cls._user_config
            else os.getenv("ANTHROPIC_API_KEY")
        )
        cls.OPENAI_API_KEY = (
            cls._user_config.get("openai_api_key") if cls._user_config
            else os.getenv("OPENAI_API_KEY")
        )

        # AIプロバイダー
        cls.AI_PROVIDER = (
            cls._user_config.get("ai_provider") if cls._user_config
            else os.getenv("AI_PROVIDER", "anthropic")
        )

        # AIモデル
        cls.AI_MODEL = (
            cls._user_config.get("ai_model") if cls._user_config
            else os.getenv("AI_MODEL", "claude-3-5-haiku-20241022")
        )

    @classmethod
    def validate_config(cls):
        """設定の検証"""
        errors = []

        if not cls.is_api_key_configured():
            errors.append(
                f"APIキーが設定されていません。"
            )

        if cls.AI_PROVIDER not in ["anthropic", "openai"]:
            errors.append(
                f"AI_PROVIDERの値が不正です: {cls.AI_PROVIDER}"
                f"（anthropic または openai を指定してください）"
            )

        return errors

    @classmethod
    def get_config_manager(cls):
        """ConfigManagerインスタンスを取得"""
        return _config_manager


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
