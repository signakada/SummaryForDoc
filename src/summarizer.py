"""
要約生成モジュール
AI API（Claude/OpenAI）を使って医療文書の要約を生成します
"""

from typing import Dict, Optional
from dataclasses import dataclass
from anthropic import Anthropic
from openai import OpenAI

from .config import config
from .prompts import PromptManager


@dataclass
class SummaryResult:
    """要約結果クラス"""
    history: Optional[str] = None  # 病歴（200-300文字）
    symptoms: Optional[str] = None  # 症状の詳細（200-300文字）
    full_summary: Optional[str] = None  # 全期間サマリー
    error: Optional[str] = None  # エラーメッセージ


class MedicalSummarizer:
    """医療文書要約クラス"""

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        初期化

        Args:
            provider: AIプロバイダー（anthropic or openai）
            model: 使用するモデル名
        """
        self.provider = provider or config.AI_PROVIDER
        self.model = model or config.AI_MODEL

        # APIクライアントの初期化
        if self.provider == "anthropic":
            self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        elif self.provider == "openai":
            self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        else:
            raise ValueError(f"サポートされていないプロバイダー: {self.provider}")

    def _call_anthropic_api(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        Anthropic Claude APIを呼び出す

        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数

        Returns:
            str: 生成されたテキスト
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return response.content[0].text

        except Exception as e:
            raise Exception(f"Claude API エラー: {str(e)}")

    def _call_openai_api(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        OpenAI GPT APIを呼び出す

        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数

        Returns:
            str: 生成されたテキスト
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"OpenAI API エラー: {str(e)}")

    def _call_api(self, prompt: str, max_tokens: int = 1024) -> str:
        """
        設定されたAPIを呼び出す

        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数

        Returns:
            str: 生成されたテキスト
        """
        if self.provider == "anthropic":
            return self._call_anthropic_api(prompt, max_tokens)
        elif self.provider == "openai":
            return self._call_openai_api(prompt, max_tokens)
        else:
            raise ValueError(f"サポートされていないプロバイダー: {self.provider}")

    def generate_summary(
        self,
        text: str,
        template_key: str = 'disability_pension',
        include_history: bool = True,
        include_symptoms: bool = True,
        include_full_summary: bool = True
    ) -> SummaryResult:
        """
        要約を生成

        Args:
            text: 個人情報削除済みの医療文書
            template_key: 使用するテンプレートのキー
            include_history: 病歴を生成するか
            include_symptoms: 症状の詳細を生成するか
            include_full_summary: 全期間サマリーを生成するか

        Returns:
            SummaryResult: 要約結果
        """
        result = SummaryResult()

        try:
            # テンプレートを取得
            template = PromptManager.get_template(template_key)

            # 病歴を生成
            if include_history:
                print("病歴を生成中...")
                prompt = PromptManager.format_prompt(template.history_prompt, text)
                result.history = self._call_api(prompt, max_tokens=600)
                print(f"✓ 病歴生成完了 ({len(result.history)}文字)")

            # 症状の詳細を生成
            if include_symptoms:
                print("症状の詳細を生成中...")
                prompt = PromptManager.format_prompt(template.symptoms_prompt, text)
                result.symptoms = self._call_api(prompt, max_tokens=600)
                print(f"✓ 症状の詳細生成完了 ({len(result.symptoms)}文字)")

            # 全期間サマリーを生成
            if include_full_summary:
                print("全期間サマリーを生成中...")
                prompt = PromptManager.format_prompt(template.summary_prompt, text)
                result.full_summary = self._call_api(prompt, max_tokens=2048)
                print(f"✓ 全期間サマリー生成完了 ({len(result.full_summary)}文字)")

        except Exception as e:
            result.error = str(e)
            print(f"❌ エラー: {e}")

        return result

    def save_results(self, result: SummaryResult, output_dir: str = None) -> Dict[str, str]:
        """
        要約結果をファイルに保存

        Args:
            result: 要約結果
            output_dir: 出力ディレクトリ

        Returns:
            Dict[str, str]: 保存したファイルのパス
        """
        from pathlib import Path
        from datetime import datetime

        if output_dir is None:
            output_dir = config.OUTPUT_DIR

        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)

        # タイムスタンプ
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        saved_files = {}

        # 病歴を保存
        if result.history:
            file_path = output_dir / f"病歴_{timestamp}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result.history)
            saved_files['history'] = str(file_path)

        # 症状の詳細を保存
        if result.symptoms:
            file_path = output_dir / f"症状の詳細_{timestamp}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result.symptoms)
            saved_files['symptoms'] = str(file_path)

        # 全期間サマリーを保存
        if result.full_summary:
            file_path = output_dir / f"全期間サマリー_{timestamp}.txt"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(result.full_summary)
            saved_files['full_summary'] = str(file_path)

        return saved_files


if __name__ == "__main__":
    # テスト用
    import sys

    # サンプルテキスト
    sample_text = """
診断名：統合失調症

【経過】
2020年4月頃より幻聴（命令性）と被害念慮が出現。
当初は自宅で様子観察していたが症状が悪化し、
同年6月15日に当院初診となった。

初診時所見：
・幻聴あり（1日に数回、命令的な内容）
・被害妄想あり（監視されている感覚）
・不眠、食欲低下
・身体的異常所見なし

治療経過：
2020年6月：リスペリドン2mg/日で治療開始
2020年8月：症状やや改善、リスペリドン3mg/日に増量
2020年10月：本人判断で服薬中断、症状再燃
2020年10月25日〜11月30日：入院治療
2021年1月〜現在：外来通院継続中

【現在の状態（2023年6月時点）】
・幻聴は軽減したが月に数回程度残存
・被害念慮はほぼ消失
・対人恐怖と意欲低下が主な問題
・服薬アドヒアランスは家族支援下で良好
"""

    print("=== 医療文書要約ツール - テスト ===\n")

    # APIキーの確認
    errors = config.validate_config()
    if errors:
        print("❌ 設定エラー:")
        for error in errors:
            print(f"  - {error}")
        print("\n.envファイルを確認してください。")
        sys.exit(1)

    print(f"使用するAI: {config.AI_PROVIDER} / {config.AI_MODEL}\n")

    # 要約生成
    summarizer = MedicalSummarizer()

    print("要約を生成中...\n")
    result = summarizer.generate_summary(
        sample_text,
        template_key='disability_pension',
        include_history=True,
        include_symptoms=True,
        include_full_summary=False  # テストなのでサマリーは省略
    )

    if result.error:
        print(f"\n❌ エラーが発生しました: {result.error}")
    else:
        print("\n" + "="*60)
        print("=== 病歴 ===")
        print("="*60)
        print(result.history)

        print("\n" + "="*60)
        print("=== 症状の詳細 ===")
        print("="*60)
        print(result.symptoms)

        # ファイルに保存
        print("\n保存中...")
        saved_files = summarizer.save_results(result)
        print("\n✓ 保存完了:")
        for key, path in saved_files.items():
            print(f"  - {path}")
