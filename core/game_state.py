"""
ゲーム状態管理システム
ビジュアルノベルゲームのすべての状態を統一管理

仕様要件:
- 現在話しているキャラクター、場所、時間帯、キャラクター感情状態
- 現在その場にはいないが登場しているキャラクター
- ストーリーフラグ、好感度フラグ(0-100)
- 現在のシーンタイプ、主人公の状態、現在の目的
- 過去の重要イベント、現在の背景・BGM、キャラクターの位置関係
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

from utils.config import Config


class SceneType(Enum):
    """シーンタイプの定義"""
    CONVERSATION = "会話"
    MOVEMENT = "移動"
    EVENT = "イベント"
    CHOICE = "選択肢"
    BATTLE = "戦闘"
    FLASHBACK = "回想"


class CharacterPosition(Enum):
    """キャラクター画面位置"""
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    HIDDEN = "hidden"


@dataclass
class CharacterState:
    """個別キャラクターの状態"""
    name: str
    affection: int = 0  # 好感度 0-100
    emotion: str = "通常"  # 感情状態
    position: CharacterPosition = CharacterPosition.HIDDEN
    present: bool = False  # 現在その場にいるか
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'name': self.name,
            'affection': self.affection,
            'emotion': self.emotion,
            'position': self.position.value,
            'present': self.present
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterState':
        """辞書から復元"""
        return cls(
            name=data['name'],
            affection=data.get('affection', 0),
            emotion=data.get('emotion', '通常'),
            position=CharacterPosition(data.get('position', 'hidden')),
            present=data.get('present', False)
        )


@dataclass
class VisualState:
    """視覚的状態の管理"""
    background: str = "default"
    bgm: str = ""
    character_images: Dict[str, str] = field(default_factory=dict)  # キャラクター名 -> 画像ファイル名
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VisualState':
        return cls(**data)


@dataclass
class GameSession:
    """ゲームセッション情報"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_played: str = field(default_factory=lambda: datetime.now().isoformat())
    play_time_minutes: int = 0
    
    def update_last_played(self):
        """最終プレイ時間を更新"""
        self.last_played = datetime.now().isoformat()


