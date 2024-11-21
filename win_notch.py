import sys
import os
import psutil
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QDialog,
    QVBoxLayout, QCheckBox, QStyle, QColorDialog, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import (
    Qt, QTimer, QPropertyAnimation, QRect, QDateTime, pyqtSignal, QSize
)
from PyQt5.QtGui import QCursor, QGuiApplication, QFont, QColor
from send2trash import send2trash  # Ensure you have installed send2trash


class OptionsDialog(QDialog):
    # Define custom signals for immediate color updates
    bg_color_changed = pyqtSignal(str)
    text_color_changed = pyqtSignal(str)

    def __init__(self, parent=None, display_options=None):
        super().__init__(parent)
        self.setWindowTitle("Notch Options")
        self.setFixedSize(250, 350)
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
        self.bg_color = self.display_options.get("bg_color", "rgba(33, 150, 243, 180)")
        self.text_color = self.display_options.get("text_color", "white")

    def select_background_color(self):
        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle("Select Background Color")
        # Initialize with current background color
        current_bg = self.bg_color
        if current_bg.startswith("rgba"):
            rgba = current_bg[5:-1].split(',')
            if len(rgba) == 4:
                r, g, b, a = [int(x.strip()) for x in rgba]
                initial_color = QColor(r, g, b, a)
            else:
                initial_color = QColor(33, 150, 243, 180)
        else:
            initial_color = QColor(33, 150, 243, 180)
        color_dialog.setCurrentColor(initial_color)
        if color_dialog.exec_():
            color = color_dialog.currentColor()
            if color.isValid():
                # Convert QColor to RGBA string with desired alpha (transparency)
                self.bg_color = f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha()})"
                # Emit signal with new color
                self.bg_color_changed.emit(self.bg_color)

    def select_text_color(self):
        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle("Select Text Color")
        # Initialize with current text color
        current_text = self.text_color
        initial_color = QColor(current_text) if QColor(current_text).isValid() else QColor("white")
        color_dialog.setCurrentColor(initial_color)
        if color_dialog.exec_():
            color = color_dialog.currentColor()
            if color.isValid():
                self.text_color = color.name()  # Hex color code
                # Emit signal with new color
                self.text_color_changed.emit(self.text_color)

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
            "bg_color": "rgba(33, 150, 243, 180)",
            "text_color": "white"
        }
        self.init_ui()

    def init_ui(self):
        # Dimensions
        self.notch_width = 300
        self.collapsed_height = 30
        self.expanded_height = 100

        # Set up window properties
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setGeometry(
            self.centered_geometry(self.notch_width, self.collapsed_height)
        )

        # Background container
        self.background_widget = QWidget(self)
        self.update_background_style()

        # Create layout for background widget
        self.background_layout = QHBoxLayout(self.background_widget)
        self.background_layout.setContentsMargins(15, 5, 15, 5)
        self.background_layout.setSpacing(10)

        # Time label
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.time_label.setStyleSheet(
            "color: white; background-color: rgba(0, 0, 0, 50); border-radius: 5px; padding: 2px 5px;"
        )
        font = QFont("Segoe UI", 10, QFont.Bold)
        self.time_label.setFont(font)
        # Remove fixed width to allow dynamic sizing
        # self.time_label.setFixedWidth(80)

        # Info label
        self.info_label = QLabel()
        self.info_label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        self.update_text_style()
        font = QFont("Segoe UI", 12, QFont.Normal)
        self.info_label.setFont(font)

        # Options button
        self.options_button = QPushButton()
        self.options_button.setIcon(
            self.style().standardIcon(QStyle.SP_DialogYesButton)
        )
        self.options_button.setStyleSheet("background: transparent;")
        self.options_button.setIconSize(QSize(24, 24))
        self.options_button.clicked.connect(self.open_options)
        self.options_button.hide()  # Hide initially

        # Add widgets to layout
        self.background_layout.addWidget(self.time_label)
        self.background_layout.addWidget(self.info_label)
        self.background_layout.addStretch()
        self.background_layout.addWidget(self.options_button)

        # Delete box
        self.delete_box = QLabel("DELETE", self.background_widget)
        self.delete_box.setAlignment(Qt.AlignCenter)
        self.delete_box.setStyleSheet("""
            color: red;
            border: 4px dashed red;
            font-size: 28px;
            font-weight: bold;
            background-color: rgba(255, 0, 0, 50);
        """)
        self.delete_box.hide()

        # Enable drag and drop
        self.setAcceptDrops(True)

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
        bg_color = self.display_options.get(
            "bg_color", "rgba(33, 150, 243, 180)"
        )
        self.background_widget.setStyleSheet(f"""
            background-color: {bg_color};
            border-radius: 15px;
        """)

    def update_text_style(self):
        text_color = self.display_options.get("text_color", "white")
        self.info_label.setStyleSheet(f"color: {text_color}; padding-left: 5px;")

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
            self.resize_animation.setEndValue(
                self.centered_geometry(self.notch_width, self.expanded_height)
            )
            self.resize_animation.start()
            self.options_button.show()

    def collapse(self):
        if self.height() != self.collapsed_height:
            self.resize_animation.stop()
            self.resize_animation.setDuration(300)
            self.resize_animation.setStartValue(self.geometry())
            self.resize_animation.setEndValue(
                self.centered_geometry(self.notch_width, self.collapsed_height)
            )
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
        if self.delete_box.isVisible():
            # Position delete_box to cover info_label and options_button
            delete_start = self.time_label.width() + 10 if self.time_label.isVisible() else 0
            delete_width = self.width() - delete_start - 10  # Adjust as needed
            self.delete_box.setGeometry(
                delete_start,  # Start after time_label and some margin
                0,
                delete_width,
                self.height()
            )
        super().resizeEvent(event)

    def closeEvent(self, event):
        self.mouse_timer.stop()
        self.info_timer.stop()
        super().closeEvent(event)

    def open_options(self):
        options_dialog = OptionsDialog(self, self.display_options)

        # Connect signals to update colors immediately
        options_dialog.bg_color_changed.connect(self.on_bg_color_changed)
        options_dialog.text_color_changed.connect(self.on_text_color_changed)

        if options_dialog.exec_():
            self.display_options = options_dialog.get_options()
            self.update_display()
            # Colors are already updated via signals
        else:
            # If the dialog was canceled, do nothing or revert if needed
            pass

    def on_bg_color_changed(self, new_color):
        self.display_options["bg_color"] = new_color
        self.update_background_style()

    def on_text_color_changed(self, new_color):
        self.display_options["text_color"] = new_color
        self.update_text_style()

    def update_display(self):
        """Updates the information displayed on the info_label."""
        display_texts = []
        if self.display_options.get("time", False):
            current_time = QDateTime.currentDateTime().toString("hh:mm:ss")
            self.time_label.setText(current_time)
            self.time_label.show()
        else:
            self.time_label.hide()

        if self.display_options.get("cpu", False):
            cpu_usage = psutil.cpu_percent(interval=None)
            display_texts.append(f"CPU: {cpu_usage}%")
        if self.display_options.get("ram", False):
            ram_usage = psutil.virtual_memory().percent
            display_texts.append(f"RAM: {ram_usage}%")
        self.info_label.setText("   ".join(display_texts))  # Use spaces instead of '|'

    # Drag and Drop Events
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.show_delete_box()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.hide_delete_box()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_urls = event.mimeData().urls()
            for url in file_urls:
                file_path = url.toLocalFile()
                if file_path and os.path.exists(file_path):
                    # Confirm deletion
                    reply = QMessageBox.question(
                        self, 'Confirm Delete',
                        f'Are you sure you want to delete:\n{file_path}?',
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        try:
                            send2trash(file_path)
                            QMessageBox.information(
                                self, 'Deleted', f'File moved to recycle bin:\n{file_path}')
                        except Exception as e:
                            QMessageBox.critical(
                                self, 'Error', f'Failed to delete {file_path}:\n{str(e)}')
                else:
                    QMessageBox.warning(
                        self, 'File Not Found',
                        f'The file does not exist:\n{file_path}'
                    )
            self.hide_delete_box()
            event.acceptProposedAction()
        else:
            event.ignore()

    def show_delete_box(self):
        # Position the delete box to cover info_label and options_button
        time_label_width = self.time_label.width() if self.time_label.isVisible() else 0
        delete_start = time_label_width + 10 if time_label_width else 0
        delete_width = self.width() - delete_start - 10  # Adjust margin as needed
        self.delete_box.setGeometry(
            delete_start,  # Start after time_label and some margin
            0,
            delete_width,
            self.height()
        )
        self.delete_box.raise_()  # Bring delete_box to the front
        self.delete_box.show()

    def hide_delete_box(self):
        self.delete_box.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    notch = WinNotch()
    notch.show()
    sys.exit(app.exec_())
