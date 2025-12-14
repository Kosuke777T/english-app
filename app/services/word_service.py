"""
単語出題・判定・ステージ管理サービス
仕様: docs/spec_v1.md の単語モードに従う
"""
from datetime import datetime, date
import random
import sqlite3
from app.services import db


def get_next_word(
    user_id: int = 1,
    grade_min: int | None = None,
    grade_max: int | None = None,
    unit: str | None = None,
    level_max: int | None = None,
) -> dict | None:
    """
    次の出題単語を取得（優先度スコアに基づく）
    
    Args:
        user_id: ユーザーID（デフォルト: 1）
        grade_min: 最小学年（None の場合は制限なし）
        grade_max: 最大学年（None の場合は制限なし）
        unit: ユニット名（None の場合は制限なし）
        level_max: 最大レベル（None の場合は制限なし）
    
    Returns:
        単語情報とステージ情報を含む辞書、該当単語がなければ None
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # WHERE句を構築
        where_conditions = []
        params = [user_id]
        
        if grade_min is not None:
            where_conditions.append("w.grade >= ?")
            params.append(grade_min)
        
        if grade_max is not None:
            where_conditions.append("w.grade <= ?")
            params.append(grade_max)
        
        if unit is not None:
            where_conditions.append("w.unit = ?")
            params.append(unit)
        
        if level_max is not None:
            where_conditions.append("w.level <= ?")
            params.append(level_max)
        
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 全単語とその進捗を取得
        query = f"""
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
            {where_clause}
            ORDER BY w.word_id
        """
        
        cursor.execute(query, tuple(params))
        
        words = cursor.fetchall()
    except sqlite3.OperationalError as e:
        # テーブルが存在しない場合
        conn.close()
        raise RuntimeError(f"データベーステーブルが存在しません。先にデータをインポートしてください: {e}")
    
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
    
    # 上位50件からランダムに選択（完全に固定されないように）
    TOP_N = 50
    top_n = min(TOP_N, len(word_scores))
    if top_n > 0:
        selected = random.choice(word_scores[:top_n])[1]
    else:
        # フォールバック（万一候補ゼロならwords全体からランダムで1件）
        fallback_query = f"""
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
            {where_clause}
            ORDER BY RANDOM()
            LIMIT 1
        """
        cursor.execute(fallback_query, tuple(params))
        fallback_row = cursor.fetchone()
        if fallback_row:
            selected = fallback_row
        else:
            conn.close()
            return None
    
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
    
    try:
        # 現在の進捗を取得
        cursor.execute("""
            SELECT stage, total_correct, total_wrong, correct_streak, avg_answer_time_sec
            FROM word_progress
            WHERE user_id = ? AND word_id = ?
        """, (user_id, word_id))
        
        progress = cursor.fetchone()
    except sqlite3.OperationalError as e:
        # テーブルが存在しない場合
        conn.close()
        raise RuntimeError(f"データベーステーブルが存在しません。先にデータをインポートしてください: {e}")
    
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
        
        # 平均回答時間を更新（ステージ昇格条件には使わないが、記録は継続）
        if total_correct == 1:
            avg_time = answer_time_sec
        else:
            avg_time = (avg_time * (total_correct - 1) + answer_time_sec) / total_correct
        
        # ステージ昇格判定（新仕様）
        # stage 1 → 2: 1回正解で昇格
        # stage 2 → 3: 2回連続正解で昇格
        # stage 3 → 4: 3回連続正解で昇格
        if stage == 1 and correct_streak >= 1:
            stage = 2
            correct_streak = 0  # 新しいステージに入ったのでリセット
        elif stage == 2 and correct_streak >= 2:
            stage = 3
            correct_streak = 0  # 新しいステージに入ったのでリセット
        elif stage == 3 and correct_streak >= 3:
            stage = 4
            correct_streak = 0  # 新しいステージに入ったのでリセット
        
        # 上限チェック（念のため）
        if stage > 4:
            stage = 4
    else:
        total_wrong += 1
        correct_streak = 0
        # ステージ降格（既存仕様を維持）
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


def get_word_stats(user_id: int) -> dict:
    """
    総単語数とステージ別クリア率(%)を返す。
    stage: 1..4
      Stage1クリア = stage>=2
      Stage2クリア = stage>=3
      Stage3クリア = stage>=4
    word_progressが無い単語は stage=1 扱い。
    """
    conn = db.get_connection()
    try:
        sql = """
        SELECT
          COUNT(*) AS total,
          SUM(CASE WHEN COALESCE(wp.stage, 1) >= 2 THEN 1 ELSE 0 END) AS cleared_s1,
          SUM(CASE WHEN COALESCE(wp.stage, 1) >= 3 THEN 1 ELSE 0 END) AS cleared_s2,
          SUM(CASE WHEN COALESCE(wp.stage, 1) >= 4 THEN 1 ELSE 0 END) AS cleared_s3
        FROM words w
        LEFT JOIN word_progress wp
          ON wp.word_id = w.word_id AND wp.user_id = ?
        """
        cur = conn.cursor()
        row = cur.execute(sql, (user_id,)).fetchone()

        total = int(row[0] or 0)
        s1 = int(row[1] or 0)
        s2 = int(row[2] or 0)
        s3 = int(row[3] or 0)

        def pct(x: int) -> float:
            return round((x * 100.0 / total), 1) if total > 0 else 0.0

        return {
            "total_words": total,
            "stage1_cleared_pct": pct(s1),
            "stage2_cleared_pct": pct(s2),
            "stage3_cleared_pct": pct(s3),
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass


def record_result(
    user_id: int,
    word_id: int,
    is_correct: bool,
    answer_time_sec: float | None = None,
) -> None:
    """
    単語の回答結果を word_progress に記録する。
    - 初回は INSERT（stage=1）
    - 正解なら stage を +1（最大4）
    - total_correct/total_wrong, correct_streak, avg_answer_time_sec, last_answered_at を更新
    """
    con = db.get_connection()
    try:
        cur = con.cursor()

        # 既存レコード取得
        row = cur.execute(
            """
            SELECT stage, total_correct, total_wrong, correct_streak, avg_answer_time_sec
            FROM word_progress
            WHERE user_id=? AND word_id=?
            """,
            (user_id, word_id),
        ).fetchone()

        if row is None:
            stage = 1
            total_correct = 0
            total_wrong = 0
            correct_streak = 0
            avg_time = 0.0

            cur.execute(
                """
                INSERT INTO word_progress(
                    user_id, word_id, stage, total_correct, total_wrong,
                    correct_streak, avg_answer_time_sec, last_answered_at
                )
                VALUES(?, ?, 1, 0, 0, 0, 0.0, datetime('now','localtime'))
                """,
                (user_id, word_id),
            )
        else:
            # sqlite3.Row でも tuple でもOKなように index で読む
            stage = int(row[0] or 1)
            total_correct = int(row[1] or 0)
            total_wrong = int(row[2] or 0)
            correct_streak = int(row[3] or 0)
            avg_time = float(row[4] or 0.0)

        # 更新値を計算
        if is_correct:
            total_correct += 1
            correct_streak += 1
            stage = min(stage + 1, 4)
        else:
            total_wrong += 1
            correct_streak = 0
            # 不正解でstageを下げたいならここで調整（今は据え置き）

        if answer_time_sec is not None:
            # シンプルに移動平均（重み付き）にする：新しい値を10%反映
            try:
                t = max(0.0, float(answer_time_sec))
            except Exception:
                t = 0.0
            avg_time = (avg_time * 0.9) + (t * 0.1)

        cur.execute(
            """
            UPDATE word_progress
            SET stage=?,
                total_correct=?,
                total_wrong=?,
                correct_streak=?,
                avg_answer_time_sec=?,
                last_answered_at=datetime('now','localtime')
            WHERE user_id=? AND word_id=?
            """,
            (stage, total_correct, total_wrong, correct_streak, avg_time, user_id, word_id),
        )

        con.commit()
    finally:
        con.close()






