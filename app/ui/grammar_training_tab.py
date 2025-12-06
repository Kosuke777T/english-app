"""
文法トレーニングタブ
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QListWidgetItem, QLineEdit, 
    QPushButton, QRadioButton, QButtonGroup, QMessageBox
)
from PyQt6.QtCore import Qt
from app.services import grammar_service
from app.services import db


class GrammarTrainingTab(QWidget):
    """文法トレーニング画面"""
    
    def __init__(self):
        super().__init__()
        self.current_topic_id = None
        self.current_question = None
        self.button_group = None
        
        self.init_ui()
        self.load_topics()
    
    def init_ui(self):
        """UIを初期化"""
        main_layout = QHBoxLayout()
        
        # 左側: トピック一覧
        left_panel = QVBoxLayout()
        left_panel.addWidget(QLabel("文法トピック"))
        self.topic_list = QListWidget()
        self.topic_list.itemClicked.connect(self.on_topic_selected)
        left_panel.addWidget(self.topic_list)
        
        left_widget = QWidget()
        left_widget.setLayout(left_panel)
        left_widget.setMaximumWidth(250)
        main_layout.addWidget(left_widget)
        
        # 右側: 問題表示エリア
        right_panel = QVBoxLayout()
        
        # トピック説明
        self.topic_description = QLabel("左側からトピックを選択してください")
        self.topic_description.setWordWrap(True)
        self.topic_description.setStyleSheet("font-size: 14px; padding: 10px;")
        right_panel.addWidget(self.topic_description)
        
        # 問題表示
        self.question_label = QLabel("")
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        right_panel.addWidget(self.question_label)
        
        # 選択肢エリア（mcq用）
        self.choice_widget = QWidget()
        self.choice_layout = QVBoxLayout()
        self.choice_widget.setLayout(self.choice_layout)
        right_panel.addWidget(self.choice_widget)
        
        # 入力欄（fill用）
        self.fill_input = QLineEdit()
        self.fill_input.setPlaceholderText("答えを入力してください")
        self.fill_input.setVisible(False)
        right_panel.addWidget(self.fill_input)
        
        # ボタン
        button_layout = QHBoxLayout()
        self.check_button = QPushButton("答え合わせ")
        self.check_button.clicked.connect(self.check_answer)
        self.check_button.setEnabled(False)
        button_layout.addWidget(self.check_button)
        
        self.next_button = QPushButton("次の問題")
        self.next_button.clicked.connect(self.load_next_question)
        self.next_button.setEnabled(False)
        button_layout.addWidget(self.next_button)
        
        right_panel.addLayout(button_layout)
        
        # 結果表示
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font-size: 14px; padding: 10px;")
        right_panel.addWidget(self.result_label)
        
        # マスター度表示
        self.mastery_label = QLabel("")
        self.mastery_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(self.mastery_label)
        
        right_panel.addStretch()
        
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        main_layout.addWidget(right_widget)
        
        self.setLayout(main_layout)
    
    def load_topics(self):
        """トピック一覧を読み込む"""
        topics = grammar_service.list_topics()
        self.topic_list.clear()
        
        for topic in topics:
            item = QListWidgetItem(topic['title'])
            item.setData(Qt.ItemDataRole.UserRole, topic['grammar_id'])
            self.topic_list.addItem(item)
    
    def on_topic_selected(self, item):
        """トピックが選択されたとき"""
        topic_id = item.data(Qt.ItemDataRole.UserRole)
        self.current_topic_id = topic_id
        
        # トピック詳細を取得
        topic = grammar_service.get_topic_detail(topic_id)
        if topic:
            self.topic_description.setText(
                f"【{topic['title']}】\n{topic.get('description', '')}"
            )
        
        # 最初の問題を読み込む
        self.load_next_question()
    
    def load_next_question(self):
        """次の問題を読み込む"""
        if not self.current_topic_id:
            return
        
        self.current_question = grammar_service.get_next_question(
            user_id=1,
            grammar_id=self.current_topic_id
        )
        
        if not self.current_question:
            QMessageBox.warning(self, "エラー", "問題データがありません。")
            return
        
        # 問題を表示
        self.question_label.setText(self.current_question['prompt_text'])
        
        # 選択肢をクリア
        for i in reversed(range(self.choice_layout.count())):
            self.choice_layout.itemAt(i).widget().setParent(None)
        
        self.button_group = QButtonGroup()
        
        # 問題タイプに応じてUIを切り替え
        if self.current_question['question_type'] == 'mcq':
            # 四択問題
            self.fill_input.setVisible(False)
            choices = [
                self.current_question.get('choice1'),
                self.current_question.get('choice2'),
                self.current_question.get('choice3'),
                self.current_question.get('choice4')
            ]
            
            for i, choice in enumerate(choices):
                if choice:
                    radio = QRadioButton(choice)
                    self.button_group.addButton(radio, i)
                    self.choice_layout.addWidget(radio)
        else:
            # 穴埋め問題
            self.fill_input.setVisible(True)
            self.fill_input.clear()
        
        self.result_label.clear()
        self.check_button.setEnabled(True)
        self.next_button.setEnabled(False)
    
    def check_answer(self):
        """答え合わせ"""
        if not self.current_question:
            return
        
        # 回答を取得
        if self.current_question['question_type'] == 'mcq':
            selected_button = self.button_group.checkedButton()
            if not selected_button:
                QMessageBox.warning(self, "エラー", "選択肢を選んでください。")
                return
            user_answer = selected_button.text()
        else:
            user_answer = self.fill_input.text().strip()
            if not user_answer:
                QMessageBox.warning(self, "エラー", "答えを入力してください。")
                return
        
        # 採点
        result = grammar_service.check_answer(
            user_id=1,
            question_id=self.current_question['question_id'],
            answer=user_answer
        )
        
        if not result:
            return
        
        # 結果表示
        if result['is_correct']:
            self.result_label.setText("✓ 正解！")
            self.result_label.setStyleSheet("font-size: 14px; color: green; font-weight: bold; padding: 10px;")
        else:
            self.result_label.setText(
                f"✗ 不正解\n正解: {result['correct_answer']}\n\n解説: {result.get('explanation', '')}"
            )
            self.result_label.setStyleSheet("font-size: 14px; color: red; padding: 10px;")
        
        # マスター度表示
        mastery = result['mastery_level']
        self.mastery_label.setText(f"マスター度: {mastery}%")
        
        self.check_button.setEnabled(False)
        self.next_button.setEnabled(True)











