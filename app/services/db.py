"""
SQLite データベース接続と初期化
学習データは AppData/Roaming/JHSEnglishTrainer/data/app.db に保存
"""
import sqlite3
import os
from pathlib import Path


def get_db_path() -> str:
    """データベースファイルのパスを取得"""
    appdata = os.getenv("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA環境変数が見つかりません")
    
    db_dir = Path(appdata) / "JHSEnglishTrainer" / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    
    return str(db_dir / "app.db")


def get_connection():
    """データベース接続を取得"""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """データベーステーブルを初期化"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # users テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT
        )
    """)
    
    # grammar_topics テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grammar_topics (
            grammar_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            level INTEGER,
            related_units TEXT,
            created_at TEXT
        )
    """)
    
    # scenarios テーブル（会話トレーニング用）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            level INTEGER,
            topic_tag TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    
    # scenario_steps テーブル（会話トレーニング用）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scenario_steps (
            step_id INTEGER PRIMARY KEY AUTOINCREMENT,
            scenario_id INTEGER NOT NULL,
            order_no INTEGER NOT NULL,
            bot_text TEXT NOT NULL,
            expected_patterns TEXT,
            required_keywords TEXT,
            hint_jp TEXT,
            model_answer TEXT,
            allowed_vocab_set TEXT,
            FOREIGN KEY (scenario_id) REFERENCES scenarios(scenario_id)
        )
    """)
    
    # conversation_progress テーブル（会話トレーニング用）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_progress (
            user_id INTEGER NOT NULL,
            scenario_id INTEGER NOT NULL,
            last_step_order INTEGER DEFAULT 0,
            cleared_count INTEGER DEFAULT 0,
            last_cleared_at TEXT,
            PRIMARY KEY (user_id, scenario_id),
            FOREIGN KEY (scenario_id) REFERENCES scenarios(scenario_id)
        )
    """)
    
    # conversation_log テーブル（会話トレーニング用）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            scenario_id INTEGER NOT NULL,
            step_id INTEGER NOT NULL,
            user_answer TEXT,
            judge_result TEXT,
            score INTEGER,
            answered_at TEXT,
            FOREIGN KEY (scenario_id) REFERENCES scenarios(scenario_id),
            FOREIGN KEY (step_id) REFERENCES scenario_steps(step_id)
        )
    """)
    
    # 単語やその他のテーブルは後で追加予定
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # テスト用
    init_db()
    print(f"データベース初期化完了: {get_db_path()}")











