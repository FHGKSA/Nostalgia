"""
テキスト表示エンジン
ビジュアルノベル用の高機能テキスト表示システム

機能:
- タイプライター効果
- ルビ（ふりがな）表示
- テキストスタイル（色、サイズ、装飾）
- 履歴機能
- 自動進行
- テキストボックス表示
- クリック待ち
"""

import re
import time
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
    QScrollArea, QPushButton, QFrame
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QTextCharFormat, QTextCursor

from utils.config import Config
from core.game_logger import GameLogger


class TextSpeed(Enum):
    """テキスト表示速度"""
    INSTANT = 0
    FAST = 20
    NORMAL = 50
    SLOW = 100


@dataclass
class TextStyle:
    """テキストスタイル定義"""
    font_family: str = "Noto Sans CJK JP"
    font_size: int = 16
    color: str = "#ffffff"
    bold: bool = False
    italic: bool = False
    outline_enabled: bool = True
    outline_color: str = "#000000"
    outline_width: int = 1
    background_color: str = "transparent"


@dataclass
class RubyText:
    """ルビ（ふりがな）テキスト"""
    base_text: str      # 親文字
    ruby_text: str      # ルビ文字
    start_pos: int      # 開始位置
    end_pos: int        # 終了位置


@dataclass
class TextSegment:
    """テキストセグメント（スタイル付きテキストの単位）"""
    text: str
    style: TextStyle = field(default_factory=TextStyle)
    ruby_list: List[RubyText] = field(default_factory=list)
    click_wait: bool = False  # このセグメント後でクリック待ち


class TextHistory:
    """テキスト履歴管理"""
    
    def __init__(self, max_lines: int = 500):
        self.max_lines = max_lines
        self.history: List[str] = []
        self.current_index = -1
    
    def add_text(self, text: str):
        """履歴にテキストを追加"""
        self.history.append(text)
        if len(self.history) > self.max_lines:
            self.history.pop(0)
        self.current_index = len(self.history) - 1
    
    def get_history(self) -> List[str]:
        """履歴を取得"""
        return self.history.copy()
    
    def clear_history(self):
        """履歴をクリア"""
        self.history.clear()
        self.current_index = -1


class TextParser:
    """テキストパーサー（マークアップ解析）"""
    
    def __init__(self):
        self.logger = GameLogger.get_instance()
        
    def parse(self, text: str) -> List[TextSegment]:
        """テキストをパース（マークアップ対応）"""
        try:
            segments = []
            current_pos = 0
            
            # ルビ記法の正規表現: 漢字《ひらがな》
            ruby_pattern = r'([^《]+)《([^》]+)》'
            
            # スタイル記法の正規表現: <color=#ff0000>テキスト</color>
            style_pattern = r'<(\w+)=([^>]+)>([^<]*)</\1>'
            
            # クリック待ち記法: [wait] または [w]
            wait_pattern = r'\[(wait|w)\]'
            
            # まずルビを処理
            text_with_ruby = self._process_ruby(text)
            
            # 次にスタイルを処理
            segments = self._process_styles(text_with_ruby)
            
            # クリック待ちを処理
            segments = self._process_wait_points(segments)
            
            return segments
            
        except Exception as e:
            self.logger.error(f"テキストパース エラー: {e}")
            # エラー時はプレーンテキストとして返す
            return [TextSegment(text=text)]
    
    def _process_ruby(self, text: str) -> str:
        """ルビ記法を処理"""
        # 実装は後で詳細化
        return text
    
    def _process_styles(self, text: str) -> List[TextSegment]:
        """スタイル記法を処理"""
        # 実装は後で詳細化
        return [TextSegment(text=text)]
    
    def _process_wait_points(self, segments: List[TextSegment]) -> List[TextSegment]:
        """クリック待ちポイントを処理"""
        # 実装は後で詳細化
        return segments


