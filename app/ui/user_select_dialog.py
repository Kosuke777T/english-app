"""
ユーザー選択ダイアログ
"""
from typing import Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QLineEdit,
    QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
from app.services import user_service


class UserSelectDialog(QDialog):
    """ユーザー選択ダイアログ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_user_id: Optional[int] = None
        self.setWindowTitle("ユーザー選択")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        self.init_ui()
        self.load_users()
    
    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout()
        
        # ユーザー一覧
        layout.addWidget(QLabel("ユーザー一覧:"))
        self.user_list = QListWidget()
        self.user_list.itemClicked.connect(self.on_user_selected)
        layout.addWidget(self.user_list)
        
        # 新規ユーザー追加エリア
        add_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("新しいユーザー名を入力")
        self.name_input.returnPressed.connect(self.add_user)
        add_layout.addWidget(self.name_input)
        
        self.add_button = QPushButton("追加")
        self.add_button.clicked.connect(self.add_user)
        add_layout.addWidget(self.add_button)
        
        layout.addLayout(add_layout)
        
        # 削除ボタン
        self.delete_button = QPushButton("削除")
        self.delete_button.clicked.connect(self.delete_user)
        self.delete_button.setEnabled(False)
        layout.addWidget(self.delete_button)
        
        # エラーメッセージ表示用ラベル
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)
        
        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        button_layout.addWidget(self.ok_button)
        
        self.cancel_button = QPushButton("キャンセル")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_users(self):
        """ユーザー一覧を読み込む"""
        self.user_list.clear()
        self.error_label.clear()
        
        try:
            users = user_service.list_users()
            for user in users:
                item = QListWidgetItem(user['name'])
                item.setData(Qt.ItemDataRole.UserRole, user['user_id'])
                self.user_list.addItem(item)
        except Exception as e:
            self.error_label.setText(f"エラー: {str(e)}")
    
    def on_user_selected(self, item):
        """ユーザーが選択されたとき"""
        self.selected_user_id = item.data(Qt.ItemDataRole.UserRole)
        self.delete_button.setEnabled(True)
    
    def add_user(self):
        """新規ユーザーを追加"""
        name = self.name_input.text().strip()
        if not name:
            self.error_label.setText("ユーザー名を入力してください")
            return
        
        try:
            new_user = user_service.create_user(name)
            self.name_input.clear()
            self.error_label.clear()
            
            # リストに追加
            item = QListWidgetItem(new_user['name'])
            item.setData(Qt.ItemDataRole.UserRole, new_user['user_id'])
            self.user_list.addItem(item)
            
            # 追加したユーザーを選択状態にする
            self.user_list.setCurrentItem(item)
            self.selected_user_id = new_user['user_id']
            self.delete_button.setEnabled(True)
        except ValueError as e:
            self.error_label.setText(str(e))
        except Exception as e:
            self.error_label.setText(f"エラー: {str(e)}")
    
    def delete_user(self):
        """選択中のユーザーを削除"""
        current_item = self.user_list.currentItem()
        if not current_item:
            return
        
        user_id = current_item.data(Qt.ItemDataRole.UserRole)
        user_name = current_item.text()
        
        # 確認ダイアログ
        reply = QMessageBox.question(
            self,
            "確認",
            f"ユーザー「{user_name}」を削除しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            user_service.delete_user(user_id)
            self.error_label.clear()
            
            # 削除したユーザーが選択中だった場合
            if self.selected_user_id == user_id:
                self.selected_user_id = None
                self.delete_button.setEnabled(False)
            
            # リストから削除
            self.user_list.takeItem(self.user_list.row(current_item))
            
            # リストが空になった場合
            if self.user_list.count() == 0:
                self.selected_user_id = None
                self.delete_button.setEnabled(False)
        except Exception as e:
            self.error_label.setText(f"エラー: {str(e)}")
    
    def get_selected_user_id(self) -> Optional[int]:
        """
        選択中のユーザーIDを取得
        
        Returns:
            選択中のユーザーID。選択されていない場合は None
        """
        return self.selected_user_id
    
    def accept(self):
        """OKボタンが押されたとき"""
        # 選択されていない場合は警告
        if self.selected_user_id is None:
            QMessageBox.warning(
                self,
                "警告",
                "ユーザーを選択してください"
            )
            return
        
        super().accept()