class GameState:
    """ゲーム状態の統合管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.config = Config.get_instance()
        
        # システム状態
        self.current_character: str = ""  # 現在話しているキャラクター
        self.current_location: str = ""   # 現在の場所
        self.current_time: str = ""       # 時間帯
        self.scene_type: SceneType = SceneType.CONVERSATION
        
        # キャラクター状態管理
        self.characters: Dict[str, CharacterState] = {}
        
        # ゲームプレイ状態
        self.story_flags: Dict[str, bool] = {}  # ストーリーフラグ
        self.protagonist_state: List[str] = []  # 主人公の状態
        self.current_objective: str = ""        # 現在の目的
        self.event_history: List[str] = []      # 過去の重要イベント
        
        # 視覚的状態
        self.visual_state = VisualState()
        
        # セッション情報
        self.session = GameSession()
        
        # 現在のテキストとシナリオ
        self.current_text: str = ""
        self.current_choices: List[str] = []
        
    def add_character(self, name: str, affection: int = 0) -> None:
        """新しいキャラクターを登録"""
        if name not in self.characters:
            self.characters[name] = CharacterState(name=name, affection=affection)
    
    def set_character_affection(self, name: str, affection: int) -> None:
        """キャラクターの好感度を設定"""
        if name in self.characters:
            self.characters[name].affection = max(0, min(100, affection))
    
    def modify_character_affection(self, name: str, change: int) -> None:
        """キャラクターの好感度を変更"""
        if name in self.characters:
            current = self.characters[name].affection
            self.set_character_affection(name, current + change)
    
    def set_character_emotion(self, name: str, emotion: str) -> None:
        """キャラクターの感情を設定"""
        if name in self.characters:
            self.characters[name].emotion = emotion
    
    def set_character_position(self, name: str, position: CharacterPosition) -> None:
        """キャラクターの画面位置を設定"""
        if name in self.characters:
            self.characters[name].position = position
            self.characters[name].present = (position != CharacterPosition.HIDDEN)
    
    def set_story_flag(self, flag_name: str, value: bool = True) -> None:
        """ストーリーフラグを設定"""
        self.story_flags[flag_name] = value
    
    def get_story_flag(self, flag_name: str) -> bool:
        """ストーリーフラグの状態を取得"""
        return self.story_flags.get(flag_name, False)
    
    def add_event_to_history(self, event: str) -> None:
        """イベント履歴に記録"""
        if event not in self.event_history:
            self.event_history.append(event)
    
    def add_protagonist_state(self, state: str) -> None:
        """主人公の状態を追加"""
        if state not in self.protagonist_state:
            self.protagonist_state.append(state)
    
    def remove_protagonist_state(self, state: str) -> None:
        """主人公の状態を削除"""
        if state in self.protagonist_state:
            self.protagonist_state.remove(state)
    
    def get_present_characters(self) -> List[str]:
        """現在その場にいるキャラクターのリスト"""
        return [name for name, char in self.characters.items() if char.present]
    
    def get_absent_characters(self) -> List[str]:
        """登場しているが現在その場にいないキャラクターのリスト"""
        return [name for name, char in self.characters.items() if not char.present and name in self.characters]
    
    def update_scene(self, scene_type: SceneType, location: str = "", 
                    current_character: str = "", time: str = "") -> None:
        """シーン情報を更新"""
        self.scene_type = scene_type
        if location:
            self.current_location = location
        if current_character:
            self.current_character = current_character
        if time:
            self.current_time = time
        
        self.session.update_last_played()
    
    def set_visual_state(self, background: str = "", bgm: str = "", 
                        character_images: Dict[str, str] = None) -> None:
        """視覚的状態を更新"""
        if background:
            self.visual_state.background = background
        if bgm:
            self.visual_state.bgm = bgm
        if character_images:
            self.visual_state.character_images.update(character_images)
    
    def to_dict(self) -> Dict[str, Any]:
        """全状態を辞書形式にエクスポート"""
        return {
            'version': '1.0',
            'system_state': {
                'current_character': self.current_character,
                'current_location': self.current_location,
                'current_time': self.current_time,
                'scene_type': self.scene_type.value
            },
            'characters': {name: char.to_dict() for name, char in self.characters.items()},
            'gameplay_state': {
                'story_flags': self.story_flags,
                'protagonist_state': self.protagonist_state,
                'current_objective': self.current_objective,
                'event_history': self.event_history
            },
            'visual_state': self.visual_state.to_dict(),
            'session': asdict(self.session),
            'current_content': {
                'text': self.current_text,
                'choices': self.current_choices
            }
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """辞書からゲーム状態を復元"""
        # システム状態
        sys_state = data.get('system_state', {})
        self.current_character = sys_state.get('current_character', '')
        self.current_location = sys_state.get('current_location', '')
        self.current_time = sys_state.get('current_time', '')
        scene_value = sys_state.get('scene_type', 'CONVERSATION')
        self.scene_type = SceneType(scene_value) if isinstance(scene_value, str) else SceneType.CONVERSATION
        
        # キャラクター状態
        char_data = data.get('characters', {})
        self.characters = {}
        for name, char_dict in char_data.items():
            self.characters[name] = CharacterState.from_dict(char_dict)
        
        # ゲームプレイ状態
        gameplay_state = data.get('gameplay_state', {})
        self.story_flags = gameplay_state.get('story_flags', {})
        self.protagonist_state = gameplay_state.get('protagonist_state', [])
        self.current_objective = gameplay_state.get('current_objective', '')
        self.event_history = gameplay_state.get('event_history', [])
        
        # 視覚的状態
        visual_data = data.get('visual_state', {})
        self.visual_state = VisualState.from_dict(visual_data)
        
        # セッション情報
        session_data = data.get('session', {})
        if session_data:
            self.session = GameSession(**session_data)
        
        # 現在のコンテンツ
        current_content = data.get('current_content', {})
        self.current_text = current_content.get('text', '')
        self.current_choices = current_content.get('choices', [])
    
    def save_to_file(self, filepath: Optional[Path] = None) -> bool:
        """ゲーム状態をファイルに保存"""
        try:
            if filepath is None:
                # data/saves/ディレクトリにセッションIDベースで保存
                save_dir = self.config.project_root / "data" / "saves"
                save_dir.mkdir(parents=True, exist_ok=True)
                filepath = save_dir / f"save_{self.session.session_id[:8]}.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
            
            print(f"ゲーム状態を保存しました: {filepath}")
            return True
            
        except Exception as e:
            print(f"保存エラー: {e}")
            return False
    
    def load_from_file(self, filepath: Path) -> bool:
        """ファイルからゲーム状態を読み込み"""
        try:
            if not filepath.exists():
                print(f"セーブファイルが見つかりません: {filepath}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.from_dict(data)
            print(f"ゲーム状態を読み込みました: {filepath}")
            return True
            
        except Exception as e:
            print(f"読み込みエラー: {e}")
            return False
    
    def get_quick_save_path(self) -> Path:
        """クイックセーブファイルパス"""
        save_dir = self.config.project_root / "data" / "saves"
        save_dir.mkdir(parents=True, exist_ok=True)
        return save_dir / "quicksave.json"
    
    def quick_save(self) -> bool:
        """クイックセーブ"""
        return self.save_to_file(self.get_quick_save_path())
    
    def quick_load(self) -> bool:
        """クイックロード"""
        return self.load_from_file(self.get_quick_save_path())
    
    def get_status_summary(self) -> str:
        """ゲーム状態の概要を文字列で取得（デバッグ用）"""
        present_chars = self.get_present_characters()
        return f"""
=== ゲーム状態サマリー ===
場所: {self.current_location}
時間: {self.current_time}
シーン: {self.scene_type.value}
会話相手: {self.current_character}
その場にいるキャラクター: {', '.join(present_chars)}
主人公状態: {', '.join(self.protagonist_state)}
目的: {self.current_objective}
ストーリーフラグ数: {len(self.story_flags)}
イベント履歴数: {len(self.event_history)}
背景: {self.visual_state.background}
BGM: {self.visual_state.bgm}
セッション時間: {self.session.play_time_minutes}分
        """.strip()


# シングルトンのゲーム状態インスタンス
_game_state_instance: Optional[GameState] = None

def get_game_state() -> GameState:
    """ゲーム状態のシングルトンインスタンスを取得"""
    global _game_state_instance
    if _game_state_instance is None:
        _game_state_instance = GameState()
    return _game_state_instance