class TypewriterEffect:
    """タイプライター効果"""
    
    def __init__(self, parent_widget: QWidget):
        self.parent = parent_widget
        self.timer = QTimer()
        self.timer.timeout.connect(self._type_next_character)
        
        self.current_segment: Optional[TextSegment] = None
        self.current_text = ""
        self.current_pos = 0
        self.typing_speed = TextSpeed.NORMAL.value
        self.is_typing = False
        
        self.on_typing_complete: Optional[Callable] = None
        self.on_character_typed: Optional[Callable[[str], None]] = None
        
        self.config = Config.get_instance()
        self.logger = GameLogger.get_instance()
    
    def start_typing(self, segment: TextSegment, speed: TextSpeed = TextSpeed.NORMAL):
        """タイピング開始"""
        try:
            self.current_segment = segment
            self.current_text = segment.text
            self.current_pos = 0
            self.typing_speed = speed.value
            self.is_typing = True
            
            if speed == TextSpeed.INSTANT:
                # 瞬間表示
                self._complete_typing()
            else:
                # タイマー開始
                self.timer.start(self.typing_speed)
                
        except Exception as e:
            self.logger.error(f"タイピング開始エラー: {e}")
    
    def _type_next_character(self):
        """次の文字をタイプ"""
        try:
            if self.current_pos < len(self.current_text):
                char = self.current_text[self.current_pos]
                
                # 文字タイプのコールバック実行
                if self.on_character_typed:
                    self.on_character_typed(char)
                
                self.current_pos += 1
            else:
                # タイピング完了
                self._complete_typing()
                
        except Exception as e:
            self.logger.error(f"文字タイプエラー: {e}")
            self._complete_typing()
    
    def _complete_typing(self):
        """タイピング完了"""
        self.timer.stop()
        self.is_typing = False
        
        if self.on_typing_complete:
            self.on_typing_complete()
    
    def skip_typing(self):
        """タイピングをスキップ"""
        if self.is_typing:
            self._complete_typing()
            # 残りのテキストを即座に表示
            if self.on_character_typed:
                remaining_text = self.current_text[self.current_pos:]
                for char in remaining_text:
                    self.on_character_typed(char)
    
    def is_active(self) -> bool:
        """タイピング中かどうかを判定"""
        return self.is_typing


