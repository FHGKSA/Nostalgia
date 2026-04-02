"""
アセット管理システム
画像・音声ファイルのキャッシュ機能、メモリ効率管理、ホットリロード

機能:
- 画像・音声ファイルの高速キャッシュ
- メモリ使用量制限とLRU管理
- ファイル自動監視（開発時のホットリロード）
- 高品質リサンプリング（画像）
- 対応形式の自動判定
- 遅延読み込み
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from collections import OrderedDict
import threading
from dataclasses import dataclass
from enum import Enum

from PIL import Image, ImageOps
import pygame.mixer

from utils.config import Config
from core.game_logger import GameLogger


class AssetType(Enum):
    """アセットタイプの定義"""
    IMAGE = "image"
    AUDIO = "audio"
    UNKNOWN = "unknown"


@dataclass
class CacheEntry:
    """キャッシュエントリ"""
    asset_path: Path
    asset_type: AssetType
    data: Any
    size_bytes: int
    access_time: float
    load_time: float
    
    def touch(self) -> None:
        """アクセス時間を更新"""
        self.access_time = time.time()


class AssetCache:
    """LRU キャッシュ実装"""
    
    def __init__(self, max_size_mb: int = 50):
        """初期化"""
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.current_size = 0
        self.hit_count = 0
        self.miss_count = 0
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[CacheEntry]:
        """キャッシュから取得"""
        with self._lock:
            if key in self.cache:
                entry = self.cache[key]
                entry.touch()
                # LRU: 最近使用したものを末尾に移動
                self.cache.move_to_end(key)
                self.hit_count += 1
                return entry
            else:
                self.miss_count += 1
                return None
    
    def put(self, key: str, entry: CacheEntry) -> None:
        """キャッシュに格納"""
        with self._lock:
            # 既存エントリがあれば削除
            if key in self.cache:
                old_entry = self.cache.pop(key)
                self.current_size -= old_entry.size_bytes
            
            # 新しいエントリを追加
            self.cache[key] = entry
            self.current_size += entry.size_bytes
            
            # サイズ制限を超えた場合、古いエントリを削除
            while self.current_size > self.max_size_bytes and self.cache:
                oldest_key, oldest_entry = self.cache.popitem(last=False)
                self.current_size -= oldest_entry.size_bytes
    
    def remove(self, key: str) -> bool:
        """キャッシュから削除"""
        with self._lock:
            if key in self.cache:
                entry = self.cache.pop(key)
                self.current_size -= entry.size_bytes
                return True
            return False
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        with self._lock:
            self.cache.clear()
            self.current_size = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        total_accesses = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_accesses * 100) if total_accesses > 0 else 0
        
        return {
            'entries': len(self.cache),
            'size_mb': round(self.current_size / (1024 * 1024), 2),
            'max_size_mb': round(self.max_size_bytes / (1024 * 1024), 2),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': round(hit_rate, 1)
        }


class AssetWatcher:
    """ファイル監視（ホットリロード用）"""
    
    def __init__(self, watch_directories: List[Path], callback):
        """初期化"""
        self.watch_dirs = watch_directories
        self.callback = callback
        self.file_mtimes: Dict[str, float] = {}
        self.running = False
        self.watch_thread = None
    
    def start_watching(self) -> None:
        """監視開始"""
        if not self.running:
            self.running = True
            self.watch_thread = threading.Thread(target=self._watch_loop, daemon=True)
            self.watch_thread.start()
    
    def stop_watching(self) -> None:
        """監視停止"""
        self.running = False
        if self.watch_thread:
            self.watch_thread.join()
    
    def _watch_loop(self) -> None:
        """監視ループ"""
        while self.running:
            try:
                self._check_file_changes()
                time.sleep(1.0)  # 1秒間隔で監視
            except Exception as e:
                # エラーは無視して継続
                pass
    
    def _check_file_changes(self) -> None:
        """ファイル変更をチェック"""
        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue
            
            for file_path in watch_dir.rglob('*'):
                if file_path.is_file():
                    str_path = str(file_path)
                    try:
                        current_mtime = file_path.stat().st_mtime
                        old_mtime = self.file_mtimes.get(str_path, 0)
                        
                        if current_mtime != old_mtime:
                            self.file_mtimes[str_path] = current_mtime
                            if old_mtime > 0:  # 初回は通知しない
                                self.callback(file_path, 'modified')
                                
                    except Exception:
                        # ファイルアクセスエラーは無視
                        pass


class AssetManager:
    """アセット管理の統合システム"""
    
    def __init__(self):
        """初期化"""
        self.config = Config.get_instance()
        self.logger = GameLogger.get_instance()
        
        # キャッシュシステム
        self.cache = AssetCache(self.config.assets.cache_size)
        
        # pygame の音声システム初期化
        try:
            pygame.mixer.init() 
            self.audio_available = True
        except Exception as e:
            self.logger.warning(f"音声システム初期化失敗: {e}")
            self.audio_available = False
        
        # 対応ファイル形式
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        self.audio_extensions = {'.wav', '.mp3', '.ogg', '.flac', '.m4a'}
        
        # ファイル監視システム
        watch_dirs = [
            self.config.get_asset_path('background'),
            self.config.get_asset_path('character'),
            self.config.get_asset_path('bgm')
        ]
        self.file_watcher = AssetWatcher(watch_dirs, self._on_file_changed)
        
        # 統計情報
        self.load_times: List[float] = []
        self.error_count = 0
        
        self.logger.info("アセット管理システム初期化完了")
    
    def start_file_watching(self) -> None:
        """ファイル監視を開始"""
        self.file_watcher.start_watching()
        self.logger.info("ファイル監視を開始しました")
    
    def stop_file_watching(self) -> None:
        """ファイル監視を停止"""
        self.file_watcher.stop_watching()
        self.logger.info("ファイル監視を停止しました")
    
    def _on_file_changed(self, file_path: Path, event_type: str) -> None:
        """ファイル変更時のコールバック"""
        relative_path = str(file_path.relative_to(self.config.project_root))
        self.cache.remove(relative_path)
        self.logger.debug(f"ファイル変更感知: {relative_path} - キャッシュクリア")
    
    def _determine_asset_type(self, file_path: Path) -> AssetType:
        """ファイル形式からアセットタイプを判定"""
        extension = file_path.suffix.lower()
        if extension in self.image_extensions:
            return AssetType.IMAGE
        elif extension in self.audio_extensions:
            return AssetType.AUDIO
        else:
            return AssetType.UNKNOWN
    
    def _load_image(self, file_path: Path, target_size: Optional[Tuple[int, int]] = None) -> Optional[Image.Image]:
        """画像ファイルを読み込み"""
        try:
            start_time = time.time()
            
            # PIL で画像を読み込み
            image = Image.open(file_path)
            
            # RGBA変換（透明度対応）
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # リサイズ（高品質）
            if target_size:
                # アスペクト比を維持してリサイズ
                image = ImageOps.contain(image, target_size, Image.Resampling.LANCZOS)
            
            load_time = (time.time() - start_time) * 1000
            self.load_times.append(load_time)
            
            self.logger.debug(f"画像読み込み完了: {file_path.name} ({load_time:.1f}ms)")
            return image
            
        except Exception as e:
            self.logger.error(f"画像読み込みエラー: {file_path}", exception=e)
            self.error_count += 1
            return None
    
    def _load_audio(self, file_path: Path) -> Optional[pygame.mixer.Sound]:
        """音声ファイルを読み込み"""
        if not self.audio_available:
            return None
        
        try:
            start_time = time.time()
            
            sound = pygame.mixer.Sound(str(file_path))
            
            load_time = (time.time() - start_time) * 1000
            self.load_times.append(load_time)
            
            self.logger.debug(f"音声読み込み完了: {file_path.name} ({load_time:.1f}ms)")
            return sound
            
        except Exception as e:
            self.logger.error(f"音声読み込みエラー: {file_path}", exception=e)
            self.error_count += 1
            return None
    
    def get_asset(self, asset_type: str, filename: str, target_size: Optional[Tuple[int, int]] = None) -> Optional[Any]:
        """アセットを取得（キャッシュ優先）"""
        # ファイルパス構築
        try:
            file_path = self.config.get_asset_path(asset_type, filename)
        except ValueError as e:
            self.logger.error(f"不正なアセットタイプ: {asset_type}")
            return None
        
        if not file_path.exists():
            self.logger.warning(f"アセットファイルが見つかりません: {file_path}")
            return None
        
        # キャッシュキー生成
        cache_key = f"{asset_type}:{filename}"
        if target_size:
            cache_key += f":{target_size[0]}x{target_size[1]}"
        
        # キャッシュから取得試行
        cached_entry = self.cache.get(cache_key)
        if cached_entry:
            return cached_entry.data
        
        # ファイル読み込み
        asset_file_type = self._determine_asset_type(file_path)
        data = None
        
        if asset_file_type == AssetType.IMAGE:
            data = self._load_image(file_path, target_size)
        elif asset_file_type == AssetType.AUDIO:
            data = self._load_audio(file_path)
        
        if data is None:
            return None
        
        # キャッシュに保存
        try:
            # サイズ専暵（概算）
            if asset_file_type == AssetType.IMAGE:
                size_bytes = data.size[0] * data.size[1] * 4  # RGBA
            elif asset_file_type == AssetType.AUDIO:
                size_bytes = len(data.get_raw()) if hasattr(data, 'get_raw') else 1024
            else:
                size_bytes = 1024
            
            entry = CacheEntry(
                asset_path=file_path,
                asset_type=asset_file_type,
                data=data,
                size_bytes=size_bytes,
                access_time=time.time(),
                load_time=self.load_times[-1] if self.load_times else 0
            )
            
            self.cache.put(cache_key, entry)
            
        except Exception as e:
            self.logger.warning(f"キャッシュ保存エラー: {e}")
        
        return data
    
    def get_background(self, filename: str, target_size: Optional[Tuple[int, int]] = None) -> Optional[Image.Image]:
        """背景画像を取得"""
        return self.get_asset('background', filename, target_size)
    
    def get_character_image(self, character: str, filename: str, target_size: Optional[Tuple[int, int]] = None) -> Optional[Image.Image]:
        """キャラクター画像を取得"""
        char_path = Path(character) / filename
        return self.get_asset('character', str(char_path), target_size)
    
    def get_bgm(self, filename: str) -> Optional[pygame.mixer.Sound]:
        """BGM音声を取得"""
        return self.get_asset('bgm', filename)
    
    def preload_assets(self, asset_list: List[Tuple[str, str]]) -> None:
        """アセットの事前読み込み"""
        self.logger.info(f"アセット事前読み込み開始: {len(asset_list)}個")
        
        loaded_count = 0
        for asset_type, filename in asset_list:
            try:
                result = self.get_asset(asset_type, filename)
                if result:
                    loaded_count += 1
            except Exception as e:
                self.logger.warning(f"事前読み込み失敗: {asset_type}:{filename} - {e}")
        
        self.logger.info(f"事前読み込み完了: {loaded_count}/{len(asset_list)}")
    
    def get_asset_info(self, asset_type: str, filename: str) -> Optional[Dict[str, Any]]:
        """アセット情報を取得"""
        try:
            file_path = self.config.get_asset_path(asset_type, filename)
        except ValueError:
            return None
        
        if not file_path.exists():
            return None
        
        stat = file_path.stat()
        asset_file_type = self._determine_asset_type(file_path)
        
        info = {
            'filename': filename,
            'path': str(file_path),
            'type': asset_file_type.value,
            'size_bytes': stat.st_size,
            'size_kb': round(stat.st_size / 1024, 2),
            'modified': stat.st_mtime
        }
        
        # 追加情報
        if asset_file_type == AssetType.IMAGE:
            try:
                with Image.open(file_path) as img:
                    info.update({
                        'dimensions': img.size,
                        'format': img.format,
                        'mode': img.mode
                    })
            except Exception:
                pass
        
        return info
    
    def list_assets(self, asset_type: str) -> List[Dict[str, Any]]:
        """指定タイプのアセット一覧を取得"""
        try:
            asset_dir = self.config.get_asset_path(asset_type)
        except ValueError:
            return []
        
        if not asset_dir.exists():
            return []
        
        assets = []
        for file_path in asset_dir.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(asset_dir)
                info = self.get_asset_info(asset_type, str(relative_path))
                if info:
                    assets.append(info)
        
        return sorted(assets, key=lambda x: x['filename'])
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        cache_stats = self.cache.get_stats()
        
        avg_load_time = sum(self.load_times) / len(self.load_times) if self.load_times else 0
        
        return {
            'cache': cache_stats,
            'performance': {
                'average_load_time_ms': round(avg_load_time, 2),
                'total_loads': len(self.load_times),
                'error_count': self.error_count
            },
            'audio_available': self.audio_available,
            'file_watcher_running': self.file_watcher.running
        }
    
    def cleanup(self) -> None:
        """リソースをクリーンアップ"""
        self.stop_file_watching()
        self.cache.clear()
        if self.audio_available:
            pygame.mixer.quit()
        self.logger.info("アセット管理システムをクリーンアップしました")


# グローバルインスタンス
_asset_manager_instance: Optional[AssetManager] = None

def get_asset_manager() -> AssetManager:
    """アセットマネージャーのシングルトンインスタンスを取得"""
    global _asset_manager_instance
    if _asset_manager_instance is None:
        _asset_manager_instance = AssetManager()
    return _asset_manager_instance