"""
PyQt6 エントリーポイント（アプリ起動）
"""
import sys
from PyQt6.QtWidgets import QApplication
from app.ui.main_window import MainWindow
from app.services import db


def main():
    """アプリケーションのメイン関数"""
    # データベース初期化
    db.init_db()
    
    # PyQt6アプリケーション作成
    app = QApplication(sys.argv)
    
    # メインウィンドウ作成
    window = MainWindow()
    window.show()
    
    # イベントループ開始
    sys.exit(app.exec())


if __name__ == "__main__":
    main()











