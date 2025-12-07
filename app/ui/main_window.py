"""
メインウィンドウ（タブ管理）
"""
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel,
    QMenuBar, QMessageBox, QDialog
)
from PyQt6.QtCore import Qt, QTimer
from app.ui.home_tab import HomeTab
from app.ui.word_training_tab import WordTrainingTab
from app.ui.grammar_training_tab import GrammarTrainingTab
from app.ui.user_select_dialog import UserSelectDialog
from app.services import user_service


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("中学生向け英語学習ソフト")
        self.setGeometry(100, 100, 900, 700)
        
        # 現在のユーザーIDを初期化
        self.current_user_id = self._ensure_default_user()
        self.current_user_name = self._get_user_name(self.current_user_id)
        
        # タブウィジェットを保持
        self.tabs = QTabWidget()
        
        # UI初期化
        self._init_menu()
        self._init_tabs()
        
        self.setCentralWidget(self.tabs)
    
    def _ensure_default_user(self) -> int:
        """
        デフォルトユーザーを確保する
        
        Returns:
            存在するユーザーの最初のID。存在しない場合は新規作成してそのID
        """
        users = user_service.list_users()
        if users:
            return users[0]['user_id']
        else:
            # ユーザーが存在しない場合は「デフォルトユーザー」を作成
            default_user = user_service.create_user("デフォルトユーザー")
            return default_user['user_id']
    
    def _get_user_name(self, user_id: int) -> str:
        """
        ユーザーIDからユーザー名を取得
        
        Args:
            user_id: ユーザーID
        
        Returns:
            ユーザー名。取得できない場合は "不明なユーザー"
        """
        user = user_service.get_user(user_id)
        return user["name"] if user is not None else "不明なユーザー"
    
    def _init_menu(self):
        """メニューバーを初期化"""
        menubar = self.menuBar()
        
        # ユーザーメニュー
        user_menu = menubar.addMenu("ユーザー")
        
        select_user_action = user_menu.addAction("ユーザーを選択…")
        select_user_action.triggered.connect(self.change_user)
    
    def _init_tabs(self):
        """タブを初期化"""
        self.tabs.clear()
        
        # ホームタブ
        self.home_tab = HomeTab(
            user_id=self.current_user_id,
            user_name=self.current_user_name,
            on_change_user=self.change_user
        )
        self.tabs.addTab(self.home_tab, "ホーム")
        
        # 単語トレーニングタブ
        self.word_tab = WordTrainingTab(user_id=self.current_user_id)
        self.tabs.addTab(self.word_tab, "単語トレーニング")
        
        # 文法トレーニングタブ
        self.grammar_tab = GrammarTrainingTab(user_id=self.current_user_id)
        self.tabs.addTab(self.grammar_tab, "文法トレーニング")
        
        # タブ切り替え時に単語モードタブが表示されたら入力欄にフォーカス
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self._last_tab = None
    
    def _on_tab_changed(self, index: int):
        """タブが切り替わったときに呼ばれる"""
        new_tab = self.tabs.widget(index)
        
        # 前のタブに on_deactivated を通知（あれば）
        if self._last_tab is not None and hasattr(self._last_tab, "on_deactivated"):
            self._last_tab.on_deactivated()
        
        # 新しいタブが WordTrainingTab なら on_activated を呼ぶ
        if new_tab is self.word_tab and hasattr(new_tab, "on_activated"):
            new_tab.on_activated()
            # 少し遅延を入れてフォーカスを設定（タブ切り替えのアニメーション完了後）
            QTimer.singleShot(100, lambda: self.word_tab.input_field.setFocus())
        
        self._last_tab = new_tab
    
    def change_user(self):
        """ユーザー選択ダイアログを開く"""
        dialog = UserSelectDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            user_id = dialog.get_selected_user_id()
            if user_id is not None:
                self.current_user_id = user_id
                self.current_user_name = self._get_user_name(user_id)
                
                # ホームタブの表示更新
                self.home_tab.update_user(self.current_user_id, self.current_user_name)
                
                # 単語・文法タブを再生成
                self._recreate_learning_tabs()
    
    def _recreate_learning_tabs(self):
        """
        current_user_id を反映した WordTrainingTab / GrammarTrainingTab を作り直す
        """
        # 既存のタブを削除（ホームタブ以外）
        while self.tabs.count() > 1:
            self.tabs.removeTab(1)
        
        # 新しいタブを追加
        self.word_tab = WordTrainingTab(user_id=self.current_user_id)
        self.tabs.addTab(self.word_tab, "単語トレーニング")
        
        self.grammar_tab = GrammarTrainingTab(user_id=self.current_user_id)
        self.tabs.addTab(self.grammar_tab, "文法トレーニング")
        
        # 現在単語モードタブが表示されている場合はフォーカスを設定
        if self.tabs.currentIndex() == 1:
            # 単語タブが選択されているので、WordTrainingTab に通知
            if hasattr(self.word_tab, "on_activated"):
                self.word_tab.on_activated()
            QTimer.singleShot(100, lambda: self.word_tab.input_field.setFocus())











