# 中学生向け英語学習ソフト v1 仕様書

Windows・完全オフライン対応・Python 3.13 + PyQt6

## 0. プロジェクト構成（v1）

本プロジェクトでは、UI（PyQt6）とロジック（services）を完全分離し、
教材データとユーザー学習データも分けて扱う。

jhs_english_trainer/
│
├── app/                         # アプリ本体（Pythonパッケージ）
│   ├── __init__.py
│   ├── main.py                  # PyQt6 エントリーポイント（アプリ起動）
│   │
│   ├── ui/                      # GUI（画面・ウィジェット）
│   │   ├── __init__.py
│   │   ├── main_window.py       # メイン画面（タブ管理）
│   │   ├── word_training_tab.py # 単語モード UI
│   │   └── grammar_training_tab.py # 文法モード UI
│   │
│   ├── services/                # ロジック層（UI非依存）
│   │   ├── __init__.py
│   │   ├── db.py                # SQLite への接続＆初期化
│   │   ├── word_service.py      # 単語出題・判定・ステージ管理
│   │   ├── grammar_service.py   # 文法出題・採点・マスター度管理
│   │   └── tts_service.py       # Windows SAPI による音声読み上げ
│   │
│   ├── models/                  # データモデル（必要なら）
│   │   └── __init__.py
│   │
│   └── utils/                   # 小さい共通処理
│       └── __init__.py
│
├── data/                        # 教材データ（初期JSON）
│   ├── words.json
│   ├── grammar_topics.json
│   └── grammar_questions.json
│
├── scripts/                     # 管理者用スクリプト
│   ├── __init__.py
│   ├── import_words_from_json.py
│   └── import_grammar_from_json.py
│
├── docs/
│   └── spec_v1.md               # 本仕様書
│
├── .gitignore
├── requirements.txt
└── README.md

## 1. システム概要

本アプリは、中学生向けの英語基礎学習（単語・文法）の習得を目的とし、
完全オフラインで動作する Windows デスクトップアプリである。

✔ 使用技術

Python 3.13

PyQt6（GUI）

SQLite3（ユーザー学習データ）

Windows SAPI（音声再生）

PyInstaller（配布用 exe 化）

✔ データ配置

教材データ（JSON） → data/

学習データ（SQLite DB） →
C:\Users\<User>\AppData\Roaming\JHSEnglishTrainer\data\app.db

※インストールディレクトリに書き込まない設計（権限対策）

## 2. 機能一覧（v1）

v1 では、以下の２モードを完成させる：

2-1. 単語モード（Word Training）
● 機能目的

日本語 → 英語スペル を段階的に定着させる

認知 → 運動記憶 → 完全想起 を行き来させる

ステージ制で習熟度を自動判定する

● 出題ステージ（4段階方式）
Stage	表示内容	目的
1	英単語全文ヒント（apple）	認知刺激・フォーム習得
2	バラバラ文字（p a e p l）	再構成で記憶強化
3	ヒントなし	完全想起
4	英語音声のみ（SAPIで再生）	リスニング → スペル想起
● 優先度スコア（AIっぽい出題制御）

各単語の出題優先度を以下で計算：

days = max(1, 今日 - last_answered(日数))

priority =
    wrong_count * 3
  + (1 / max(1, correct_streak)) * 4
  + days * 1.5
  + stage_penalty


stage_penalty：

Stage	penalty
1	+5
2	+3
3	+1
4	0

→ 「苦手・最近やってない・覚えきってない」単語が優先的に出る。

● ステージ昇格・降格ルール

正解時：

stage1→2：連続正解2回

stage2→3：連続正解3回 & 平均回答 ≤ 5秒

stage3→4：連続正解3回

不正解時：

correct_streak = 0

stage = max(1, stage - 1)

2-2. 文法モード（Grammar Training）
● 機能目的

中学英語の文法を系統的に学ぶ

トピック一覧 → ドリル → 採点 → マスター度更新の流れを作る

● 文法トピック例（v1）

be動詞（現在）

一般動詞（現在）

三単現

現在進行形

※topics.json でいつでも追加可能

● 問題タイプ（v1）
種類	内容
mcq	四択問題
fill	穴埋め、「He ( ) tennis.」
● マスター度の更新方法

採点結果に応じて：

正解：mastery += 5

不正解：mastery -= 7

範囲：0〜100

## 3. UI 仕様（PyQt6）
3-1. メイン画面（MainWindow）

タブ構造

ホーム（v1では最低限）

単語トレーニング

文法トレーニング

