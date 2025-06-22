import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QPushButton, 
                             QVBoxLayout, QWidget, QLabel, QTextEdit,
                             QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor
import win32gui
import win32ui
import win32con
import numpy as np
from PIL import Image
import io
import base64
import ollama
import json

class BalatroAdvisor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Balatro Advisor")
        self.setMinimumSize(800, 600)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                padding: 15px;
                font-size: 16px;
                border-radius: 5px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0a3d91;
            }
            QLabel {
                color: white;
                font-size: 16px;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
            }
        """)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Add title
        title = QLabel("Balatro Advisor")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 32px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        # Add description
        description = QLabel("Analyze your Balatro game state and get strategic advice")
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("font-size: 16px; margin-bottom: 30px;")
        layout.addWidget(description)
        
        # Create buttons
        self.analyze_hand_btn = QPushButton("Analyze Current Hand")
        self.analyze_shop_btn = QPushButton("Analyze Shop")
        self.analyze_state_btn = QPushButton("Analyze Game State")
        
        # Add buttons to layout
        layout.addWidget(self.analyze_hand_btn)
        layout.addWidget(self.analyze_shop_btn)
        layout.addWidget(self.analyze_state_btn)
        
        # Add output area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setMinimumHeight(200)
        layout.addWidget(self.output_area)
        
        # Connect buttons to functions
        self.analyze_hand_btn.clicked.connect(self.analyze_current_hand)
        self.analyze_shop_btn.clicked.connect(self.analyze_shop)
        self.analyze_state_btn.clicked.connect(self.analyze_game_state)
        
        # Add status bar
        self.statusBar().showMessage("Ready")
        
    def capture_game_window(self):
        """Capture the Balatro game window"""
        try:
            # Find the Balatro window
            hwnd = win32gui.FindWindow(None, "Balatro")
            if not hwnd:
                raise Exception("Balatro window not found")
            
            # Get window dimensions
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top
            
            # Create device context
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # Create bitmap object
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # Copy window content
            saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
            
            # Convert to PIL Image
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            im = Image.frombuffer(
                'RGB',
                (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                bmpstr, 'raw', 'BGRX', 0, 1)
            
            # Clean up
            win32gui.DeleteObject(saveBitMap.GetHandle())
            saveDC.DeleteDC()
            mfcDC.DeleteDC()
            win32gui.ReleaseDC(hwnd, hwndDC)
            
            return im
            
        except Exception as e:
            self.statusBar().showMessage(f"Error capturing window: {str(e)}")
            return None

    def get_ollama_analysis(self, image, prompt):
        """Get analysis from Ollama using Mixtral model"""
        try:
            # Convert image to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # Create the message for Ollama
            response = ollama.chat(
                model='mixtral',
                messages=[
                    {
                        'role': 'system',
                        'content': """You are an expert Balatro player and advisor. Your analysis should be:
                        1. Detailed and specific
                        2. Focused on strategic decision-making
                        3. Consider both immediate and long-term implications
                        4. Provide clear, actionable advice
                        5. Explain your reasoning
                        Format your response in clear sections with bullet points where appropriate.
                        Always end your analysis with '--- Analysis Complete ---'"""
                    },
                    {
                        'role': 'user',
                        'content': prompt,
                        'images': [img_str]
                    }
                ],
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'top_k': 40,
                    'num_ctx': 4096
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            return f"Error getting analysis: {str(e)}"

    def analyze_current_hand(self):
        """Analyze the current hand and provide advice"""
        self.statusBar().showMessage("Analyzing current hand...")
        try:
            # Capture game window
            screenshot = self.capture_game_window()
            if screenshot is None:
                raise Exception("Failed to capture game window")
            
            prompt = """Analyze this Balatro game state and provide detailed advice on the current hand.
            
            Please provide a comprehensive analysis covering:
            
            1. Current Hand Analysis:
               - List all cards in hand
               - Identify any special combinations or synergies
               - Evaluate the hand's potential scoring
            
            2. Joker Effects:
               - List all active jokers
               - Explain how they affect the current hand
               - Identify any powerful combinations
            
            3. Game State:
               - Current score and target
               - Cards remaining in deck
               - Any active tarot or planet effects
            
            4. Strategic Recommendations:
               - Best play options
               - Risk assessment
               - Alternative strategies
            
            Format your response in clear sections with bullet points for easy reading."""
            
            analysis = self.get_ollama_analysis(screenshot, prompt)
            self.output_area.setText(analysis)
            self.statusBar().showMessage("Analysis complete")
            
        except Exception as e:
            self.output_area.setText(f"Error: {str(e)}")
            self.statusBar().showMessage("Error occurred")

    def analyze_shop(self):
        """Analyze the shop and provide purchase recommendations"""
        self.statusBar().showMessage("Analyzing shop...")
        try:
            # Capture game window
            screenshot = self.capture_game_window()
            if screenshot is None:
                raise Exception("Failed to capture game window")
            
            prompt = """Analyze this Balatro shop and provide detailed purchase recommendations.
            
            Please provide a comprehensive analysis covering:
            
            1. Available Items:
               - List all jokers with their prices
               - List any tarot or planet cards
               - Note any special items or effects
            
            2. Current Resources:
               - Available money
               - Current deck composition
               - Active jokers and their effects
            
            3. Strategic Value:
               - Rate each item's value (High/Medium/Low)
               - Explain synergies with current setup
               - Consider long-term potential
            
            4. Purchase Recommendations:
               - Prioritized list of items to buy
               - Alternative options
               - Items to avoid and why
            
            Format your response in clear sections with bullet points for easy reading."""
            
            analysis = self.get_ollama_analysis(screenshot, prompt)
            self.output_area.setText(analysis)
            self.statusBar().showMessage("Analysis complete")
            
        except Exception as e:
            self.output_area.setText(f"Error: {str(e)}")
            self.statusBar().showMessage("Error occurred")

    def analyze_game_state(self):
        """Analyze the overall game state and provide strategic advice"""
        self.statusBar().showMessage("Analyzing game state...")
        try:
            # Capture game window
            screenshot = self.capture_game_window()
            if screenshot is None:
                raise Exception("Failed to capture game window")
            
            prompt = """Analyze this Balatro game state and provide comprehensive strategic advice.
            
            Please provide a detailed analysis covering:
            
            1. Overall Game Progress:
               - Current round/level
               - Score and win conditions
               - Available resources
            
            2. Deck Composition:
               - Current deck strength
               - Key cards and combinations
               - Areas for improvement
            
            3. Active Effects:
               - Joker synergies and combinations
               - Tarot and planet card effects
               - Special conditions or modifiers
            
            4. Strategic Outlook:
               - Short-term goals (next 1-2 rounds)
               - Long-term strategy
               - Risk assessment
            
            5. Recommendations:
               - Immediate actions to take
               - Shop priorities
               - Deck building suggestions
            
            Format your response in clear sections with bullet points for easy reading."""
            
            analysis = self.get_ollama_analysis(screenshot, prompt)
            self.output_area.setText(analysis)
            self.statusBar().showMessage("Analysis complete")
            
        except Exception as e:
            self.output_area.setText(f"Error: {str(e)}")
            self.statusBar().showMessage("Error occurred")

def main():
    app = QApplication(sys.argv)
    window = BalatroAdvisor()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 