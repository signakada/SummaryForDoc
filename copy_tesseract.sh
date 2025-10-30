#!/bin/bash

# Tesseractをアプリバンドルにコピーするスクリプト

APP_PATH="build/macos/SummaryForDoc.app/Contents/Resources"
TESSERACT_DIR="$APP_PATH/tesseract"

echo "Tesseractをアプリバンドルにコピー中..."

# Tesseractディレクトリを作成
mkdir -p "$TESSERACT_DIR"
mkdir -p "$TESSERACT_DIR/tessdata"
mkdir -p "$TESSERACT_DIR/lib"

# Tesseractバイナリをコピー
echo "- Tesseractバイナリをコピー..."
cp /opt/homebrew/Cellar/tesseract/5.5.1/bin/tesseract "$TESSERACT_DIR/"
chmod +x "$TESSERACT_DIR/tesseract"

# 学習データをコピー（日本語と英語のみ）
echo "- 学習データをコピー..."
cp /opt/homebrew/Cellar/tesseract/5.5.1/share/tessdata/eng.traineddata "$TESSERACT_DIR/tessdata/"
cp /opt/homebrew/Cellar/tesseract-lang/4.1.0/share/tessdata/jpn.traineddata "$TESSERACT_DIR/tessdata/"

# 依存ライブラリをコピー
echo "- 依存ライブラリをコピー..."

# libtesseract (最も重要)
echo "  - libtesseract..."
cp /opt/homebrew/Cellar/tesseract/5.5.1/lib/libtesseract.5.dylib "$TESSERACT_DIR/lib/"

# leptonica (Tesseractが依存)
echo "  - libleptonica..."
cp /opt/homebrew/opt/leptonica/lib/libleptonica.6.dylib "$TESSERACT_DIR/lib/"

# libarchive (Tesseractが依存)
echo "  - libarchive..."
cp /opt/homebrew/opt/libarchive/lib/libarchive.13.dylib "$TESSERACT_DIR/lib/"

# 画像処理ライブラリ (leptonicaが依存)
echo "  - 画像処理ライブラリ..."
cp /opt/homebrew/opt/jpeg-turbo/lib/libjpeg.8.dylib "$TESSERACT_DIR/lib/" 2>/dev/null
cp /opt/homebrew/opt/libpng/lib/libpng16.16.dylib "$TESSERACT_DIR/lib/" 2>/dev/null
cp /opt/homebrew/opt/libtiff/lib/libtiff.6.dylib "$TESSERACT_DIR/lib/" 2>/dev/null
cp /opt/homebrew/opt/webp/lib/libwebp.7.dylib "$TESSERACT_DIR/lib/" 2>/dev/null
cp /opt/homebrew/opt/giflib/lib/libgif.7.dylib "$TESSERACT_DIR/lib/" 2>/dev/null
cp /opt/homebrew/opt/openjpeg/lib/libopenjp2.7.dylib "$TESSERACT_DIR/lib/" 2>/dev/null
cp /opt/homebrew/opt/zstd/lib/libzstd.1.dylib "$TESSERACT_DIR/lib/" 2>/dev/null

# ライブラリの参照パスを修正
echo "- ライブラリパスを修正中..."

# Tesseractバイナリの参照パスを相対パスに変更
install_name_tool -change /opt/homebrew/Cellar/tesseract/5.5.1/lib/libtesseract.5.dylib \
  @executable_path/../Resources/tesseract/lib/libtesseract.5.dylib "$TESSERACT_DIR/tesseract"

install_name_tool -change /opt/homebrew/opt/leptonica/lib/libleptonica.6.dylib \
  @executable_path/../Resources/tesseract/lib/libleptonica.6.dylib "$TESSERACT_DIR/tesseract"

install_name_tool -change /opt/homebrew/opt/libarchive/lib/libarchive.13.dylib \
  @executable_path/../Resources/tesseract/lib/libarchive.13.dylib "$TESSERACT_DIR/tesseract"

# libtesseractの依存関係を修正
install_name_tool -change /opt/homebrew/opt/leptonica/lib/libleptonica.6.dylib \
  @loader_path/libleptonica.6.dylib "$TESSERACT_DIR/lib/libtesseract.5.dylib"

install_name_tool -change /opt/homebrew/opt/libarchive/lib/libarchive.13.dylib \
  @loader_path/libarchive.13.dylib "$TESSERACT_DIR/lib/libtesseract.5.dylib"

echo "✅ Tesseractのコピーが完了しました"
echo ""
echo "アプリバンドル: build/macos/SummaryForDoc.app"
echo "Tesseractパス: $TESSERACT_DIR"
echo ""
echo "依存関係を確認:"
otool -L "$TESSERACT_DIR/tesseract" | head -10
