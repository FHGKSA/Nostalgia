# Nostalgia

> AI Visual Novel Engine - Ollama APIと連携した対話型ストーリー生成

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.6.0+-green.svg)](https://pypi.org/project/PyQt6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#license)

## 概要

**Nostalgia** は、Ollama APIと連携してユーザー対話型のストーリーを動的生成する、リッチなアニメーション表現を重視したビジュアルノベルエンジンです。

### 主な特徴

- 🤖 **AI駆動ストーリー** - Ollama APIによる動的シナリオ生成
- 🎨 **PyQt6ベース** - 高品質なGUIとカスタマイズ性
- ✨ **リッチアニメーション** - 立ち絵のフェード・スライド・エフェクト
- 📝 **完全ログ記録** - 選択肢・会話履歴のテキストファイル保存
- 💾 **状態管理** - 好感度・フラグ・キャラクター情報の永続化
- 🎵 **マルチメディア対応** - BGM・効果音・立ち絵・背景画像
- 🌐 **クロスプラットフォーム** - Windows・Linux・macOS対応

## スクリーンショット

![メインゲーム画面](docs/screenshots/main_game.png)
![設定画面](docs/screenshots/settings.png)

## システム要件

### 最小要件

- **OS**: Windows 10/11, Ubuntu 18.04+, macOS 10.15+
- **Python**: 3.8以上
- **RAM**: 4GB
- **GPU**: 統合グラフィックス
- **ストレージ**: 1GB

### 推奨要件

- **OS**: Windows 11, Ubuntu 22.04+, macOS 12+
- **Python**: 3.10以上
- **RAM**: 8GB以上
- **GPU**: 専用グラフィックス
- **ストレージ**: 5GB以上

### 外部依存

- **Ollama Server**: ローカルLLM推論エンジン（別途インストール必要）

## インストールガイド

### 1. リポジトリのクローン

```bash
git clone https://github.com/FHGKSA/Nostalgia.git
cd Nostalgia/working_dir
```

### 2. Python依存関係のインストール

#### 仮想環境の利用（推奨）

```bash
# 仮想環境の作成
python -m venv venv

# 仮想環境の有効化
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

#### システムワイドインストール

```bash
pip install -r requirements.txt
```

### 3. Ollamaのセットアップ

#### Ollamaのインストール

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# https://ollama.com からインストーラーをダウンロード
```

#### 推奨モデルのダウンロード

```bash
# 日本語対応モデル（例）
ollama pull llama3.1:8b

# VisualNovel特化モデル（カスタム）
ollama pull Berghof-ERP-7B-Q8_0:latest
```

### 4. 設定の調整

`config.yaml`を編集してOllamaサーバーの設定を調整：

```yaml
ollama:
  host: "localhost"  # Ollamaサーバーのホスト
  port: 11434        # Ollamaサーバーのポート
  default_model: "llama3.1:8b"
  timeout: 30
```

### 5. アプリケーションの起動

```bash
python main.py
```

## 使用方法

### 基本的な使い方

1. **アプリケーション起動**: `python main.py`を実行
2. **ゲーム開始**: メイン画面から「新しいストーリー」を選択
3. **AIとの対話**: テキストボックスで選択肢を選んだり、自由入力で対話
4. **設定調整**: 設定画面でフォント・アニメーション速度等を調整

### アセットの配置

```
working_dir/
├── 背景/           # 背景画像 (.jpg, .png)
├── 立ち絵/         # キャラクター画像
│   ├── ヒロイン1/
│   └── ヒロイン2/
├── BGM/            # 背景音楽 (.mp3, .wav, .ogg)
└── 初期プロンプト/  # AIへの初期指示ファイル
```

### カスタム設定

`config.yaml`で以下の設定をカスタマイズ可能：

- **アニメーション速度**: フェード・スライド・タイピング速度
- **テキスト表示**: フォントサイズ・色・アウトライン
- **AI設定**: モデル・ホスト・タイムアウト
- **ログ設定**: ファイル出力・レベル・ローテーション

## プロジェクト構成

```
working_dir/
├── main.py                 # メインエントリーポイント
├── requirements.txt        # Python依存関係
├── config.yaml            # アプリケーション設定
├── README.md              # このファイル
├── LICENSE                # ライセンス情報
│
├── gui/                   # ユーザーインターフェース
│   ├── __init__.py
│   ├── main_window.py     # メインウィンドウ
│   └── settings_dialog.py # 設定ダイアログ
│
├── core/                  # コアシステム
│   ├── __init__.py
│   ├── game_state.py      # ゲーム状態管理
│   ├── game_logger.py     # ログ・デバッグシステム
│   ├── ollama_client.py   # Ollama API通信
│   ├── text_engine.py     # テキスト処理エンジン
│   └── asset_manager.py   # アセット管理・キャッシュ
│
├── utils/                 # ユーティリティ
│   ├── __init__.py
│   └── config.py          # 設定管理
│
├── data/                  # ゲームデータ
│   └── saves/             # セーブファイル
│
├── logs/                  # ログファイル
│   ├── game.log
│   └── session_*.json
│
├── 背景/                  # 背景画像
├── 立ち絵/                # キャラクター画像
├── BGM/                   # 背景音楽
└── 初期プロンプト/         # AI初期指示
```

## 開発・貢献

### 開発環境のセットアップ

```bash
# ソースコードのクローン
git clone https://github.com/FHGKSA/Nostalgia.git
cd Nostalgia/working_dir

# 開発用依存関係を含めてインストール
pip install -r requirements.txt

# テストの実行
pytest
```

### コントリビューション

プロジェクトへの貢献を歓迎します！詳細は[CONTRIBUTING.md](CONTRIBUTING.md)をご覧ください。

### 課題・提案

- [Issues](https://github.com/FHGKSA/Nostalgia/issues)
- [Discussions](https://github.com/FHGKSA/Nostalgia/discussions)

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルをご覧ください。

## 謝辞

- [Ollama](https://ollama.com/) - ローカルLLM実行環境
- [PyQt6](https://www.qt.io/qt-for-python) - GUIフレームワーク
- [Visual Novel community](https://vndb.org/) - インスピレーション

## 関連プロジェクト

- [`参考資料/VN_original_NFSW_tuned_model/`](参考資料/VN_original_NFSW_tuned_model/) - Visual Novel風テキスト生成AI（QLoRA）

---

**注意**: このプロジェクトはAllamaローカルLLMサーバーを必要とします。本番環境では適切なモデルの選択とプロンプトエンジニアリングを行ってください。

Windows上でVisualNovel風の画面を表示するAI対話型ゲームエンジン

## 概要

Ollama API (IP: 192.168.11.38) と連携してユーザー対話型のストーリーを動的生成する、リッチなアニメーション表現を重視したビジュアルノベルエンジンです。

## 特徴

- **PyQt6ベース** - 高品質なGUIとカスタマイズ性
- **AI駆動ストーリー** - Ollama APIによる動的シナリオ生成
- **リッチアニメーション** - 立ち絵のフェード・スライド・エフェクト
- **完全ログ記録** - 選択肢・会話履歴のテキストファイル保存
- **状態管理** - 好感度・フラグ・キャラクター情報の永続化

## プロジェクト構成

```
working_dir/
├── main.py                 # メインエントリーポイント
├── requirements.txt        # Python依存関係
├── config.yaml            # アプリケーション設定（自動生成）
│
├── gui/                   # ユーザーインターフェース
│   ├── main_window.py     # メインウィンドウ
│   ├── game_display.py    # 立ち絵・背景表示
│   ├── text_panel.py      # テキスト・選択肢パネル
│   └── animation_engine.py # アニメーション制御
│
├── core/                  # コアシステム
│   ├── game_state.py      # ゲーム状態管理
│   ├── game_logger.py     # ログ・デバッグシステム 
│   ├── ollama_client.py   # Ollama API通信
│   └── asset_manager.py   # アセット管理・キャッシュ
│
├── utils/                 # ユーティリティ
│   └── config.py          # 設定管理
│
├── data/                  # ゲームデータ
│   └── saves/             # セーブファイル
│
└── logs/                  # ログファイル
    └── game.log
```

## セットアップ

1. **依存関係のインストール**
   ```bash
   pip install -r requirements.txt
   ```

2. **Ollama API の確認**
   ```bash
   curl http://192.168.11.38:11434/api/generate
   ```

3. **アプリケーション起動**
   ```bash
   python main.py
   ```

## 設定

初回起動時に `config.yaml` が自動生成されます。必要に応じて以下を調整してください：

- **Ollama接続設定** - IPアドレス・ポート・モデル名
- **アニメーション設定** - エフェクト速度・イージング
- **ウィンドウ設定** - 解像度・フルスクリーン対応

## 開発状況

- [x] プロジェクト構造とセットアップ
- [ ] 依存関係確認とインストール
- [ ] 設定管理システム構築  
- [ ] ゲーム状態管理クラス実装
- [ ] Ollama API通信クライアント
- [ ] ログ・デバッグシステム実装
- [ ] アセット管理システム実装
- [ ] メインGUI構築
- [ ] アニメーションエンジン実装
- [ ] テキストエンジン実装
- [ ] ゲームループと統合

## 技術選択

- **GUI**: PyQt6 (高機能UI、ゲーム向けカスタマイズ性)
- **API通信**: HTTP REST API (requests)
- **状態保存**: JSON形式 (人間可読、デバッグ容易)
- **表現重視**: 軽量フレームワークより視覚的魅力を優先

## ライセンス

このプロジェクトは個人用途で開発されています。