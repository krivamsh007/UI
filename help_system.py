from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
import os

class HelpDialog(QDialog):
    def __init__(self, help_text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout(self)
        self.text_browser = QTextBrowser()
        self.text_browser.setText(help_text)
        layout.addWidget(self.text_browser)
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

def get_help_section(section_title, help_file="HELP.md"):
    # Compute absolute path relative to this file's location.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    help_file_path = os.path.join(script_dir, help_file)
    
    help_content = ""
    try:
        with open(help_file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        capture = False
        for line in lines:
            if line.strip().startswith("## "):
                # When encountering a header, check if we should start or stop capturing.
                if capture and section_title.lower() not in line.strip().lower():
                    break
                if section_title.lower() in line.strip().lower():
                    capture = True
                    continue
            if capture:
                help_content += line
        if not help_content:
            help_content = "Help section not found for: " + section_title
    except Exception as e:
        help_content = f"Error loading help content: {e}"
    return help_content
