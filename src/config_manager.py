"""
設定ファイル管理モジュール
ユーザー設定を保存・読み込みします
"""

import json
from pathlib import Path
from typing import Optional, Dict, Any
import os


class ConfigManager:
    """設定ファイル管理クラス"""

    def __init__(self):
        """初期化"""
        # 設定ファイルの保存先を決定
        if os.name == 'nt':  # Windows
            config_dir = Path(os.environ.get('APPDATA', Path.home())) / 'SummaryForDoc'
        elif os.name == 'posix':  # macOS, Linux
            if 'darwin' in os.sys.platform:  # macOS
                config_dir = Path.home() / 'Library' / 'Application Support' / 'SummaryForDoc'
            else:  # Linux
                config_dir = Path.home() / '.config' / 'SummaryForDoc'
        else:
            # フォールバック
            config_dir = Path.home() / '.summaryfordoc'

        self.config_dir = config_dir
        self.config_file = config_dir / 'config.json'

        # ディレクトリが存在しない場合は作成
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """
        設定を保存

        Args:
            config_data: 設定データの辞書

        Returns:
            bool: 保存成功の場合True
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            # ファイルのパーミッションを設定（Unix系のみ）
            if os.name == 'posix':
                os.chmod(self.config_file, 0o600)  # 所有者のみ読み書き可能

            return True
        except Exception as e:
            print(f"設定の保存に失敗しました: {e}")
            return False

    def load_config(self) -> Optional[Dict[str, Any]]:
        """
        設定を読み込み

        Returns:
            Optional[Dict[str, Any]]: 設定データの辞書、ファイルが存在しない場合はNone
        """
        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            return config_data
        except Exception as e:
            print(f"設定の読み込みに失敗しました: {e}")
            return None

    def config_exists(self) -> bool:
        """
        設定ファイルが存在するか確認

        Returns:
            bool: 設定ファイルが存在する場合True
        """
        return self.config_file.exists()

    def get_anthropic_api_key(self) -> Optional[str]:
        """
        Anthropic APIキーを取得

        Returns:
            Optional[str]: APIキー、設定されていない場合はNone
        """
        config = self.load_config()
        if config:
            return config.get('anthropic_api_key')
        return None

    def get_openai_api_key(self) -> Optional[str]:
        """
        OpenAI APIキーを取得

        Returns:
            Optional[str]: APIキー、設定されていない場合はNone
        """
        config = self.load_config()
        if config:
            return config.get('openai_api_key')
        return None

    def get_api_key(self) -> Optional[str]:
        """
        現在のプロバイダーのAPIキーを取得（後方互換性のため）

        Returns:
            Optional[str]: APIキー、設定されていない場合はNone
        """
        return self.get_anthropic_api_key()

    def get_ai_provider(self) -> str:
        """
        AIプロバイダーを取得

        Returns:
            str: AIプロバイダー（デフォルト: anthropic）
        """
        config = self.load_config()
        if config:
            return config.get('ai_provider', 'anthropic')
        return 'anthropic'

    def get_ai_model(self) -> str:
        """
        AIモデルを取得

        Returns:
            str: AIモデル（デフォルト: claude-3-5-haiku-20241022）
        """
        config = self.load_config()
        if config:
            provider = self.get_ai_provider()
            if provider == 'openai':
                return config.get('ai_model', 'gpt-4o-mini')
            else:
                return config.get('ai_model', 'claude-3-5-haiku-20241022')
        return 'claude-3-5-haiku-20241022'

    def save_api_settings(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        ai_provider: str = 'anthropic',
        ai_model: Optional[str] = None
    ) -> bool:
        """
        API設定を保存

        Args:
            anthropic_api_key: Anthropic APIキー（Noneの場合は既存の値を保持）
            openai_api_key: OpenAI APIキー（Noneの場合は既存の値を保持）
            ai_provider: AIプロバイダー
            ai_model: AIモデル（Noneの場合はデフォルト値を使用）

        Returns:
            bool: 保存成功の場合True
        """
        # 既存の設定を読み込み
        config_data = self.load_config() or {}

        # APIキーを更新（Noneでない場合のみ）
        if anthropic_api_key is not None:
            config_data['anthropic_api_key'] = anthropic_api_key
        if openai_api_key is not None:
            config_data['openai_api_key'] = openai_api_key

        # プロバイダーとモデルを更新
        config_data['ai_provider'] = ai_provider

        # モデルの設定
        if ai_model:
            config_data['ai_model'] = ai_model
        else:
            # デフォルトモデルを設定
            if ai_provider == 'openai':
                config_data['ai_model'] = 'gpt-4o-mini'
            else:
                config_data['ai_model'] = 'claude-3-5-haiku-20241022'

        return self.save_config(config_data)

    def get_custom_prompts(self) -> Dict[str, Dict[str, str]]:
        """
        カスタムプロンプトを取得

        Returns:
            Dict[str, Dict[str, str]]: カスタムプロンプトの辞書
        """
        config = self.load_config()
        if config:
            return config.get('custom_prompts', {})
        return {}

    def save_custom_prompt(
        self,
        key: str,
        name: str,
        history_prompt: str,
        symptoms_prompt: str,
        summary_prompt: str
    ) -> bool:
        """
        カスタムプロンプトを保存

        Args:
            key: プロンプトのキー（一意の識別子）
            name: プロンプトの表示名
            history_prompt: 病歴用プロンプト
            symptoms_prompt: 症状用プロンプト
            summary_prompt: サマリー用プロンプト

        Returns:
            bool: 保存成功の場合True
        """
        config_data = self.load_config() or {}

        # カスタムプロンプトがない場合は初期化
        if 'custom_prompts' not in config_data:
            config_data['custom_prompts'] = {}

        # プロンプトを保存
        config_data['custom_prompts'][key] = {
            'name': name,
            'history_prompt': history_prompt,
            'symptoms_prompt': symptoms_prompt,
            'summary_prompt': summary_prompt
        }

        return self.save_config(config_data)

    def delete_custom_prompt(self, key: str) -> bool:
        """
        カスタムプロンプトを削除

        Args:
            key: プロンプトのキー

        Returns:
            bool: 削除成功の場合True
        """
        config_data = self.load_config() or {}

        if 'custom_prompts' in config_data and key in config_data['custom_prompts']:
            del config_data['custom_prompts'][key]
            return self.save_config(config_data)

        return False

    def delete_config(self) -> bool:
        """
        設定ファイルを削除

        Returns:
            bool: 削除成功の場合True
        """
        try:
            if self.config_file.exists():
                self.config_file.unlink()
            return True
        except Exception as e:
            print(f"設定の削除に失敗しました: {e}")
            return False


if __name__ == "__main__":
    # テスト用
    manager = ConfigManager()
    print(f"設定ファイルパス: {manager.config_file}")
    print(f"設定ファイル存在: {manager.config_exists()}")

    if manager.config_exists():
        print(f"AIプロバイダー: {manager.get_ai_provider()}")
        print(f"AIモデル: {manager.get_ai_model()}")
        print(f"APIキー設定済み: {bool(manager.get_api_key())}")
