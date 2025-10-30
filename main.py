"""
医療文書要約ツール - メインGUIアプリ (Flet)
Mac・Windows・Linux対応
"""

import flet as ft
from pathlib import Path
from typing import List
import subprocess
import platform

try:
    import flet_dropzone as ftd
    DROPZONE_AVAILABLE = True
except ImportError:
    DROPZONE_AVAILABLE = False
    print("⚠️  flet-dropzone が利用できません。ビルド版では動作します。")

from src.config import config
from src.file_reader import FileReader
from src.pii_remover import PIIRemover
from src.summarizer import MedicalSummarizer
from src.prompts import PromptManager


class MedicalSummarizerApp:
    """医療文書要約ツール GUIアプリ"""

    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "医療文書要約ツール"
        self.page.window.width = 900
        self.page.window.height = 700
        self.page.padding = 20
        self.page.scroll = ft.ScrollMode.AUTO

        # 状態管理
        self.selected_files: List[Path] = []
        self.cleaned_text = ""
        self.summary_result = None
        self.pii_log = []
        self.confirmation_mode = True   # 確認モード（デフォルトON）

        # コンポーネント
        self.file_list = None
        self.history_checkbox = None
        self.symptoms_checkbox = None
        self.summary_checkbox = None
        self.template_dropdown = None
        self.process_button = None
        self.result_container = None
        self.status_text = None
        self.masked_text_field = None  # 編集可能なテキストフィールド
        self.confirm_button = None      # 確認完了ボタン
        self.search_field = None        # 検索フィールド
        self.search_results = []        # 検索結果のリスト
        self.current_search_index = 0   # 現在の検索結果インデックス
        self.search_result_text = None  # 検索結果表示テキスト
        self.confirmation_toggle = None # 確認モードトグル
        self.create_summary_button = None # 要約作成ボタン（確認モード用）

        # 初期化
        self._check_config()
        self._build_ui()

    def _check_config(self):
        """設定をチェック"""
        errors = config.validate_config()
        if errors:
            # エラーダイアログを表示
            def close_dialog(e):
                self.page.window.destroy()

            dialog = ft.AlertDialog(
                title=ft.Text("設定エラー"),
                content=ft.Text("\n".join(errors) + "\n\n.envファイルを確認してください。"),
                actions=[
                    ft.TextButton("閉じる", on_click=close_dialog)
                ]
            )
            self.page.overlay.append(dialog)
            dialog.open = True

    def _build_ui(self):
        """UIを構築"""

        # タイトル
        title = ft.Text(
            "医療文書要約ツール",
            size=28,
            weight=ft.FontWeight.BOLD,
            color="#1976d2"  # BLUE_700
        )

        # ファイル選択エリア
        def open_file_picker(e):
            print("ファイル選択ボタンがクリックされました")  # デバッグ
            try:
                file_paths = []

                # macOSの場合はosascriptを使用
                if platform.system() == "Darwin":
                    applescript = '''
                    tell application "System Events"
                        activate
                        set fileList to choose file with prompt "ファイルを選択してください（txt, pdf, jpg, png）" of type {"txt", "pdf", "public.image"} with multiple selections allowed
                        set filePaths to {}
                        repeat with aFile in fileList
                            set end of filePaths to POSIX path of aFile
                        end repeat
                        return filePaths
                    end tell
                    '''

                    result = subprocess.run(
                        ['osascript', '-e', applescript],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )

                    if result.returncode == 0 and result.stdout.strip():
                        # 結果を解析（カンマ区切りのパス）
                        output = result.stdout.strip()
                        if output:
                            # "path1, path2, path3"の形式を分割
                            file_paths = [p.strip() for p in output.split(',')]
                    else:
                        print("ファイル選択がキャンセルされました")
                        return
                else:
                    # Windows/Linuxの場合のフォールバック
                    self.page.show_snack_bar(
                        ft.SnackBar(content=ft.Text("このプラットフォームではファイル選択がサポートされていません"))
                    )
                    return

                if file_paths:
                    print(f"{len(file_paths)}個のファイルが選択されました")
                    for file_path_str in file_paths:
                        file_path = Path(file_path_str)
                        if file_path.exists() and file_path not in self.selected_files:
                            self.selected_files.append(file_path)
                            print(f"ファイルを追加: {file_path.name}")

                    self._update_file_list()
                    self.process_button.disabled = len(self.selected_files) == 0
                    self.page.update()
                else:
                    print("ファイルが選択されませんでした")

            except subprocess.TimeoutExpired:
                print("ファイル選択がタイムアウトしました")
            except Exception as ex:
                print(f"ファイルピッカーエラー: {ex}")
                import traceback
                traceback.print_exc()
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(f"ファイル選択エラー: {str(ex)}"))
                )

        # ファイルリスト表示
        self.file_list = ft.Column(spacing=5)

        # ファイル選択エリアのコンテンツ
        file_select_content = ft.Column([
            ft.Icon("cloud_upload", size=48, color="#1976d2"),
            ft.Text(
                "ファイルをここにドラッグ&ドロップ" if DROPZONE_AVAILABLE else "ファイルを選択してください",
                size=16,
                weight=ft.FontWeight.BOLD,
                color="#1976d2"
            ),
            ft.Text("txt, pdf, jpg, png に対応", size=12, color="#616161"),
            ft.ElevatedButton(
                "📁 ファイルを選択",
                icon="upload_file",
                on_click=open_file_picker,
                style=ft.ButtonStyle(
                    bgcolor="#1976d2",
                    color="#ffffff",
                ),
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10)

        # ドロップゾーンが利用可能な場合は、ドラッグ&ドロップ対応エリアを作成
        if DROPZONE_AVAILABLE:
            file_select_area = ftd.Dropzone(
                content=ft.Container(
                    content=file_select_content,
                    width=None,
                    height=180,
                    alignment=ft.alignment.center,
                    bgcolor="#e3f2fd",  # BLUE_50
                    border=ft.border.all(2, "#90caf9"),  # BLUE_200
                    border_radius=10,
                ),
                on_dropped=self._on_file_dropped,
            )
        else:
            # ドロップゾーンが利用できない場合は通常のコンテナ
            file_select_area = ft.Container(
                content=file_select_content,
                width=None,
                height=180,
                alignment=ft.alignment.center,
                bgcolor="#e3f2fd",  # BLUE_50
                border=ft.border.all(2, "#90caf9"),  # BLUE_200
                border_radius=10,
            )

        file_section = ft.Container(
            content=ft.Column([
                ft.Text("📄 読み込んだファイル:", size=16, weight=ft.FontWeight.BOLD),
                self.file_list,
                file_select_area,
            ]),
            padding=15,
            border=ft.border.all(1, "#90caf9"),  # BLUE_200
            border_radius=10,
        )

        # 出力オプション
        self.history_checkbox = ft.Checkbox(
            label="病歴（200-300文字）",
            value=True
        )
        self.symptoms_checkbox = ft.Checkbox(
            label="症状の詳細（200-300文字）",
            value=True
        )
        self.summary_checkbox = ft.Checkbox(
            label="全期間サマリー（詳細版）",
            value=True
        )

        # テンプレート選択
        template_options = [
            ft.dropdown.Option(key="disability_pension", text="障害年金診断書（標準）"),
            ft.dropdown.Option(key="mental_health_handbook", text="精神障害者保健福祉手帳"),
            ft.dropdown.Option(key="self_support_medical", text="自立支援医療"),
        ]

        self.template_dropdown = ft.Dropdown(
            label="テンプレート",
            options=template_options,
            value="disability_pension",
            width=300
        )

        # 確認モードトグル
        self.confirmation_toggle = ft.Switch(
            label="確認モード（個人情報削除を目視確認してから要約作成）",
            value=True,
            active_color="#1976d2",
            on_change=self._on_toggle_confirmation_mode
        )

        options_section = ft.Container(
            content=ft.Column([
                ft.Text("⚙️ 動作モード:", size=16, weight=ft.FontWeight.BOLD),
                self.confirmation_toggle,
                ft.Divider(),
                ft.Text("📝 出力する要約:", size=16, weight=ft.FontWeight.BOLD),
                self.history_checkbox,
                self.symptoms_checkbox,
                self.summary_checkbox,
                ft.Divider(),
                self.template_dropdown,
            ]),
            padding=15,
            border=ft.border.all(1, "#90caf9"),  # BLUE_200
            border_radius=10,
        )

        # 実行ボタン（初期状態は確認モードON）
        self.process_button = ft.ElevatedButton(
            "🔍 個人情報削除を確認",
            icon="search",
            on_click=self._on_process,
            style=ft.ButtonStyle(
                color="#ffffff",  # WHITE
                bgcolor="#1976d2",  # BLUE_700
            ),
            height=50,
            disabled=True
        )

        # ステータステキスト
        self.status_text = ft.Text("", size=14, color="#616161")  # GREY_700

        # 結果表示エリア
        self.result_container = ft.Column(spacing=15)

        # メインレイアウト
        self.page.add(
            title,
            ft.Divider(),
            file_section,
            options_section,
            self.process_button,
            self.status_text,
            ft.Divider(),
            self.result_container
        )

    def _on_file_dropped(self, e):
        """ファイルがドロップされたときの処理"""
        if not hasattr(e, 'files') or not e.files:
            print("ファイルがドロップされませんでした")
            return

        print(f"ドロップされたファイル: {e.files}")

        # ドロップされたファイルを追加
        for file_path_str in e.files:
            file_path = Path(file_path_str)
            if file_path.exists() and file_path not in self.selected_files:
                # サポートされているファイル形式かチェック
                if file_path.suffix.lower() in ['.txt', '.pdf', '.jpg', '.jpeg', '.png']:
                    self.selected_files.append(file_path)
                    print(f"ファイルを追加: {file_path.name}")
                else:
                    print(f"サポートされていないファイル形式: {file_path.suffix}")

        self._update_file_list()
        self.process_button.disabled = len(self.selected_files) == 0
        self.page.update()

    def _update_file_list(self):
        """ファイルリストを更新"""
        self.file_list.controls.clear()

        if not self.selected_files:
            self.file_list.controls.append(
                ft.Text("（ファイルが選択されていません）", color="#9e9e9e")  # GREY_500
            )
        else:
            for i, file_path in enumerate(self.selected_files):
                def make_remove_handler(index):
                    def handler(e):
                        self.selected_files.pop(index)
                        self._update_file_list()
                        self.process_button.disabled = len(self.selected_files) == 0
                        self.page.update()
                    return handler

                file_row = ft.Row([
                    ft.Icon("description", size=20, color="#42a5f5"),  # BLUE_400
                    ft.Text(file_path.name, expand=True),
                    ft.IconButton(
                        icon="delete",
                        icon_color="#ef5350",  # RED_400
                        tooltip="削除",
                        on_click=make_remove_handler(i)
                    )
                ])
                self.file_list.controls.append(file_row)

    def _on_toggle_confirmation_mode(self, e):
        """確認モードのトグルが変更されたときの処理"""
        self.confirmation_mode = self.confirmation_toggle.value

        # ボタンのラベルを更新
        if self.confirmation_mode:
            self.process_button.text = "🔍 個人情報削除を確認"
            self.process_button.icon = "search"
        else:
            self.process_button.text = "個人情報を削除して要約作成"
            self.process_button.icon = "play_arrow"

        self.page.update()

    def _on_process(self, e):
        """要約作成ボタンが押されたときの処理"""
        self.process_button.disabled = True
        self.result_container.controls.clear()
        self.status_text.value = "処理中..."
        self.page.update()

        try:
            # 1. ファイル読み込み
            self.status_text.value = "📖 ファイルを読み込み中..."
            self.page.update()

            reader = FileReader()
            all_text = reader.read_multiple_files(self.selected_files)

            # 2. 個人情報削除
            self.status_text.value = "🔒 個人情報を削除中..."
            self.page.update()

            remover = PIIRemover()
            self.cleaned_text, self.pii_log = remover.clean_text(all_text)

            # 確認モードの分岐
            if self.confirmation_mode:
                # 確認モードON：確認画面を表示
                self.status_text.value = "✅ 個人情報の削除が完了しました（確認してください）"
                self.status_text.color = "#1976d2"  # BLUE_700
                self.page.update()

                # マスクされたテキストと削除サマリーを表示
                self._show_masked_text_with_summary(self.cleaned_text, remover.get_summary_report())
            else:
                # 確認モードOFF：自動で要約生成
                self._execute_summary_generation()

        except Exception as ex:
            self.status_text.value = f"❌ エラー: {str(ex)}"
            self.status_text.color = "#d32f2f"  # RED_700

        finally:
            self.process_button.disabled = False
            self.page.update()

    def _execute_summary_generation(self):
        """要約生成を実行（確認モードOFFまたは確認完了後）"""
        try:
            # 3. 要約生成
            self.status_text.value = "🤖 AI要約を生成中..."
            self.page.update()

            summarizer = MedicalSummarizer()
            self.summary_result = summarizer.generate_summary(
                self.cleaned_text,
                template_key=self.template_dropdown.value,
                include_history=self.history_checkbox.value,
                include_symptoms=self.symptoms_checkbox.value,
                include_full_summary=self.summary_checkbox.value
            )

            if self.summary_result.error:
                raise Exception(self.summary_result.error)

            # 4. 結果表示
            self._show_results()

            # 5. ファイル保存
            saved_files = summarizer.save_results(self.summary_result)

            self.status_text.value = f"✅ 完了しました！ ({len(saved_files)}件のファイルを保存)"
            self.status_text.color = "#388e3c"  # GREEN_700
            self.page.update()

        except Exception as ex:
            self.status_text.value = f"❌ エラー: {str(ex)}"
            self.status_text.color = "#d32f2f"  # RED_700
            self.page.update()

    def _show_masked_text_with_summary(self, masked_text: str, summary_report: str):
        """マスクされたテキストと削除サマリーを表示（デバッグ用）"""
        self.result_container.controls.clear()

        # 削除サマリー
        self.result_container.controls.append(
            self._create_result_card(
                "🔒 個人情報削除サマリー",
                summary_report,
                "#fff3e0"  # ORANGE_50
            )
        )

        # 説明テキスト
        instruction_text = ft.Text(
            "⚠️ 下記のテキストを確認し、必要に応じて手動で個人情報を削除してください。\n"
            "検索機能を使って特定の文字列を探すことができます。\n"
            "確認が完了したら「確認完了して要約作成」ボタンを押してください。",
            size=14,
            color="#d32f2f",  # RED_700
            weight=ft.FontWeight.BOLD
        )

        # 検索フィールド
        self.search_field = ft.TextField(
            label="検索ワード（氏名、住所など）",
            width=300,
            border_color="#1976d2",
        )

        # 検索結果表示テキスト
        self.search_result_text = ft.Text("", size=12, color="#616161")

        # 検索ボタン
        search_button = ft.ElevatedButton(
            "🔍 検索",
            on_click=self._on_search,
            style=ft.ButtonStyle(
                bgcolor="#1976d2",
                color="#ffffff",
            ),
        )

        # 前へボタン
        prev_button = ft.IconButton(
            icon="arrow_back",
            tooltip="前の結果",
            on_click=self._on_prev_search,
        )

        # 次へボタン
        next_button = ft.IconButton(
            icon="arrow_forward",
            tooltip="次の結果",
            on_click=self._on_next_search,
        )

        # 削除ボタン
        delete_button = ft.ElevatedButton(
            "❌ この箇所を削除",
            on_click=self._on_delete_current_match,
            style=ft.ButtonStyle(
                bgcolor="#d32f2f",
                color="#ffffff",
            ),
        )

        # 検索バー
        search_bar = ft.Row([
            self.search_field,
            search_button,
            prev_button,
            next_button,
            delete_button,
            self.search_result_text,
        ], spacing=10)

        # 編集可能なマスク済みテキストフィールド
        self.masked_text_field = ft.TextField(
            value=masked_text,
            multiline=True,
            min_lines=10,
            max_lines=20,
            border_color="#1976d2",  # BLUE_700
            bgcolor="#ffffff",
        )

        # 確認完了して要約作成ボタン
        self.create_summary_button = ft.ElevatedButton(
            "✅ 確認完了して要約作成",
            icon="check_circle",
            on_click=self._on_create_summary_after_confirmation,
            style=ft.ButtonStyle(
                color="#ffffff",
                bgcolor="#388e3c",  # GREEN_700
            ),
            height=50,
        )

        # コンテナに追加
        masked_text_container = ft.Container(
            content=ft.Column([
                ft.Text("📝 マスク済み文字起こし（編集可能）", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                instruction_text,
                search_bar,
                ft.Divider(),
                self.masked_text_field,
                self.create_summary_button,
            ]),
            padding=15,
            bgcolor="#e3f2fd",  # BLUE_50
            border_radius=10,
        )

        self.result_container.controls.append(masked_text_container)
        self.page.update()

    def _on_search(self, e):
        """検索ボタンが押されたときの処理"""
        search_word = self.search_field.value
        if not search_word:
            self.search_result_text.value = "検索ワードを入力してください"
            self.search_result_text.color = "#d32f2f"
            self.page.update()
            return

        # テキスト内を検索
        text = self.masked_text_field.value
        self.search_results = []

        # すべてのマッチ箇所を見つける
        start = 0
        while True:
            pos = text.find(search_word, start)
            if pos == -1:
                break
            self.search_results.append(pos)
            start = pos + 1

        if not self.search_results:
            self.search_result_text.value = f"「{search_word}」は見つかりませんでした"
            self.search_result_text.color = "#616161"
            self.page.update()
            return

        # 最初の結果を表示
        self.current_search_index = 0
        self._show_search_result()

    def _on_prev_search(self, e):
        """前の検索結果に移動"""
        if not self.search_results:
            return

        self.current_search_index = (self.current_search_index - 1) % len(self.search_results)
        self._show_search_result()

    def _on_next_search(self, e):
        """次の検索結果に移動"""
        if not self.search_results:
            return

        self.current_search_index = (self.current_search_index + 1) % len(self.search_results)
        self._show_search_result()

    def _show_search_result(self):
        """現在の検索結果を表示"""
        if not self.search_results:
            return

        text = self.masked_text_field.value
        pos = self.search_results[self.current_search_index]
        search_word = self.search_field.value

        # 周辺テキストを取得（前後50文字）
        start = max(0, pos - 50)
        end = min(len(text), pos + len(search_word) + 50)
        context = text[start:end]

        # 検索結果情報を表示
        self.search_result_text.value = (
            f"🔍 {self.current_search_index + 1}/{len(self.search_results)}件目\n"
            f"位置: {pos}文字目\n"
            f"周辺: ...{context}..."
        )
        self.search_result_text.color = "#1976d2"
        self.page.update()

    def _on_delete_current_match(self, e):
        """現在の検索結果を削除"""
        if not self.search_results:
            self.search_result_text.value = "検索結果がありません"
            self.search_result_text.color = "#d32f2f"
            self.page.update()
            return

        text = self.masked_text_field.value
        pos = self.search_results[self.current_search_index]
        search_word = self.search_field.value

        # マッチ箇所を削除（空文字に置換）
        new_text = text[:pos] + text[pos + len(search_word):]
        self.masked_text_field.value = new_text

        # 検索結果リストを更新（削除後の位置を再計算）
        self.search_results.pop(self.current_search_index)

        # 後続の検索結果の位置を調整
        for i in range(self.current_search_index, len(self.search_results)):
            self.search_results[i] -= len(search_word)

        if self.search_results:
            # 次の結果を表示（範囲外なら最後の結果）
            if self.current_search_index >= len(self.search_results):
                self.current_search_index = len(self.search_results) - 1
            self._show_search_result()
            self.search_result_text.value += "\n✅ 削除しました"
        else:
            self.search_result_text.value = f"✅「{search_word}」はすべて削除されました"
            self.search_result_text.color = "#388e3c"

        self.page.update()

    def _on_create_summary_after_confirmation(self, e):
        """確認完了して要約作成ボタンが押されたときの処理"""
        # ユーザーが編集したテキストを取得
        self.cleaned_text = self.masked_text_field.value

        # 確認画面を非表示にする
        self.result_container.controls.clear()
        self.page.update()

        # 要約生成を実行
        self._execute_summary_generation()

    def _show_results(self):
        """結果を表示"""
        self.result_container.controls.clear()

        # 病歴
        if self.summary_result.history:
            self.result_container.controls.append(
                self._create_result_card(
                    "病歴",
                    self.summary_result.history,
                    "#e3f2fd"  # BLUE_50
                )
            )

        # 症状の詳細
        if self.summary_result.symptoms:
            self.result_container.controls.append(
                self._create_result_card(
                    "症状の詳細",
                    self.summary_result.symptoms,
                    "#e8f5e9"  # GREEN_50
                )
            )

        # 全期間サマリー
        if self.summary_result.full_summary:
            self.result_container.controls.append(
                self._create_result_card(
                    "全期間サマリー",
                    self.summary_result.full_summary,
                    "#fff3e0"  # ORANGE_50
                )
            )

    def _create_result_card(self, title: str, content: str, bg_color):
        """結果カードを作成"""
        def copy_to_clipboard(e):
            self.page.set_clipboard(content)
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"{title}をクリップボードにコピーしました"))
            )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    ft.IconButton(
                        icon="copy",
                        tooltip="コピー",
                        on_click=copy_to_clipboard
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Text(content, size=14, selectable=True),
                ft.Text(f"({len(content)}文字)", size=12, color="#757575")  # GREY_600
            ]),
            padding=15,
            bgcolor=bg_color,
            border_radius=10,
        )


def main(page: ft.Page):
    """メイン関数"""
    app = MedicalSummarizerApp(page)


if __name__ == "__main__":
    ft.app(target=main)
