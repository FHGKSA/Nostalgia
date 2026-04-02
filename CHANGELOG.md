# 変更履歴 (Changelog)

このファイルでは、[Nostalgia](https://github.com/FHGKSA/Nostalgia) の全ての重要な変更を記録しています。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) に基づいており、
このプロジェクトは [Semantic Versioning](https://semver.org/lang/ja/) に準拠しています。

## [未リリース]

### 追加
- なし

### 変更
- なし

### 廃止予定
- なし

### 削除
- なし

### 修正
- なし

### セキュリティ
- なし

## [1.0.0] - 2026-04-02

### 追加
- **初期リリース**: Nostalgiaの最初のバージョン
- **PyQt6ベースのGUI**: メインウィンドウとゲーム表示機能
- **Ollama API連携**: ローカルLLMとの対話機能
- **アニメーションエンジン**: 立ち絵・背景のフェード・スライドアニメーション
- **テキスト表示エンジン**: タイピングエフェクト、ルビ対応
- **状態管理システム**: ゲーム進行・キャラクター情報の永続化
- **アセット管理**: 画像・音声・BGMの自動読み込み・キャッシュ
- **ログシステム**: 詳細なデバッグログ・セッション記録
- **設定管理**: YAML形式の設定ファイル・GUI設定画面
- **マルチプラットフォーム対応**: Windows, Linux, macOS
- **日本語フォントサポート**: 複数フォントのフォールバック機能

### プロジェクト構成
- `core/`: コアシステム（状態管理、AI通信、ログ、アセット管理）
- `gui/`: ユーザーインターフェース（メインウィンドウ、設定画面）
- `utils/`: ユーティリティ（設定ファイル管理）
- `data/`: ゲームデータ（セーブファイル、ユーザーデータ）
- `logs/`: ログファイル（デバッグログ、セッション記録）

### 技術仕様
- **Python**: 3.8以上
- **GUI Framework**: PyQt6 6.6.0+
- **AI Backend**: Ollama API
- **設定形式**: YAML
- **ログ形式**: JSON + テキスト
- **画像対応**: PNG, JPG, WebP
- **音声対応**: MP3, WAV, OGG

### ドキュメント
- 完全なREADME.md（インストール・使用方法）
- ライセンス（MIT License）
- コントリビューションガイド（日本語対応）
- 包括的な.gitignore設定

### 注意事項
- Ollama サーバーの別途インストールが必要
- Visual Novel特化モデル（`Berghof-ERP-7B-Q8_0`等）の利用を推奨
- アセット（背景・BGM・キャラクター画像）は含まれていません

---

## 凡例

- `追加`: 新機能
- `変更`: 既存機能の変更
- `廃止予定`: 近い将来削除される機能
- `削除`: 削除された機能
- `修正`: バグ修正
- `セキュリティ`: セキュリティ脆弱性の修正

## リンク

更新情報は以下で確認できます：

- [GitHub Releases](https://github.com/FHGKSA/Nostalgia/releases)
- [Issues](https://github.com/FHGKSA/Nostalgia/issues)
- [Pull Requests](https://github.com/FHGKSA/Nostalgia/pulls)