#!/usr/bin/env python3
import sys
import os
import datetime
import pyperclip
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QTextEdit, QFileDialog, QMessageBox,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox, QProgressBar,
    QComboBox, QFrame, QSplitter, QTabWidget, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette

from config_manager import ConfigManager
from openai_service import OpenAIService

# Application stylesheet
STYLESHEET = """
QMainWindow, QDialog {
    background-color: #f5f5f7;
}

QLabel {
    font-size: 14px;
    color: #333333;
}

QLabel#title {
    font-size: 18px;
    font-weight: bold;
    color: #1a1a1a;
    margin-bottom: 10px;
}

QLabel#section_title {
    font-size: 16px;
    font-weight: bold;
    color: #1a1a1a;
    padding: 5px 0;
}

QPushButton {
    background-color: #0071e3;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: bold;
    min-width: 100px;
}

QPushButton:hover {
    background-color: #0077ed;
}

QPushButton:pressed {
    background-color: #005bbf;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

QPushButton#secondary {
    background-color: #e0e0e0;
    color: #333333;
}

QPushButton#secondary:hover {
    background-color: #d0d0d0;
}

QPushButton#secondary:pressed {
    background-color: #c0c0c0;
}

QTextEdit {
    background-color: white;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 8px;
    font-size: 14px;
    selection-background-color: #b2d7ff;
}

QProgressBar {
    border: 1px solid #cccccc;
    border-radius: 4px;
    text-align: center;
    background-color: #f0f0f0;
}

QProgressBar::chunk {
    background-color: #0071e3;
    width: 10px;
    margin: 0.5px;
}

QComboBox {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 5px;
    min-width: 6em;
    background-color: white;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left-width: 1px;
    border-left-color: #cccccc;
    border-left-style: solid;
}

QLineEdit {
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 8px;
    background-color: white;
}

QFrame#separator {
    background-color: #dddddd;
    max-height: 1px;
    margin: 10px 0;
}

QFrame#card {
    background-color: white;
    border-radius: 8px;
    padding: 15px;
    margin: 5px 0;
}
"""


class ApiKeyDialog(QDialog):
    """Dialog for setting the OpenAI API key."""
    
    def __init__(self, config_manager, openai_service, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.openai_service = openai_service
        self.setWindowTitle("OpenAI API Settings")
        self.setMinimumWidth(500)
        
        layout = QFormLayout(self)
        
        # API Key input
        self.api_key_input = QLineEdit(self.config_manager.get_openai_api_key())
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("OpenAI API Key:", self.api_key_input)
        
        # Show/Hide password button
        self.show_hide_button = QPushButton("Show")
        self.show_hide_button.setCheckable(True)
        self.show_hide_button.clicked.connect(self.toggle_password_visibility)
        layout.addRow("", self.show_hide_button)
        
        # Whisper model selection
        self.whisper_model_combo = QComboBox()
        self.whisper_model_combo.addItems(self.openai_service.get_available_whisper_models())
        current_whisper_model = self.config_manager.get_whisper_model()
        self.whisper_model_combo.setCurrentText(current_whisper_model)
        layout.addRow("Transcription Model:", self.whisper_model_combo)
        
        # Text model selection
        self.text_model_combo = QComboBox()
        self.text_model_combo.addItems(self.openai_service.get_available_text_models())
        current_text_model = self.config_manager.get_text_model()
        self.text_model_combo.setCurrentText(current_text_model)
        layout.addRow("Text Processing Model:", self.text_model_combo)
        
        # Model info
        whisper_info = QLabel("Note: gpt-4o-transcribe and gpt-4o-mini-transcribe are newer models that may provide better transcription quality.")
        whisper_info.setWordWrap(True)
        layout.addRow("", whisper_info)
        
        # Info label
        info_label = QLabel("Your settings are stored locally in ~/.config/whisper-converter/")
        info_label.setWordWrap(True)
        layout.addRow("", info_label)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)
    
    def toggle_password_visibility(self):
        """Toggle between showing and hiding the API key."""
        if self.show_hide_button.isChecked():
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_hide_button.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_hide_button.setText("Show")
    
    def get_api_key(self):
        """Get the entered API key."""
        return self.api_key_input.text()
    
    def get_whisper_model(self):
        """Get the selected Whisper model."""
        return self.whisper_model_combo.currentText()
    
    def get_text_model(self):
        """Get the selected text model."""
        return self.text_model_combo.currentText()


