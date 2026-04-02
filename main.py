#!/usr/bin/env python3
"""
AIVisualNovelGUIFrameWork
メインアプリケーションエントリーポイント

Windows上でVisualNovel風の画面を表示するAI対話型ゲームアプリ
Ollama API (192.168.11.38) と連携してユーザー対話型のストーリー生成
"""

import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QLocale, QTranslator
from PyQt6.QtGui import QIcon, QFont

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ローカルimport
from gui.main_window import MainWindow
from utils.config import Config
from core.game_logger import GameLogger


def setup_application():
    """アプリケーションの基本設定"""
    app = QApplication(sys.argv)
    app.setApplicationName("Nostalgia")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AIVisualNovelGUIFrameWork")
    
    # 日本語フォントの設定（フォールバック付き）
    import platform
    if platform.system() == "Windows":
        font_families = ["Yu Gothic UI", "Meiryo UI", "MS UI Gothic", "Arial Unicode MS"]
    else:
        font_families = ["Noto Sans CJK JP", "VL Gothic", "DejaVu Sans", "Arial Unicode MS"]
    
    for font_family in font_families:
        font = QFont(font_family, 10)
        if font.exactMatch():
            app.setFont(font)
            break
    else:
        # フォールバック：デフォルトフォントを使用
        font = QFont()
        font.setPointSize(10)
        app.setFont(font)
    
    # 文字エンコーディングの設定
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'C.UTF-8')
        except locale.Error:
            pass  # システムデフォルトを使用
    
    return app


def main():
    """メインエントリーポイント"""
    # 設定の初期化
    config = Config.get_instance()
    config.load_config()
    
    # ログシステムの初期化
    logger = GameLogger.get_instance()
    logger.info("=== Nostalgia 起動 ===")
    
    # アプリケーション作成
    app = setup_application()
    
    try:
        # メインウィンドウ作成・表示
        main_window = MainWindow()
        main_window.show()
        
        logger.info("メインウィンドウを表示しました")
        
        # イベントループ開始
        exit_code = app.exec()
        
        logger.info(f"アプリケーション終了 (exit_code: {exit_code})")
        return exit_code
        
    except Exception as e:
        logger.error(f"アプリケーション実行中にエラーが発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        logger.info("=== Nostalgia 終了 ===")


if __name__ == "__main__":
    sys.exit(main())