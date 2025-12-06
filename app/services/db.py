"""
SQLite データベース接続と初期化
学習データは AppData\Roaming\JHSEnglishTrainer\data\app.db に保存
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
    
    # words テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            word_id INTEGER PRIMARY KEY AUTOINCREMENT,
            english TEXT NOT NULL,
            japanese TEXT NOT NULL,
            grade INTEGER,
            unit TEXT,
            level INTEGER,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    
    # word_progress テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS word_progress (
            user_id INTEGER NOT NULL,
            word_id INTEGER NOT NULL,
            stage INTEGER DEFAULT 1,
            total_correct INTEGER DEFAULT 0,
            total_wrong INTEGER DEFAULT 0,
            correct_streak INTEGER DEFAULT 0,
            avg_answer_time_sec REAL DEFAULT 0.0,
            last_answered_at TEXT,
            PRIMARY KEY (user_id, word_id),
            FOREIGN KEY (word_id) REFERENCES words(word_id)
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
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        )
    """)
    
    # grammar_questions テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grammar_questions (
            question_id INTEGER PRIMARY KEY AUTOINCREMENT,
            grammar_id INTEGER NOT NULL,
            question_type TEXT NOT NULL,
            prompt_text TEXT NOT NULL,
            choice1 TEXT,
            choice2 TEXT,
            choice3 TEXT,
            choice4 TEXT,
            correct_answer TEXT NOT NULL,
            explanation TEXT,
            FOREIGN KEY (grammar_id) REFERENCES grammar_topics(grammar_id)
        )
    """)
    
    # grammar_progress テーブル
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grammar_progress (
            user_id INTEGER NOT NULL,
            grammar_id INTEGER NOT NULL,
            correct_count INTEGER DEFAULT 0,
            wrong_count INTEGER DEFAULT 0,
            mastery_level INTEGER DEFAULT 0,
            last_studied_at TEXT,
            PRIMARY KEY (user_id, grammar_id),
            FOREIGN KEY (grammar_id) REFERENCES grammar_topics(grammar_id)
        )
    """)
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # テスト用
    init_db()
    print(f"データベース初期化完了: {get_db_path()}")