class WorkerThread(QThread):
    """Worker thread for running time-consuming operations."""
    
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    progress = pyqtSignal(int)
    
    def __init__(self, task_type, func, *args, **kwargs):
        super().__init__()
        self.task_type = task_type
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        """Run the function in a separate thread."""
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize configuration and services
        self.config_manager = ConfigManager()
        self.openai_service = OpenAIService(self.config_manager.get_openai_api_key())
        
        # Set up UI
        self.setWindowTitle("Whisper Converter")
        self.setMinimumSize(800, 600)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # File selection section
        self.setup_file_selection()
        
        # Transcribed text section
        self.setup_transcribed_text()
        
        # Cleaned text section
        self.setup_cleaned_text()
        
        # Title generation section
        self.setup_title_generation()
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Variables to store data
        self.selected_file_path = None
        self.generated_title = None
        self.generated_filename = None
    
    def setup_file_selection(self):
        """Set up the file selection section."""
        file_section = QWidget()
        file_layout = QHBoxLayout(file_section)
        
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setWordWrap(True)
        
        select_file_button = QPushButton("Select Audio File")
        select_file_button.clicked.connect(self.select_audio_file)
        
        settings_button = QPushButton("Settings")
        settings_button.clicked.connect(self.open_settings)
        
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(select_file_button)
        file_layout.addWidget(settings_button)
        
        self.main_layout.addWidget(file_section)
        
        # Model info label
        self.model_info_label = QLabel(f"Using transcription model: {self.config_manager.get_whisper_model()}")
        self.main_layout.addWidget(self.model_info_label)
        
        # Transcribe button
        self.transcribe_button = QPushButton("Transcribe")
        self.transcribe_button.clicked.connect(self.transcribe_audio)
        self.transcribe_button.setEnabled(False)
        
        self.main_layout.addWidget(self.transcribe_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.main_layout.addWidget(self.progress_bar)
    
    def setup_transcribed_text(self):
        """Set up the transcribed text section."""
        # Label
        self.main_layout.addWidget(QLabel("Transcribed Text:"))
        
        # Text edit
        self.transcribed_text = QTextEdit()
        self.transcribed_text.setReadOnly(False)
        self.transcribed_text.setPlaceholderText("Transcribed text will appear here...")
        self.main_layout.addWidget(self.transcribed_text)
        
        # Buttons for transcribed text
        transcribed_buttons = QWidget()
        transcribed_buttons_layout = QHBoxLayout(transcribed_buttons)
        
        clear_transcribed_button = QPushButton("Clear")
        clear_transcribed_button.clicked.connect(lambda: self.transcribed_text.clear())
        
        copy_transcribed_button = QPushButton("Copy to Clipboard")
        copy_transcribed_button.clicked.connect(lambda: self.copy_to_clipboard(self.transcribed_text.toPlainText()))
        
        download_transcribed_button = QPushButton("Download")
        download_transcribed_button.clicked.connect(lambda: self.download_text(self.transcribed_text.toPlainText(), "transcribed"))
        
        clean_text_button = QPushButton("Clean This Text")
        clean_text_button.clicked.connect(self.clean_text)
        
        transcribed_buttons_layout.addWidget(clear_transcribed_button)
        transcribed_buttons_layout.addWidget(copy_transcribed_button)
        transcribed_buttons_layout.addWidget(download_transcribed_button)
        transcribed_buttons_layout.addWidget(clean_text_button)
        
        self.main_layout.addWidget(transcribed_buttons)
    
    def setup_cleaned_text(self):
        """Set up the cleaned text section."""
        # Label
        self.main_layout.addWidget(QLabel("Cleaned Text:"))
        
        # Text edit
        self.cleaned_text = QTextEdit()
        self.cleaned_text.setReadOnly(False)
        self.cleaned_text.setPlaceholderText("Cleaned text will appear here...")
        self.main_layout.addWidget(self.cleaned_text)
        
        # Buttons for cleaned text
        cleaned_buttons = QWidget()
        cleaned_buttons_layout = QHBoxLayout(cleaned_buttons)
        
        clear_cleaned_button = QPushButton("Clear")
        clear_cleaned_button.clicked.connect(lambda: self.cleaned_text.clear())
        
        copy_cleaned_button = QPushButton("Copy to Clipboard")
        copy_cleaned_button.clicked.connect(lambda: self.copy_to_clipboard(self.cleaned_text.toPlainText()))
        
        download_cleaned_button = QPushButton("Download")
        download_cleaned_button.clicked.connect(lambda: self.download_text(self.cleaned_text.toPlainText(), "cleaned"))
        
        cleaned_buttons_layout.addWidget(clear_cleaned_button)
        cleaned_buttons_layout.addWidget(copy_cleaned_button)
        cleaned_buttons_layout.addWidget(download_cleaned_button)
        
        self.main_layout.addWidget(cleaned_buttons)
    
    def setup_title_generation(self):
        """Set up the title generation section."""
        generate_title_button = QPushButton("Generate Title")
        generate_title_button.clicked.connect(self.generate_title)
        
        self.title_label = QLabel("Title: Not generated yet")
        self.title_label.setWordWrap(True)
        
        self.main_layout.addWidget(generate_title_button)
        self.main_layout.addWidget(self.title_label)
    
    def select_audio_file(self):
        """Open a file dialog to select an audio file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            str(Path.home()),
            "Audio Files (*.mp3 *.wav *.m4a *.flac *.ogg *.mp4);;All Files (*)"
        )
        
        if file_path:
            self.selected_file_path = file_path
            self.file_path_label.setText(f"Selected: {os.path.basename(file_path)}")
            self.transcribe_button.setEnabled(True)
    
    def open_settings(self):
        """Open the settings dialog."""
        dialog = ApiKeyDialog(self.config_manager, self.openai_service, self)
        if dialog.exec():
            # Get values from dialog
            api_key = dialog.get_api_key()
            whisper_model = dialog.get_whisper_model()
            text_model = dialog.get_text_model()
            
            # Update config and service
            self.config_manager.set_openai_api_key(api_key)
            self.config_manager.set_whisper_model(whisper_model)
            self.config_manager.set_text_model(text_model)
            self.openai_service.set_api_key(api_key)
            
            # Update UI
            self.model_info_label.setText(f"Using transcription model: {whisper_model}")
            
            self.statusBar().showMessage("Settings updated", 3000)
    
    def transcribe_audio(self):
        """Transcribe the selected audio file."""
        if not self.selected_file_path:
            return
        
        if not self.config_manager.get_openai_api_key():
            QMessageBox.warning(
                self,
                "API Key Required",
                "Please set your OpenAI API key in Settings before transcribing."
            )
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.statusBar().showMessage("Transcribing audio...")
        self.transcribe_button.setEnabled(False)
        
        # Get selected model
        whisper_model = self.config_manager.get_whisper_model()
        
        # Start worker thread
        self.worker = WorkerThread(
            "transcribe",
            self.openai_service.transcribe_audio,
            self.selected_file_path,
            whisper_model
        )
        self.worker.finished.connect(self.on_transcription_complete)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_transcription_complete(self, text):
        """Handle completion of transcription."""
        self.transcribed_text.setPlainText(text)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.transcribe_button.setEnabled(True)
        self.statusBar().showMessage("Transcription complete", 3000)
    
    def clean_text(self):
        """Clean the transcribed text."""
        text = self.transcribed_text.toPlainText()
        if not text:
            QMessageBox.warning(
                self,
                "No Text",
                "Please transcribe an audio file first."
            )
            return
        
        if not self.config_manager.get_openai_api_key():
            QMessageBox.warning(
                self,
                "API Key Required",
                "Please set your OpenAI API key in Settings before cleaning text."
            )
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.statusBar().showMessage("Cleaning text...")
        
        # Get selected model
        text_model = self.config_manager.get_text_model()
        
        # Start worker thread
        self.worker = WorkerThread(
            "clean",
            self.openai_service.clean_text,
            text,
            text_model
        )
        self.worker.finished.connect(self.on_cleaning_complete)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_cleaning_complete(self, text):
        """Handle completion of text cleaning."""
        self.cleaned_text.setPlainText(text)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.statusBar().showMessage("Text cleaning complete", 3000)
    
    def generate_title(self):
        """Generate a title for the transcribed text."""
        text = self.transcribed_text.toPlainText()
        if not text:
            QMessageBox.warning(
                self,
                "No Text",
                "Please transcribe an audio file first."
            )
            return
        
        if not self.config_manager.get_openai_api_key():
            QMessageBox.warning(
                self,
                "API Key Required",
                "Please set your OpenAI API key in Settings before generating a title."
            )
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.statusBar().showMessage("Generating title...")
        
        # Get selected model
        text_model = self.config_manager.get_text_model()
        
        # Start worker thread
        self.worker = WorkerThread(
            "title",
            self.openai_service.generate_title,
            text,
            text_model
        )
        self.worker.finished.connect(self.on_title_generation_complete)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def on_title_generation_complete(self, result):
        """Handle completion of title generation."""
        title, filename = result
        self.generated_title = title
        self.generated_filename = filename
        
        self.title_label.setText(f"Title: {title}")
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.statusBar().showMessage("Title generation complete", 3000)
    
    def on_error(self, error_message):
        """Handle errors from worker threads."""
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.transcribe_button.setEnabled(True)
        self.statusBar().showMessage("Error", 3000)
        
        QMessageBox.critical(
            self,
            "Error",
            error_message
        )
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        if not text:
            return
        
        pyperclip.copy(text)
        self.statusBar().showMessage("Copied to clipboard", 3000)
    
    def download_text(self, text, text_type):
        """Download text to a file."""
        if not text:
            return
        
        # Determine filename
        if self.generated_filename and text_type == "cleaned":
            default_filename = f"{self.generated_filename}-cleaned.txt"
        elif self.generated_filename and text_type == "transcribed":
            default_filename = f"{self.generated_filename}.txt"
        else:
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            default_filename = f"transcript-{timestamp}-{text_type}.txt"
        
        # Open save dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Text",
            str(Path.home() / default_filename),
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.statusBar().showMessage(f"Saved to {file_path}", 3000)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Error saving file: {str(e)}"
                )


def main():
    """Main entry point for the application."""
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
