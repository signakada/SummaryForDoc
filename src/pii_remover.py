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
        # スペースを含む姓名に対応（例：山本　百花、田中 太郎）
        pattern3 = r'(?:患者)?氏名[：:\s]*([一-龯ァ-ヴー]{1,5}[\s　]+[一-龯ァ-ヴー]{1,5}|[一-龯ァ-ヴー]{2,10})(?=\s|$|\n|/)'

        # パターン4: ファイル名などで患者番号の後にアンダースコアで区切られた氏名
        # 例: _山本　百花_ のようなパターン（患者番号は既に削除されている想定）
        pattern4 = r'_([一-龯ァ-ヴー]{1,5}[\s　]+[一-龯ァ-ヴー]{1,5}|[一-龯ァ-ヴー]{2,10})_'

        # パターン5: [患者番号]や[ID]の直後にある氏名
        # 例: [患者番号]山本　百花_ のようなパターン
        pattern5 = r'\[(?:患者番号|ID)\]([一-龯ァ-ヴー]{1,5}[\s　]+[一-龯ァ-ヴー]{1,5}|[一-龯ァ-ヴー]{2,10})_'

        # パターン6: 数字の直後にある氏名（スペース付き姓名のみ、誤検知防止）
        # 例: ６２２山本　太郎 のようなパターン
        pattern6 = r'\d+([一-龯]{1,5}[\s　]+[一-龯]{1,5})(?=\s|$|\n)'

        # 医療用語をチェック
        def is_medical_term(match_text: str) -> bool:
            for term in self.MEDICAL_TERMS:
                if term in match_text:
                    return True
            return False

        # パターン3（明示的な氏名記載）を優先して置換
        def replace_explicit_name(match):
            name = match.group(1).strip()
            if not is_medical_term(name) and len(name.replace(' ', '').replace('　', '')) >= 2:
                self.replacement_log.append(('氏名', name))
                return match.group(0).replace(name, '[氏名]')
            return match.group(0)

        protected_text = re.sub(pattern3, replace_explicit_name, protected_text)

        # パターン4（ファイル名のアンダースコア区切り氏名）を置換
        def replace_filename_name(match):
            name = match.group(1).strip()
            if not is_medical_term(name) and len(name.replace(' ', '').replace('　', '')) >= 2:
                self.replacement_log.append(('氏名', name))
                return '_[氏名]_'
            return match.group(0)

        protected_text = re.sub(pattern4, replace_filename_name, protected_text)

        # パターン5（[患者番号]の直後の氏名）を置換
        def replace_after_id_name(match):
            name = match.group(1).strip()
            if not is_medical_term(name) and len(name.replace(' ', '').replace('　', '')) >= 2:
                self.replacement_log.append(('氏名', name))
                # [患者番号]や[ID]の部分を保持して、氏名だけ[氏名]に置換
                return match.group(0).replace(name, '[氏名]')
            return match.group(0)

        protected_text = re.sub(pattern5, replace_after_id_name, protected_text)

        # パターン6（数字の直後の氏名）を置換
        def replace_after_number_name(match):
            name = match.group(1).strip()
            # スペースを含む姓名のみ（誤検知防止）
            if not is_medical_term(name) and len(name.replace(' ', '').replace('　', '')) >= 2:
                self.replacement_log.append(('氏名', name))
                # 数字の部分は保持して、氏名だけ[氏名]に置換
                return match.group(0).replace(name, '[氏名]')
            return match.group(0)

        protected_text = re.sub(pattern6, replace_after_number_name, protected_text)

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
        病歴の日付（月日のみ、年のみ）は保護します

        Args:
            text: 元のテキスト

        Returns:
            str: 生年月日を削除したテキスト
        """
        result = text

        # パターン1: 「生年月日：」の後ろ（最優先）
        def replace_explicit_birthdate(match):
            self.replacement_log.append(('生年月日', match.group(0)))
            return '生年月日：[生年月日]'
        result = re.sub(r'生年月日[：:\s]*([\d年月日明大昭平令和MTSHR\.\/\-\(\)]{6,})', replace_explicit_birthdate, result)

        # パターン2: 西暦+和暦の複合形式（生年月日の可能性が極めて高い）
        # 2003(H15)/10/19、1985(S60)/3/9
        def replace_complex_date(match):
            self.replacement_log.append(('生年月日', match.group(0)))
            return '[生年月日]'
        result = re.sub(r'\d{4}\([MTSHR]\d{1,3}\)[/\-\.]\d{1,2}[/\-\.]\d{1,2}', replace_complex_date, result)

        # パターン3: 西暦4桁+月+日の完全な日付（生年月日の可能性が高い）
        # ただし、病歴の記述（平成○年、令和○年など）を誤検知しないように年月日が揃っているもののみ
        # 1985年3月9日、1985/3/9、1985-3-9
        def replace_full_date(match):
            matched = match.group(0)
            # 1900年代〜2020年代の範囲に限定（生年月日として妥当な範囲）
            year_match = re.match(r'(19\d{2}|20[0-2]\d)', matched)
            if year_match:
                self.replacement_log.append(('生年月日', matched))
                return '[生年月日]'
            return matched
        result = re.sub(r'\d{4}[年/\-\.]\d{1,2}[月/\-\.]\d{1,2}日?', replace_full_date, result)

        # パターン4: 和暦の完全な日付（年月日がすべて揃っているもの）
        # 昭和60年3月9日、S60.3.9、S60/3/9
        def replace_japanese_era_date(match):
            self.replacement_log.append(('生年月日', match.group(0)))
            return '[生年月日]'
        result = re.sub(r'[明大昭平令和]{1,2}\d{1,3}[年\.]\d{1,2}[月\.]\d{1,2}日?', replace_japanese_era_date, result)
        result = re.sub(r'[MTSHR]\d{1,3}[\.\/]\d{1,2}[\.\/]\d{1,2}', replace_japanese_era_date, result)

        return result

    def remove_addresses(self, text: str) -> str:
        """
        住所を削除

        Args:
            text: 元のテキスト

        Returns:
            str: 住所を削除したテキスト
        """
        result = text

        # パターン1: 〒123-4567（郵便番号）
        def replace_postal_code(match):
            self.replacement_log.append(('郵便番号', match.group(0)))
            return '[郵便番号]'
        result = re.sub(r'〒?\d{3}-?\d{4}', replace_postal_code, result)

        # パターン2: 住所：〇〇（明示的な住所表記を先に処理）
        def replace_explicit_address(match):
            full_match = match.group(0)
            # すでに[住所]が含まれていないかチェック
            if '[住所]' not in full_match and '[郵便番号]' not in full_match:
                self.replacement_log.append(('住所', full_match))
                return '住所：[住所]'
            return full_match
        result = re.sub(r'住所[：:\s]*[^\n]+', replace_explicit_address, result)

        # パターン3: 東京都渋谷区〇〇1-2-3（都道府県で始まる住所パターン）
        def replace_prefecture_address(match):
            matched = match.group(0)
            # すでにマスク済みでないかチェック
            if '[住所]' not in matched and '[郵便番号]' not in matched:
                self.replacement_log.append(('住所', matched))
                return '[住所]'
            return matched
        result = re.sub(r'[東京大阪京都北海道青森岩手宮城秋田山形福島茨城栃木群馬埼玉千葉神奈川新潟富山石川福井山梨長野岐阜静岡愛知三重滋賀兵庫奈良和歌山鳥取島根岡山広島山口徳島香川愛媛高知福岡佐賀長崎熊本大分宮崎鹿児島沖縄][都道府県]{0,1}[一-龯ぁ-んァ-ヴー]+[市区町村郡]{1}[一-龯ぁ-んァ-ヴー0-9\-ー]+', replace_prefecture_address, result)

        return result

    def remove_phone_numbers(self, text: str) -> str:
        """
        電話番号を削除

        Args:
            text: 元のテキスト

        Returns:
            str: 電話番号を削除したテキスト
        """
        # 順番に処理（より具体的なパターンから）
        result = text

        # パターン1: (03) 1234-5678 形式
        def replace_with_parens(match):
            self.replacement_log.append(('電話番号', match.group(0)))
            return '[電話番号]'
        result = re.sub(r'\(\d{2,4}\)\s*\d{2,4}-\d{4}', replace_with_parens, result)

        # パターン2: 03-1234-5678、090-1234-5678 形式
        def replace_with_hyphens(match):
            matched = match.group(0)
            # 年月日（2023-04-15など）と誤認しないようにチェック
            if re.match(r'\d{4}-\d{1,2}-\d{1,2}', matched):
                return matched  # 日付なので置換しない
            # 郵便番号(123-4567)との区別
            if re.match(r'\d{3}-\d{4}', matched):
                return matched  # 郵便番号パターンなので置換しない

            self.replacement_log.append(('電話番号', matched))
            return '[電話番号]'
        result = re.sub(r'\d{2,4}-\d{3,4}-\d{4}', replace_with_hyphens, result)

        # パターン3: 0312345678、09012345678 形式（ハイフンなし）
        # より厳格に：先頭が0で始まる10-11桁の数字のみ
        def replace_no_hyphens(match):
            matched = match.group(0)
            # 年（2023など）と誤認しないよう、先頭が0であることを確認
            if not matched.startswith('0'):
                return matched

            self.replacement_log.append(('電話番号', matched))
            return '[電話番号]'
        result = re.sub(r'\b0\d{9,10}\b', replace_no_hyphens, result)

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
            # 明示的なID表記
            (r'(?:診察券|患者ID|患者番号|カルテ番号)[：:\s]*[\w\-]+', 'ID'),
            (r'ID[：:\s]*[\w\-]+', 'ID'),
            # 患者番号: 240065 のような形式
            (r'患者番号[：:\s]*\d{4,8}', 'ID'),
            # ファイル名などの患者番号（6桁前後の数字 + アンダースコア）
            # 例: 240065_ のようなパターン（単語境界で囲まれている場合）
            (r'\b\d{4,8}_', '患者番号'),
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

        # 順番に削除処理を実行（誤検知を防ぐため、より具体的なパターンから）
        result = self.remove_birthdates(result)    # 生年月日
        result = self.remove_phone_numbers(result) # 電話番号 - 郵便番号より先に
        result = self.remove_addresses(result)     # 住所（郵便番号含む）
        result = self.remove_medical_ids(result)   # ID情報
        result = self.remove_names(result)         # 氏名は最後

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
