# コントリビューションガイド

Nostalgiaプロジェクトへのご参加をありがとうございます！
このガイドでは、プロジェクトへの貢献方法について説明します。

## 行動規範

すべての参加者は以下の行動規範を守ってください：

- 他の参加者を尊重し、建設的なフィードバックを提供する
- 包容的で歓迎的な環境を維持する
- 技術的な議論に集中し、個人攻撃を避ける
- 日本語または英語でコミュニケーションを行う

## 貢献の方法

### 1. Issue報告

バグや改善提案がある場合は、[Issues](https://github.com/FHGKSA/Nostalgia/issues)で報告してください。

#### バグレポートには以下を含めてください：

- **環境情報**: OS、Pythonバージョン、依存関係バージョン
- **再現手順**: 問題を再現するための具体的な手順
- **期待する動作**: 本来どのように動作すべきか
- **実際の動作**: 実際に何が起こったか
- **ログ出力**: エラーメッセージやログファイルの内容
- **スクリーンショット**: UI関連の問題の場合

#### 機能要求には以下を含めてください：

- **機能の説明**: 提案する機能の詳細
- **使用事例**: その機能が必要な理由・場面
- **実装案**: 可能であれば技術的なアプローチ

### 2. Pull Request

コードの変更を提案する場合は、Pull Requestを作成してください。

#### 事前準備

```bash
# リポジトリをフォーク
git clone https://github.com/FHGKSA/Nostalgia.git
cd Nostalgia/working_dir

# 開発用ブランチを作成
git checkout -b feature/your-feature-name

# 依存関係をインストール
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

#### コーディング規約

- **PEP 8**: Pythonコーディングスタイルガイドに従う
- **型ヒント**: 可能な限り型注釈を使用する
- **docstring**: 関数・クラスには適切なドキュメント文字列を記述
- **コメント**: 日本語または英語で分かりやすく記述
- **命名規則**: 変数・関数名は英語、コメント・ログは日本語OK

#### コード例

```python
from typing import Optional, Dict, Any

class ExampleClass:
    """例示クラス - 適切なdocstringを記述"""
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """
        クラスの初期化
        
        Args:
            name: インスタンス名
            config: 設定辞書（オプション）
        """
        self.name = name
        self.config = config or {}
    
    def process_data(self, data: str) -> str:
        """
        データを処理する
        
        Args:
            data: 処理対象のデータ
            
        Returns:
            処理済みのデータ
            
        Raises:
            ValueError: データが無効な場合
        """
        if not data.strip():
            raise ValueError("データが空です")
        
        # 処理ロジック
        return data.strip().upper()
```

#### テスト

新しい機能やバグ修正には、適切なテストを含めてください：

```bash
# テストの実行
pytest

# カバレッジレポート
pytest --cov=core --cov=gui --cov=utils --cov-report=html
```

#### Pull Requestのガイドライン

- **明確なタイトル**: 変更内容が分かるタイトルを付ける
- **詳細な説明**: 変更理由、実装内容、テスト方法を記述
- **小さな変更**: 一度に大きな変更をせず、小さな単位で分割
- **最新の状態**: main/masterブランチと競合しないよう、最新に保つ

### 3. ドキュメント改善

ドキュメントの改善も重要な貢献です：

- **README.md**: インストール方法、使用方法の改善
- **コメント**: コード内のコメント・docstringing充実
- **Wiki**: 使用例、トラブルシューティング情報
- **翻訳**: 英語ドキュメントの日本語翻訳

### 4. アセットの貢献

フリー素材のアセット提供も歓迎します：

- **背景画像**: Creative Commons、パブリックドメイン素材
- **BGM**: ロイヤリティフリー音楽
- **フォント**: オープンソースフォント
- **アイコン**: UI用のアイコンセット

**注意**: 著作権に問題のない素材のみ提供してください。

## 開発環境

### 必要なツール

- **Python 3.8+**: プログラミング言語
- **Poetry** または **pip**: 依存関係管理
- **Git**: バージョン管理
- **PyQt6**: GUI開発用
- **pytest**: テストフレームワーク
- **Ollama**: AI機能開発用（推論サーバー）

### 開発用設定

```bash
# 開発用依存関係（requirements.txtに含まれている）
pip install pytest pytest-qt pytest-cov
pip install black isort flake8 mypy  # コード品質ツール

# コードフォーマット
black .
isort .

# リンター
flake8 .
mypy core/ gui/ utils/
```

### デバッグ

```bash
# デバッグモードでの実行
python main.py --debug

# ログレベル変更
export LOG_LEVEL=DEBUG
python main.py

# プロファイリング
python -m cProfile -o profile.stats main.py
```

## リリースプロセス

メンテナーのみが実行：

1. **バージョン更新**: `main.py`、`setup.py`でバージョン番号変更
2. **変更履歴**: `CHANGELOG.md`に新機能・修正内容を記録
3. **タグ作成**: `git tag v1.x.x`でバージョンタグを作成
4. **リリース**: GitHub Releasesで正式リリース

## 質問・相談

開発に関する質問や相談は以下で受け付けています：

- **Issues**: 技術的な質問・提案
- **Discussions**: 一般的な議論・アイデア交換
- **Discord**: リアルタイムチャット（招待リンク）

## 感謝

あなたの貢献がこのプロジェクトをより良くします。
どんな小さな貢献でも歓迎いたします！

---

**Happy Coding!** 🚀