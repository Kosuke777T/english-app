"""
単語トレーニングタブ
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from app.services import word_service, tts_service
from app.services import db


class WordTrainingTab(QWidget):
    """単語トレーニング画面"""
    
    def __init__(self, user_id: int = 1):
        super().__init__()
        self.user_id = user_id
        self.current_word: dict | None = None
        self.last_answer_correct: bool | None = None
        self.start_time = None
        self.timer = QTimer()
        
        self.init_ui()
        self.load_next_word()
        
        # 初期化完了後に入力欄にフォーカスを当てる
        self.input_field.setFocus()
        
        # ステージ4の音声再生用タイマー（必要に応じてキャンセル可能にするため）
        self._stage4_audio_timer = None
    
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
    
    def _update_stage_ui(self, word: dict):
        """
        ステージに応じてUIを更新する
        
        Args:
            word: 単語情報の辞書（stage, japanese, hint を含む）
        """
        stage = word['stage']
        hint = word.get('hint', '')
        
        if stage == 1:
            # ステージ1：日本語をそのまま表示
            self.japanese_label.setText(word['japanese'])
            self.hint_label.setText(hint if hint else "[ヒントなし]")
        elif stage == 2:
            # ステージ2：日本語は表示するが、英単語をシャッフル表示
            self.japanese_label.setText(word['japanese'])
            self.hint_label.setText(hint if hint else "[ヒントなし]")
        elif stage == 3:
            # ステージ3：日本語だけ表示（ヒントなし）
            self.japanese_label.setText(word['japanese'])
            self.hint_label.setText(hint if hint else "[ヒントなし]")
        elif stage == 4:
            # ★ステージ4：音声のみ。日本語は表示しない
            self.japanese_label.setText("")  # 完全に空にする
            self.hint_label.setText("[音声のみ - 音声を聞いて入力してください]")
        else:
            # 念のため
            self.japanese_label.setText(word['japanese'])
            self.hint_label.setText(hint if hint else "[ヒントなし]")
    
    def load_next_word(self):
        """次の単語を読み込む"""
        # 前回の回答が不正解（False）の場合は新しい単語を取得しない
        # None（初期状態）または True（正解後）の場合は新しい単語を取得
        if self.last_answer_correct is False:
            return
        
        import time
        self.start_time = time.time()
        
        # 新しい単語を取得
        self.current_word = word_service.get_next_word(user_id=self.user_id)
        
        if not self.current_word:
            QMessageBox.warning(self, "エラー", "単語データがありません。\n先にデータをインポートしてください。")
            return
        
        # 状態をリセット
        self.last_answer_correct = None
        
        # ★(1) UI更新（すべてのラベル・入力欄・ボタンの状態を先に更新）
        stage = self.current_word['stage']
        hint = self.current_word['hint']
        
        # ステージ別の表示更新
        self._update_stage_ui(self.current_word)
        
        self.stage_label.setText(f"ステージ {stage}")
        
        # 入力欄とボタンの状態をリセット
        self.input_field.clear()
        self.input_field.setEnabled(True)
        self.result_label.clear()
        self.check_button.setEnabled(True)
        self.next_button.setEnabled(False)  # 出題直後は無効
        
        # 連続正解数表示
        streak = self.current_word.get('correct_streak', 0)
        self.streak_label.setText(f"連続正解: {streak}回")
        
        # ★(2) UIの更新を確実に反映させる
        QApplication.processEvents()
        
        # ★(3) 入力欄にフォーカスを当てる
        self.input_field.setFocus()
        
        # ★(4) ステージ4の音声再生は削除
        # 音声再生はタブが選択されたときの on_activated() から行う
        # （アプリ起動時に勝手に音声が流れるのを防ぐため）
    
    def check_answer(self):
        """答え合わせ"""
        if not self.current_word:
            return
        
        user_answer = self.input_field.text().strip().lower()
        correct_answer = self.current_word['english'].lower()
        
        import time
        answer_time = time.time() - self.start_time if self.start_time else 0.0
        
        is_correct = user_answer == correct_answer
        
        # 判定結果を保存
        self.last_answer_correct = is_correct
        
        if is_correct:
            # (A) 正解の場合
            # ★(1) ラベル更新を最優先で実行（即座に表示）
            self.result_label.setText(f"✓ 正解！\n正解: {self.current_word['english']}")
            self.result_label.setStyleSheet("font-size: 16px; color: green; font-weight: bold;")
            
            # ★(2) 入力欄の状態変更
            self.input_field.setEnabled(False)
            self.check_button.setEnabled(False)
            self.input_field.clear()
            # 「次の単語」ボタンは有効のまま（手動でスキップ可能）
            self.next_button.setEnabled(True)
            
            # ★(3) GUIの更新を確実に反映（正解ラベルが表示されるのを待つ）
            QApplication.processEvents()
            
            # ★(4) その後に重い処理（DB書き込み）
            word_service.record_answer(
                user_id=self.user_id,
                word_id=self.current_word['word_id'],
                is_correct=True,
                answer_time_sec=answer_time
            )
            
            # ★(5) TTS再生（正解ラベル表示後に音声を再生）
            tts_service.speak(self.current_word['english'])
            
            # ★(5) 最後に1秒後に自動的に次の単語へ進む
            QTimer.singleShot(1000, self._load_next_word_after_correct)
        else:
            # (B) 不正解の場合
            # ラベル更新を最優先
            self.result_label.setText(
                f"✗ 不正解です。もう一度入力してね。\n正解: {self.current_word['english']}"
            )
            self.result_label.setStyleSheet("font-size: 16px; color: red; font-weight: bold;")
            QApplication.processEvents()
            
            # その後に重い処理（DB書き込み）
            word_service.record_answer(
                user_id=self.user_id,
                word_id=self.current_word['word_id'],
                is_correct=False,
                answer_time_sec=answer_time
            )
            
            # 同じ current_word を維持（get_next_word は呼ばない）
            # 「次の単語」ボタンは無効のまま
            self.next_button.setEnabled(False)
            
            # 入力欄をクリアして再入力可能に
            self.input_field.clear()
            self.input_field.setEnabled(True)
            self.input_field.setFocus()
    
    def _load_next_word_after_correct(self):
        """
        正解表示後に次の単語を読み込むためのヘルパー。
        正解時の1秒ディレイ後に呼ばれる。
        """
        # 結果ラベルをクリア
        self.result_label.clear()
        
        # 入力欄をクリアして有効化（次の問題入力の準備）
        self.input_field.clear()
        self.input_field.setEnabled(True)
        
        # 通常の「次の単語を読み込む処理」を呼び出す
        self.load_next_word()
        
        # 念のため、入力欄にフォーカスを当てる（load_next_word内でも設定しているが確実にするため）
        self.input_field.setFocus()
    
    def on_activated(self):
        """
        単語トレーニングタブが選択されたときに呼ばれる想定のメソッド。
        ステージ4なら 2秒後に音声を再生する。
        """
        if not self.current_word:
            return
        
        stage = self.current_word.get("stage", 1)
        if stage != 4:
            return
        
        # すでにタイマーが動いていたら一旦止める（多重再生防止）
        # 今回は QTimer.singleShot を使うだけなので、変数不要でも良いですが
        # 念のため保持しておく
        
        def _play():
            # タブが非表示になっていない前提で再生
            # current_word が変わっていたら、その単語を読む
            if self.current_word and self.current_word.get("stage", 1) == 4:
                tts_service.speak(self.current_word["english"])
        
        # 2秒後に音声を再生
        QTimer.singleShot(2000, _play)











