# 中学生向け英語学習ソフト

Windows・完全オフライン対応の英語学習アプリケーション

## 概要

中学生向けの英語基礎学習（単語・文法）をサポートするデスクトップアプリです。

- **単語モード**: 4段階のステージ制で単語を段階的に習得
- **文法モード**: トピック別の文法問題で系統的に学習
- **完全オフライン**: インターネット接続不要
- **Windows SAPI**: 音声読み上げ機能付き

## 技術スタック

- Python 3.13
- PyQt6 (GUI)
- SQLite3 (学習データ)
- Windows SAPI (音声再生)
- PyInstaller (配布用)

## セットアップ

### 1. 依存パッケージのインストール

```powershell
pip install -r requirements.txt
```

### 2. データベースの初期化

アプリを初めて起動すると、自動的にデータベースが初期化されます。

データベースの保存場所:
```
C:\Users\<User>\AppData\Roaming\JHSEnglishTrainer\data\app.db
```

### 3. 教材データのインポート

```powershell
# 単語データをインポート
python scripts/import_words_from_json.py

# 文法データをインポート
python scripts/import_grammar_from_json.py
```

### 4. アプリの起動

```powershell
python app/main.py
```

## プロジェクト構成

```
jhs_english_trainer/
├── app/                    # アプリ本体
│   ├── main.py            # エントリーポイント
│   ├── ui/                # GUI
│   ├── services/          # ロジック層
│   ├── models/            # データモデル
│   └── utils/            # ユーティリティ
├── data/                  # 教材データ（JSON）
├── scripts/               # インポートスクリプト
└── docs/                  # ドキュメント
```

## 配布方法

PyInstallerでexe化:

```powershell
pyinstaller --noconsole --onefile --name JHSEnglishTrainer app/main.py
```

完成物: `dist/JHSEnglishTrainer.exe`

## ライセンス

このプロジェクトは教育目的で作成されています。











