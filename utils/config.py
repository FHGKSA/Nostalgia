"""
設定管理システム
アプリケーション全体の設定を統一管理
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class OllamaConfig:
    """Ollama API設定"""
    host: str = "192.168.11.38"
    port: int = 11434
    timeout: int = 30
    model_name: str = "japanese_vn_model"
    default_model: str = "japanese_vn_model"
    
    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass
class AssetConfig:
    """アセット設定"""
    background_dir: str = "背景"
    character_dir: str = "立ち絵"
    bgm_dir: str = "BGM"
    prompt_dir: str = "初期プロンプト"
    cache_size: int = 50  # MBでのキャッシュサイズ
    image_quality: int = 95  # JPEG品質 (1-100)


@dataclass
class WindowConfig:
    """ウィンドウ設定"""
    width: int = 1280
    height: int = 720
    title: str = "AI Visual Novel Engine"
    resizable: bool = True
    fullscreen_available: bool = True


@dataclass
class AnimationConfig:
    """アニメーション設定"""
    fade_duration: int = 500  # ms
    slide_duration: int = 800  # ms
    text_typing_speed: int = 50  # ms per character
    easing_curve: str = "ease_in_out"


@dataclass
class TextConfig:
    """テキスト表示設定"""
    typing_speed: int = 30  # ms per character
    character_delay: int = 50  # ms
    auto_advance_time: int = 3000  # ms
    font_size: int = 16
    line_height: float = 1.2
    text_color: str = "#ffffff"
    background_color: str = "rgba(0,0,0,0.7)"
    border_color: str = "#444444"
    ruby_size_ratio: float = 0.6
    outline_enabled: bool = True
    outline_color: str = "#000000"
    outline_width: int = 1
    history_max_lines: int = 500


@dataclass
class LogConfig:
    """ログ設定"""
    level: str = "INFO"
    file_path: str = "logs/game.log"
    file_enabled: bool = True
    max_size: int = 10  # MB
    backup_count: int = 5
    console_output: bool = True


class Config:
    """設定管理の単一インスタンス"""
    _instance: Optional['Config'] = None
    
    def __init__(self):
        if Config._instance is not None:
            raise Exception("Config is singleton. Use get_instance().")
        
        self.project_root = Path(__file__).parent.parent
        self.config_file = self.project_root / "config.yaml"
        
        # デフォルト設定
        self.ollama = OllamaConfig()
        self.assets = AssetConfig()
        self.window = WindowConfig()
        self.animation = AnimationConfig()
        self.text = TextConfig()
        self.log = LogConfig()
        
        Config._instance = self
    
    @classmethod
    def get_instance(cls) -> 'Config':
        """シングルトンインスタンス取得"""
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance
    
    def load_config(self) -> None:
        """設定ファイルから読み込み"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if data:
                    self._update_from_dict(data)
                    print(f"設定を読み込みました: {self.config_file}")
            else:
                print("設定ファイルが存在しません。デフォルト設定を使用します。")
                self.save_config()  # デフォルト設定を保存
                
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")
    
    def save_config(self) -> None:
        """設定ファイルに保存"""
        try:
            config_dict = {
                'ollama': asdict(self.ollama),
                'assets': asdict(self.assets),
                'window': asdict(self.window),
                'animation': asdict(self.animation),
                'text': asdict(self.text),
                'log': asdict(self.log)
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            print(f"設定を保存しました: {self.config_file}")
            
        except Exception as e:
            print(f"設定ファイル保存エラー: {e}")    
    def get(self, section: str, default=None):
        """設定値を取得（辞書形式インターフェース）"""
        if hasattr(self, section):
            section_obj = getattr(self, section)
            if hasattr(section_obj, '__dict__'):
                # データクラスの場合は辞書に変換
                return asdict(section_obj)
            else:
                return section_obj
        return default or {}    
    def _update_from_dict(self, data: Dict[str, Any]) -> None:
        """辞書から設定を更新"""
        if 'ollama' in data:
            self.ollama = OllamaConfig(**data['ollama'])
        if 'assets' in data:
            self.assets = AssetConfig(**data['assets'])
        if 'window' in data:
            self.window = WindowConfig(**data['window'])
        if 'animation' in data:
            self.animation = AnimationConfig(**data['animation'])
        if 'log' in data:
            self.log = LogConfig(**data['log'])
    
    def get_asset_path(self, asset_type: str, filename: str = "") -> Path:
        """アセットの絶対パスを取得"""
        asset_dirs = {
            'background': self.assets.background_dir,
            'character': self.assets.character_dir,
            'bgm': self.assets.bgm_dir,
            'prompt': self.assets.prompt_dir
        }
        
        if asset_type not in asset_dirs:
            raise ValueError(f"Unknown asset type: {asset_type}")
        
        base_path = self.project_root / asset_dirs[asset_type]
        
        if filename:
            return base_path / filename
        
        return base_path
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書として出力（デバッグ用）"""
        return {
            'ollama': asdict(self.ollama),
            'assets': asdict(self.assets),
            'window': asdict(self.window),
            'animation': asdict(self.animation),
            'log': asdict(self.log)
        }


# 設定の型ヒント用エイリアス
ConfigType = Config