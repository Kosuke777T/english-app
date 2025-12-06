"""
grammar_topics.json と grammar_questions.json から文法データをインポート
"""
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services import db


def import_grammar():
    """文法トピックと問題をインポート"""
    topics_path = project_root / "data" / "grammar_topics.json"
    questions_path = project_root / "data" / "grammar_questions.json"
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # トピックをインポート
    if topics_path.exists():
        with open(topics_path, 'r', encoding='utf-8') as f:
            topics = json.load(f)
        
        topic_map = {}  # title -> grammar_id
        
        for topic in topics:
            # 既存チェック
            cursor.execute("SELECT grammar_id FROM grammar_topics WHERE title = ?", (topic['title'],))
            existing = cursor.fetchone()
            
            if existing:
                grammar_id = existing['grammar_id']
                print(f"スキップ（トピック）: {topic['title']} (既に存在)")
            else:
                cursor.execute("""
                    INSERT INTO grammar_topics (title, description, level, related_units)
                    VALUES (?, ?, ?, ?)
                """, (
                    topic['title'],
                    topic.get('description'),
                    topic.get('level'),
                    json.dumps(topic.get('related_units', []), ensure_ascii=False)
                ))
                grammar_id = cursor.lastrowid
                print(f"インポート（トピック）: {topic['title']}")
            
            topic_map[topic['title']] = grammar_id
        
        conn.commit()
    
    # 問題をインポート
    if questions_path.exists():
        with open(questions_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        imported = 0
        for q in questions:
            grammar_title = q['grammar_title']
            grammar_id = topic_map.get(grammar_title)
            
            if not grammar_id:
                print(f"エラー: トピック '{grammar_title}' が見つかりません")
                continue
            
            # 既存チェック（prompt_textで判定）
            cursor.execute("""
                SELECT question_id FROM grammar_questions 
                WHERE grammar_id = ? AND prompt_text = ?
            """, (grammar_id, q['prompt_text']))
            
            if cursor.fetchone():
                print(f"スキップ（問題）: {q['prompt_text']} (既に存在)")
                continue
            
            cursor.execute("""
                INSERT INTO grammar_questions 
                (grammar_id, question_type, prompt_text, choice1, choice2, choice3, choice4, 
                 correct_answer, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                grammar_id,
                q['question_type'],
                q['prompt_text'],
                q.get('choice1'),
                q.get('choice2'),
                q.get('choice3'),
                q.get('choice4'),
                q['correct_answer'],
                q.get('explanation')
            ))
            imported += 1
            print(f"インポート（問題）: {q['prompt_text']}")
        
        conn.commit()
        print(f"\n完了: {imported}件の問題をインポートしました")
    
    conn.close()


if __name__ == "__main__":
    import_grammar()











