"""
単語出題・判定・ステージ管理サービス
"""
from datetime import datetime, date
import random
from app.services import db


def get_next_word(user_id: int = 1) -> dict:
    """
    次の出題単語を取得（優先度スコアに基づく）
    
    Args:
        user_id: ユーザーID（デフォルト: 1）
    
    Returns:
        単語情報とステージ情報を含む辞書
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 全単語とその進捗を取得
    cursor.execute("""
        SELECT 
            w.word_id,
            w.english,
            w.japanese,
            COALESCE(wp.stage, 1) as stage,
            COALESCE(wp.total_correct, 0) as total_correct,
            COALESCE(wp.total_wrong, 0) as total_wrong,
            COALESCE(wp.correct_streak, 0) as correct_streak,
            COALESCE(wp.avg_answer_time_sec, 0.0) as avg_answer_time_sec,
            wp.last_answered_at
        FROM words w
        LEFT JOIN word_progress wp ON w.word_id = wp.word_id AND wp.user_id = ?
        ORDER BY w.word_id
    """, (user_id,))
    
    words = cursor.fetchall()
    if not words:
        conn.close()
        return None
    
    # 優先度スコアを計算
    today = date.today()
    word_scores = []
    
    for word in words:
        stage = word['stage']
        wrong_count = word['total_wrong']
        correct_streak = max(1, word['correct_streak'])
        last_answered = word['last_answered_at']
        
        # 日数計算
        if last_answered:
            last_date = datetime.fromisoformat(last_answered).date()
            days = max(1, (today - last_date).days)
        else:
            days = 999  # 未回答の単語は優先度高
        
        # ステージペナルティ
        stage_penalty = {1: 5, 2: 3, 3: 1, 4: 0}.get(stage, 5)
        
        # 優先度スコア計算
        priority = (
            wrong_count * 3
            + (1 / correct_streak) * 4
            + days * 1.5
            + stage_penalty
        )
        
        word_scores.append((priority, word))
    
    # 優先度が高い順にソート（ランダム要素を追加）
    word_scores.sort(key=lambda x: x[0], reverse=True)
    
    # 上位3つからランダムに選択（完全に固定されないように）
    top_n = min(3, len(word_scores))
    selected = random.choice(word_scores[:top_n])[1]
    
    conn.close()
    
    # ステージに応じたヒントを生成
    english = selected['english']
    stage = selected['stage']
    
    if stage == 1:
        hint = english  # 全文表示
    elif stage == 2:
        # バラバラ文字
        chars = list(english)
        random.shuffle(chars)
        hint = " ".join(chars)
    elif stage == 3:
        hint = ""  # ヒントなし
    else:  # stage == 4
        hint = "[音声のみ]"  # 音声のみ
    
    return {
        'word_id': selected['word_id'],
        'english': english,
        'japanese': selected['japanese'],
        'stage': stage,
        'hint': hint,
        'correct_streak': selected['correct_streak'],
        'avg_answer_time_sec': selected['avg_answer_time_sec']
    }


def record_answer(user_id: int, word_id: int, is_correct: bool, answer_time_sec: float):
    """
    回答を記録し、ステージを更新
    
    Args:
        user_id: ユーザーID
        word_id: 単語ID
        is_correct: 正解かどうか
        answer_time_sec: 回答時間（秒）
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # 現在の進捗を取得
    cursor.execute("""
        SELECT stage, total_correct, total_wrong, correct_streak, avg_answer_time_sec
        FROM word_progress
        WHERE user_id = ? AND word_id = ?
    """, (user_id, word_id))
    
    progress = cursor.fetchone()
    
    if progress:
        stage = progress['stage']
        total_correct = progress['total_correct']
        total_wrong = progress['total_wrong']
        correct_streak = progress['correct_streak']
        avg_time = progress['avg_answer_time_sec']
    else:
        stage = 1
        total_correct = 0
        total_wrong = 0
        correct_streak = 0
        avg_time = 0.0
    
    # 回答を記録
    if is_correct:
        total_correct += 1
        correct_streak += 1
        
        # 平均回答時間を更新
        if total_correct == 1:
            avg_time = answer_time_sec
        else:
            avg_time = (avg_time * (total_correct - 1) + answer_time_sec) / total_correct
        
        # ステージ昇格判定
        if stage == 1 and correct_streak >= 2:
            stage = 2
        elif stage == 2 and correct_streak >= 3 and avg_time <= 5.0:
            stage = 3
        elif stage == 3 and correct_streak >= 3:
            stage = 4
    else:
        total_wrong += 1
        correct_streak = 0
        stage = max(1, stage - 1)
    
    # 進捗を更新または挿入
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO word_progress 
        (user_id, word_id, stage, total_correct, total_wrong, correct_streak, 
         avg_answer_time_sec, last_answered_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, word_id) DO UPDATE SET
            stage = excluded.stage,
            total_correct = excluded.total_correct,
            total_wrong = excluded.total_wrong,
            correct_streak = excluded.correct_streak,
            avg_answer_time_sec = excluded.avg_answer_time_sec,
            last_answered_at = excluded.last_answered_at
    """, (user_id, word_id, stage, total_correct, total_wrong, correct_streak, avg_time, now))
    
    conn.commit()
    conn.close()











