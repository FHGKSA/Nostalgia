"""
設定ダイアログ
Ollama接続設定とモデル選択機能

機能:
- Ollama IP:Port設定
- モデル一覧取得・表示
- 現在選択モデルの表示・変更
- 設定の保存・適用
"""

import asyncio
from typing import List, Optional, Dict, Any
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLineEdit, QPushButton, QComboBox, QLabel, QTextEdit,
    QTabWidget, QWidget, QProgressBar, QMessageBox,
    QSpacerItem, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QPixmap, QIcon

from utils.config import Config
from core.ollama_client import get_ollama_client
from core.game_logger import GameLogger


class ModelListUpdateThread(QThread):
    """モデル一覧更新の背景処理スレッド"""
    models_updated = pyqtSignal(list)  # モデル一覧更新シグナル
    error_occurred = pyqtSignal(str)   # エラー発生シグナル
    
    def __init__(self, host: str, port: int):
        super().__init__()
        self.host = host
        self.port = port
        
    def run(self):
        """背景でモデル一覧を取得"""
        try:
            ollama_client = get_ollama_client()
            
            # 一時的に接続設定を変更
            original_host = ollama_client.host
            original_port = ollama_client.port
            
            ollama_client.host = self.host
            ollama_client.port = self.port
            
            # モデル一覧を取得
            models = ollama_client.get_available_models()
            
            # 設定を元に戻す
            ollama_client.host = original_host
            ollama_client.port = original_port
            
            self.models_updated.emit(models)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class SettingsDialog(QDialog):
    """設定ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config.get_instance()
        self.logger = GameLogger.get_instance()
        self.ollama_client = get_ollama_client()
        self.model_update_thread = None
        
        self.init_ui()
        self.load_current_settings()
        
    def init_ui(self):
        """UIの初期化"""
        self.setWindowTitle("設定 - AI Visual Novel Framework")
        self.setModal(True)
        self.resize(600, 500)
        
        # フォント設定
        if hasattr(self.parent(), 'get_japanese_font'):
            self.setFont(self.parent().get_japanese_font(10))
        
        layout = QVBoxLayout()
        
        # タブウィジェット
        self.tab_widget = QTabWidget()
        
        # Ollama接続設定タブ
        ollama_tab = self.create_ollama_tab()
        self.tab_widget.addTab(ollama_tab, "Ollama接続設定")
        
        # モデル設定タブ
        model_tab = self.create_model_tab()
        self.tab_widget.addTab(model_tab, "モデル設定")
        
        # システム設定タブ
        system_tab = self.create_system_tab()
        self.tab_widget.addTab(system_tab, "システム設定")
        
        layout.addWidget(self.tab_widget)
        
        # ボタンエリア
        button_layout = self.create_button_layout()
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def create_ollama_tab(self) -> QWidget:
        """Ollama接続設定タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 接続設定グループ
        connection_group = QGroupBox("Ollama サーバー接続設定")
        connection_layout = QFormLayout()
        
        # IP アドレス設定
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("例: 192.168.11.38")
        connection_layout.addRow("IP アドレス:", self.host_edit)
        
        # ポート設定
        self.port_edit = QLineEdit()
        self.port_edit.setPlaceholderText("例: 11434")
        connection_layout.addRow("ポート:", self.port_edit)
        
        # 接続テストボタン
        self.test_connection_btn = QPushButton("接続テスト")
        self.test_connection_btn.clicked.connect(self.test_connection)
        connection_layout.addRow("", self.test_connection_btn)
        
        # 接続状態表示
        self.connection_status_label = QLabel("未接続")
        self.connection_status_label.setStyleSheet("color: gray;")
        connection_layout.addRow("接続状態:", self.connection_status_label)
        
        connection_group.setLayout(connection_layout)
        layout.addWidget(connection_group)
        
        # サーバー情報グループ
        info_group = QGroupBox("サーバー情報")
        info_layout = QFormLayout()
        
        self.server_info_text = QTextEdit()
        self.server_info_text.setMaximumHeight(100)
        self.server_info_text.setReadOnly(True)
        info_layout.addRow("情報:", self.server_info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # スペーサー
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        widget.setLayout(layout)
        return widget
    
    def create_model_tab(self) -> QWidget:
        """モデル設定タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 現在のモデル表示グループ
        current_group = QGroupBox("現在の選択モデル")
        current_layout = QFormLayout()
        
        self.current_model_label = QLabel("未選択")
        self.current_model_label.setStyleSheet("font-weight: bold; color: blue;")
        current_layout.addRow("選択中モデル:", self.current_model_label)
        
        current_group.setLayout(current_layout)
        layout.addWidget(current_group)
        
        # モデル選択グループ
        model_group = QGroupBox("利用可能モデル一覧")
        model_layout = QVBoxLayout()
        
        # 更新ボタンと進捗バー
        update_layout = QHBoxLayout()
        self.update_models_btn = QPushButton("モデル一覧を更新")
        self.update_models_btn.clicked.connect(self.update_model_list)
        
        self.model_update_progress = QProgressBar()
        self.model_update_progress.setVisible(False)
        
        update_layout.addWidget(self.update_models_btn)
        update_layout.addWidget(self.model_update_progress)
        update_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        model_layout.addLayout(update_layout)
        
        # モデル選択コンボボックス
        model_select_layout = QFormLayout()
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_selected)
        model_select_layout.addRow("モデル選択:", self.model_combo)
        
        model_layout.addLayout(model_select_layout)
        
        # モデル情報表示
        self.model_info_text = QTextEdit()
        self.model_info_text.setMaximumHeight(150)
        self.model_info_text.setReadOnly(True)
        model_layout.addWidget(QLabel("選択モデル情報:"))
        model_layout.addWidget(self.model_info_text)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_system_tab(self) -> QWidget:
        """システム設定タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # ログレベル設定
        log_group = QGroupBox("ログ設定")
        log_layout = QFormLayout()
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        log_layout.addRow("ログレベル:", self.log_level_combo)
        
        self.enable_file_log_cb = QCheckBox("ファイルログを有効化")
        log_layout.addRow("", self.enable_file_log_cb)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # キャッシュ設定
        cache_group = QGroupBox("キャッシュ設定")
        cache_layout = QFormLayout()
        
        self.asset_cache_size_edit = QLineEdit()
        self.asset_cache_size_edit.setPlaceholderText("例: 100")
        cache_layout.addRow("アセットキャッシュサイズ:", self.asset_cache_size_edit)
        
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)
        
        # スペーサー
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        widget.setLayout(layout)
        return widget
    
    def create_button_layout(self) -> QHBoxLayout:
        """ボタンレイアウトを作成"""
        layout = QHBoxLayout()
        
        # スペーサー
        layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        # ボタン
        self.apply_btn = QPushButton("適用")
        self.apply_btn.clicked.connect(self.apply_settings)
        
        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self.accept_settings)
        
        self.cancel_btn = QPushButton("キャンセル")
        self.cancel_btn.clicked.connect(self.reject)
        
        layout.addWidget(self.apply_btn)
        layout.addWidget(self.ok_btn)
        layout.addWidget(self.cancel_btn)
        
        return layout
    
    def load_current_settings(self):
        """現在の設定を読み込み"""
        try:
            # Ollama設定
            ollama_config = self.config.ollama
            self.host_edit.setText(ollama_config.host)
            self.port_edit.setText(str(ollama_config.port))
            
            # 現在のモデル表示
            current_model = ollama_config.default_model or '未選択'
            self.current_model_label.setText(current_model)
            
            # システム設定（存在確認してからアクセス）
            if hasattr(self.config, 'log'):
                log_level = self.config.log.level or 'INFO'
                self.log_level_combo.setCurrentText(log_level)
                
                enable_file_log = getattr(self.config.log, 'file_enabled', True)
                self.enable_file_log_cb.setChecked(enable_file_log)
            
            if hasattr(self.config, 'assets'):
                cache_size = self.config.assets.cache_size or 100
                self.asset_cache_size_edit.setText(str(cache_size))
            
            self.logger.info("設定画面に現在の設定を読み込みました")
            
        except Exception as e:
            self.logger.error(f"設定読み込みエラー: {e}")
    
    def test_connection(self):
        """Ollama接続テスト"""
        try:
            self.test_connection_btn.setEnabled(False)
            self.test_connection_btn.setText("テスト中...")
            
            host = self.host_edit.text().strip() or "localhost"
            port = int(self.port_edit.text().strip() or "11434")
            
            # 接続テスト実行
            QTimer.singleShot(100, lambda: self._run_connection_test(host, port))
            
        except ValueError:
            self.connection_status_label.setText("ポート番号が無効です")
            self.connection_status_label.setStyleSheet("color: red;")
            self.test_connection_btn.setEnabled(True)
            self.test_connection_btn.setText("接続テスト")
    
    def _run_connection_test(self, host: str, port: int):
        """接続テストを実行"""
        try:
            # 一時的にクライアント設定を変更
            original_host = self.ollama_client.host
            original_port = self.ollama_client.port
            
            self.ollama_client.host = host
            self.ollama_client.port = port
            
            # 接続テスト
            if self.ollama_client.test_connection():
                self.connection_status_label.setText("接続成功")
                self.connection_status_label.setStyleSheet("color: green;")
                
                # サーバー情報を取得
                models = self.ollama_client.get_available_models()
                server_info = f"接続先: {host}:{port}\n利用可能モデル数: {len(models)}"
                self.server_info_text.setPlainText(server_info)
                
            else:
                self.connection_status_label.setText("接続失敗")
                self.connection_status_label.setStyleSheet("color: red;")
                self.server_info_text.setPlainText("サーバーに接続できませんでした。")
            
            # 設定を元に戻す
            self.ollama_client.host = original_host
            self.ollama_client.port = original_port
            
        except Exception as e:
            self.connection_status_label.setText(f"エラー: {str(e)}")
            self.connection_status_label.setStyleSheet("color: red;")
            self.server_info_text.setPlainText(f"接続エラー: {e}")
            
        finally:
            self.test_connection_btn.setEnabled(True)
            self.test_connection_btn.setText("接続テスト")
    
    def update_model_list(self):
        """モデル一覧を更新"""
        try:
            host = self.host_edit.text().strip() or "localhost"
            port = int(self.port_edit.text().strip() or "11434")
            
            # UI状態の更新
            self.update_models_btn.setEnabled(False)
            self.model_update_progress.setVisible(True)
            self.model_update_progress.setRange(0, 0)  # 不確定進捗
            
            # 背景スレッドでモデル一覧を取得
            self.model_update_thread = ModelListUpdateThread(host, port)
            self.model_update_thread.models_updated.connect(self.on_models_updated)
            self.model_update_thread.error_occurred.connect(self.on_model_update_error)
            self.model_update_thread.finished.connect(self.on_model_update_finished)
            self.model_update_thread.start()
            
        except ValueError:
            QMessageBox.warning(self, "エラー", "ポート番号が無効です。")
    
    @pyqtSlot(list)
    def on_models_updated(self, models: List[str]):
        """モデル一覧更新完了"""
        self.model_combo.clear()
        self.model_combo.addItems(models)
        
        if models:
            self.model_combo.setCurrentText(self.current_model_label.text())
            self.logger.info(f"モデル一覧を更新しました: {len(models)}件")
        else:
            self.logger.warning("利用可能なモデルが見つかりませんでした")
    
    @pyqtSlot(str)
    def on_model_update_error(self, error_msg: str):
        """モデル一覧更新エラー"""
        QMessageBox.critical(self, "エラー", f"モデル一覧の取得に失敗しました:\n{error_msg}")
        self.logger.error(f"モデル一覧取得エラー: {error_msg}")
    
    def on_model_update_finished(self):
        """モデル一覧更新処理完了"""
        self.update_models_btn.setEnabled(True)
        self.model_update_progress.setVisible(False)
        self.model_update_thread = None
    
    def on_model_selected(self, model_name: str):
        """モデル選択時の処理"""
        if model_name:
            # モデル情報を表示（簡単な情報のみ）
            info_text = f"選択モデル: {model_name}\n"
            info_text += f"タイプ: LLM\n"
            info_text += f"状態: 利用可能"
            
            self.model_info_text.setPlainText(info_text)
    
    def apply_settings(self):
        """設定を適用"""
        try:
            # Ollama設定の更新
            new_host = self.host_edit.text().strip() or "localhost"
            new_port = int(self.port_edit.text().strip() or "11434")
            
            self.ollama_client.host = new_host
            self.ollama_client.port = new_port
            
            # 選択モデルの更新
            selected_model = self.model_combo.currentText()
            if selected_model:
                self.current_model_label.setText(selected_model)
            
            # 設定ファイルの更新（YAMLファイルの直接更新）
            import yaml
            from pathlib import Path
            
            config_path = Path.cwd() / "config.yaml"
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Ollama設定の更新
            if 'ollama' not in config_data:
                config_data['ollama'] = {}
            config_data['ollama']['host'] = new_host
            config_data['ollama']['port'] = new_port
            if selected_model:
                config_data['ollama']['default_model'] = selected_model
            
            # システム設定の更新
            if 'logging' not in config_data:
                config_data['logging'] = {}
            config_data['logging']['level'] = self.log_level_combo.currentText()
            config_data['logging']['file_enabled'] = self.enable_file_log_cb.isChecked()
            
            if 'asset_manager' not in config_data:
                config_data['asset_manager'] = {}
            cache_size = int(self.asset_cache_size_edit.text() or "100")
            config_data['asset_manager']['cache_size'] = cache_size
            
            # 設定ファイルに保存
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            QMessageBox.information(self, "成功", "設定を適用しました。")
            self.logger.info("設定が正常に適用されました")
            
        except Exception as e:
            QMessageBox.critical(self, "エラー", f"設定の適用に失敗しました:\n{e}")
            self.logger.error(f"設定適用エラー: {e}")
    
    def accept_settings(self):
        """設定を適用して閉じる"""
        self.apply_settings()
        self.accept()
    
    def closeEvent(self, event):
        """ダイアログ終了時の処理"""
        if self.model_update_thread and self.model_update_thread.isRunning():
            self.model_update_thread.terminate()
            self.model_update_thread.wait()
        event.accept()