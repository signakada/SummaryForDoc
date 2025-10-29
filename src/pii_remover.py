"""
個人情報削除モジュール
医療文書から個人情報（氏名、生年月日、住所、電話番号など）を削除します
"""

import re
from typing import List, Tuple, Dict


class PIIRemover:
    """個人情報削除クラス"""

    # 保護対象の医療用語（誤検知を防ぐ）
    MEDICAL_TERMS = [
        # 病名・症状
        '統合失調症', '双極性障害', 'うつ病', '不安障害', '適応障害',
        '認知症', 'てんかん', 'パーキンソン病', '糖尿病', '高血圧',
        '脂質異常症', '気管支喘息', '慢性閉塞性肺疾患', '心不全',
        '狭心症', '心筋梗塞', '脳梗塞', '脳出血', 'くも膜下出血',
        '頭痛', '発熱', '咳嗽', '呼吸困難', '胸痛', '腹痛',
        '幻聴', '妄想', '幻覚', '被害念慮', '抑うつ', '不安',
        # 薬剤名
        'リスペリドン', 'オランザピン', 'クエチアピン', 'アリピプラゾール',
        'パリペリドン', 'ハロペリドール', 'レボメプロマジン',
        'リチウム', 'バルプロ酸', 'カルバマゼピン', 'ラモトリギン',
        'フルボキサミン', 'パロキセチン', 'セルトラリン', 'エスシタロプラム',
        'デュロキセチン', 'ミルタザピン', 'ボルチオキセチン',
        'ロラゼパム', 'クロナゼパム', 'ジアゼパム', 'エチゾラム',
        # その他
        '医師', '看護師', '薬剤師', '患者', '家族', '母', '父',
    ]

    def __init__(self):
        """初期化"""
        self.replacement_log = []  # 置換ログ

    def remove_names(self, text: str) -> str:
        """
        氏名を削除
        日本人の氏名パターンを検出して [氏名] に置換

        Args:
            text: 元のテキスト

        Returns:
            str: 氏名を削除したテキスト
        """
        # 医療用語は保護
        protected_text = text

        # パターン1: 漢字の姓名（2-4文字の姓 + 2-3文字の名）
        # 例: 田中太郎、佐藤花子
        pattern1 = r'(?<![一-龯])[一-龯]{2,4}(?:\s*)[一-龯]{2,3}(?![一-龯])'

        # パターン2: カタカナの姓名
        # 例: タナカタロウ、サトウハナコ
        pattern2 = r'[ァ-ヴー]{2,10}'

        # パターン3: 「患者氏名：〇〇」「氏名：〇〇」などの明示的な記載
        pattern3 = r'(?:患者)?氏名[：:\s]*([一-龯ァ-ヴー\s]{2,10})'

        # 医療用語をチェック
        def is_medical_term(match_text: str) -> bool:
            for term in self.MEDICAL_TERMS:
                if term in match_text:
                    return True
            return False

        # パターン3（明示的な氏名記載）を優先して置換
        def replace_explicit_name(match):
            name = match.group(1).strip()
            if not is_medical_term(name):
                self.replacement_log.append(('氏名', name))
                return match.group(0).replace(name, '[氏名]')
            return match.group(0)

        protected_text = re.sub(pattern3, replace_explicit_name, protected_text)

        # パターン1（漢字の姓名）を置換
        def replace_kanji_name(match):
            name = match.group(0)
            if not is_medical_term(name) and len(name) >= 4:
                self.replacement_log.append(('氏名', name))
                return '[氏名]'
            return name

        # より慎重に置換（誤検知を減らす）
        # protected_text = re.sub(pattern1, replace_kanji_name, protected_text)

        return protected_text

    def remove_birthdates(self, text: str) -> str:
        """
        生年月日を削除

        Args:
            text: 元のテキスト

        Returns:
            str: 生年月日を削除したテキスト
        """
        patterns = [
            # 1985年3月9日、1985/3/9、1985-3-9
            (r'\d{4}[年/\-]\d{1,2}[月/\-]\d{1,2}日?', '生年月日'),
            # 昭和60年3月9日、S60.3.9、S60/3/9
            (r'[明大昭平令和]{1,2}\d{1,3}[年\.]\d{1,2}[月\.]\d{1,2}日?', '生年月日'),
            (r'[MTSHR]\d{1,3}[\.\/]\d{1,2}[\.\/]\d{1,2}', '生年月日'),
            # 生年月日：の後ろ
            (r'生年月日[：:\s]*[\d年月日明大昭平令和MTSHR\.\/\-]{6,}', '生年月日'),
        ]

        result = text
        for pattern, label in patterns:
            def replace_with_log(match):
                self.replacement_log.append((label, match.group(0)))
                return '[生年月日]'

            result = re.sub(pattern, replace_with_log, result)

        return result

    def remove_addresses(self, text: str) -> str:
        """
        住所を削除

        Args:
            text: 元のテキスト

        Returns:
            str: 住所を削除したテキスト
        """
        patterns = [
            # 〒123-4567
            (r'〒?\d{3}-?\d{4}', '郵便番号'),
            # 東京都渋谷区〇〇1-2-3
            (r'[都道府県]{1}[一-龯ぁ-んァ-ヴー]+[市区町村郡]{1}[一-龯ぁ-んァ-ヴー0-9\-ー]+', '住所'),
            # 住所：の後ろ
            (r'住所[：:\s]*[^\n]{5,50}', '住所'),
        ]

        result = text
        for pattern, label in patterns:
            def replace_with_log(match):
                self.replacement_log.append((label, match.group(0)))
                return f'[{label}]'

            result = re.sub(pattern, replace_with_log, result)

        return result

    def remove_phone_numbers(self, text: str) -> str:
        """
        電話番号を削除

        Args:
            text: 元のテキスト

        Returns:
            str: 電話番号を削除したテキスト
        """
        patterns = [
            # 03-1234-5678、090-1234-5678
            r'\d{2,4}-\d{2,4}-\d{4}',
            # 0312345678、09012345678
            r'\d{10,11}',
            # (03) 1234-5678
            r'\(\d{2,4}\)\s*\d{2,4}-\d{4}',
        ]

        result = text
        for pattern in patterns:
            def replace_with_log(match):
                # 日付（2023-04-15など）と誤認しないようにチェック
                matched = match.group(0)
                # ハイフンで区切られていて、最初が1-2桁なら日付の可能性
                if re.match(r'\d{1,2}-\d{1,2}-\d{1,2}', matched):
                    return matched  # 日付なので置換しない

                self.replacement_log.append(('電話番号', matched))
                return '[電話番号]'

            result = re.sub(pattern, replace_with_log, result)

        return result

    def remove_medical_ids(self, text: str) -> str:
        """
        診察券番号・患者IDを削除

        Args:
            text: 元のテキスト

        Returns:
            str: ID情報を削除したテキスト
        """
        patterns = [
            (r'(?:診察券|患者ID|カルテ番号)[：:\s]*[\w\-]+', 'ID'),
            (r'ID[：:\s]*[\w\-]+', 'ID'),
        ]

        result = text
        for pattern, label in patterns:
            def replace_with_log(match):
                self.replacement_log.append((label, match.group(0)))
                return f'[{label}]'

            result = re.sub(pattern, replace_with_log, result)

        return result

    def clean_text(self, text: str) -> Tuple[str, List[Tuple[str, str]]]:
        """
        すべての個人情報を削除

        Args:
            text: 元のテキスト

        Returns:
            Tuple[str, List[Tuple[str, str]]]:
                (個人情報を削除したテキスト, 置換ログ)
        """
        self.replacement_log = []  # ログをリセット

        result = text

        # 順番に削除処理を実行
        result = self.remove_birthdates(result)
        result = self.remove_addresses(result)
        result = self.remove_phone_numbers(result)
        result = self.remove_medical_ids(result)
        result = self.remove_names(result)  # 氏名は最後（他の削除で文脈が減る）

        return result, self.replacement_log

    def get_summary_report(self) -> str:
        """
        削除サマリーレポートを生成

        Returns:
            str: レポート
        """
        if not self.replacement_log:
            return "個人情報は検出されませんでした。"

        report_lines = ["=== 削除した個人情報 ==="]

        # カテゴリごとに集計
        categories: Dict[str, List[str]] = {}
        for category, value in self.replacement_log:
            if category not in categories:
                categories[category] = []
            categories[category].append(value)

        for category, values in categories.items():
            report_lines.append(f"\n{category}: {len(values)}件")
            for i, value in enumerate(values[:3], 1):  # 最初の3件のみ表示
                report_lines.append(f"  {i}. {value}")
            if len(values) > 3:
                report_lines.append(f"  ... 他 {len(values) - 3}件")

        return "\n".join(report_lines)


if __name__ == "__main__":
    # テスト用
    sample_text = """
    患者氏名：田中太郎
    生年月日：1975年3月9日
    住所：東京都渋谷区神南1-2-3
    電話番号：03-1234-5678
    診察券番号：123456

    診断名：統合失調症
    2020年4月頃より幻聴と被害念慮が出現。
    リスペリドン3mg/日で治療中。
    """

    remover = PIIRemover()
    cleaned_text, log = remover.clean_text(sample_text)

    print("=== 元のテキスト ===")
    print(sample_text)
    print("\n=== 個人情報削除後 ===")
    print(cleaned_text)
    print("\n" + remover.get_summary_report())
