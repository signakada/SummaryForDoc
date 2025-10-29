# 医療文書要約ツール

医療文書（テキスト・PDF・画像）から個人情報を削除し、診断書用の要約を自動生成するツールです。

## 特徴

- **クロスプラットフォーム対応**: Mac・Windows・Linux で動作（Flet使用）
- **モダンなUI**: マテリアルデザインで使いやすい
- **ドラッグ&ドロップ対応**: ファイルを簡単に追加
- **複数ファイル対応**: テキスト・PDF・画像を一度に処理

## 機能

- ✅ ファイル読み込み（.txt / .pdf / .jpg / .png）
- ✅ 個人情報の自動削除（氏名、生年月日、住所、電話番号）
- ✅ 2種類の要約生成
  - 診断書用の病歴（200-300文字）
  - 症状の詳細（200-300文字）
  - 全期間サマリー（詳細版）
- ✅ 複数のテンプレート
  - 障害年金診断書
  - 精神障害者保健福祉手帳
  - 自立支援医療
  - カスタム（自分で編集可能）

## セットアップ

### 1. Pythonのインストール
Python 3.10以上が必要です。

### 2. 依存ライブラリのインストール
```bash
pip install -r requirements.txt
```

### 3. Tesseract OCRのインストール（画像読み込み用）

**Mac:**
```bash
brew install tesseract
brew install tesseract-lang
```

**Windows:**
[Tesseract のダウンロードページ](https://github.com/UB-Mannheim/tesseract/wiki)からインストーラーをダウンロードし、インストール時に「日本語」を選択してください。

### 4. APIキーの設定

`.env`ファイルをプロジェクトのルートディレクトリに作成：

```bash
cp .env.example .env
```

`.env`を編集してAPIキーを記載：

```
ANTHROPIC_API_KEY=your_api_key_here
# または
OPENAI_API_KEY=your_api_key_here
```

**APIキーの取得方法:**
- Claude: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/

## 使い方

### GUIアプリを起動
```bash
python main.py
```

### 基本的な流れ
1. ファイルをドラッグ&ドロップまたは「ファイル選択」ボタンで追加
2. 出力する要約の種類を選択（病歴・症状の詳細・全期間サマリー）
3. テンプレートを選択（障害年金診断書など）
4. 「個人情報を削除して要約作成」ボタンをクリック
5. 結果を確認してファイル保存またはコピー

## プロジェクト構造

```
SummaryForDoc/
├── main.py                 # Flet GUIアプリのメイン
├── src/
│   ├── config.py           # APIキー・設定管理
│   ├── file_reader.py      # ファイル読み込み（TXT/PDF/画像）
│   ├── pii_remover.py      # 個人情報削除
│   ├── summarizer.py       # API呼び出し・要約生成
│   └── prompts.py          # プロンプトテンプレート管理
├── output/                 # 出力ファイル保存先
├── tests/                  # テスト用サンプルファイル
├── requirements.txt        # 依存ライブラリ
├── .env.example            # 環境変数の例
└── README.md              # このファイル
```

## 注意事項

- ⚠️ **個人情報削除は100%完璧ではありません。必ず目視確認してください。**
- ⚠️ API料金がかかります（1回数円〜十数円程度）。
- ⚠️ OCR精度は画像の質に依存します。鮮明な画像を使用してください。

## 開発ロードマップ

### Phase 1: コア機能（完了予定）
- [x] プロジェクト構造作成
- [ ] 設定管理
- [ ] ファイル読み込み（テキスト）
- [ ] 個人情報削除
- [ ] AI要約生成
- [ ] プロンプトテンプレート

### Phase 2: GUI実装（Flet）
- [ ] 基本画面レイアウト
- [ ] ファイル選択機能
- [ ] ドラッグ&ドロップ
- [ ] 結果表示画面

### Phase 3: 追加機能
- [ ] PDF対応
- [ ] 画像対応（OCR）
- [ ] テンプレート切替
- [ ] カスタムプロンプト編集

### Phase 4: 仕上げ
- [ ] エラーハンドリング
- [ ] 進行状況表示
- [ ] 実行ファイル化（PyInstaller）

## ビルド方法（実行ファイル化）

### Mac
```bash
flet pack main.py --name "医療文書要約ツール" --icon icon.png
```

### Windows
```bash
flet pack main.py --name "医療文書要約ツール" --icon icon.ico
```

## ライセンス

個人使用のみ

## 技術スタック

- **GUI**: Flet (Flutter-based)
- **言語**: Python 3.10+
- **AI API**: Anthropic Claude / OpenAI GPT
- **PDF**: PyPDF2
- **OCR**: Tesseract + pytesseract
- **画像処理**: Pillow
