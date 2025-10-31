@echo off
REM Tesseractをアプリビルドディレクトリにコピーするスクリプト

echo Tesseractをアプリビルドディレクトリにコピー中...

REM Tesseractのインストールパス（標準インストール先）
set TESSERACT_PATH=C:\Program Files\Tesseract-OCR

REM ビルドディレクトリ（Fletの標準的なビルド構造）
set BUILD_PATH=build\windows
set TESSERACT_DIR=%BUILD_PATH%\tesseract

REM Tesseractディレクトリが存在しない場合のエラーチェック
if not exist "%TESSERACT_PATH%\tesseract.exe" (
    echo エラー: Tesseractが見つかりません
    echo %TESSERACT_PATH% にTesseractがインストールされているか確認してください
    echo.
    echo Tesseractのインストール方法:
    echo 1. https://github.com/UB-Mannheim/tesseract/wiki からインストーラーをダウンロード
    echo 2. インストール時に日本語言語データを選択
    pause
    exit /b 1
)

REM ビルドディレクトリが存在しない場合のエラーチェック
if not exist "%BUILD_PATH%" (
    echo エラー: ビルドディレクトリが見つかりません
    echo 先に 'flet build windows' を実行してください
    pause
    exit /b 1
)

REM Tesseractディレクトリを作成
echo - Tesseractディレクトリを作成...
if not exist "%TESSERACT_DIR%" mkdir "%TESSERACT_DIR%"
if not exist "%TESSERACT_DIR%\tessdata" mkdir "%TESSERACT_DIR%\tessdata"

REM Tesseract実行ファイルをコピー
echo - Tesseract実行ファイルをコピー...
copy "%TESSERACT_PATH%\tesseract.exe" "%TESSERACT_DIR%\" >nul

REM 学習データをコピー（日本語と英語）
echo - 学習データをコピー...
if exist "%TESSERACT_PATH%\tessdata\eng.traineddata" (
    copy "%TESSERACT_PATH%\tessdata\eng.traineddata" "%TESSERACT_DIR%\tessdata\" >nul
) else (
    echo   警告: eng.traineddata が見つかりません
)

if exist "%TESSERACT_PATH%\tessdata\jpn.traineddata" (
    copy "%TESSERACT_PATH%\tessdata\jpn.traineddata" "%TESSERACT_DIR%\tessdata\" >nul
) else (
    echo   警告: jpn.traineddata が見つかりません
    echo   Tesseractインストール時に日本語データを選択してください
)

REM 必要なDLLをコピー
echo - 依存DLLをコピー...

REM Tesseractの主要DLL
if exist "%TESSERACT_PATH%\libtesseract-5.dll" (
    copy "%TESSERACT_PATH%\libtesseract-5.dll" "%TESSERACT_DIR%\" >nul
) else (
    echo   警告: libtesseract-5.dll が見つかりません
)

REM Leptonica（画像処理ライブラリ）
if exist "%TESSERACT_PATH%\libleptonica-1.84.1.dll" (
    copy "%TESSERACT_PATH%\libleptonica-*.dll" "%TESSERACT_DIR%\" >nul
) else if exist "%TESSERACT_PATH%\libleptonica-1.82.0.dll" (
    copy "%TESSERACT_PATH%\libleptonica-*.dll" "%TESSERACT_DIR%\" >nul
) else if exist "%TESSERACT_PATH%\leptonica-1.84.1.dll" (
    copy "%TESSERACT_PATH%\leptonica-*.dll" "%TESSERACT_DIR%\" >nul
) else (
    echo   警告: leptonica DLL が見つかりません
)

REM その他の依存DLL（画像フォーマット対応）
for %%F in (
    libarchive-*.dll
    libcrypto-*.dll
    libcurl-*.dll
    libgif-*.dll
    libjpeg-*.dll
    liblzma-*.dll
    libpng*.dll
    libtiff*.dll
    libwebp-*.dll
    libzstd.dll
    zlib*.dll
) do (
    if exist "%TESSERACT_PATH%\%%F" (
        copy "%TESSERACT_PATH%\%%F" "%TESSERACT_DIR%\" >nul 2>&1
    )
)

echo.
echo ✅ Tesseractのコピーが完了しました
echo.
echo ビルドディレクトリ: %BUILD_PATH%
echo Tesseractパス: %TESSERACT_DIR%
echo.

REM コピーされたファイルを確認
echo コピーされたファイル:
dir /b "%TESSERACT_DIR%"
echo.
echo 学習データ:
dir /b "%TESSERACT_DIR%\tessdata"
echo.

pause
