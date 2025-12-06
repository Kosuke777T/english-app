"""
単語トレーニングタブ
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from app.services import word_service, tts_service
from app.services import db


class WordTrainingTab(QWidget):
    """単語トレーニング画面"""
    
    def __init__(self):
        super().__init__()
        self.current_word = None
        self.start_time = None
        self.timer = QTimer()
        
        self.init_ui()
        self.load_next_word()
    
    def init_ui(self):
        """UIを初期化"""
        layout = QVBoxLayout()
        
        # 日本語意味
        self.japanese_label = QLabel("")
        self.japanese_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.japanese_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.japanese_label)
        
        # ステージ表示
        self.stage_label = QLabel("")
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stage_label)
        
        # ヒント表示
        self.hint_label = QLabel("")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hint_label.setStyleSheet("font-size: 18px; color: #666;")
        layout.addWidget(self.hint_label)
        
        # 入力欄
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("英語を入力してください")
        self.input_field.returnPressed.connect(self.check_answer)
        layout.addWidget(self.input_field)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        self.check_button = QPushButton("答え合わせ")
        self.check_button.clicked.connect(self.check_answer)
        button_layout.addWidget(self.check_button)
        
        self.next_button = QPushButton("次の単語")
        self.next_button.clicked.connect(self.load_next_word)
        self.next_button.setEnabled(False)
        button_layout.addWidget(self.next_button)
        
        layout.addLayout(button_layout)
        
        # 結果表示
        self.result_label = QLabel("")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setStyleSheet("font-size: 16px;")
        layout.addWidget(self.result_label)
        
        # 連続正解数表示
        self.streak_label = QLabel("")
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.streak_label)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def load_next_word(self):
        """次の単語を読み込む"""
        import time
        self.start_time = time.time()
        
        self.current_word = word_service.get_next_word(user_id=1)
        
        if not self.current_word:
            QMessageBox.warning(self, "エラー", "単語データがありません。\n先にデータをインポートしてください。")
            return
        
        # UI更新
        self.japanese_label.setText(self.current_word['japanese'])
        self.stage_label.setText(f"ステージ {self.current_word['stage']}")
        
        stage = self.current_word['stage']
        hint = self.current_word['hint']
        
        if stage == 4:
            # ステージ4: 音声のみ
            self.hint_label.setText("[音声のみ - 音声を聞いて入力してください]")
            tts_service.speak(self.current_word['english'])
        else:
            self.hint_label.setText(hint if hint else "[ヒントなし]")
        
        self.input_field.clear()
        self.input_field.setEnabled(True)
        self.input_field.setFocus()
        self.result_label.clear()
        self.check_button.setEnabled(True)
        self.next_button.setEnabled(False)
        
        # 連続正解数表示
        streak = self.current_word.get('correct_streak', 0)
        self.streak_label.setText(f"連続正解: {streak}回")
    
    def check_answer(self):
        """答え合わせ"""
        if not self.current_word:
            return
        
        user_answer = self.input_field.text().strip()
        correct_answer = self.current_word['english'].lower()
        
        import time
        answer_time = time.time() - self.start_time
        
        is_correct = user_answer.lower() == correct_answer
        
        # 結果を記録
        word_service.record_answer(
            user_id=1,
            word_id=self.current_word['word_id'],
            is_correct=is_correct,
            answer_time_sec=answer_time
        )
        
        # 結果表示
        if is_correct:
            self.result_label.setText("✓ 正解！")
            self.result_label.setStyleSheet("font-size: 16px; color: green; font-weight: bold;")
        else:
            self.result_label.setText(f"✗ 不正解\n正解: {self.current_word['english']}")
            self.result_label.setStyleSheet("font-size: 16px; color: red; font-weight: bold;")
        
        self.input_field.setEnabled(False)
        self.check_button.setEnabled(False)
        self.next_button.setEnabled(True)











