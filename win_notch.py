import sys
import psutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel,
                             QPushButton, QDialog, QVBoxLayout, QCheckBox, QStyle, QColorDialog)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QDateTime
from PyQt5.QtGui import QCursor, QGuiApplication, QFont

class OptionsDialog(QDialog):
    def __init__(self, parent=None, display_options=None):
        super().__init__(parent)
        self.setWindowTitle("Notch Options")
        self.setFixedSize(250, 300)
        self.display_options = display_options or {}
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Display options checkboxes
        self.time_checkbox = QCheckBox("Show Time")
        self.cpu_checkbox = QCheckBox("Show CPU Usage")
        self.ram_checkbox = QCheckBox("Show RAM Usage")

        # Set initial states
        self.time_checkbox.setChecked(self.display_options.get("time", True))
        self.cpu_checkbox.setChecked(self.display_options.get("cpu", False))
        self.ram_checkbox.setChecked(self.display_options.get("ram", False))

        layout.addWidget(self.time_checkbox)
        layout.addWidget(self.cpu_checkbox)
        layout.addWidget(self.ram_checkbox)

        # Color selection buttons
        self.bg_color_button = QPushButton("Select Background Color")
        self.bg_color_button.clicked.connect(self.select_background_color)
        layout.addWidget(self.bg_color_button)

        self.text_color_button = QPushButton("Select Text Color")
        self.text_color_button.clicked.connect(self.select_text_color)
        layout.addWidget(self.text_color_button)

        # Exit program button
        self.exit_button = QPushButton("Exit Program")
        self.exit_button.clicked.connect(self.exit_program)
        layout.addWidget(self.exit_button)

        # OK button
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        layout.addWidget(ok_button)

        self.setLayout(layout)

        # Store colors
        self.bg_color = self.display_options.get("bg_color", "rgba(33, 150, 243, 70)")
        self.text_color = self.display_options.get("text_color", "white")

    def select_background_color(self):
        # Use an instance of QColorDialog instead of getColor()
        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle("Select Background Color")
        if color_dialog.exec_():
            color = color_dialog.currentColor()
            if color.isValid():
                # Convert QColor to RGBA string with desired alpha (transparency)
                self.bg_color = f"rgba({color.red()}, {color.green()}, {color.blue()}, 70)"  # Adjust alpha as needed

    def select_text_color(self):
        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle("Select Text Color")
        if color_dialog.exec_():
            color = color_dialog.currentColor()
            if color.isValid():
                self.text_color = color.name()  # Hex color code

    def exit_program(self):
        QApplication.quit()

    def get_options(self):
        return {
            "time": self.time_checkbox.isChecked(),
            "cpu": self.cpu_checkbox.isChecked(),
            "ram": self.ram_checkbox.isChecked(),
            "bg_color": self.bg_color,
            "text_color": self.text_color,
        }
class WinNotch(QMainWindow):
    def __init__(self):
        super().__init__()
        self.display_options = {
            "time": True,
            "cpu": False,
            "ram": False,
            "bg_color": "rgba(33, 150, 243, 70)",
            "text_color": "white"
        }
        self.init_ui()

    def init_ui(self):
        # Dimensions
        self.notch_width = 300
        self.collapsed_height = 30
        self.expanded_height = 100

        # Set up window properties
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(self.centered_geometry(self.notch_width, self.collapsed_height))

        # Background container
        self.background_widget = QWidget(self)
        self.background_widget.setGeometry(0, 0, self.notch_width, self.collapsed_height)
        self.update_background_style()

        # Info label
        self.info_label = QLabel(self.background_widget)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.update_text_style()
        font = QFont("Arial", 12, QFont.Bold)
        self.info_label.setFont(font)
        self.info_label.setGeometry(0, 0, self.width(), self.height())

        # Options button
        self.options_button = QPushButton(self.background_widget)
        self.options_button.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.options_button.setStyleSheet("background: transparent;")
        self.options_button.setGeometry(self.notch_width - 35, 5, 30, 30)
        self.options_button.clicked.connect(self.open_options)
        self.options_button.hide()  # Hide initially

        # Timer to update information every second
        self.info_timer = QTimer()
        self.info_timer.timeout.connect(self.update_display)
        self.info_timer.start(1000)  # Update every 1 second
        self.update_display()  # Initial call to display info immediately

        # Animation for smooth expand/collapse
        self.resize_animation = QPropertyAnimation(self, b"geometry")

        # Mouse proximity detection
        self.mouse_timer = QTimer()
        self.mouse_timer.timeout.connect(self.check_mouse_proximity)
        self.mouse_timer.start(50)  # Check every 50ms

    def update_background_style(self):
        bg_color = self.display_options.get("bg_color", "rgba(33, 150, 243, 70)")
        self.background_widget.setStyleSheet(f"""
            background-color: {bg_color};
            border-radius: 15px;
        """)

    def update_text_style(self):
        text_color = self.display_options.get("text_color", "white")
        self.info_label.setStyleSheet(f"color: {text_color};")

    def centered_geometry(self, width, height):
        screen_geometry = QGuiApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - width) // 2
        y = 0  # Top of the screen
        return QRect(x, y, width, height)

    def expand(self):
        if self.height() != self.expanded_height:
            self.resize_animation.stop()
            self.resize_animation.setDuration(300)
            self.resize_animation.setStartValue(self.geometry())
            self.resize_animation.setEndValue(self.centered_geometry(self.notch_width, self.expanded_height))
            self.resize_animation.start()
            self.options_button.show()

    def collapse(self):
        if self.height() != self.collapsed_height:
            self.resize_animation.stop()
            self.resize_animation.setDuration(300)
            self.resize_animation.setStartValue(self.geometry())
            self.resize_animation.setEndValue(self.centered_geometry(self.notch_width, self.collapsed_height))
            self.resize_animation.start()
            self.options_button.hide()

    def check_mouse_proximity(self):
        cursor_pos = QCursor.pos()
        notch_geometry = self.geometry()
        hoverable_area = QRect(
            notch_geometry.x(),
            notch_geometry.y(),
            notch_geometry.width(),
            notch_geometry.height() + 10  # Buffer below the notch
        )
        if hoverable_area.contains(cursor_pos):
            self.expand()
        else:
            self.collapse()

    def resizeEvent(self, event):
        self.background_widget.setGeometry(0, 0, self.width(), self.height())
        self.info_label.setGeometry(0, 0, self.width(), self.height())
        self.options_button.move(self.width() - 35, 5)
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.mouse_timer.stop()
        self.info_timer.stop()
        super().closeEvent(event)

    def open_options(self):
        options_dialog = OptionsDialog(self, self.display_options)
        if options_dialog.exec_():
            self.display_options = options_dialog.get_options()
            self.update_display()
            self.update_background_style()
            self.update_text_style()

    def update_display(self):
        """Updates the information displayed on the info_label."""
        display_texts = []
        if self.display_options.get("time", False):
            current_time = QDateTime.currentDateTime().toString("hh:mm:ss")
            display_texts.append(f"{current_time}")
        if self.display_options.get("cpu", False):
            cpu_usage = psutil.cpu_percent(interval=None)
            display_texts.append(f"CPU: {cpu_usage}%")
        if self.display_options.get("ram", False):
            ram_usage = psutil.virtual_memory().percent
            display_texts.append(f"RAM: {ram_usage}%")
        self.info_label.setText(" | ".join(display_texts))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    notch = WinNotch()
    notch.show()
    sys.exit(app.exec_())
