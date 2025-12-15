"""
単語トレーニングタブ
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QApplication, QComboBox
)
from PyQt6.QtCore import Qt, QTimer, QSettings
from PyQt6.QtGui import QFont
import random
from app.services import word_service
from app.services.tts_service import tts_service
from app.services import db


# 音声選択の候補リスト（表示名, voice ID）
VOICE_CHOICES = [
    ("Aria (US 女性)", "en-US-AriaNeural"),
    ("Guy (US 男性)", "en-US-GuyNeural"),
    ("Libby (UK 女性)", "en-GB-LibbyNeural"),
]


class WordTrainingTab(QWidget):
    """単語トレーニング画面"""
    
    def __init__(self, user_id: int = 1):
        super().__init__()
        self.user_id = user_id
        self.current_word: dict | None = None
        self.last_answer_correct: bool | None = None
        self.start_time = None
        self.timer = QTimer()
        self.is_active = False  # タブが選択されているとき True
        self.question_counter = 0  # 出題された問題数（セッション中）
        
        # QSettings で設定を保存/読み込み
        self.settings = QSettings("JHSEnglishTrainer", "EnglishApp")
        
        # 保存済みの TTS voice を読み出し（なければ Libby）
        saved_voice = self.settings.value("tts_voice", "en-GB-LibbyNeural", type=str)
        tts_service.set_voice(saved_voice)
        
        self.init_ui(saved_voice)
        # 初回出題は行わない（スタートボタンが押されるまで待つ）
        self._disable_ui()
        
        # ステージ4の音声再生用タイマー（必要に応じてキャンセル可能にするため）
        self._stage4_audio_timer = None
    
    def init_ui(self, initial_voice: str):
        """UIを初期化"""
        layout = QVBoxLayout()
        
        # ★ ネイティブ音声選択バー
        voice_layout = QHBoxLayout()
        voice_label = QLabel("ネイティブ音声：")
        self.voice_combo = QComboBox()
        
        for display_name, voice_id in VOICE_CHOICES:
            self.voice_combo.addItem(display_name, voice_id)
        
        # initial_voice を元にコンボボックスの初期選択を合わせる
        index_to_select = 0
        for i in range(self.voice_combo.count()):
            if self.voice_combo.itemData(i) == initial_voice:
                index_to_select = i
                break
        self.voice_combo.setCurrentIndex(index_to_select)
        
        self.voice_combo.currentIndexChanged.connect(self._on_voice_changed)
        
        voice_layout.addWidget(voice_label)
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch()
        
        layout.addLayout(voice_layout)
        
        # ★ 問題番号ラベル（日本語ラベルのすぐ上、中央配置）
        self.question_label = QLabel("第 0 問")
        self.question_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.question_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.question_label)
        
        # 日本語意味
        self.japanese_label = QLabel("")
        self.japanese_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.japanese_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(self.japanese_label)
        
        # ステージ表示
        self.stage_label = QLabel("")
        self.stage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stage_label)
        
        # ヒント表示（初期状態は空白）- 英単語を表示するラベル
        self.hint_label = QLabel("")
        self.hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # フォントサイズを3倍に（スタイルシートの色設定のみ残す）
        font = self.hint_label.font()
        font.setPointSize(font.pointSize() * 3)
        self.hint_label.setFont(font)
        self.hint_label.setStyleSheet("color: #666;")  # 色のみ設定（フォントサイズはフォントオブジェクトで制御）
        layout.addWidget(self.hint_label)
        
        # 入力欄
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("英語を入力してください")
        self.input_field.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # フォントサイズを3倍に
        font = self.input_field.font()
        font.setPointSize(font.pointSize() * 3)
        self.input_field.setFont(font)
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
        
        # 連続正解数表示とスタートボタン
        streak_layout = QVBoxLayout()
        self.streak_label = QLabel("")
        self.streak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        streak_layout.addWidget(self.streak_label)
        
        # スタートボタン
        self.start_button = QPushButton("スタート")
        self.start_button.clicked.connect(self._on_start_clicked)
        streak_layout.addWidget(self.start_button)
        streak_layout.addStretch()
        
        layout.addLayout(streak_layout)
        
        # ★ フィルタUI
        filter_layout = QVBoxLayout()
        
        # 学年フィルタ
        grade_layout = QHBoxLayout()
        grade_label = QLabel("学年フィルタ：")
        self.grade_combo = QComboBox()
        self.grade_combo.addItems([
            "中1だけ",
            "中2だけ",
            "中3だけ",
            "中1〜2",
            "中2〜3",
            "中1〜3（すべて）"
        ])
        self.grade_combo.setCurrentText("中1〜3（すべて）")
        grade_layout.addWidget(grade_label)
        grade_layout.addWidget(self.grade_combo)
        grade_layout.addStretch()
        filter_layout.addLayout(grade_layout)
        
        # カテゴリフィルタ
        unit_layout = QHBoxLayout()
        unit_label = QLabel("カテゴリ：")
        self.unit_combo = QComboBox()
        self.unit_combo.addItems([
            "すべて",
            "food",
            "animal",
            "time",
            "color",
            "place",
            "family",
            "school",
            "culture",
            "transport",
            "tech",
            "concept"
        ])
        self.unit_combo.setCurrentText("すべて")
        unit_layout.addWidget(unit_label)
        unit_layout.addWidget(self.unit_combo)
        unit_layout.addStretch()
        filter_layout.addLayout(unit_layout)
        
        # 最大レベルフィルタ
        level_layout = QHBoxLayout()
        level_label = QLabel("最大レベル：")
        self.level_combo = QComboBox()
        self.level_combo.addItems([
            "レベル1まで",
            "レベル2まで",
            "レベル3まで（すべて）"
        ])
        self.level_combo.setCurrentText("レベル3まで（すべて）")
        level_layout.addWidget(level_label)
        level_layout.addWidget(self.level_combo)
        level_layout.addStretch()
        filter_layout.addLayout(level_layout)
        
        # ステージモードフィルタ
        stage_mode_layout = QHBoxLayout()
        stage_mode_label = QLabel("ステージモード：")
        self.stage_mode_combo = QComboBox()
        self.stage_mode_combo.addItems([
            "ステージ1から",
            "ステージ2から",
            "ステージ3から",
            "ステージ4から",
            "ランダム"
        ])
        self.stage_mode_combo.setCurrentText("ステージ1から")
        stage_mode_layout.addWidget(stage_mode_label)
        stage_mode_layout.addWidget(self.stage_mode_combo)
        stage_mode_layout.addStretch()
        filter_layout.addLayout(stage_mode_layout)
        
        layout.addLayout(filter_layout)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def _get_display_stage(self, actual_stage: int) -> int:
        """
        実ステージ（1〜4）とステージモードの設定から、
        表示に使うステージ番号（1〜4）を返す。
        
        Args:
            actual_stage: DB上の実ステージ（1〜4）
        
        Returns:
            表示に使うステージ番号（1〜4）
        """
        mode = self.stage_mode_combo.currentText()
        
        if mode == "ステージ1から":
            return 1
        elif mode == "ステージ2から":
            return 2
        elif mode == "ステージ3から":
            return 3
        elif mode == "ステージ4から":
            return 4
        elif mode == "ランダム":
            return random.randint(1, 4)
        else:
            # 上記以外の値が来た場合は actual_stage をそのまま返す
            return actual_stage
    
    def _generate_hint_for_stage(self, english: str, display_stage: int) -> str:
        """
        表示ステージに基づいてヒントを生成する
        
        Args:
            english: 英単語
            display_stage: 表示ステージ（1〜4）
        
        Returns:
            ヒント文字列
        """
        if display_stage == 1:
            # ステージ1：全文表示
            return english
        elif display_stage == 2:
            # ステージ2：バラバラ文字
            chars = list(english)
            random.shuffle(chars)
            return " ".join(chars)
        elif display_stage == 3:
            # ステージ3：ヒントなし
            return ""
        else:  # display_stage == 4
            # ステージ4：音声のみ
            return "[音声のみ]"
    
    def _update_stage_ui(self, word: dict):
        """
        ステージに応じてUIを更新する（表示ステージを使用）
        
        Args:
            word: 単語情報の辞書（stage, japanese, english を含む）
        """
        # 実ステージ（DB上の値）
        actual_stage = word['stage']
        
        # 表示に使うステージ（モードで上書き）
        display_stage = self._get_display_stage(actual_stage)
        
        # 表示ステージに基づいてヒントを生成
        english = word['english']
        hint = self._generate_hint_for_stage(english, display_stage)
        
        if display_stage == 1:
            # ステージ1：日本語をそのまま表示
            self.japanese_label.setText(word['japanese'])
            self.hint_label.setText(hint if hint else "[ヒントなし]")
        elif display_stage == 2:
            # ステージ2：日本語は表示するが、英単語をシャッフル表示
            self.japanese_label.setText(word['japanese'])
            self.hint_label.setText(hint if hint else "[ヒントなし]")
        elif display_stage == 3:
            # ステージ3：日本語だけ表示（ヒントなし）
            self.japanese_label.setText(word['japanese'])
            self.hint_label.setText(hint if hint else "[ヒントなし]")
        elif display_stage == 4:
            # ★ステージ4：音声のみ。日本語は表示しない
            self.japanese_label.setText("")  # 完全に空にする
            self.hint_label.setText("[音声のみ - 音声を聞いて入力してください]")
        else:
            # 念のため
            self.japanese_label.setText(word['japanese'])
            self.hint_label.setText(hint if hint else "[ヒントなし]")
        
        # ステージラベルには表示ステージを表示
        self.stage_label.setText(f"ステージ {display_stage}")
    
    def load_next_word(self):
        """次の単語を読み込む"""
        # 前回の回答が不正解（False）の場合は新しい単語を取得しない
        # None（初期状態）または True（正解後）の場合は新しい単語を取得
        if self.last_answer_correct is False:
            return
        
        import time
        self.start_time = time.time()
        
        # フィルタパラメータを取得
        grade_min, grade_max, unit, level_max = self._get_filter_params()
        
        # 新しい単語を取得
        self.current_word = word_service.get_next_word(
            user_id=self.user_id,
            grade_min=grade_min,
            grade_max=grade_max,
            unit=unit,
            level_max=level_max
        )
        
        if not self.current_word:
            QMessageBox.warning(self, "エラー", "単語データがありません。\n先にデータをインポートしてください。")
            return
        
        # TTS を事前初期化（正解時の音声再生を即座に行うため）
        tts_service.warmup()
        
        # 状態をリセット
        self.last_answer_correct = None
        
        # ★(1) UI更新（すべてのラベル・入力欄・ボタンの状態を先に更新）
        # ステージ別の表示更新（_update_stage_ui内で表示ステージを計算してステージラベルも更新）
        self._update_stage_ui(self.current_word)
        
        # 入力欄とボタンの状態をリセット
        self.input_field.clear()
        self.input_field.setEnabled(True)
        self.result_label.clear()
        self.check_button.setEnabled(True)
        self.next_button.setEnabled(False)  # 出題直後は無効
        
        # 連続正解数表示
        streak = self.current_word.get('correct_streak', 0)
        self.streak_label.setText(f"連続正解: {streak}回")
        
        # ★ 問題カウンタ更新
        self.question_counter += 1
        self.question_label.setText(f"第 {self.question_counter} 問")
        
        # ★ 一瞬だけハイライトして「次の問題になった」ことを視覚的に見せる
        normal_style = "font-size: 14px;"
        highlight_style = "font-size: 14px; background-color: #FFFACD;"  # 薄い黄色
        
        self.question_label.setStyleSheet(highlight_style)
        
        def _reset_style():
            self.question_label.setStyleSheet(normal_style)
        
        QTimer.singleShot(200, _reset_style)  # 0.2秒後に元に戻す
        
        # ★(2) UIの更新を確実に反映させる
        QApplication.processEvents()
        
        # ★(3) 入力欄にフォーカスを当てる
        self.input_field.setFocus()
        
        # ★(4) ステージ4のときだけ、タブがアクティブなら音声を2秒後に再生
        # 表示ステージを取得
        actual_stage = self.current_word.get("stage", 1)
        display_stage = self._get_display_stage(actual_stage)
        
        if display_stage == 4 and self.is_active:
            def _play():
                # 2秒後も still アクティブ & 同じ単語が表示ステージ4なら再生
                if self.is_active and self.current_word:
                    current_actual_stage = self.current_word.get("stage", 1)
                    current_display_stage = self._get_display_stage(current_actual_stage)
                    if current_display_stage == 4:
                        tts_service.speak(self.current_word["english"])
            QTimer.singleShot(2000, _play)
    
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
            # ★(1) 正解した瞬間に即座に音声再生（TTS は事前初期化済み）
            tts_service.speak(self.current_word['english'])
            
            # ★(2) ラベル更新を実行（即座に表示）
            self.result_label.setText(f"✓ 正解！\n正解: {self.current_word['english']}")
            self.result_label.setStyleSheet("font-size: 16px; color: green; font-weight: bold;")
            
            # ★(3) 入力欄の状態変更
            self.input_field.setEnabled(False)
            self.check_button.setEnabled(False)
            self.input_field.clear()
            # 「次の単語」ボタンは有効のまま（手動でスキップ可能）
            self.next_button.setEnabled(True)
            
            # ★(4) GUIの更新を確実に反映（正解ラベルが表示されるのを待つ）
            QApplication.processEvents()
            
            # ★(5) その後に重い処理（DB書き込み）
            word_service.record_answer(
                user_id=self.user_id,
                word_id=self.current_word['word_id'],
                is_correct=True,
                answer_time_sec=answer_time
            )
            
            # ★(6) 正解音声を十分に聞いてから次の問題に移るため 2秒待つ
            QTimer.singleShot(2000, self._load_next_word_after_correct)
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
        正解時の2秒ディレイ後に呼ばれる。
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
        単語トレーニングタブが選択されたときに呼ばれる。
        """
        self.is_active = True
        
        # すでに current_word が表示ステージ4の場合は、2秒後に音声を流す
        if self.current_word:
            actual_stage = self.current_word.get("stage", 1)
            display_stage = self._get_display_stage(actual_stage)
            if display_stage == 4:
                def _play():
                    # まだタブがアクティブで表示ステージ4のままなら再生
                    if self.is_active and self.current_word:
                        current_actual_stage = self.current_word.get("stage", 1)
                        current_display_stage = self._get_display_stage(current_actual_stage)
                        if current_display_stage == 4:
                            tts_service.speak(self.current_word["english"])
                QTimer.singleShot(2000, _play)
    
    def on_deactivated(self):
        """
        別タブに切り替わったときに呼ぶ想定。
        """
        self.is_active = False
    
    def _on_voice_changed(self, index: int):
        """音声選択変更時のハンドラ"""
        voice_id = self.voice_combo.itemData(index)
        if not voice_id:
            return
        
        # TTS サービスに反映
        tts_service.set_voice(voice_id)
        
        # QSettings に保存
        self.settings.setValue("tts_voice", voice_id)
        self.settings.sync()
    
    def _get_filter_params(self) -> tuple[int | None, int | None, str | None, int | None]:
        """
        フィルタコンボボックスの現在値からフィルタパラメータを計算する
        
        Returns:
            (grade_min, grade_max, unit, level_max) のタプル
        """
        # grade
        grade_text = self.grade_combo.currentText()
        if grade_text == "中1だけ":
            grade_min, grade_max = 1, 1
        elif grade_text == "中2だけ":
            grade_min, grade_max = 2, 2
        elif grade_text == "中3だけ":
            grade_min, grade_max = 3, 3
        elif grade_text == "中1〜2":
            grade_min, grade_max = 1, 2
        elif grade_text == "中2〜3":
            grade_min, grade_max = 2, 3
        else:  # "中1〜3（すべて）" など
            grade_min, grade_max = None, None
        
        # unit
        unit_text = self.unit_combo.currentText()
        if unit_text == "すべて":
            unit = None
        else:
            unit = unit_text  # "food" など
        
        # level
        level_text = self.level_combo.currentText()
        if level_text == "レベル1まで":
            level_max = 1
        elif level_text == "レベル2まで":
            level_max = 2
        else:  # "レベル3まで（すべて）"
            level_max = None
        
        return grade_min, grade_max, unit, level_max
    
    def _disable_ui(self):
        """UIを無効化（スタート前の状態）"""
        self.input_field.setEnabled(False)
        self.check_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.japanese_label.setText("")
        self.hint_label.setText("")
        self.result_label.setText("")
        self.streak_label.setText("")
        self.stage_label.setText("")
        self.question_label.setText("第 0 問")
    
    def _enable_ui(self):
        """UIを有効化（スタート後の状態）"""
        self.input_field.setEnabled(True)
        self.check_button.setEnabled(True)
        # next_buttonは出題直後は無効のまま（load_next_word内で制御）
    
    def _on_start_clicked(self):
        """スタートボタンが押されたときの処理"""
        self._enable_ui()
        self.load_next_word()
        self.input_field.setFocus()











