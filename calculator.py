'''아이폰 계산기와 유사한 UI를 가지는 PyQt 계산기 예제.'''

import ast
import math
import operator
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

    _ALIGN_RIGHT_BOTTOM = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom
    _SIZE_POLICY = (QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    _EXPANDING_POLICY = QSizePolicy.Policy.Expanding
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

    _ALIGN_RIGHT_BOTTOM = Qt.AlignRight | Qt.AlignBottom
    _SIZE_POLICY = (QSizePolicy.Expanding, QSizePolicy.Expanding)
    _EXPANDING_POLICY = QSizePolicy.Expanding


# iOS 계산기 다크 모드 팔레트
_BG = '#000000'
_NUMBER = '#333333'
_NUMBER_TEXT = '#FFFFFF'
_UTILITY = '#A5A5A5'
_UTILITY_TEXT = '#000000'
_OPERATOR = '#FF9F0A'
_OPERATOR_TEXT = '#FFFFFF'

_NUMBER_PRESSED = '#737373'
_UTILITY_PRESSED = '#D4D4D2'
_OPERATOR_PRESSED = '#E89E36'

_GAP = 10
_H_MARGIN = 16
_V_MARGIN = 20


def _set_font_weight_light(font: QFont) -> None:
    try:
        font.setWeight(QFont.Weight.Light)
    except AttributeError:
        font.setWeight(QFont.Light)


def _set_font_weight_medium(font: QFont) -> None:
    try:
        font.setWeight(QFont.Weight.Medium)
    except AttributeError:
        font.setWeight(QFont.Medium)


def _display_font(px: int) -> QFont:
    for family in ('.AppleSystemUIFont', 'SF Pro Display', 'Helvetica Neue', 'Arial'):
        font = QFont(family, px)
        if font.exactMatch() or family == 'Arial':
            _set_font_weight_light(font)
            return font
    font = QFont('Arial', px)
    _set_font_weight_light(font)
    return font


def _button_font(px: int) -> QFont:
    for family in ('.AppleSystemUIFont', 'SF Pro Text', 'Helvetica Neue', 'Arial'):
        font = QFont(family, px)
        if font.exactMatch() or family == 'Arial':
            _set_font_weight_medium(font)
            return font
    font = QFont('Arial', px)
    _set_font_weight_medium(font)
    return font


def _button_style(role: str, radius: int) -> str:
    if role == 'operator':
        bg, fg, press = _OPERATOR, _OPERATOR_TEXT, _OPERATOR_PRESSED
    elif role == 'utility':
        bg, fg, press = _UTILITY, _UTILITY_TEXT, _UTILITY_PRESSED
    else:
        bg, fg, press = _NUMBER, _NUMBER_TEXT, _NUMBER_PRESSED

    r = max(radius, 1)
    return (
        'QPushButton {'
        f'background-color: {bg};'
        f'color: {fg};'
        'border: none;'
        f'border-radius: {r}px;'
        'padding: 0;'
        '}'
        'QPushButton:pressed {'
        f'background-color: {press};'
        f'color: {fg};'
        '}'
    )


def _normalize_expression(raw: str) -> str:
    s = raw.replace('×', '*').replace('÷', '/')
    s = s.replace('−', '-').replace('\u2212', '-')
    return s


def _last_number_segment(raw: str) -> str:
    n = _normalize_expression(raw)
    i = len(n) - 1
    while i >= 0 and (n[i].isdigit() or n[i] == '.'):
        i -= 1
    return n[i + 1 :]


def _strip_trailing_ops_display(e: str) -> str:
    while e and e[-1] in '+×÷*':
        e = e[:-1]
    while len(e) > 1 and e[-1] in '-−':
        prev = e[-2]
        if prev.isdigit() or prev == '.':
            e = e[:-1]
        else:
            break
    return e


def _format_result(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError('non-finite')
    iv = int(round(value))
    if abs(value - iv) < 1e-9:
        return str(iv)
    return f'{value:.12g}'.rstrip('0').rstrip('.')


def _safe_eval_expression(expr: str) -> float:
    expr = _normalize_expression(expr).strip()
    while expr and expr[-1] in '+-*/':
        expr = expr[:-1].strip()
    if not expr:
        raise ValueError('empty')

    tree = ast.parse(expr, mode='eval')

    bin_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
    }

    def _eval(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool):
                raise ValueError('bad constant')
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError('bad constant')
        if isinstance(node, ast.Num):  # Python < 3.8 호환
            return float(node.n)
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.UAdd):
                return +_eval(node.operand)
            if isinstance(node.op, ast.USub):
                return -_eval(node.operand)
            raise ValueError('bad unary')
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in bin_ops:
                raise ValueError('bad binop')
            left = _eval(node.left)
            right = _eval(node.right)
            return bin_ops[op_type](left, right)
        raise ValueError('disallowed syntax')

    return _eval(tree)


