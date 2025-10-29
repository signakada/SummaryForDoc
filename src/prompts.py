"""
プロンプトテンプレート管理モジュール
各種診断書や申請書用のプロンプトを管理します
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class PromptTemplate:
    """プロンプトテンプレートクラス"""
    name: str  # テンプレート名
    description: str  # 説明
    history_prompt: str  # 病歴用プロンプト
    symptoms_prompt: str  # 症状の詳細用プロンプト
    summary_prompt: str  # 全期間サマリー用プロンプト


class PromptManager:
    """プロンプト管理クラス"""

    # テンプレート定義
    TEMPLATES: Dict[str, PromptTemplate] = {}

    @classmethod
    def initialize_templates(cls):
        """テンプレートを初期化"""

        # 1. 障害年金診断書（標準）
        cls.TEMPLATES['disability_pension'] = PromptTemplate(
            name='障害年金診断書（標準）',
            description='障害年金申請用の診断書に記載する内容',
            history_prompt="""以下は個人情報を削除した医療文書です。
障害年金診断書の「病歴」欄に記載する内容を200-300文字で作成してください。

必ず含める項目:
- 診断名（正式名称）
- 発症時期（いつから症状が始まったか）
- 初診時期（いつ初めて受診したか）
- 治療経過（どんな治療をしてきたか）
- 入院歴があれば時期と期間

文体: 簡潔な医学的記述（である調）
文字数: 200-300文字厳守

【医療文書】
{text}

【出力】
診断名から始めて、時系列順に簡潔に記載してください。""",

            symptoms_prompt="""以下は個人情報を削除した医療文書です。
障害年金診断書の「症状の詳細」欄に記載する内容を200-300文字で作成してください。

必ず含める項目:
- 現在の主要な症状（具体的に）
- 症状の頻度や程度
- 日常生活への影響（ADL）
- 就労能力への影響
- 必要な支援や見守りの内容

文体: 簡潔な医学的記述（である調）
文字数: 200-300文字厳守

【医療文書】
{text}

【出力】
現在の状態を中心に、具体的な影響を記載してください。""",

            summary_prompt="""以下は個人情報を削除した医療文書です。
全期間の経過を詳しくまとめてください。

以下の構成で記載:
1. 診断名
2. 発症と初診の経緯
3. 治療経過（時系列で詳細に）
   - 薬物療法の内容と変更
   - 入院治療があれば詳細
   - 検査結果
4. 現在の状態
   - 症状
   - 日常生活状況
   - 就労状況
5. 今後の治療方針

文体: 詳細な医学的記述
文字数: 制限なし（詳しく書く）

【医療文書】
{text}

【出力】
見出しをつけて、時系列順に詳しく記載してください。"""
        )

        # 2. 精神障害者保健福祉手帳
        cls.TEMPLATES['mental_health_handbook'] = PromptTemplate(
            name='精神障害者保健福祉手帳',
            description='精神障害者保健福祉手帳申請用',
            history_prompt="""以下は個人情報を削除した医療文書です。
精神障害者保健福祉手帳申請用の「病歴」を200-300文字で作成してください。

必ず含める項目:
- 診断名
- 発症時期
- 初診と治療開始時期
- 病状の経過（安定/変動/悪化の傾向）
- 主な治療内容

文体: 簡潔な医学的記述
文字数: 200-300文字

【医療文書】
{text}

【出力】""",

            symptoms_prompt="""以下は個人情報を削除した医療文書です。
精神障害者保健福祉手帳申請用の「現在の症状」を200-300文字で作成してください。

必ず含める項目:
- 主要な精神症状
- 日常生活の制限（家事、外出、対人関係など）
- 単独での生活の可否
- 援助の必要性

文体: 簡潔な医学的記述
文字数: 200-300文字

【医療文書】
{text}

【出力】""",

            summary_prompt=cls.TEMPLATES['disability_pension'].summary_prompt
        )

        # 3. 自立支援医療
        cls.TEMPLATES['self_support_medical'] = PromptTemplate(
            name='自立支援医療',
            description='自立支援医療申請用',
            history_prompt="""以下は個人情報を削除した医療文書です。
自立支援医療申請用の「病歴」を200-300文字で作成してください。

必ず含める項目:
- 診断名
- 発症時期と初診時期
- これまでの治療経過（簡潔に）
- 現在の治療内容

文字数: 200-300文字

【医療文書】
{text}

【出力】""",

            symptoms_prompt="""以下は個人情報を削除した医療文書です。
自立支援医療申請用の「症状と治療の必要性」を200-300文字で作成してください。

必ず含める項目:
- 現在の主要な症状
- 症状による生活への支障
- 継続治療の必要性とその理由
- 治療を中断した場合のリスク

文字数: 200-300文字

【医療文書】
{text}

【出力】""",

            summary_prompt=cls.TEMPLATES['disability_pension'].summary_prompt
        )

    @classmethod
    def get_template(cls, template_key: str) -> PromptTemplate:
        """
        テンプレートを取得

        Args:
            template_key: テンプレートのキー

        Returns:
            PromptTemplate: テンプレート

        Raises:
            KeyError: 存在しないキー
        """
        if not cls.TEMPLATES:
            cls.initialize_templates()

        if template_key not in cls.TEMPLATES:
            raise KeyError(
                f"テンプレート '{template_key}' が見つかりません。\n"
                f"利用可能なテンプレート: {list(cls.TEMPLATES.keys())}"
            )

        return cls.TEMPLATES[template_key]

    @classmethod
    def get_all_templates(cls) -> Dict[str, PromptTemplate]:
        """すべてのテンプレートを取得"""
        if not cls.TEMPLATES:
            cls.initialize_templates()
        return cls.TEMPLATES

    @classmethod
    def get_template_names(cls) -> List[str]:
        """テンプレート名のリストを取得"""
        if not cls.TEMPLATES:
            cls.initialize_templates()
        return [template.name for template in cls.TEMPLATES.values()]

    @classmethod
    def create_custom_template(
        cls,
        key: str,
        name: str,
        description: str,
        history_prompt: str,
        symptoms_prompt: str,
        summary_prompt: str
    ) -> PromptTemplate:
        """
        カスタムテンプレートを作成

        Args:
            key: テンプレートのキー
            name: テンプレート名
            description: 説明
            history_prompt: 病歴用プロンプト
            symptoms_prompt: 症状用プロンプト
            summary_prompt: サマリー用プロンプト

        Returns:
            PromptTemplate: 作成されたテンプレート
        """
        template = PromptTemplate(
            name=name,
            description=description,
            history_prompt=history_prompt,
            symptoms_prompt=symptoms_prompt,
            summary_prompt=summary_prompt
        )

        cls.TEMPLATES[key] = template
        return template

    @classmethod
    def format_prompt(cls, prompt_template: str, text: str) -> str:
        """
        プロンプトに医療文書を埋め込む

        Args:
            prompt_template: プロンプトテンプレート
            text: 医療文書

        Returns:
            str: 完成したプロンプト
        """
        return prompt_template.format(text=text)


# 初期化
PromptManager.initialize_templates()


if __name__ == "__main__":
    # テスト用
    print("=== 利用可能なテンプレート ===")
    for key, template in PromptManager.get_all_templates().items():
        print(f"\n[{key}]")
        print(f"名前: {template.name}")
        print(f"説明: {template.description}")

    print("\n\n=== テンプレート使用例 ===")
    template = PromptManager.get_template('disability_pension')
    sample_text = "統合失調症。2020年4月頃より幻聴が出現..."

    print("\n--- 病歴プロンプト ---")
    print(PromptManager.format_prompt(template.history_prompt, sample_text))