class TextBox(QFrame):
    """テキストボックスウィジェット"""
    
    # シグナル定義
    text_completed = pyqtSignal()
    click_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.config = Config.get_instance()
        self.logger = GameLogger.get_instance()
        
        self.current_text = ""
        self.displayed_text = ""
        
        self._setup_ui()
        self._setup_typewriter()
    
    def _setup_ui(self):
        """UIセットアップ"""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 10, 15, 10)
        
        # テキスト表示ラベル
        self.text_label = QLabel()
        self.text_label.setWordWrap(True)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # スタイル設定
        self._apply_text_style()
        
        layout.addWidget(self.text_label)
        self.setLayout(layout)
        
        # テキストボックスのスタイル
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.config.text.background_color};
                border: 2px solid {self.config.text.border_color};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
    
    def _apply_text_style(self):
        """テキストスタイル適用"""
        try:
            # 日本語フォント設定
            if hasattr(self.parent(), 'get_japanese_font'):
                font = self.parent().get_japanese_font(self.config.text.font_size)
            else:
                font = QFont("Noto Sans CJK JP", self.config.text.font_size)
            
            self.text_label.setFont(font)
            
            # CSS スタイル設定
            style_sheet = f"""
                QLabel {{
                    color: {self.config.text.text_color};
                    line-height: {int(self.config.text.font_size * self.config.text.line_height)}px;
                }}
            """
            
            if self.config.text.outline_enabled:
                # アウトライン効果（CSS shadow で近似）
                style_sheet += f"""
                    text-shadow: 
                        {self.config.text.outline_width}px {self.config.text.outline_width}px 0px {self.config.text.outline_color},
                        -{self.config.text.outline_width}px {self.config.text.outline_width}px 0px {self.config.text.outline_color},
                        {self.config.text.outline_width}px -{self.config.text.outline_width}px 0px {self.config.text.outline_color},
                        -{self.config.text.outline_width}px -{self.config.text.outline_width}px 0px {self.config.text.outline_color};
                """
            
            self.text_label.setStyleSheet(style_sheet)
            
        except Exception as e:
            self.logger.error(f"テキストスタイル適用エラー: {e}")
    
    def _setup_typewriter(self):
        """タイプライター効果セットアップ"""
        self.typewriter = TypewriterEffect(self)
        self.typewriter.on_character_typed = self._on_character_typed
        self.typewriter.on_typing_complete = self._on_typing_complete
    
    def display_text(self, text: str, speed: TextSpeed = TextSpeed.NORMAL):
        """テキストを表示"""
        try:
            self.current_text = text
            self.displayed_text = ""
            self.text_label.setText("")
            
            # テキストをパースしてセグメントに分割
            parser = TextParser()
            segments = parser.parse(text)
            
            if segments:
                # 最初のセグメントからタイピング開始
                self.typewriter.start_typing(segments[0], speed)
            
        except Exception as e:
            self.logger.error(f"テキスト表示エラー: {e}")
            self.text_label.setText(text)  # エラー時は即座に表示
    
    def _on_character_typed(self, char: str):
        """文字がタイプされた時のコールバック"""
        self.displayed_text += char
        self.text_label.setText(self.displayed_text)
    
    def _on_typing_complete(self):
        """タイピング完了時のコールバック"""
        self.text_completed.emit()
    
    def skip_typewriter(self):
        """タイプライター効果をスキップ"""
        self.typewriter.skip_typing()
    
    def clear_text(self):
        """テキストをクリア"""
        self.current_text = ""
        self.displayed_text = ""
        self.text_label.setText("")
        
    def is_typing(self) -> bool:
        """タイピング中かどうかを判定"""
        return self.typewriter.is_active()
    
    def mousePressEvent(self, event):
        """マウスクリック処理"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_typing():
                self.skip_typewriter()
            else:
                self.click_requested.emit()
        super().mousePressEvent(event)


class TextEngine:
    """テキストエンジン（メインクラス）"""
    
    def __init__(self, text_widget: QWidget):
        self.text_widget = text_widget
        self.config = Config.get_instance()
        self.logger = GameLogger.get_instance()
        
        # コンポーネント初期化
        self.history = TextHistory(self.config.text.history_max_lines)
        self.parser = TextParser()
        
        # 状態管理
        self.current_segments: List[TextSegment] = []
        self.current_segment_index = 0
        self.is_auto_advance = False
        self.auto_advance_timer = QTimer()
        self.auto_advance_timer.timeout.connect(self._auto_advance)
        
        # テキストボックス作成
        self.text_box = TextBox(text_widget)
        self.text_box.text_completed.connect(self._on_text_completed)
        self.text_box.click_requested.connect(self._on_click_requested)
        
        # レイアウトに追加
        if hasattr(text_widget, 'layout') and text_widget.layout():
            text_widget.layout().addWidget(self.text_box)
        
        self.logger.info("テキストエンジンが初期化されました")
    
    def display_text(self, text: str, auto_advance: bool = False, speed: TextSpeed = TextSpeed.NORMAL):
        """テキストを表示"""
        try:
            # 履歴に追加
            self.history.add_text(text)
            
            # テキストをパース
            self.current_segments = self.parser.parse(text)
            self.current_segment_index = 0
            self.is_auto_advance = auto_advance
            
            # 最初のセグメントを表示
            if self.current_segments:
                self._display_current_segment(speed)
            
            self.logger.info(f"テキスト表示開始: {text[:50]}...")
            
        except Exception as e:
            self.logger.error(f"テキスト表示エラー: {e}")
    
    def _display_current_segment(self, speed: TextSpeed):
        """現在のセグメントを表示"""
        if self.current_segment_index < len(self.current_segments):
            segment = self.current_segments[self.current_segment_index]
            self.text_box.display_text(segment.text, speed)
    
    def _on_text_completed(self):
        """テキスト表示完了時の処理"""
        current_segment = self.current_segments[self.current_segment_index]
        
        if current_segment.click_wait:
            # クリック待ち
            return
        
        if self.is_auto_advance:
            # 自動進行タイマー開始
            self.auto_advance_timer.start(self.config.text.auto_advance_time)
        
    def _on_click_requested(self):
        """クリック要求時の処理"""
        if self.auto_advance_timer.isActive():
            self.auto_advance_timer.stop()
        
        self._advance_to_next_segment()
    
    def _auto_advance(self):
        """自動進行"""
        self.auto_advance_timer.stop()
        self._advance_to_next_segment()
    
    def _advance_to_next_segment(self):
        """次のセグメントに進む"""
        self.current_segment_index += 1
        
        if self.current_segment_index < len(self.current_segments):
            # 次のセグメント表示
            self._display_current_segment(TextSpeed.NORMAL)
        else:
            # 全セグメント完了
            self.logger.info("全テキストセグメント表示完了")
    
    def get_history(self) -> List[str]:
        """履歴を取得"""
        return self.history.get_history()
    
    def clear_text(self):
        """テキストをクリア"""
        self.text_box.clear_text()
        self.auto_advance_timer.stop()
    
    def skip_current_text(self):
        """現在のテキストをスキップ"""
        self.text_box.skip_typewriter()
        self.auto_advance_timer.stop()


# シングルトンインスタンス
_text_engine_instance: Optional[TextEngine] = None

def get_text_engine(text_widget: QWidget = None) -> TextEngine:
    """テキストエンジンのシングルトンインスタンス取得"""
    global _text_engine_instance
    if _text_engine_instance is None:
        if text_widget is None:
            raise ValueError("テキストエンジンの初期化にはtext_widgetが必要です")
        _text_engine_instance = TextEngine(text_widget)
    return _text_engine_instance