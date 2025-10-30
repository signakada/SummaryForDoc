#!/bin/bash

# Tesseractをアプリバンドルにコピーするスクリプト

APP_PATH="build/macos/SummaryForDoc.app/Contents/Resources"
TESSERACT_DIR="$APP_PATH/tesseract"

echo "Tesseractをアプリバンドルにコピー中..."

# Tesseractディレクトリを作成
mkdir -p "$TESSERACT_DIR"
mkdir -p "$TESSERACT_DIR/tessdata"

# Tesseractバイナリをコピー
echo "- Tesseractバイナリをコピー..."
cp /opt/homebrew/Cellar/tesseract/5.5.1/bin/tesseract "$TESSERACT_DIR/"
chmod +x "$TESSERACT_DIR/tesseract"

# 学習データをコピー（日本語と英語のみ）
echo "- 学習データをコピー..."
cp /opt/homebrew/Cellar/tesseract/5.5.1/share/tessdata/eng.traineddata "$TESSERACT_DIR/tessdata/"
cp /opt/homebrew/Cellar/tesseract-lang/4.1.0/share/tessdata/jpn.traineddata "$TESSERACT_DIR/tessdata/"

# 依存ライブラリをコピー（必要に応じて）
echo "- 依存ライブラリをコピー..."
mkdir -p "$TESSERACT_DIR/lib"

# leptonica
cp /opt/homebrew/opt/leptonica/lib/liblept.5.dylib "$TESSERACT_DIR/lib/" 2>/dev/null || echo "  leptonica not found (may not be needed)"

# libjpeg
cp /opt/homebrew/opt/jpeg-turbo/lib/libjpeg.8.dylib "$TESSERACT_DIR/lib/" 2>/dev/null || echo "  libjpeg not found (may not be needed)"

# libpng
cp /opt/homebrew/opt/libpng/lib/libpng16.16.dylib "$TESSERACT_DIR/lib/" 2>/dev/null || echo "  libpng not found (may not be needed)"

# libtiff
cp /opt/homebrew/opt/libtiff/lib/libtiff.6.dylib "$TESSERACT_DIR/lib/" 2>/dev/null || echo "  libtiff not found (may not be needed)"

echo "✅ Tesseractのコピーが完了しました"
echo ""
echo "アプリバンドル: build/macos/SummaryForDoc.app"
echo "Tesseractパス: $TESSERACT_DIR"
