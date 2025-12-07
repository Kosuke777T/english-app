"""
ホームタブ
"""
from typing import Optional, Callable
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt


class HomeTab(QWidget):
    """ホームタブ"""
    
    def __init__(
        self,
        user_id: int,
        user_name: Optional[str] = None,
        on_change_user: Optional[Callable[[], None]] = None
    ):
        super().__init__()
        self.user_id = user_id
        self.user_name = user_name or "不明なユーザー"
        self.on_change_user = on_change_user
        
        self.init_ui()
    
    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # タイトル
        title_label = QLabel("中学生向け英語学習ソフトへようこそ！")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px;")
        layout.addWidget(title_label)
        
        layout.addSpacing(30)
        
        # 現在のユーザー表示
        user_info_layout = QVBoxLayout()
        user_info_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        current_user_label = QLabel("現在のユーザー:")
        current_user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        current_user_label.setStyleSheet("font-size: 14px; color: #666;")
        user_info_layout.addWidget(current_user_label)
        
        self.user_name_label = QLabel(self.user_name)
        self.user_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user_name_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        user_info_layout.addWidget(self.user_name_label)
        
        layout.addLayout(user_info_layout)
        
        layout.addSpacing(20)
        
        # ユーザー選択ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.change_user_button = QPushButton("ユーザーを選択 / 登録…")
        self.change_user_button.setStyleSheet("font-size: 14px; padding: 10px 20px;")
        self.change_user_button.clicked.connect(self._on_change_user_clicked)
        button_layout.addWidget(self.change_user_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        layout.addSpacing(30)
        
        # 説明文
        description_label = QLabel(
            "単語トレーニングや文法トレーニングで学習を始めましょう。\n"
            "ユーザーを切り替えることで、複数の学習者で同じアプリを使い分けることができます。"
        )
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("font-size: 12px; color: #888; margin: 20px;")
        layout.addWidget(description_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _on_change_user_clicked(self):
        """ユーザー変更ボタンがクリックされたとき"""
        if self.on_change_user:
            self.on_change_user()
    
    def update_user(self, user_id: int, user_name: str) -> None:
        """
        現在表示中のユーザー情報を更新し、
        ラベルの表示も更新する。
        
        Args:
            user_id: 新しいユーザーID
            user_name: 新しいユーザー名
        """
        self.user_id = user_id
        self.user_name = user_name
        self.user_name_label.setText(user_name)