class CalculatorWindow(QWidget):
    '''입력만 가능한 계산기 UI 창.'''

    def __init__(self):
        super().__init__()
        self.expression = '0'
        self._after_equals = False
        self._round_buttons = []
        self._zero_button = None
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle('Calculator')
        self.setMinimumSize(320, 520)
        self.setStyleSheet(f'background-color: {_BG};')

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(_H_MARGIN, _V_MARGIN, _H_MARGIN, _V_MARGIN)
        main_layout.setSpacing(0)

        self.display = QLabel(self.expression)
        self.display.setAlignment(_ALIGN_RIGHT_BOTTOM)
        self.display.setMinimumHeight(96)
        self.display.setSizePolicy(_EXPANDING_POLICY, _EXPANDING_POLICY)
        self.display.setFont(_display_font(52))
        self.display.setStyleSheet(
            f'''
            color: {_NUMBER_TEXT};
            background-color: {_BG};
            padding: 8px 4px 16px 8px;
            '''
        )

        self._grid = QGridLayout()
        self._grid.setHorizontalSpacing(_GAP)
        self._grid.setVerticalSpacing(_GAP)
        for c in range(4):
            self._grid.setColumnStretch(c, 1)
        for r in range(5):
            self._grid.setRowStretch(r, 1)

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
            button.setSizePolicy(_SIZE_POLICY[0], _SIZE_POLICY[1])
            button.clicked.connect(self._handle_button_click)
            button.setProperty('calc_role', role)
            if role == 'number_zero':
                self._zero_button = button
            else:
                self._round_buttons.append(button)
            self._grid.addWidget(button, row, col, row_span, col_span)

        main_layout.addWidget(self.display, stretch=2)
        main_layout.addLayout(self._grid, stretch=3)
        self.setLayout(main_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_button_geometry()

    def showEvent(self, event):
        super().showEvent(event)
        self._apply_button_geometry()

    def _apply_button_geometry(self):
        inner_w = max(self.width() - 2 * _H_MARGIN, 200)
        cell = (inner_w - 3 * _GAP) / 4.0
        d = int(max(cell, 56))

        label_pt = max(14, min(32, int(d * 0.36)))
        disp_pt = max(34, min(64, int(d * 0.85)))
        for btn in self._round_buttons:
            btn.setFixedSize(d, d)
            btn.setFont(_button_font(label_pt))
            role = btn.property('calc_role') or 'number'
            btn.setStyleSheet(_button_style(str(role), d // 2))

        if self._zero_button is not None:
            zero_w = int(2 * d + _GAP)
            self._zero_button.setFixedSize(zero_w, d)
            self._zero_button.setFont(_button_font(label_pt))
            self._zero_button.setStyleSheet(_button_style('number', d // 2))

        self.display.setFont(_display_font(disp_pt))

    def _handle_button_click(self):
        button = self.sender()
        if button is None:
            return

        text = button.text()

        if text == 'AC':
            self.expression = '0'
            self._after_equals = False
        elif text == '+/-':
            if self.expression == 'Error':
                return
            self._after_equals = False
            self._toggle_sign()
        elif text == '=':
            if self.expression == 'Error':
                return
            try:
                value = _safe_eval_expression(self.expression)
                self.expression = _format_result(value)
            except (ValueError, SyntaxError, ZeroDivisionError, TypeError, OverflowError):
                self.expression = 'Error'
            self._after_equals = True
        elif text == '%':
            if self.expression == 'Error':
                return
            self._after_equals = False
            self._apply_percent()
        elif text in '0123456789':
            if self.expression == 'Error':
                self.expression = text
            elif self._after_equals:
                self.expression = text
            elif self.expression == '0':
                self.expression = text
            else:
                self.expression += text
            self._after_equals = False
        elif text == '.':
            if self.expression == 'Error':
                self.expression = '0.'
            elif self._after_equals:
                self.expression = '0.'
            elif self.expression == '0':
                self.expression = '0.'
            else:
                last = _last_number_segment(self.expression)
                if '.' in last:
                    return
                self.expression += '.'
            self._after_equals = False
        elif text in ('+', '-', '×', '÷'):
            if self.expression == 'Error':
                return
            self._after_equals = False
            self._append_binary_operator(text)

        self.display.setText(self.expression)

    def _append_binary_operator(self, op: str) -> None:
        e = _strip_trailing_ops_display(self.expression)
        if not e or e in ('-', '−'):
            e = '0'
        self.expression = e + op

    def _apply_percent(self) -> None:
        try:
            value = _safe_eval_expression(self.expression)
            self.expression = _format_result(value / 100.0)
        except (ValueError, SyntaxError, ZeroDivisionError, TypeError, OverflowError):
            self.expression = 'Error'

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
    calculator.resize(390, 640)
    calculator.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
