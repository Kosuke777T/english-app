"""
文法出題・採点・マスター度管理サービス
"""
import random
from datetime import datetime
from app.services import db


def list_topics():
    """
    文法トピック一覧を取得
    
    Returns:
        トピックのリスト
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT grammar_id, title, description, level
        FROM grammar_topics
        ORDER BY level, grammar_id
    """)
    
    topics = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return topics


def get_topic_detail(grammar_id: int) -> dict:
    """
    トピックの詳細情報を取得
    
    Args:
        grammar_id: 文法トピックID
    
    Returns:
        トピック情報の辞書
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT grammar_id, title, description, level, related_units
        FROM grammar_topics
        WHERE grammar_id = ?
    """, (grammar_id,))
    
    topic = cursor.fetchone()
    conn.close()
    
    if topic:
        return dict(topic)
    return None


def get_next_question(user_id: int, grammar_id: int) -> dict:
    """
    次の問題を取得
    
    Args:
        user_id: ユーザーID
        grammar_id: 文法トピックID
    
    Returns:
        問題情報の辞書
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 該当トピックの問題を取得
    cursor.execute("""
        SELECT question_id, question_type, prompt_text,
               choice1, choice2, choice3, choice4, correct_answer, explanation
        FROM grammar_questions
        WHERE grammar_id = ?
        ORDER BY RANDOM()
        LIMIT 1
    """, (grammar_id,))
    
    question = cursor.fetchone()
    conn.close()
    
    if not question:
        return None
    
    return dict(question)


def check_answer(user_id: int, question_id: int, answer: str) -> dict:
    """
    回答をチェックし、マスター度を更新
    
    Args:
        user_id: ユーザーID
        question_id: 問題ID
        answer: ユーザーの回答
    
    Returns:
        採点結果（is_correct, explanation, mastery_level）
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 問題情報を取得
    cursor.execute("""
        SELECT grammar_id, correct_answer, explanation
        FROM grammar_questions
        WHERE question_id = ?
    """, (question_id,))
    
    question = cursor.fetchone()
    if not question:
        conn.close()
        return None
    
    grammar_id = question['grammar_id']
    correct_answer = question['correct_answer']
    explanation = question['explanation']
    
    # 正誤判定（大文字小文字・空白を無視）
    is_correct = answer.strip().lower() == correct_answer.strip().lower()
    
    # 進捗を取得
    cursor.execute("""
        SELECT mastery_level, correct_count, wrong_count
        FROM grammar_progress
        WHERE user_id = ? AND grammar_id = ?
    """, (user_id, grammar_id))
    
    progress = cursor.fetchone()
    
    if progress:
        mastery = progress['mastery_level']
        correct_count = progress['correct_count']
        wrong_count = progress['wrong_count']
    else:
        mastery = 0
        correct_count = 0
        wrong_count = 0
    
    # マスター度を更新
    if is_correct:
        mastery = min(100, mastery + 5)
        correct_count += 1
    else:
        mastery = max(0, mastery - 7)
        wrong_count += 1
    
    # 進捗を更新または挿入
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO grammar_progress 
        (user_id, grammar_id, correct_count, wrong_count, mastery_level, last_studied_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, grammar_id) DO UPDATE SET
            correct_count = excluded.correct_count,
            wrong_count = excluded.wrong_count,
            mastery_level = excluded.mastery_level,
            last_studied_at = excluded.last_studied_at
    """, (user_id, grammar_id, correct_count, wrong_count, mastery, now))
    
    conn.commit()
    conn.close()
    
    return {
        'is_correct': is_correct,
        'explanation': explanation,
        'mastery_level': mastery,
        'correct_answer': correct_answer
    }











