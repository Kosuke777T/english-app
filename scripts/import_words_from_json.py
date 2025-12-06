"""
words.json から単語データをインポート
"""
import json
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services import db


def import_words():
    """words.jsonから単語をインポート"""
    json_path = project_root / "data" / "words.json"
    
    if not json_path.exists():
        print(f"エラー: {json_path} が見つかりません")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        words = json.load(f)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    imported = 0
    for word in words:
        # 既存チェック（englishで判定）
        cursor.execute("SELECT word_id FROM words WHERE english = ?", (word['english'],))
        if cursor.fetchone():
            print(f"スキップ: {word['english']} (既に存在)")
            continue
        
        cursor.execute("""
            INSERT INTO words (english, japanese, grade, unit, level)
            VALUES (?, ?, ?, ?, ?)
        """, (
            word['english'],
            word['japanese'],
            word.get('grade'),
            word.get('unit'),
            word.get('level')
        ))
        imported += 1
        print(f"インポート: {word['english']} - {word['japanese']}")
    
    conn.commit()
    conn.close()
    
    print(f"\n完了: {imported}件の単語をインポートしました")


if __name__ == "__main__":
    import_words()











