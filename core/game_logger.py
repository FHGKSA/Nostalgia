"""
ログ・デバッグシステム
ユーザーの選択肢・会話内容をテキストファイルに記録し、デバッグ情報も管理

機能:
- 全ユーザー操作のログ記録
- 選択肢・会話内容の詳細保存  
- デバッグレベル別出力
- ファイルローテーション
- 色付きコンソール出力
- セッション別ログ管理
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum
import json

import colorlog

from utils.config import Config


class LogLevel(Enum):
    """ログレベルの定義"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class GameEvent(Enum):
    """ゲームイベントタイプ"""
    GAME_START = "game_start"
    GAME_END = "game_end"
    SCENE_CHANGE = "scene_change"
    CHARACTER_INTERACTION = "character_interaction"
    USER_CHOICE = "user_choice"
    STORY_GENERATION = "story_generation"
    AFFECTION_CHANGE = "affection_change"
    FLAG_SET = "flag_set"
    SAVE_GAME = "save_game"
    LOAD_GAME = "load_game"
    ERROR_OCCURRED = "error_occurred"


class GameLogger:
    """ゲーム専用ログシステム"""
    
    _instance: Optional['GameLogger'] = None
    
    def __init__(self):
        """初期化"""
        if GameLogger._instance is not None:
            raise Exception("GameLogger is singleton. Use get_instance().")
        
        self.config = Config.get_instance()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # ログディレクトリの作成
        self.log_dir = self.config.project_root / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # ログファイルパス
        self.game_log_file = self.log_dir / f"game_{self.session_id}.log"
        self.choice_log_file = self.log_dir / f"choices_{self.session_id}.txt" 
        self.debug_log_file = self.log_dir / f"debug_{self.session_id}.log"
        
        # ロガーセットアップ
        self._setup_loggers()
        
        # セッション情報記録用
        self.session_data = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'events': [],
            'user_choices': [],
            'conversations': [],
            'errors': []
        }
        
        GameLogger._instance = self
    
    @classmethod
    def get_instance(cls) -> 'GameLogger':
        """シングルトンインスタンスを取得"""
        if cls._instance is None:
            cls._instance = GameLogger()
        return cls._instance
    
    def _setup_loggers(self) -> None:
        """各種ロガーのセットアップ"""
        # メインゲームロガー
        self.game_logger = logging.getLogger('game')
        self.game_logger.setLevel(logging.INFO)
        
        # ファイルハンドラ（ゲームログ）
        game_handler = logging.FileHandler(
            self.game_log_file, 
            encoding='utf-8'
        )
        game_handler.setLevel(logging.INFO)
        
        # デバッグロガー
        self.debug_logger = logging.getLogger('debug')
        self.debug_logger.setLevel(logging.DEBUG)
        
        # ファイルハンドラ（デバッグログ）
        debug_handler = logging.FileHandler(
            self.debug_log_file,
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        
        # コンソールハンドラ（色付き）
        if self.config.log.console_output:
            console_handler = colorlog.StreamHandler()
            console_handler.setLevel(logging.INFO)
            
            # カラーフォーマット
            color_formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt='%H:%M:%S',
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green', 
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(color_formatter)
            
            self.game_logger.addHandler(console_handler)
            self.debug_logger.addHandler(console_handler)
        
        # ファイルフォーマット
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        game_handler.setFormatter(file_formatter)
        debug_handler.setFormatter(file_formatter)
        
        self.game_logger.addHandler(game_handler)
        self.debug_logger.addHandler(debug_handler)
    
    def log_game_event(self, event_type: GameEvent, description: str, 
                      data: Dict[str, Any] = None) -> None:
        """ゲームイベントをログ記録"""
        timestamp = datetime.now().isoformat()
        
        event_record = {
            'timestamp': timestamp,
            'event_type': event_type.value,
            'description': description,
            'data': data or {}
        }
        
        self.session_data['events'].append(event_record)
        
        # ログ出力
        log_message = f"[{event_type.value.upper()}] {description}"
        if data:
            log_message += f" | Data: {json.dumps(data, ensure_ascii=False)}"
        
        self.game_logger.info(log_message)
    
    def log_user_choice(self, scene_context: str, available_choices: List[str], 
                       selected_choice: str, choice_index: int = -1) -> None:
        """ユーザーの選択肢をログ記録"""
        timestamp = datetime.now().isoformat()
        
        choice_record = {
            'timestamp': timestamp,
            'scene_context': scene_context,
            'available_choices': available_choices,
            'selected_choice': selected_choice,
            'choice_index': choice_index
        }
        
        self.session_data['user_choices'].append(choice_record)
        
        # 専用ファイルに記録（人間が読みやすい形式）
        with open(self.choice_log_file, 'a', encoding='utf-8') as f:
            f.write(f"\\n{'='*60}\\n")
            f.write(f"時刻: {timestamp}\\n")
            f.write(f"シーン: {scene_context}\\n")
            f.write(f"選択肢:\\n")
            for i, choice in enumerate(available_choices, 1):
                marker = " >>> " if choice == selected_choice else "     "
                f.write(f"{marker}{i}. {choice}\\n")
            f.write(f"選択結果: {selected_choice}\\n")
        
        # ゲームログにも記録
        self.log_game_event(
            GameEvent.USER_CHOICE,
            f"ユーザー選択: {selected_choice}",
            {
                'scene': scene_context,
                'choices': available_choices,
                'selected': selected_choice,
                'index': choice_index
            }
        )
    
    def log_conversation(self, character: str, dialogue: str, 
                        is_ai_generated: bool = False, generation_time: float = 0) -> None:
        """会話内容をログ記録"""
        timestamp = datetime.now().isoformat()
        
        conversation_record = {
            'timestamp': timestamp,
            'character': character,
            'dialogue': dialogue,
            'is_ai_generated': is_ai_generated,
            'generation_time': generation_time
        }
        
        self.session_data['conversations'].append(conversation_record)
        
        # ログ出力
        source = "AI生成" if is_ai_generated else "定型"
        self.log_game_event(
            GameEvent.CHARACTER_INTERACTION,
            f"{character}: {dialogue[:50]}...",
            {
                'character': character,
                'full_dialogue': dialogue,
                'source': source,
                'generation_time': generation_time
            }
        )
    
    def log_affection_change(self, character: str, old_value: int, 
                           new_value: int, reason: str = "") -> None:
        """好感度変更をログ記録"""
        change = new_value - old_value
        change_str = f"+{change}" if change > 0 else str(change)
        
        self.log_game_event(
            GameEvent.AFFECTION_CHANGE,
            f"{character}の好感度変化: {old_value} → {new_value} ({change_str})",
            {
                'character': character,
                'old_value': old_value,
                'new_value': new_value,
                'change': change,
                'reason': reason
            }
        )
    
    def log_scene_change(self, old_scene: str, new_scene: str, 
                        location: str = "", time: str = "") -> None:
        """シーン変更をログ記録"""
        self.log_game_event(
            GameEvent.SCENE_CHANGE,
            f"シーン変更: {old_scene} → {new_scene}",
            {
                'old_scene': old_scene,
                'new_scene': new_scene,
                'location': location,
                'time': time
            }
        )
    
    def log_story_generation(self, request_type: str, prompt_summary: str, 
                           response_summary: str, generation_time: float,
                           success: bool = True, error_message: str = "") -> None:
        """AI ストーリー生成をログ記録"""
        self.log_game_event(
            GameEvent.STORY_GENERATION,
            f"{request_type}: {'成功' if success else '失敗'}",
            {
                'request_type': request_type,
                'prompt_summary': prompt_summary,
                'response_summary': response_summary,
                'generation_time': generation_time,
                'success': success,
                'error_message': error_message
            }
        )
    
    def debug(self, message: str, data: Any = None) -> None:
        """デバッグメッセージを出力"""
        if data:
            message += f" | Data: {json.dumps(data, ensure_ascii=False, default=str)}"
        self.debug_logger.debug(message)
    
    def info(self, message: str) -> None:
        """情報メッセージを出力"""
        self.game_logger.info(message)
    
    def warning(self, message: str, data: Any = None) -> None:
        """警告メッセージを出力"""
        if data:
            message += f" | Data: {json.dumps(data, ensure_ascii=False, default=str)}"
        self.game_logger.warning(message)
    
    def error(self, message: str, exception: Exception = None, data: Any = None) -> None:
        """エラーメッセージを出力"""
        error_record = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'exception': str(exception) if exception else None,
            'data': data
        }
        
        self.session_data['errors'].append(error_record)
        
        if exception:
            message += f" | Exception: {str(exception)}"
        if data:
            message += f" | Data: {json.dumps(data, ensure_ascii=False, default=str)}"
        
        self.game_logger.error(message)
        
        # エラーイベントとしても記録
        self.log_game_event(
            GameEvent.ERROR_OCCURRED,
            message,
            error_record
        )
    
    def critical(self, message: str, exception: Exception = None) -> None:
        """クリティカルエラーメッセージを出力"""
        if exception:
            message += f" | Exception: {str(exception)}"
        self.game_logger.critical(message)
    
    def save_session_summary(self) -> None:
        """セッションサマリーを保存"""
        summary_file = self.log_dir / f"session_summary_{self.session_id}.json"
        
        self.session_data['end_time'] = datetime.now().isoformat()
        self.session_data['stats'] = {
            'total_events': len(self.session_data['events']),
            'user_choices': len(self.session_data['user_choices']),
            'conversations': len(self.session_data['conversations']),
            'errors': len(self.session_data['errors'])
        }
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, ensure_ascii=False, indent=2)
            
            self.info(f"セッションサマリーを保存: {summary_file}")
            
        except Exception as e:
            self.error(f"セッションサマリー保存エラー: {str(e)}")
    
    def get_session_stats(self) -> Dict[str, int]:
        """現在のセッション統計を取得"""
        return {
            'events': len(self.session_data['events']),
            'choices': len(self.session_data['user_choices']),
            'conversations': len(self.session_data['conversations']),
            'errors': len(self.session_data['errors'])
        }
    
    def cleanup_old_logs(self, keep_days: int = 7) -> None:
        """古いログファイルをクリーンアップ"""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (keep_days * 24 * 60 * 60)
        
        cleaned_count = 0
        for log_file in self.log_dir.glob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    cleaned_count += 1
                except Exception as e:
                    self.warning(f"ログファイル削除エラー: {log_file} - {str(e)}")
        
        if cleaned_count > 0:
            self.info(f"{cleaned_count}個の古いログファイルを削除しました")
    
    def get_log_files_info(self) -> Dict[str, Any]:
        """ログファイル情報を取得"""
        info = {
            'session_id': self.session_id,
            'log_directory': str(self.log_dir),
            'files': {}
        }
        
        for log_file in [self.game_log_file, self.choice_log_file, self.debug_log_file]:
            if log_file.exists():
                stat = log_file.stat()
                info['files'][log_file.name] = {
                    'size_bytes': stat.st_size,
                    'size_kb': round(stat.st_size / 1024, 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
        
        return info