"""
メインウィンドウ（タブ管理）
"""
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from app.ui.word_training_tab import WordTrainingTab
from app.ui.grammar_training_tab import GrammarTrainingTab


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("中学生向け英語学習ソフト")
        self.setGeometry(100, 100, 900, 700)
        
        # タブウィジェット
        tabs = QTabWidget()
        
        # ホームタブ
        home_tab = QWidget()
        home_layout = QVBoxLayout()
        home_label = QLabel("中学生向け英語学習ソフトへようこそ！")
        home_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(home_label)
        home_tab.setLayout(home_layout)
        tabs.addTab(home_tab, "ホーム")
        
        # 単語トレーニングタブ
        word_tab = WordTrainingTab()
        tabs.addTab(word_tab, "単語トレーニング")
        
        # 文法トレーニングタブ
        grammar_tab = GrammarTrainingTab()
        tabs.addTab(grammar_tab, "文法トレーニング")
        
        self.setCentralWidget(tabs)











