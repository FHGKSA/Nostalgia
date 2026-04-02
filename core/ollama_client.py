"""
Ollama API通信クライアント
ゲームロジックとAIモデル間の通信を管理

機能:
- テキスト生成リクエスト（シナリオ生成）
- 選択肢生成の依頼
- ハッピーエンド・エンディング生成
- ゲーム状態を考慮したプロンプト生成
- エラーハンドリングとタイムアウト処理
"""

import json
import requests
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from utils.config import Config


class RequestType(Enum):
    """リクエストタイプの定義"""
    STORY_GENERATION = "story_generation"    # ストーリー生成
    CHOICE_SUGGESTION = "choice_suggestion"  # 選択肢提案
    NEXT_EVENT = "next_event"               # 次のイベント推測
    HAPPY_ENDING = "happy_ending"           # ハッピーエンド生成
    SCENE_DESCRIPTION = "scene_description"  # シーン描写


@dataclass
class OllamaRequest:
    """Ollamaリクエストの構造"""
    model: str
    prompt: str
    stream: bool = False
    options: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """API リクエスト用の辞書に変換"""
        data = {
            "model": self.model,
            "prompt": self.prompt,
            "stream": self.stream
        }
        if self.options:
            data["options"] = self.options
        return data


@dataclass
class OllamaResponse:
    """Ollamaレスポンスの構造"""
    success: bool
    response_text: str
    error_message: str = ""
    model_used: str = ""
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None
    
    @classmethod
    def from_api_response(cls, response_data: Dict[str, Any]) -> 'OllamaResponse':
        """API応答から OllamaResponse を生成"""
        return cls(
            success=True,
            response_text=response_data.get('response', ''),
            model_used=response_data.get('model', ''),
            total_duration=response_data.get('total_duration'),
            load_duration=response_data.get('load_duration')
        )
    
    @classmethod
    def error_response(cls, error_message: str) -> 'OllamaResponse':
        """エラーレスポンスを生成"""
        return cls(
            success=False,
            response_text='',
            error_message=error_message
        )