3-2. 単語トレーニング画面
画面要素

日本語意味ラベル

ステージ別ヒント表示

入力欄（QLineEdit）

「答え合わせ」

結果ラベル（正解/不正解）

「次の単語」

ステージ表示／連続正解数（任意）

3-3. 文法トレーニング画面
画面構成

左：トピック一覧 (QListWidget)

右上：トピック説明

右中：問題表示領域

mcq → ラジオボタン or 選択肢ボタン

fill → QLineEdit

右下：答え合わせ / 次の問題

結果（正誤、解説、マスター度）

## 4. ロジック層仕様（services）
4-1. word_service
● 提供関数

get_next_word(user_id) -> dict

record_answer(user_id, word_id, is_correct, answer_time_sec)

● 管理する項目

stage

correct_streak

total_correct

total_wrong

avg_answer_time_sec

last_answered_at

4-2. grammar_service
● 提供関数

list_topics()

get_topic_detail(grammar_id)

get_next_question(user_id, grammar_id)

check_answer(user_id, question_id, answer)

● 管理する項目

correct_count

wrong_count

mastery_level

last_studied_at

4-3. tts_service（Windows SAPI）
● 提供関数

speak(text: str)

仕様：

win32com.client.Dispatch("SAPI.SpVoice") を使用

外部TTS APIは使用しない（完全オフライン）

## 5. データ仕様（JSON & SQLite）
5-1. words.json（例）
[
  {
    "english": "apple",
    "japanese": "りんご",
    "grade": 1,
    "unit": "food",
    "level": 1
  }
]

5-2. grammar_topics.json（例）
[
  {
    "title": "be動詞（現在形）",
    "description": "I am / You are / He is",
    "level": 1,
    "related_units": ["self_intro"]
  }
]

5-3. grammar_questions.json（例）
[
  {
    "grammar_title": "be動詞（現在形）",
    "question_type": "mcq",
    "prompt_text": "「私は学生です。」",
    "choice1": "I is a student.",
    "choice2": "I am a student.",
    "choice3": "I are a student.",
    "choice4": "I be a student.",
    "correct_answer": "I am a student.",
    "explanation": "I のときは am を使います。"
  }
]

5-4. SQLite テーブル仕様

すべて db.py 内の init_db() で作成する。

● words
word_id      INTEGER PK
english      TEXT
japanese     TEXT
grade        INTEGER
unit         TEXT
level        INTEGER
created_at   TEXT

● word_progress
user_id
word_id
stage
total_correct
total_wrong
correct_streak
avg_answer_time_sec
last_answered_at
PRIMARY KEY (user_id, word_id)

● grammar_topics
● grammar_questions
● grammar_progress

（前述の定義の通り）

## 6. 配布方法

PyInstaller で exe 化して配布する。

コマンド例：
pyinstaller --noconsole --onefile --name JHSEnglishTrainer app/main.py

完成物：
dist/JHSEnglishTrainer.exe


→ これをZIP化して別PCに配布すれば動作。

## 7. 開発フロー（Cursor ＋ ChatGPT）
● ChatGPT（あなたの頭脳役）

設計

思考整理

ロジック仕様決定

● Cursor（実装役）

この spec_v1.md を読み取り、
指示を与えるとソースコードを生成する

★ Cursor への基本指示例
● プロジェクト骨組み生成

docs/spec_v1.md に基づいて
指定されたフォルダ構成と空ファイル群を自動生成してください。
main.py から PyQt6 アプリが起動できる最小構造を作ってください。

● 単語モード追加

word_service.py を仕様書 v1 の単語モードに合わせて実装して。
ステージ・スコア計算・昇格ルールも含めてお願いします。

● 文法モード追加

grammar_service.py を仕様書の文法モード仕様に沿って実装して。
list_topics → get_next_question → check_answer の流れでお願いします。

## 8. PowerShell 7 動作要件

本アプリの開発テストは PowerShell 7 を用いる。

● 単体テスト用テンプレ
$code = @'
from app.services import db

def main():
    print("DB Path:", db.get_db_path())

if __name__ == "__main__":
    main()
'@

python -c "$code"

## 9. v1 の完成条件

単語モードで

出題 → 答え合わせ → ステージ更新 → 次の問題
が一通り動く

文法モードで

トピック一覧 → 問題出題 → 答え合わせ → マスター度更新
ができる

Windows SAPI で英単語を読み上げ可能

学習データが AppData の SQLite に保存される

PyInstaller で exe 化し、Python なしでも起動できる