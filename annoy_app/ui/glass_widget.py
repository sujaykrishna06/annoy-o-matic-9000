"""
Apple-inspired Glassmorphism UI Widget built with PyQt6, DWM Acrylic Blur, and hardware DWM rounded corners.
"""
import sys
import time
import random
import threading
import pyautogui

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import (
    QColor, QPainter, QPen, QBrush, QLinearGradient, QFont, QCursor
)
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTextEdit, QComboBox, QDoubleSpinBox, QSpinBox, QPushButton, QFrame
)

try:
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

from annoy_app.config import (
    GLASS_TRANSPARENCY_ALPHA, GLASS_COLOR_RGB, CORNER_RADIUS, PRANK_PACKS, PASTE_ENTER_DELAY_MS
)
from annoy_app.core.win32_dwm import (
    enable_windows_acrylic_blur, set_windows_rounded_corners, get_acrylic_bg_color, safe_print
)
from annoy_app.core.clipboard import ClipboardGuard
from annoy_app.core.engine import WorkerSignals, apply_chaos_transform
from annoy_app.core.window_focus import get_running_chat_apps, focus_and_target_input


class AppleGlassCardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        # State
        self.is_running = False
        self.is_paused = False
        self.stop_requested = False
        self.mode = "letter"
        self.chaos_enabled = False
        self.sent_count = 0
        self.running_chat_apps = []

        # Dragging variables
        self._drag_pos = None

        # Clipboard Manager
        self.clipboard_guard = ClipboardGuard()

        self.signals = WorkerSignals()
        self.signals.update_status.connect(self._on_update_status)
        self.signals.update_meter.connect(self._on_update_meter)
        self.signals.finished.connect(self._on_finished)
        self.signals.trigger_glitch.connect(self._on_trigger_glitch)
        
        self.signals.request_start.connect(self.start_autotyper)
        self.signals.request_pause.connect(self.toggle_pause)
        self.signals.request_stop.connect(self.stop_autotyper)

        self._setup_ui()
        self._refresh_target_apps()
        self._start_global_key_listeners()

    def showEvent(self, event):
        super().showEvent(event)
        hwnd = int(self.winId())
        # Solely rely on DWMWA_WINDOW_CORNER_PREFERENCE hardware rounding (no software setMask)
        enable_windows_acrylic_blur(hwnd, bg_color=get_acrylic_bg_color())
        set_windows_rounded_corners(hwnd)

    def paintEvent(self, event):
        """Paints ultra-transparent glass fill & specular edge highlights."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        r = CORNER_RADIUS

        # Light glass fill over Acrylic Blur
        glass_brush = QBrush(QColor(255, 255, 255, 6))
        painter.setBrush(glass_brush)

        # Dynamic Glow Border Color
        if self.is_running and not self.is_paused:
            border_color = QColor(255, 69, 58, 200) # Pulsing Crimson Red
        else:
            border_color = QColor(10, 132, 255, 140) # Cyan/Blue Glass

        pen = QPen(border_color, 1)
        painter.setPen(pen)
        painter.drawRoundedRect(1, 1, w - 2, h - 2, r, r)

        # Specular Top Highlight Line
        top_grad = QLinearGradient(0, 1, w, 1)
        top_grad.setColorAt(0.0, QColor(255, 255, 255, 0))
        top_grad.setColorAt(0.5, QColor(255, 255, 255, 180))
        top_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(QPen(top_grad, 1.5))
        painter.drawLine(r, 1, w - r, 1)

        # Specular Left Highlight Line
        left_grad = QLinearGradient(1, 0, 1, h)
        left_grad.setColorAt(0.0, QColor(255, 255, 255, 180))
        left_grad.setColorAt(0.6, QColor(255, 255, 255, 40))
        left_grad.setColorAt(1.0, QColor(255, 255, 255, 10))
        painter.setPen(QPen(left_grad, 1.5))
        painter.drawLine(1, r, 1, h - r)

    def _setup_ui(self):
        self.setFixedWidth(380)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(9)

        # 1. macOS Header Bar with Traffic Lights
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 4)

        dots_layout = QHBoxLayout()
        dots_layout.setSpacing(6)

        btn_close = QPushButton()
        btn_close.setFixedSize(12, 12)
        btn_close.setStyleSheet("background: #ff5f56; border-radius: 6px; border: 1px solid #e0443e;")
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.clicked.connect(self.close)

        btn_min = QPushButton()
        btn_min.setFixedSize(12, 12)
        btn_min.setStyleSheet("background: #ffbd2e; border-radius: 6px; border: 1px solid #dea123;")
        btn_min.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_min.clicked.connect(self.hide)

        btn_pin = QPushButton()
        btn_pin.setFixedSize(12, 12)
        btn_pin.setStyleSheet("background: #27c93f; border-radius: 6px; border: 1px solid #1aab29;")

        dots_layout.addWidget(btn_close)
        dots_layout.addWidget(btn_min)
        dots_layout.addWidget(btn_pin)
        header.addLayout(dots_layout)

        title_lbl = QLabel("😈 Annoy-O-Matic 9000")
        title_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title_lbl.setStyleSheet("color: #ffffff; padding-left: 8px;")
        header.addWidget(title_lbl)

        header.addStretch()

        tag = QLabel(" FLOATING ")
        tag.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        tag.setStyleSheet("color: #0a84ff; background: rgba(10, 132, 255, 0.25); border-radius: 8px; padding: 2px 6px;")
        header.addWidget(tag)

        layout.addLayout(header)

        # 2. AUTO FOCUS CHAT APP SELECTION ROW
        lbl_target = QLabel("TARGET CHAT APP (AUTO FOCUS)")
        lbl_target.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        lbl_target.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        layout.addWidget(lbl_target)

        app_row = QHBoxLayout()
        app_row.setSpacing(6)

        self.app_combo = QComboBox()
        self.app_combo.setFont(QFont("Segoe UI", 9))
        self.app_combo.setStyleSheet("""
            QComboBox {
                background: rgba(0, 0, 0, 0.35);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QComboBox QAbstractItemView {
                background: #1a1a20;
                color: #ffffff;
                selection-background-color: #0a84ff;
            }
        """)
        app_row.addWidget(self.app_combo)

        btn_refresh_apps = QPushButton("🔄")
        btn_refresh_apps.setFixedSize(28, 28)
        btn_refresh_apps.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh_apps.setToolTip("Refresh Running Chat Apps")
        btn_refresh_apps.setStyleSheet("""
            QPushButton {
                background: rgba(0, 0, 0, 0.35);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover { background: rgba(10, 132, 255, 0.6); }
        """)
        btn_refresh_apps.clicked.connect(self._refresh_target_apps)
        app_row.addWidget(btn_refresh_apps)

        layout.addLayout(app_row)

        # 3. PRANK PACK SELECTION ROW
        lbl_prank = QLabel("SELECT PRANK PACK")
        lbl_prank.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        lbl_prank.setStyleSheet("color: rgba(255, 255, 255, 0.6); margin-top: 2px;")
        layout.addWidget(lbl_prank)

        self.prank_combo = QComboBox()
        self.prank_combo.setFont(QFont("Segoe UI", 9))
        self.prank_combo.addItems(list(PRANK_PACKS.keys()))
        self.prank_combo.setStyleSheet("""
            QComboBox {
                background: rgba(0, 0, 0, 0.35);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 4px 8px;
                font-size: 11px;
            }
            QComboBox QAbstractItemView {
                background: #1a1a20;
                color: #ffffff;
                selection-background-color: #0a84ff;
            }
        """)
        self.prank_combo.currentIndexChanged.connect(self._on_prank_selected)
        layout.addWidget(self.prank_combo)

        # 4. TARGET TEXT SECTION
        lbl_text = QLabel("TARGET MESSAGE TEXT")
        lbl_text.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        lbl_text.setStyleSheet("color: rgba(255, 255, 255, 0.6); margin-top: 2px;")
        layout.addWidget(lbl_text)

        self.text_box = QTextEdit()
        self.text_box.setFixedHeight(65)
        self.text_box.setPlainText("sujay")
        self.text_box.setFont(QFont("Consolas", 10))
        self.text_box.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 0.35);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 6px;
            }
            QTextEdit:focus {
                border: 1px solid #0a84ff;
            }
        """)
        layout.addWidget(self.text_box)

        # 5. UNIFIED SEGMENTED CONTROL BAR
        seg_bar = QFrame()
        seg_bar.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 10px;
            }
        """)
        seg_layout = QHBoxLayout(seg_bar)
        seg_layout.setContentsMargins(3, 3, 3, 3)
        seg_layout.setSpacing(4)

        self.btn_mode_letter = QPushButton("🔤 Letter")
        self.btn_mode_word = QPushButton("💬 Word")
        self.btn_mode_line = QPushButton("📄 Line")
        self.btn_chaos = QPushButton("🔥 Chaos: OFF")

        for b in (self.btn_mode_letter, self.btn_mode_word, self.btn_mode_line, self.btn_chaos):
            b.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            b.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        self.btn_mode_letter.clicked.connect(lambda: self._set_mode("letter"))
        self.btn_mode_word.clicked.connect(lambda: self._set_mode("word"))
        self.btn_mode_line.clicked.connect(lambda: self._set_mode("line"))
        self.btn_chaos.clicked.connect(self._toggle_chaos)

        seg_layout.addWidget(self.btn_mode_letter)
        seg_layout.addWidget(self.btn_mode_word)
        seg_layout.addWidget(self.btn_mode_line)
        seg_layout.addWidget(self.btn_chaos)

        layout.addWidget(seg_bar)
        self._update_seg_styles()

        # 6. DELAY SETTINGS CARD
        settings_card = QFrame()
        settings_card.setStyleSheet("""
            QFrame {
                background: rgba(0, 0, 0, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 10px;
            }
            QLabel { color: #ffffff; font-size: 11px; font-weight: 600; }
            QDoubleSpinBox, QSpinBox {
                background: rgba(0, 0, 0, 0.45);
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.25);
                border-radius: 6px;
                padding: 2px 20px 2px 6px;
                font-weight: bold;
                height: 26px;
            }
            QDoubleSpinBox:focus, QSpinBox:focus {
                border: 1px solid #0a84ff;
            }
            QDoubleSpinBox::up-button, QSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 18px;
                height: 12px;
                border-left: 1px solid rgba(255, 255, 255, 0.2);
                border-bottom: 1px solid rgba(255, 255, 255, 0.15);
                border-top-right-radius: 5px;
                background: rgba(255, 255, 255, 0.12);
            }
            QDoubleSpinBox::down-button, QSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 18px;
                height: 12px;
                border-left: 1px solid rgba(255, 255, 255, 0.2);
                border-bottom-right-radius: 5px;
                background: rgba(255, 255, 255, 0.12);
            }
            QDoubleSpinBox::up-button:hover, QSpinBox::up-button:hover,
            QDoubleSpinBox::down-button:hover, QSpinBox::down-button:hover {
                background: rgba(10, 132, 255, 0.7);
            }
            QDoubleSpinBox::up-arrow, QSpinBox::up-arrow {
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='8' height='5'><polygon points='4,0 8,5 0,5' fill='%23ffffff'/></svg>");
                width: 8px;
                height: 5px;
            }
            QDoubleSpinBox::down-arrow, QSpinBox::down-arrow {
                image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='8' height='5'><polygon points='0,0 8,0 4,5' fill='%23ffffff'/></svg>");
                width: 8px;
                height: 5px;
            }
        """)
        s_layout = QHBoxLayout(settings_card)
        s_layout.setContentsMargins(10, 8, 10, 8)
        s_layout.setSpacing(6)

        # Msg Delay (s): Label
        lbl_msg = QLabel("Msg Delay (s):")
        lbl_msg.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        s_layout.addWidget(lbl_msg)
        
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.delay_spin.setRange(0.05, 5.0)
        self.delay_spin.setSingleStep(0.05)
        self.delay_spin.setValue(0.15)
        self.delay_spin.setFixedWidth(74)
        s_layout.addWidget(self.delay_spin)

        s_layout.addStretch()

        # Start Delay (s): Label
        lbl_start = QLabel("Start Delay (s):")
        lbl_start.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        s_layout.addWidget(lbl_start)

        self.countdown_spin = QSpinBox()
        self.countdown_spin.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.countdown_spin.setRange(1, 10)
        self.countdown_spin.setValue(3)
        self.countdown_spin.setFixedWidth(64)
        s_layout.addWidget(self.countdown_spin)

        layout.addWidget(settings_card)

        # 7. CHAOS METER & RANK BADGE
        meter_layout = QHBoxLayout()
        lbl_meter = QLabel("CHAOS METER")
        lbl_meter.setFont(QFont("Segoe UI", 7, QFont.Weight.Bold))
        lbl_meter.setStyleSheet("color: rgba(255, 255, 255, 0.6);")
        meter_layout.addWidget(lbl_meter)

        meter_layout.addStretch()

        self.rank_lbl = QLabel("😊 Mild Annoyance")
        self.rank_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.rank_lbl.setStyleSheet("color: #30d158;")
        meter_layout.addWidget(self.rank_lbl)
        layout.addLayout(meter_layout)

        # Chaos Meter Frame Bar
        self.meter_bar = QFrame()
        self.meter_bar.setFixedHeight(8)
        self.meter_bar.setStyleSheet("background: rgba(0,0,0,0.3); border-radius: 4px;")
        layout.addWidget(self.meter_bar)

        # 8. STATUS BANNER CARD
        self.status_card = QFrame()
        self.status_card.setStyleSheet("""
            QFrame {
                background: rgba(10, 132, 255, 0.15);
                border: 1px solid rgba(10, 132, 255, 0.3);
                border-radius: 8px;
            }
        """)
        sc_layout = QHBoxLayout(self.status_card)
        sc_layout.setContentsMargins(8, 6, 8, 6)

        self.status_lbl = QLabel("Ready • Press Start (F5)")
        self.status_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.status_lbl.setStyleSheet("color: #64d2ff; background: transparent;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sc_layout.addWidget(self.status_lbl)
        layout.addWidget(self.status_card)

        # 9. ACTION BUTTONS (F5=Start, F8=Pause, ESC=Abort)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.start_btn = QPushButton("▶  Start (F5)")
        self.start_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.start_btn.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(48, 209, 88, 0.9), stop:1 rgba(34, 160, 68, 0.95));
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 10px;
                padding: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(52, 225, 95, 0.95), stop:1 rgba(38, 185, 78, 1));
            }
            QPushButton:disabled { opacity: 0.4; }
        """)
        self.start_btn.clicked.connect(self.start_autotyper)
        btn_layout.addWidget(self.start_btn)

        self.pause_btn = QPushButton("⏸ Pause (F8)")
        self.pause_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.pause_btn.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.pause_btn.setEnabled(False)
        self.pause_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255, 214, 10, 0.9), stop:1 rgba(210, 170, 5, 0.95));
                color: #11111b;
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 10px;
                padding: 8px;
            }
            QPushButton:disabled { opacity: 0.4; }
        """)
        self.pause_btn.clicked.connect(self.toggle_pause)
        btn_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⬛ Abort (ESC)")
        self.stop_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.stop_btn.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255, 69, 58, 0.9), stop:1 rgba(215, 45, 36, 0.95));
                color: #ffffff;
                border: 1px solid rgba(255, 255, 255, 0.4);
                border-radius: 10px;
                padding: 8px;
            }
            QPushButton:disabled { opacity: 0.4; }
        """)
        self.stop_btn.clicked.connect(self.stop_autotyper)
        btn_layout.addWidget(self.stop_btn)

        layout.addLayout(btn_layout)

        self.adjustSize()

    def _refresh_target_apps(self):
        """Scans running windows against process executable name whitelist."""
        self.app_combo.clear()
        self.running_chat_apps = get_running_chat_apps()

        if self.running_chat_apps:
            for w in self.running_chat_apps:
                display_name = f"🟢 {w.exe_name} — {w.title[:22]}" if len(w.title) > 22 else f"🟢 {w.exe_name} — {w.title}"
                self.app_combo.addItem(display_name, userData=w)
        else:
            self.app_combo.addItem("⚠️ No supported chat apps detected", userData=None)

        self.app_combo.addItem("👇 Manual Focus (Countdown Only)", userData="manual")

    def _update_seg_styles(self):
        active_style = "background: rgba(10, 132, 255, 0.85); color: #ffffff; border-radius: 7px; border: none; padding: 4px;"
        inactive_style = "background: transparent; color: rgba(255, 255, 255, 0.6); border: none; padding: 4px;"

        self.btn_mode_letter.setStyleSheet(active_style if self.mode == "letter" else inactive_style)
        self.btn_mode_word.setStyleSheet(active_style if self.mode == "word" else inactive_style)
        self.btn_mode_line.setStyleSheet(active_style if self.mode == "line" else inactive_style)

        if self.chaos_enabled:
            self.btn_chaos.setText("🔥 Chaos: ON")
            self.btn_chaos.setStyleSheet("background: rgba(255, 69, 58, 0.85); color: #ffffff; border-radius: 7px; border: none; padding: 4px;")
        else:
            self.btn_chaos.setText("🔥 Chaos: OFF")
            self.btn_chaos.setStyleSheet(inactive_style)

    def _set_mode(self, new_mode):
        self.mode = new_mode
        self._update_seg_styles()

    def _toggle_chaos(self):
        self.chaos_enabled = not self.chaos_enabled
        self._update_seg_styles()

    def _on_prank_selected(self, index):
        selected = self.prank_combo.currentText()
        content = PRANK_PACKS.get(selected)
        if content:
            self.text_box.setPlainText(content)
            if "\n" in content:
                self._set_mode("line")

    def _start_glow_timer(self):
        self.glow_timer = QTimer(self)
        self.glow_timer.timeout.connect(self._on_glow_step)
        self.glow_timer.start(200)

    def _stop_glow_timer(self):
        if hasattr(self, 'glow_timer') and self.glow_timer.isActive():
            self.glow_timer.stop()

    def _on_glow_step(self):
        if self.is_running and not self.is_paused:
            self.update()

    def _start_global_key_listeners(self):
        if PYNPUT_AVAILABLE:
            def on_press(key):
                if key == keyboard.Key.esc and self.is_running:
                    self.signals.request_stop.emit()
                elif key == keyboard.Key.f8 and self.is_running:
                    self.signals.request_pause.emit()
                elif key == keyboard.Key.f5 and not self.is_running:
                    self.signals.request_start.emit()

            listener = keyboard.Listener(on_press=on_press)
            listener.daemon = True
            listener.start()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def _on_update_status(self, text, color):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet(f"color: {color}; background: transparent;")

    def _on_update_meter(self, count):
        self.sent_count = count
        if count < 10:
            rank, color = "😊 Mild Annoyance", "#30d158"
        elif count < 25:
            rank, color = "😈 Nuisance", "#ffd60a"
        elif count < 50:
            rank, color = "🔥 Menace", "#ff9f0a"
        elif count < 100:
            rank, color = "💀 Certified Chaos Agent", "#ff453a"
        else:
            rank, color = "👑 GOD OF TROLLING", "#bf5af2"

        self.rank_lbl.setText(rank)
        self.rank_lbl.setStyleSheet(f"color: {color};")

        self.meter_bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {color}, stop:1 rgba(0,0,0,0.2));
                border-radius: 4px;
            }}
        """)

    def _on_trigger_glitch(self, remaining):
        col = random.choice(["#ff453a", "#0a84ff", "#30d158", "rgba(255,255,255,0.2)"])
        self.text_box.setStyleSheet(f"""
            QTextEdit {{
                background: rgba(0, 0, 0, 0.45);
                color: #ffffff;
                border: 2px solid {col};
                border-radius: 10px;
                padding: 6px;
            }}
        """)

    def _on_finished(self, status_msg):
        self.is_running = False
        self.is_paused = False
        self.stop_requested = False
        self._stop_glow_timer()
        
        # Restore or clear clipboard cleanly
        self.clipboard_guard.restore_or_clear()

        self.start_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.pause_btn.setText("⏸ Pause (F8)")
        self._on_update_status(status_msg, "#64d2ff")
        safe_print(f"[AutoTyper] Run finished cleanly. State reset: is_running={self.is_running}")

    def toggle_pause(self):
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.pause_btn.setText("▶ Resume")
            self._on_update_status("⏸ PAUSED (Press F8 or Resume)", "#ffd60a")
        else:
            self.pause_btn.setText("⏸ Pause (F8)")
            self._on_update_status("⚡ Resuming typing...", "#30d158")

    def start_autotyper(self):
        if self.is_running:
            safe_print("[AutoTyper] Start ignored: already running.")
            return

        text_content = self.text_box.toPlainText().strip()
        if not text_content:
            return

        # Backup original OS clipboard
        self.clipboard_guard.backup()

        self.is_running = True
        self.is_paused = False
        self.stop_requested = False
        self.sent_count = 0

        self._start_glow_timer()

        self.start_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.pause_btn.setText("⏸ Pause (F8)")
        self.stop_btn.setEnabled(True)

        msg_delay = self.delay_spin.value()
        start_countdown = self.countdown_spin.value()

        # Check selected target chat app for auto-focus
        target_win = self.app_combo.currentData()

        safe_print(f"[AutoTyper] Starting run: mode={self.mode}, delay={msg_delay}s, countdown={start_countdown}s, target={target_win}")

        threading.Thread(
            target=self._run_process,
            args=(text_content, self.mode, msg_delay, start_countdown, self.chaos_enabled, target_win),
            daemon=True
        ).start()

    def stop_autotyper(self):
        if self.is_running:
            self.stop_requested = True
            self.signals.update_status.emit("⚠️ Abort Requested...", "#ff453a")

    def _run_process(self, text, mode, msg_delay, start_countdown, chaos_mode, target_win):
        # Auto-Focus & UIA Text Field Target Phase
        if target_win and hasattr(target_win, 'hwnd'):
            self.signals.update_status.emit(f"🎯 Focusing {target_win.exe_name}...", "#64d2ff")
            uia_ok, focus_msg = focus_and_target_input(target_win.hwnd, target_win.exe_name)
            self.signals.update_status.emit(focus_msg, "#30d158" if uia_ok else "#ffd60a")
            time.sleep(0.5)

        # Countdown Phase
        for remaining in range(start_countdown, 0, -1):
            if self.stop_requested:
                self.signals.finished.emit("Stopped by user")
                return

            self.signals.update_status.emit(f"⏳ Typing in {remaining}s...", "#ffd60a")
            self.signals.trigger_glitch.emit(remaining)
            time.sleep(0.8)

        if self.stop_requested:
            self.signals.finished.emit("Stopped by user")
            return

        # Parse Text into Chunks
        if mode == "letter":
            chunks = list(text)
        elif mode == "word":
            chunks = text.split()
        elif mode == "line":
            chunks = text.splitlines()
        else:
            chunks = [text]

        total = len(chunks)
        self.signals.update_status.emit(f"⚡ Sending 0/{total}...", "#30d158")

        # Typing Loop
        for i, chunk in enumerate(chunks, 1):
            while self.is_paused:
                if self.stop_requested:
                    self.signals.finished.emit(f"🛑 Aborted at {i-1}/{total}")
                    return
                time.sleep(0.2)

            if self.stop_requested:
                self.signals.finished.emit(f"🛑 Aborted at {i-1}/{total}")
                return

            out_chunk = apply_chaos_transform(chunk) if chaos_mode else chunk
            display_chunk = (out_chunk[:15] + "...") if len(out_chunk) > 18 else out_chunk
            self.signals.update_status.emit(f"⚡ {i}/{total}: '{display_chunk}'", "#30d158")

            # Safe copy with retry protection
            copy_ok = self.clipboard_guard.safe_copy(out_chunk, retries=3)
            if not copy_ok:
                safe_print(f"[AutoTyper] Warning: Clipboard lock timeout on chunk {i}")

            try:
                pyautogui.hotkey('ctrl', 'v')
                # Configurable micro-delay between Paste and Enter (PASTE_ENTER_DELAY_MS = 0.06s)
                time.sleep(PASTE_ENTER_DELAY_MS)
                pyautogui.press('enter')
            except pyautogui.FailSafeException:
                self.signals.finished.emit("🛑 Fail-Safe Triggered! Mouse in corner.")
                return

            self.signals.update_meter.emit(i)

            # Humanized Jitter Delay (+/- 35% random variation)
            jitter = msg_delay * random.uniform(0.65, 1.35)
            if random.random() < 0.05:
                jitter += random.uniform(0.25, 0.45)

            time.sleep(max(0.01, jitter))

        self.signals.finished.emit(f"✅ Sent {total} messages!")
