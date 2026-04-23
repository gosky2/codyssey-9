'''아이폰 계산기와 유사한 UI를 가지는 PyQt 계산기 예제.'''

import sys

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QApplication,
        QGridLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QApplication,
        QGridLayout,
        QLabel,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )


class CalculatorWindow(QWidget):
    '''입력만 가능한 계산기 UI 창.'''

    def __init__(self):
        super().__init__()
        self.expression = '0'
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle('Calculator')
        self.setMinimumSize(360, 580)
        self.setStyleSheet('background-color: #000000;')

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        self.display = QLabel(self.expression)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.display.setFixedHeight(120)
        self.display.setFont(QFont('Arial', 44))
        self.display.setStyleSheet(
            '''
            color: #FFFFFF;
            background-color: #000000;
            padding-right: 12px;
            '''
        )

        button_layout = QGridLayout()
        button_layout.setHorizontalSpacing(10)
        button_layout.setVerticalSpacing(10)

        buttons = [
            ('AC', 0, 0, 1, 1, 'utility'),
            ('+/-', 0, 1, 1, 1, 'utility'),
            ('%', 0, 2, 1, 1, 'utility'),
            ('÷', 0, 3, 1, 1, 'operator'),
            ('7', 1, 0, 1, 1, 'number'),
            ('8', 1, 1, 1, 1, 'number'),
            ('9', 1, 2, 1, 1, 'number'),
            ('×', 1, 3, 1, 1, 'operator'),
            ('4', 2, 0, 1, 1, 'number'),
            ('5', 2, 1, 1, 1, 'number'),
            ('6', 2, 2, 1, 1, 'number'),
            ('-', 2, 3, 1, 1, 'operator'),
            ('1', 3, 0, 1, 1, 'number'),
            ('2', 3, 1, 1, 1, 'number'),
            ('3', 3, 2, 1, 1, 'number'),
            ('+', 3, 3, 1, 1, 'operator'),
            ('0', 4, 0, 1, 2, 'number_zero'),
            ('.', 4, 2, 1, 1, 'number'),
            ('=', 4, 3, 1, 1, 'operator'),
        ]

        for text, row, col, row_span, col_span, role in buttons:
            button = QPushButton(text)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            button.setMinimumHeight(76)
            button.setFont(QFont('Arial', 24))
            button.clicked.connect(self._handle_button_click)
            button.setStyleSheet(self._button_style(role))
            button_layout.addWidget(button, row, col, row_span, col_span)

        main_layout.addWidget(self.display)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    @staticmethod
    def _button_style(role):
        if role == 'operator':
            background = '#FF9F0A'
            foreground = '#FFFFFF'
        elif role == 'utility':
            background = '#A5A5A5'
            foreground = '#000000'
        else:
            background = '#333333'
            foreground = '#FFFFFF'

        return (
            'QPushButton {'
            f'background-color: {background};'
            f'color: {foreground};'
            'border: none;'
            'border-radius: 38px;'
            '}'
            'QPushButton:pressed {'
            'opacity: 0.7;'
            'background-color: #6B6B6B;'
            '}'
        )

    def _handle_button_click(self):
        button = self.sender()
        if button is None:
            return

        text = button.text()

        if text == 'AC':
            self.expression = '0'
        elif text == '+/-':
            self._toggle_sign()
        elif self.expression == '0':
            self.expression = text
        else:
            self.expression += text

        self.display.setText(self.expression)

    def _toggle_sign(self):
        if not self.expression or self.expression == '0':
            return
        if self.expression.startswith('-'):
            self.expression = self.expression[1:]
        else:
            self.expression = '-' + self.expression


def main():
    app = QApplication(sys.argv)
    calculator = CalculatorWindow()
    calculator.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