class OllamaClient:
    """Ollama API通信クライアント"""
    
    def __init__(self):
        """初期化"""
        self.config = Config.get_instance()
        
        # 動的に変更可能な設定値
        self._host = self.config.get('ollama', {}).get('host', 'localhost')
        self._port = self.config.get('ollama', {}).get('port', 11434)
        self._default_model = self.config.get('ollama', {}).get('default_model', 'llama2')
        self._timeout = self.config.get('ollama', {}).get('timeout', 30)
        
        # デフォルトオプション
        self.default_options = {
            "temperature": 0.8,
            "top_p": 0.9,
            "top_k": 40,
            "num_predict": 512,
        }
    
    @property
    def host(self) -> str:
        """Ollamaサーバーのホスト"""
        return self._host
    
    @host.setter
    def host(self, value: str):
        """Ollamaサーバーのホストを設定"""
        self._host = value
        
    @property
    def port(self) -> int:
        """Ollamaサーバーのポート"""
        return self._port
        
    @port.setter
    def port(self, value: int):
        """Ollamaサーバーのポートを設定"""
        self._port = value
    
    @property
    def base_url(self) -> str:
        """ベースURLを動的に生成"""
        return f"http://{self._host}:{self._port}"
    
    @property
    def generate_endpoint(self) -> str:
        """生成APIエンドポイント"""
        return f"{self.base_url}/api/generate"
        
    @property
    def tags_endpoint(self) -> str:
        """モデル一覧APIエンドポイント"""
        return f"{self.base_url}/api/tags"
    
    @property
    def default_model(self) -> str:
        """デフォルトモデル名"""
        return self._default_model
        
    @default_model.setter
    def default_model(self, value: str):
        """デフォルトモデル名を設定"""
        self._default_model = value
        
    @property
    def timeout(self) -> int:
        """タイムアウト値"""
        return self._timeout
    
    def test_connection(self) -> Tuple[bool, str]:
        """Ollama サーバーとの接続をテスト"""
        try:
            response = requests.get(self.tags_endpoint, timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                return True, f"接続成功。利用可能なモデル数: {len(models)}"
            else:
                return False, f"HTTPエラー: {response.status_code}"
        except requests.RequestException as e:
            return False, f"接続エラー: {str(e)}"
    
    def get_available_models(self) -> List[str]:
        """利用可能なモデル一覧を取得"""
        try:
            response = requests.get(self.tags_endpoint, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception:
            return []
    
    def _send_request(self, request: OllamaRequest) -> OllamaResponse:
        """Ollama APIにリクエストを送信"""
        try:
            headers = {'Content-Type': 'application/json'}
            
            response = requests.post(
                self.generate_endpoint,
                json=request.to_dict(),
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return OllamaResponse.from_api_response(response_data)
            else:
                return OllamaResponse.error_response(
                    f"APIエラー: HTTP {response.status_code} - {response.text}"
                )
                
        except requests.Timeout:
            return OllamaResponse.error_response("リクエストタイムアウト")
        except requests.RequestException as e:
            return OllamaResponse.error_response(f"通信エラー: {str(e)}")
        except Exception as e:
            return OllamaResponse.error_response(f"予期しないエラー: {str(e)}")
    
    def _build_context_prompt(self, game_state: Any) -> str:
        """ゲーム状態からコンテキストプロンプトを構築"""
        context_parts = []
        
        # 基本的な状況設定
        if game_state.current_location:
            context_parts.append(f"現在の場所: {game_state.current_location}")
        if game_state.current_time:
            context_parts.append(f"時間帯: {game_state.current_time}")
        if game_state.current_character:
            context_parts.append(f"対話相手: {game_state.current_character}")
        
        # キャラクター情報
        present_chars = game_state.get_present_characters()
        if present_chars:
            char_info = []
            for char_name in present_chars:
                char = game_state.characters[char_name]
                char_info.append(f"{char_name}(好感度:{char.affection}, {char.emotion})")
            context_parts.append(f"登場キャラクター: {', '.join(char_info)}")
        
        # 主人公の状態
        if game_state.protagonist_state:
            context_parts.append(f"主人公の状態: {', '.join(game_state.protagonist_state)}")
        
        # 現在の目的
        if game_state.current_objective:
            context_parts.append(f"現在の目的: {game_state.current_objective}")
        
        # 重要なストーリーフラグ
        active_flags = [flag for flag, value in game_state.story_flags.items() if value]
        if active_flags:
            context_parts.append(f"達成済みのイベント: {', '.join(active_flags[:3])}")  # 最大3つまで
        
        return "\\n".join(context_parts)
    
    def generate_story_continuation(self, game_state: Any, user_input: str = "") -> OllamaResponse:
        """ストーリーの続きを生成"""
        context = self._build_context_prompt(game_state)
        
        prompt = f"""あなたは魅力的なビジュアルノベルのシナリオライターです。
        
現在の状況:
{context}

前回のテキスト: {game_state.current_text}

{f"プレイヤーの行動: {user_input}" if user_input else ""}

上記の状況を踏まえて、ストーリーを自然に続けてください。感情豊かで魅力的な文章で、200-400文字程度で記述してください。キャラクターの感情や行動を具体的に描写し、読者が没入できるような展開にしてください。"""
        
        request = OllamaRequest(
            model=self.default_model,
            prompt=prompt,
            options=self.default_options
        )
        
        return self._send_request(request)
    
    def generate_choices(self, game_state: Any) -> OllamaResponse:
        """選択肢を生成"""
        context = self._build_context_prompt(game_state)
        
        prompt = f"""現在のビジュアルノベルゲームの状況：

{context}

現在のシーンでプレイヤーが選択できる行動を3つ提案してください。各選択肢は以下の形式で出力してください：

1. [選択肢1の内容]
2. [選択肢2の内容]  
3. [選択肢3の内容]

選択肢の条件：
- 各選択肢は30文字以内
- キャラクターとの関係を深める内容
- ストーリー進行に影響する内容
- プレイヤーが選びたくなる魅力的な内容

番号と内容のみを出力し、説明文は不要です。"""
        
        request = OllamaRequest(
            model=self.default_model,
            prompt=prompt,
            options={**self.default_options, "num_predict": 200}
        )
        
        return self._send_request(request)
    
    def generate_next_event_prediction(self, game_state: Any) -> OllamaResponse:
        """次に起こりそうなイベントの予測"""
        context = self._build_context_prompt(game_state)
        
        prompt = f"""ビジュアルノベルの展開予測を行ってください。

現在の状況:
{context}

上記の状況から、次に起こりそうな出来事やイベントを3つ予測してください。各予測は1行で簡潔に記述してください：

予測1: [イベント内容]
予測2: [イベント内容]
予測3: [イベント内容]

予測は物語の自然な流れに沿ったものにしてください。"""
        
        request = OllamaRequest(
            model=self.default_model,
            prompt=prompt,
            options={**self.default_options, "num_predict": 300}
        )
        
        return self._send_request(request)
    
    def generate_happy_ending(self, game_state: Any, ending_condition: str = "") -> OllamaResponse:
        """ハッピーエンディングを生成"""
        context = self._build_context_prompt(game_state)
        
        prompt = f"""ビジュアルノベルのハッピーエンディングを作成してください。

現在までの状況:
{context}

{f"エンディング条件: {ending_condition}" if ending_condition else ""}

この状況から、主人公が見事にハッピーエンディングを迎える感動的な結末を400-600文字で描いてください。

要件:
- 登場キャラクターとの関係が良い形で結ばれる
- 主人公の成長や目標達成が描かれる
- 読者が満足できる心温まる結末
- "めでたしめでたし"で終わる

感動的で美しいエンディングを作成してください。"""
        
        request = OllamaRequest(
            model=self.default_model,
            prompt=prompt,
            options={**self.default_options, "num_predict": 800}
        )
        
        return self._send_request(request)
    
    def analyze_scenario_quality(self, scenario_text: str) -> OllamaResponse:
        """シナリオの品質を分析"""
        prompt = f"""以下のビジュアルノベルシナリオテキストを分析してください：

"{scenario_text}"

以下の観点から評価してください（5段階評価で数値のみ回答）：

感情表現: [1-5]
没入感: [1-5] 
キャラクター魅力: [1-5]
ストーリー進行: [1-5]

各項目を改行区切りで数値のみ出力してください。"""
        
        request = OllamaRequest(
            model=self.default_model,
            prompt=prompt,
            options={**self.default_options, "num_predict": 100}
        )
        
        return self._send_request(request)
    
    def extract_choices_from_response(self, response_text: str) -> List[str]:
        """レスポンステキストから選択肢を抽出"""
        choices = []
        lines = response_text.strip().split('\\n')
        
        for line in lines:
            line = line.strip()
            # "1. " "2. " "3. " 形式の選択肢を抽出
            if line and (line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
                choice_text = line[2:].strip()  # 番号と空白を除去
                if choice_text:
                    choices.append(choice_text)
        
        # フォールバック：番号なしの場合は最初の3行を使用
        if not choices:
            choices = [line.strip() for line in lines[:3] if line.strip()]
        
        return choices[:3]  # 最大3つまで
    
    def get_model_info(self) -> Dict[str, Any]:
        """現在使用中のモデル情報を取得"""
        return {
            "model_name": self.default_model,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "default_options": self.default_options
        }


# グローバルインスタンス
_ollama_client_instance: Optional[OllamaClient] = None

def get_ollama_client() -> OllamaClient:
    """Ollama クライアントのシングルトンインスタンスを取得"""
    global _ollama_client_instance
    if _ollama_client_instance is None:
        _ollama_client_instance = OllamaClient()
    return _ollama_client_instance