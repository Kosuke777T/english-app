"""
ユーザー管理サービス
"""
from typing import List, Optional, Dict
from datetime import datetime
from app.services import db


def create_user(name: str) -> Dict:
    """
    users テーブルに新しいユーザーを追加し、
    追加されたユーザー情報を dict で返します。
    
    Args:
        name: ユーザー名
    
    Returns:
        追加されたユーザー情報の辞書
        例: {"user_id": 1, "name": "太郎", "created_at": "..."}
    
    Raises:
        ValueError: name が空文字や空白だけの場合
    """
    # バリデーション
    if not name or not name.strip():
        raise ValueError("ユーザー名は空文字や空白だけにできません")
    
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # created_at を ISO8601 形式で設定
    created_at = datetime.now().isoformat()
    
    # ユーザーを追加
    cursor.execute("""
        INSERT INTO users (name, created_at)
        VALUES (?, ?)
    """, (name.strip(), created_at))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # 追加されたユーザー情報を返す
    return {
        "user_id": user_id,
        "name": name.strip(),
        "created_at": created_at
    }


def list_users() -> List[Dict]:
    """
    users テーブルの全ユーザーを取得して、
    [{"user_id": ..., "name": ...}, ...] のような形で返します。
    
    Returns:
        ユーザー情報のリスト（user_id の昇順）
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, name, created_at
        FROM users
        ORDER BY user_id
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    # dict のリストに変換
    return [dict(row) for row in rows]


def get_user(user_id: int) -> Optional[Dict]:
    """
    指定 user_id のユーザーを1件取得して dict で返します。
    
    Args:
        user_id: ユーザーID
    
    Returns:
        ユーザー情報の辞書。ヒットしない場合は None
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT user_id, name, created_at
        FROM users
        WHERE user_id = ?
    """, (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def delete_user(user_id: int) -> None:
    """
    指定 user_id のユーザーを削除します。
    
    Args:
        user_id: ユーザーID
    
    Note:
        ここでは ON DELETE CASCADE 等は考えず、
        単純に users から削除します。
        （将来、単語や文法の progress との整合性は別途考えます。）
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        DELETE FROM users
        WHERE user_id = ?
    """, (user_id,))
    
    conn.commit()
    conn.close()


def get_current_user_id() -> int:
    """
    現在のユーザーIDを取得（v1では固定値）
    
    Returns:
        ユーザーID（デフォルト: 1）
    """
    # v1では固定ユーザーID 1を使用
    # 将来的にはユーザー選択機能を実装
    return 1

