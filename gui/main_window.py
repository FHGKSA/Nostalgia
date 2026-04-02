"""
メインウィンドウ
ビジュアルノベル風の上下分割レイアウト

構成:
- 上段: 立ち絵・背景・BGM表示エリア（ゲーム画面）
- 下段: テキスト表示・ユーザー入力・選択肢エリア
- メニューバー: ファイル操作・設定・デバッグ機能
- ステータスバー: ゲーム状態・統計情報表示
"""

import sys
from typing import Optional, Dict, Any, List
from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QToolBar, QStatusBar, QLabel, QFrame,
    QApplication, QMessageBox, QDialog, QTextEdit, QPushButton,
    QProgressBar, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QAction, QIcon, QPixmap, QFont, QKeySequence, QFontDatabase, QFontInfo, QFontMetrics

from utils.config import Config
from core.game_state import get_game_state
from core.game_logger import GameLogger, GameEvent
from core.asset_manager import get_asset_manager
from core.ollama_client import get_ollama_client
from core.text_engine import get_text_engine, TextSpeed

# GUI コンポーネント（循環インポート回避のため関数内で読み込み）


class StatusPanel(QWidget):
    """ステータス情報パネル"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.config = Config.get_instance()
        self.game_state = get_game_state()
        self.logger = GameLogger.get_instance()
        self.parent_window = parent  # 親ウィンドウの参照を保持
        
        self._setup_ui()
        
        # 定期更新タイマー
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)  # 1秒間隔
    
    def _setup_ui(self):
        """UI構築"""
        layout = QHBoxLayout()
        
        # ゲーム情報
        self.game_info_label = QLabel("ゲーム準備中...")
        
        # 日本語フォント設定
        if self.parent_window and hasattr(self.parent_window, 'get_japanese_font'):
            status_font = self.parent_window.get_japanese_font(10)
            self.game_info_label.setFont(status_font)
        
        layout.addWidget(self.game_info_label)
        
        layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # システム統計
        self.stats_label = QLabel("統計: -")
        
        # 日本語フォント設定
        if self.parent_window and hasattr(self.parent_window, 'get_japanese_font'):
            stats_font = self.parent_window.get_japanese_font(10)
            self.stats_label.setFont(stats_font)
        
        layout.addWidget(self.stats_label)
        
        layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # API接続状態
        self.api_status_label = QLabel("API: 未接続")
        
        # 日本語フォント設定
        if self.parent_window and hasattr(self.parent_window, 'get_japanese_font'):
            api_font = self.parent_window.get_japanese_font(10)
            self.api_status_label.setFont(api_font)
        
        layout.addWidget(self.api_status_label)
        
        self.setLayout(layout)
    
    def update_status(self):
        """ステータス情報を更新"""
        # ゲーム情報の更新
        if self.game_state.current_location:
            game_info = f"📍 {self.game_state.current_location}"
            if self.game_state.current_character:
                game_info += f" | 👤 {self.game_state.current_character}"
            self.game_info_label.setText(game_info)
        
        # ログ統計の更新
        try:
            log_stats = self.logger.get_session_stats()
            stats_text = f"📊 イベント: {log_stats['events']}, 選択: {log_stats['choices']}"
            self.stats_label.setText(stats_text)
        except Exception:
            pass
        
        # API状態の更新（軽量チェック）
        try:
            client = get_ollama_client()
            # 接続テストは重いので、設定情報のみ表示
            api_text = f"🔗 {client.config.ollama.host}:{client.config.ollama.port}"
            self.api_status_label.setText(api_text)
        except Exception:
            self.api_status_label.setText("API: エラー")
    
    def refresh_status(self):
        """設定変更後のステータス更新"""
        try:
            # 設定ファイルを再読込
            config = Config.get_instance()
            
            # API設定の表示更新
            ollama_config = config.ollama
            host = ollama_config.host or 'localhost'
            port = ollama_config.port or 11434
            model = ollama_config.default_model or '未選択'
            
            api_text = f"🔗 {host}:{port} | 🤖 {model}"
            self.api_status_label.setText(api_text)
            
            # それ以外の情報も更新
            self.update_status()
            
        except Exception as e:
            self.logger.error(f"ステータス更新エラー: {e}")
            self.api_status_label.setText("API: 設定エラー")


class GameDisplayWidget(QFrame):
    """上段: ゲーム画面表示エリア"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.asset_manager = get_asset_manager()
        self.logger = GameLogger.get_instance()
        self.parent_window = parent  # 親ウィンドウの参照を保持
        
        self._setup_ui()
        
        # 現在表示中の背景・キャラクター
        self.current_background = None
        self.current_characters = {}
        
    def _setup_ui(self):
        """UI構築"""
        # フレームスタイル
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(400)
        
        # レイアウト
        layout = QVBoxLayout()
        
        # プレースホルダーラベル
        self.display_label = QLabel("ゲーム画面")
        self.display_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 日本語フォント設定
        if self.parent_window and hasattr(self.parent_window, 'get_japanese_font'):
            font = self.parent_window.get_japanese_font(24)
            self.display_label.setFont(font)
        
        self.display_label.setStyleSheet("""
            QLabel {
                background-color: #2b2b2b;
                color: white;
                border: 2px dashed #555;
            }
        """)
        layout.addWidget(self.display_label)
        
        self.setLayout(layout)
    
    def set_background(self, background_file: str):
        """背景を設定"""
        try:
            # アセットマネージャーから背景を取得
            background_image = self.asset_manager.get_background(
                background_file, 
                target_size=(1280, 720)
            )
            
            if background_image:
                # PIL Image から QPixmap に変換
                import io
                buffer = io.BytesIO()
                background_image.save(buffer, format='PNG')
                buffer.seek(0)
                
                pixmap = QPixmap()
                pixmap.loadFromData(buffer.getvalue())
                
                # ラベルに表示
                self.display_label.setPixmap(pixmap.scaled(
                    self.display_label.size(), 
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                
                self.current_background = background_file
                self.logger.debug(f"背景設定完了: {background_file}")
            
        except Exception as e:
            self.logger.error(f"背景設定エラー: {background_file}", exception=e)
    
    def add_character(self, character_name: str, image_file: str, position: str = "center"):
        """キャラクターを追加"""
        try:
            character_image = self.asset_manager.get_character_image(
                character_name,
                image_file,
                target_size=(400, 600)
            )
            
            if character_image:
                self.current_characters[character_name] = {
                    'image_file': image_file,
                    'position': position
                }
                self.logger.debug(f"キャラクター追加: {character_name} ({image_file})")
                # TODO: 実際の描画処理は後のアニメーションエンジンで実装
            
        except Exception as e:
            self.logger.error(f"キャラクター追加エラー: {character_name}", exception=e)


class TextPanelWidget(QFrame):
    """下段: テキスト・選択肢表示エリア"""
    
    # シグナル定義
    choice_selected = pyqtSignal(int, str)  # 選択肢番号, 選択肢テキスト
    user_input_submitted = pyqtSignal(str)  # ユーザー入力
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.logger = GameLogger.get_instance()
        self.parent_window = parent  # 親ウィンドウの参照を保持
        
        self._setup_ui()
        self._setup_text_engine()
        
        # 現在の選択肢
        self.current_choices = []
    
    def _setup_ui(self):
        """ユーザーインターフェースの構築"""
        # フレームスタイル
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setMinimumHeight(250)
        
        layout = QVBoxLayout()
        
        # テキストエンジン用コンテナ
        self.text_container = QWidget()
        self.text_container.setMinimumHeight(150)
        self.text_container_layout = QVBoxLayout(self.text_container)
        layout.addWidget(self.text_container)
        
        # 選択肢エリア
        self.choice_layout = QHBoxLayout()
        layout.addLayout(self.choice_layout)
        
        # ユーザー入力エリア（初期は非表示）
        self.user_input = QTextEdit()
        self.user_input.setMaximumHeight(60)
        self.user_input.setPlaceholderText("ここに入力して Enter で送信...")
        
        # 日本語フォント設定
        if self.parent_window and hasattr(self.parent_window, 'get_japanese_font'):
            input_font = self.parent_window.get_japanese_font(12)
            self.user_input.setFont(input_font)
        
        self.user_input.hide()
        layout.addWidget(self.user_input)
        
        # 送信ボタン（初期は非表示）
        self.submit_button = QPushButton("送信")
        self.submit_button.clicked.connect(self._on_submit_input)
        self.submit_button.hide()
        layout.addWidget(self.submit_button)
        
        self.setLayout(layout)
    
    def _setup_text_engine(self):
        """テキストエンジンのセットアップ"""
        try:
            self.text_engine = get_text_engine(self.text_container)
            self.logger.info("テキストエンジンを統合しました")
        except Exception as e:
            self.logger.error(f"テキストエンジンセットアップエラー: {e}")
    
    def display_text(self, text: str, character: str = "", speed: TextSpeed = TextSpeed.NORMAL, auto_advance: bool = False):
        """テキストを表示（新テキストエンジン使用）"""
        try:
            # キャラクター名がある場合
            if character:
                formatted_text = f"**{character}**: {text}"
            else:
                formatted_text = text
            
            # テキストエンジンで表示
            if hasattr(self, 'text_engine'):
                self.text_engine.display_text(formatted_text, auto_advance, speed)
            
            # ログ記録
            self.logger.info(f"テキスト表示: {character} - {text[:30]}...")
            
        except Exception as e:
            self.logger.error(f"テキスト表示エラー: {e}")
    
    def get_text_history(self) -> List[str]:
        """テキスト履歴を取得"""
        if hasattr(self, 'text_engine'):
            return self.text_engine.get_history()
        return []
    
    def clear_text(self):
        """テキストをクリア"""
        if hasattr(self, 'text_engine'):
            self.text_engine.clear_text()
    
    def skip_current_text(self):
        """現在のテキストをスキップ"""
        if hasattr(self, 'text_engine'):
            self.text_engine.skip_current_text()
    
    def show_choices(self, choices: list):
        """選択肢を表示"""
        # 既存の選択肢ボタンをクリア
        self.clear_choices()
        
        self.current_choices = choices
        
        for i, choice in enumerate(choices):
            button = QPushButton(f"{i+1}. {choice}")
            button.clicked.connect(lambda checked, idx=i: self._on_choice_selected(idx))
            
            # 日本語フォント設定
            if self.parent_window and hasattr(self.parent_window, 'get_japanese_font'):
                button_font = self.parent_window.get_japanese_font(12)
                button.setFont(button_font)
            
            button.setStyleSheet("""
                QPushButton {
                    background-color: #4a4a4a;
                    color: white;
                    border: 1px solid #666;
                    padding: 8px;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton:pressed {
                    background-color: #3a3a3a;
                }
            """)
            self.choice_layout.addWidget(button)
        
        self.logger.debug(f"選択肢表示: {len(choices)}個")
    
    def clear_choices(self):
        """選択肢をクリア"""
        while self.choice_layout.count():
            child = self.choice_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def show_user_input(self, show: bool = True):
        """ユーザー入力エリアの表示/非表示"""
        if show:
            self.user_input.show()
            self.submit_button.show()
            self.user_input.setFocus()
        else:
            self.user_input.hide()
            self.submit_button.hide()
    
    def _on_choice_selected(self, choice_index: int):
        """選択肢が選ばれた時の処理"""
        if 0 <= choice_index < len(self.current_choices):
            choice_text = self.current_choices[choice_index]
            self.choice_selected.emit(choice_index, choice_text)
            self.clear_choices()
    
    def _on_submit_input(self):
        """ユーザー入力送信"""
        text = self.user_input.toPlainText().strip()
        if text:
            self.user_input_submitted.emit(text)
            self.user_input.clear()
            self.show_user_input(False)


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        
        # コアシステム参照
        self.config = Config.get_instance()
        self.logger = GameLogger.get_instance()
        self.game_state = get_game_state()
        
        # 日本語フォントの初期化
        self._init_japanese_fonts()
        
        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._connect_signals()
        
        # 初期化完了ログ
        self.logger.log_game_event(
            GameEvent.GAME_START, 
            "メインウィンドウ初期化完了"
        )
    
    def _init_japanese_fonts(self):
        """日本語フォントの初期化"""
        import platform
        
        # プラットフォーム別のフォント候補（WSL環境対応）
        if platform.system() == "Windows":
            self.font_candidates = ["Yu Gothic UI", "Meiryo UI", "MS UI Gothic", "Arial Unicode MS"]
        else:
            # Linux/WSL環境では新しくインストールした日本語フォントを優先
            self.font_candidates = [
                "Noto Sans CJK JP",     # メインの日本語フォント
                "TakaoPGothic",         # Takaoゴシック
                "VL Gothic",            # VLゴシック 
                "TakaoPMincho",         # 明朝体（バックアップ）
                "DejaVu Sans",          # 汎用フォント
                "Liberation Sans"       # フォールバック
            ]
        
        # 利用可能なフォントを確認（フォント存在チェック + 日本語描画テスト）
        self.japanese_font_family = None
        for font_name in self.font_candidates:
            # フォントを作成してテスト
            test_font = QFont(font_name)
            font_info = QFontInfo(test_font)
            
            # フォント名の一致確認（部分一致も許可）
            font_matched = (font_info.family() == font_name or 
                          font_name in font_info.family() or
                          font_info.family() in font_name)
            
            if font_matched:
                # 日本語描画テスト用の字形メトリクス確認
                font_metrics = QFontMetrics(test_font)
                japanese_test_chars = "あいうえお漢字テスト"
                
                # 日本語文字の幅が適切に計算できるかチェック
                if font_metrics.horizontalAdvance(japanese_test_chars) > 0:
                    self.japanese_font_family = font_info.family()
                    self.logger.info(f"日本語フォント選択完了: {self.japanese_font_family} (候補: {font_name})")
                    break
                else:
                    self.logger.debug(f"フォント {font_name} は日本語描画に不適切")
            else:
                self.logger.debug(f"フォント {font_name} が見つかりません (実際: {font_info.family()})")
        
        if not self.japanese_font_family:
            # デフォルトフォントを使用
            self.japanese_font_family = QFont().family()
            self.logger.warning(f"日本語フォントが見つかりません。デフォルト使用: {self.japanese_font_family}")
    
    def get_japanese_font(self, size: int = 12, bold: bool = False) -> QFont:
        """日本語フォントを取得（WSL環境向け改善版）"""
        if hasattr(self, 'japanese_font_family') and self.japanese_font_family:
            # WSL環境では、フォントサイズを少し大きめに設定
            adjusted_size = max(size, 10)  # 最小10pt
            font = QFont(self.japanese_font_family, adjusted_size)
            font.setBold(bold)
            
            # WSL/X11環境での日本語フォント表示改善設定
            font.setStyleHint(QFont.StyleHint.SansSerif)
            font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
            
            self.logger.debug(f"フォント生成: {self.japanese_font_family}, サイズ: {adjusted_size}pt")
            return font
        else:
            # フォールバック: システムフォント
            font = QFont("DejaVu Sans", max(size, 10))
            font.setBold(bold)
            self.logger.warning(f"フォールバックフォント使用: DejaVu Sans, サイズ: {max(size, 10)}pt")
            return font
    
    def _setup_ui(self):
        """UI構築"""
        # ウィンドウ設定
        self.setWindowTitle(self.config.window.title)
        self.setGeometry(100, 100, self.config.window.width, self.config.window.height)
        
        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト（上下分割）
        main_layout = QVBoxLayout()
        
        # スプリッター（上下分割）
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 上段: ゲーム画面
        self.game_display = GameDisplayWidget(self)  # 親を渡す
        splitter.addWidget(self.game_display)
        
        # 下段: テキスト・選択肢
        self.text_panel = TextPanelWidget(self)  # 親を渡す
        splitter.addWidget(self.text_panel)
        
        # 分割比率の設定（上段70%, 下段30%）
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)
        
        # ウィンドウアイコン（存在する場合）
        icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
    
    def _setup_menu(self):
        """メニューバーのセットアップ"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")
        
        new_game_action = QAction("新しいゲーム(&N)", self)
        new_game_action.setShortcut(QKeySequence.StandardKey.New)
        new_game_action.triggered.connect(self.new_game)
        file_menu.addAction(new_game_action)
        
        save_action = QAction("セーブ(&S)", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_game)
        file_menu.addAction(save_action)
        
        load_action = QAction("ロード(&L)", self)
        load_action.setShortcut(QKeySequence.StandardKey.Open)
        load_action.triggered.connect(self.load_game)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("終了(&Q)", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 設定メニュー
        settings_menu = menubar.addMenu("設定(&S)")
        
        settings_action = QAction("設定(&P)", self)
        settings_action.setShortcut("Ctrl+P")
        settings_action.triggered.connect(self.open_settings)
        settings_menu.addAction(settings_action)
        
        # デバッグメニュー
        debug_menu = menubar.addMenu("デバッグ(&D)")
        
        show_logs_action = QAction("ログ表示(&L)", self)
        show_logs_action.triggered.connect(self.show_logs)
        debug_menu.addAction(show_logs_action)
        
        test_api_action = QAction("API接続テスト(&A)", self)
        test_api_action.triggered.connect(self.test_api_connection)
        debug_menu.addAction(test_api_action)
        
        stats_action = QAction("統計情報(&S)", self)
        stats_action.triggered.connect(self.show_statistics)
        debug_menu.addAction(stats_action)
        
        debug_menu.addSeparator()
        
        # テキストエンジンテスト
        text_test_action = QAction("テキスト表示テスト(&T)", self)
        text_test_action.triggered.connect(self.test_text_engine)
        debug_menu.addAction(text_test_action)
        
        text_speed_test_action = QAction("タイピング速度テスト(&Y)", self)
        text_speed_test_action.triggered.connect(self.test_typing_speed)
        debug_menu.addAction(text_speed_test_action)
        
        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")
        
        about_action = QAction("バージョン情報(&A)", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # アプリケーション情報メニュー
        info_menu = menubar.addMenu("ヘルプ(&H)")
        
        about_action = QAction("バージョン情報(&A)", self)
        about_action.triggered.connect(self.show_about)
        info_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """ステータスバーのセットアップ"""
        status_bar = self.statusBar()
        
        # ステータスパネルを追加（親を渡す）
        self.status_panel = StatusPanel(self)
        status_bar.addPermanentWidget(self.status_panel)
        
        # 初期メッセージ
        status_bar.showMessage("AI Visual Novel Engine - Ready", 3000)
    
    def _connect_signals(self):
        """シグナル接続"""
        # テキストパネルからのシグナル
        self.text_panel.choice_selected.connect(self.on_choice_selected)
        self.text_panel.user_input_submitted.connect(self.on_user_input)
    
    # ゲームフロー関連メソッド
    def new_game(self):
        """新しいゲーム開始"""
        self.logger.log_game_event(GameEvent.GAME_START, "新しいゲームを開始")
        
        # テスト用の初期シーン
        self.game_display.set_background("library.jpg")
        self.text_panel.display_text("図書館にやってきました。静かで落ち着いた雰囲気です。", "ナレーション")
        
        # テスト用選択肢
        test_choices = ["本を探す", "席に座る", "ヒロインを探す"]
        self.text_panel.show_choices(test_choices)
        
        self.statusBar().showMessage("ゲーム開始", 2000)
    
    def save_game(self):
        """ゲームセーブ"""
        success = self.game_state.quick_save()
        if success:
            self.statusBar().showMessage("ゲームをセーブしました", 2000)
            self.logger.log_game_event(GameEvent.SAVE_GAME, "クイックセーブ実行")
        else:
            QMessageBox.warning(self, "エラー", "セーブに失敗しました。")
    
    def load_game(self):
        """ゲームロード"""
        success = self.game_state.quick_load()
        if success:
            self.statusBar().showMessage("ゲームをロードしました", 2000)
            self.logger.log_game_event(GameEvent.LOAD_GAME, "クイックロード実行")
            # TODO: UI状態の復元
        else:
            QMessageBox.warning(self, "エラー", "ロードに失敗しました。")
    
    @pyqtSlot(int, str)
    def on_choice_selected(self, choice_index: int, choice_text: str):
        """選択肢が選ばれた時の処理"""
        self.logger.log_user_choice(
            scene_context=f"{self.game_state.current_location or '不明な場所'}",
            available_choices=self.text_panel.current_choices,
            selected_choice=choice_text,
            choice_index=choice_index
        )
        
        # テスト用レスポンス
        response_text = f"「{choice_text}」を選択しました。"
        self.text_panel.display_text(response_text, "システム")
        
        self.statusBar().showMessage(f"選択: {choice_text}", 2000)
    
    @pyqtSlot(str)
    def on_user_input(self, text: str):
        """ユーザー入力処理"""
        self.logger.info(f"ユーザー入力: {text}")
        # TODO: AI生成処理との連携
    
    # デバッグ機能
    def show_logs(self):
        """ログ表示"""
        log_info = self.logger.get_log_files_info()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("ログ情報")
        dialog.setGeometry(200, 200, 500, 300)
        
        layout = QVBoxLayout()
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        
        log_content = f"セッションID: {log_info['session_id']}\\n"
        log_content += f"ログディレクトリ: {log_info['log_directory']}\\n\\n"
        
        for filename, fileinfo in log_info['files'].items():
            log_content += f"{filename}:\\n"
            log_content += f"  サイズ: {fileinfo['size_kb']} KB\\n"
            log_content += f"  更新: {fileinfo['modified']}\\n\\n"
        
        info_text.setPlainText(log_content)
        layout.addWidget(info_text)
        
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def test_api_connection(self):
        """API接続テスト"""
        try:
            client = get_ollama_client()
            success, message = client.test_connection()
            
            if success:
                QMessageBox.information(self, "API接続テスト", f"✅ 接続成功\\n{message}")
            else:
                QMessageBox.warning(self, "API接続テスト", f"❌ 接続失敗\\n{message}")
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"API接続テストでエラーが発生しました:\\n{str(e)}")
    
    def show_statistics(self):
        """統計情報表示"""
        # 各システムから統計を収集
        log_stats = self.logger.get_session_stats()
        asset_stats = get_asset_manager().get_statistics()
        
        dialog = QDialog(self)
        dialog.setWindowTitle("統計情報")
        dialog.setGeometry(200, 200, 400, 300)
        
        layout = QVBoxLayout()
        
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        
        content = f"""=== ゲーム統計 ===
イベント数: {log_stats['events']}
ユーザー選択回数: {log_stats['choices']}
会話回数: {log_stats['conversations']}

=== アセット統計 ===
キャッシュエントリ: {asset_stats['cache']['entries']}
キャッシュサイズ: {asset_stats['cache']['size_mb']} MB
ヒット率: {asset_stats['cache']['hit_rate']}%

=== パフォーマンス ===
平均読み込み時間: {asset_stats['performance']['average_load_time_ms']} ms
総読み込み数: {asset_stats['performance']['total_loads']}
"""
        
        stats_text.setPlainText(content)
        layout.addWidget(stats_text)
        
        close_button = QPushButton("閉じる")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec()
    
    def closeEvent(self, event):
        """ウィンドウ閉じる時の処理"""
        # セッションサマリー保存
        self.logger.save_session_summary()
        
        # アセット管理クリーンアップ
        get_asset_manager().cleanup()
        
        # ゲーム終了ログ
        self.logger.log_game_event(GameEvent.GAME_END, "アプリケーション終了")
        
        event.accept()
    
    def open_settings(self):
        """設定画面を開く"""
        try:
            # 遅延インポートで循環インポートを回避
            from gui.settings_dialog import SettingsDialog
            
            settings_dialog = SettingsDialog(self)
            result = settings_dialog.exec()
            
            if result == QDialog.DialogCode.Accepted:
                # 設定が変更された場合の処理
                self._refresh_after_settings()
                self.logger.info("設定が更新されました")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"設定画面の表示に失敗しました:\n{e}")
            self.logger.error(f"設定画面エラー: {e}")
    
    def _refresh_after_settings(self):
        """設定更新後のUI更新処理"""
        try:
            # ステータスパネルのモデル表示を更新
            if hasattr(self, 'status_panel'):
                self.status_panel.refresh_status()
                
            # ログレベル反映（必要に応じて）
            config = Config.get_instance()
            
            self.logger.info("設定変更をUIに反映しました")
            
        except Exception as e:
            self.logger.error(f"設定反映エラー: {e}")
    
    def show_about(self):
        """バージョン情報ダイアログ"""
        from PyQt6.QtCore import QT_VERSION_STR, PYQT_VERSION_STR
        import sys
        
        about_text = f"""
<h2>AI Visual Novel Framework</h2>
<p><b>バージョン:</b> 1.0.0</p>
<p><b>説明:</b> Ollama APIを使用したAI駆動のビジュアルノベルエンジン</p>

<h3>システム情報</h3>
<p><b>Python:</b> {sys.version}</p>
<p><b>PyQt6:</b> {PYQT_VERSION_STR}</p>
<p><b>Qt:</b> {QT_VERSION_STR}</p>
<p><b>プラットフォーム:</b> {sys.platform}</p>

<h3>機能</h3>
<ul>
<li>AI ストーリー生成（Ollama API）</li>
<li>キャラクター立ち絵・背景表示</li>
<li>BGM・効果音再生</li>
<li>セーブ・ロード機能</li>
<li>設定カスタマイズ</li>
</ul>

<p>© 2026 AI Visual Novel Framework Project</p>
"""
        
        QMessageBox.about(self, "AI Visual Novel Framework について", about_text)
    
    def test_text_engine(self):
        """テキストエンジンのテスト"""
        test_texts = [
            "こんにちは！これはテキストエンジンのテストです。",
            "これは**太郎**が話すテキストです。タイプライター効果を確認できますか？",
            "長いテキストの表示テストです。このテキストは複数行にわたって表示され、自動的に改行されるはずです。日本語文字の表示も正常に動作することを確認します。",
            "終わりです。次のテストまでお待ちください。[wait]"
        ]
        
        import random
        selected_text = random.choice(test_texts)
        
        try:
            if hasattr(self.text_panel, 'display_text'):
                self.text_panel.display_text(selected_text, "システム", TextSpeed.NORMAL)
                self.logger.info(f"テキストエンジンテスト実行: {selected_text[:30]}...")
            else:
                QMessageBox.warning(self, "エラー", "テキストパネルが利用できません")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"テキストエンジンテストに失敗しました:\n{e}")
            self.logger.error(f"テキストエンジンテストエラー: {e}")
    
    def test_typing_speed(self):
        """タイピング速度のテスト"""
        speed_options = [
            ("瞬間表示", TextSpeed.INSTANT),
            ("高速", TextSpeed.FAST),
            ("標準", TextSpeed.NORMAL),
            ("低速", TextSpeed.SLOW)
        ]
        
        import random
        speed_name, speed = random.choice(speed_options)
        
        test_text = f"これは{speed_name}での表示テストです。文字が一つずつ表示されることを確認してください。"
        
        try:
            if hasattr(self.text_panel, 'display_text'):
                self.text_panel.display_text(test_text, f"速度テスト({speed_name})", speed)
                self.logger.info(f"タイピング速度テスト実行: {speed_name}")
            else:
                QMessageBox.warning(self, "エラー", "テキストパネルが利用できません")
                
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"タイピング速度テストに失敗しました:\n{e}")
            self.logger.error(f"タイピング速度テストエラー: {e}")