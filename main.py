"""
医療文書要約ツール - メインGUIアプリ (Flet)
Mac・Windows・Linux対応
"""

import flet as ft
from pathlib import Path
from typing import List
import subprocess
import platform

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

        # コンポーネント
        self.file_list = None
        self.history_checkbox = None
        self.symptoms_checkbox = None
        self.summary_checkbox = None
        self.template_dropdown = None
        self.process_button = None
        self.result_container = None
        self.status_text = None

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

        pick_button = ft.ElevatedButton(
            "ファイルを選択 (txt, pdf, jpg, png)",
            icon="upload_file",
            on_click=open_file_picker
        )

        # ファイルリスト表示
        self.file_list = ft.Column(spacing=5)

        file_section = ft.Container(
            content=ft.Column([
                ft.Text("📄 読み込んだファイル:", size=16, weight=ft.FontWeight.BOLD),
                self.file_list,
                pick_button
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

        options_section = ft.Container(
            content=ft.Column([
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

        # 実行ボタン
        self.process_button = ft.ElevatedButton(
            "個人情報を削除して要約作成",
            icon="play_arrow",
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
            self.cleaned_text, pii_log = remover.clean_text(all_text)

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

        except Exception as ex:
            self.status_text.value = f"❌ エラー: {str(ex)}"
            self.status_text.color = "#d32f2f"  # RED_700

        finally:
            self.process_button.disabled = False
            self.page.update()

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
